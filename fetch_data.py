#!/usr/bin/env python3
"""
Fire-Sale Watch — data fetcher.

Reads config.yaml, pulls price history for every fund in your universe via
yfinance, computes how far each one is below its 52-week high and its
all-time high, then writes:

  * data.json      — raw computed metrics for every fund
  * dashboard.html — a self-contained dashboard you can open in any browser

Run by the cron job daily, or by hand anytime:  ./update.sh
"""

import datetime as dt
import json
import os
import sys
import traceback

import pandas as pd
import yaml
import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.yaml")
DATA_PATH = os.path.join(HERE, "data.json")
HTML_PATH = os.path.join(HERE, "dashboard.html")
TEMPLATE_PATH = os.path.join(HERE, "dashboard_template.html")
LOG_PATH = os.path.join(HERE, "update.log")


def log(msg: str) -> None:
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, "a") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def parse_industries(path: str) -> dict:
    """
    Harvest the human-written industry label from each universe line's inline
    comment (YAML drops comments, so read the raw file). A line like

        - XLE      # Energy

    yields {"XLE": "Energy"}. Section-header comments ("# --- Sector SPDRs ---")
    start with '#', not '- ', so they're skipped.
    """
    labels: dict[str, str] = {}
    try:
        with open(path) as fh:
            for line in fh:
                s = line.strip()
                if not s.startswith("- ") or "#" not in s:
                    continue
                sym, _, comment = s[2:].partition("#")
                sym, comment = sym.strip().upper(), comment.strip()
                if sym and comment:
                    labels[sym] = comment
    except OSError:
        pass
    return labels


def load_config() -> dict:
    with open(CONFIG_PATH) as fh:
        cfg = yaml.safe_load(fh) or {}
    cfg.setdefault("criteria", {})
    cfg.setdefault("settings", {})
    cfg.setdefault("universe", [])
    c = cfg["criteria"]
    c.setdefault("reference_high", "52w")
    c.setdefault("min_drawdown_pct", 40)
    c.setdefault("max_drawdown_pct", 100)
    c.setdefault("min_assets_usd", 0)
    cfg["settings"].setdefault("history_period", "max")
    # tickers may carry inline "# comments" already stripped by YAML; normalise
    cfg["industries"] = parse_industries(CONFIG_PATH)
    cfg["universe"] = [str(t).strip().upper() for t in cfg["universe"] if str(t).strip()]
    return cfg


def get_assets(ticker: str) -> float | None:
    """Best-effort assets-under-management / net assets in USD. May be None."""
    try:
        info = yf.Ticker(ticker).get_info()
    except Exception:
        return None
    for key in ("totalAssets", "netAssets", "marketCap"):
        val = info.get(key)
        if val:
            try:
                return float(val)
            except (TypeError, ValueError):
                continue
    return None


def get_meta(ticker: str) -> dict:
    """Best-effort name + type + category. Falls back gracefully if Yahoo is stingy."""
    name, qtype, category = ticker, "", ""
    try:
        info = yf.Ticker(ticker).get_info()
        name = info.get("longName") or info.get("shortName") or ticker
        qtype = info.get("quoteType") or ""
        category = info.get("category") or ""
    except Exception:
        pass
    return {"name": name, "type": qtype, "category": category}


def compute(tickers: list[str], period: str, industries: dict | None = None) -> list[dict]:
    industries = industries or {}
    log(f"Downloading price history for {len(tickers)} funds (period={period})...")
    # One batched request is gentler on Yahoo's rate limits than many small ones.
    raw = yf.download(
        tickers,
        period=period,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True,
    )

    results = []
    for t in tickers:
        try:
            close = (raw["Close"] if len(tickers) == 1 else raw[t]["Close"]).dropna()
        except Exception as exc:
            close = None
            log(f"  {t}: ERROR {exc!r}")
        results.append(metrics_from_close(t, close, industries.get(t)))

    # Retry pass: Yahoo intermittently drops a ticker from a batched download.
    # Re-fetch any miss individually once so a transient gap self-heals.
    missed = [r["ticker"] for r in results if not r.get("ok")]
    if missed:
        log(f"Retrying {len(missed)} fund(s) individually: {', '.join(missed)}")
        for i, r in enumerate(results):
            if r.get("ok"):
                continue
            t = r["ticker"]
            try:
                close = yf.Ticker(t).history(period=period, auto_adjust=True)["Close"].dropna()
            except Exception as exc:
                close = None
                log(f"  {t}: retry ERROR {exc!r}")
            results[i] = metrics_from_close(t, close, industries.get(t))
    return results


HORIZONS_YEARS = (1, 3, 5, 10)
GROWTH_BASE = 100_000.0  # hypothetical $100K invested `years` ago


def horizon_metrics(close, last: float) -> tuple[dict, dict]:
    """
    For each horizon in HORIZONS_YEARS, compute the annualised return (CAGR, %)
    and what $100K invested that long ago would be worth today.

    Returns ({"5": cagr%|None, ...}, {"5": growth$|None, ...}). A horizon is
    None when the price history doesn't reach back that far.
    """
    cagr: dict[str, float | None] = {}
    growth: dict[str, float | None] = {}
    last_date = close.index.max()
    for years in HORIZONS_YEARS:
        key = str(years)
        cutoff = last_date - pd.Timedelta(days=round(years * 365.25))
        past = close[close.index <= cutoff]
        start = float(past.iloc[-1]) if len(past) else 0.0
        if not past.size or start <= 0:
            cagr[key] = growth[key] = None
            continue
        yrs = (last_date - past.index[-1]).days / 365.25
        ratio = last / start
        cagr[key] = round((ratio ** (1.0 / yrs) - 1.0) * 100.0, 1) if yrs > 0 else None
        growth[key] = round(GROWTH_BASE * ratio)
    return cagr, growth


def metrics_from_close(ticker: str, close, industry_label: str | None = None) -> dict:
    """Turn a price-close series into the metrics dict, or an error record."""
    if close is None or len(close) == 0:
        log(f"  {ticker}: no data")
        return {"ticker": ticker, "ok": False, "error": "no data",
                "industry": industry_label or ""}
    last = float(close.iloc[-1])
    as_of = close.index[-1].strftime("%Y-%m-%d")
    cutoff = close.index.max() - pd.Timedelta(days=365)
    hi_52 = float(close[close.index >= cutoff].max())
    hi_ath = float(close.max())
    dd_52 = (last / hi_52 - 1.0) * 100.0 if hi_52 else 0.0
    dd_ath = (last / hi_ath - 1.0) * 100.0 if hi_ath else 0.0
    cagr, growth = horizon_metrics(close, last)
    meta = get_meta(ticker)
    assets = get_assets(ticker)
    # Prefer the curated config.yaml label; fall back to Yahoo's fund category.
    industry = industry_label or meta["category"] or ""
    log(f"  {ticker}: last={last:.2f}  52w={dd_52:+.1f}%  ath={dd_ath:+.1f}%"
        f"  cagr1={cagr['1']}")
    return {
        "ticker": ticker,
        "ok": True,
        "name": meta["name"],
        "type": meta["type"],
        "industry": industry,
        "last": round(last, 2),
        "high_52w": round(hi_52, 2),
        "high_ath": round(hi_ath, 2),
        "drawdown_52w": round(dd_52, 1),
        "drawdown_ath": round(dd_ath, 1),
        "cagr": cagr,
        "growth_100k": growth,
        "assets_usd": assets,
        "as_of": as_of,
    }


def render_html(payload: dict) -> None:
    with open(TEMPLATE_PATH) as fh:
        template = fh.read()
    embedded = json.dumps(payload, separators=(",", ":"))
    html = template.replace("/*__DATA__*/null", embedded)
    with open(HTML_PATH, "w") as fh:
        fh.write(html)


def main() -> int:
    try:
        cfg = load_config()
    except Exception as exc:
        log(f"FATAL: could not read config.yaml: {exc!r}")
        return 1

    if not cfg["universe"]:
        log("FATAL: universe is empty in config.yaml")
        return 1

    funds = compute(cfg["universe"], cfg["settings"]["history_period"], cfg["industries"])
    ok = [f for f in funds if f.get("ok")]

    payload = {
        "generated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "criteria": cfg["criteria"],
        "funds": funds,
        "count_ok": len(ok),
        "count_total": len(funds),
    }

    with open(DATA_PATH, "w") as fh:
        json.dump(payload, fh, indent=2)
    log(f"Wrote {DATA_PATH} ({len(ok)}/{len(funds)} funds)")

    render_html(payload)
    log(f"Wrote {HTML_PATH}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log("UNCAUGHT:\n" + traceback.format_exc())
        sys.exit(1)
