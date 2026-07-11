# 🔥 Fire-Sale Watch

A local dashboard that flags big index funds, ETFs, and mutual funds trading at a
deep discount from their highs — Buffett's *"be greedy when others are fearful"* moment.
A cron job refreshes it automatically; you open it anytime.

## Open the dashboard
```bash
./open.sh
```
Or just open `dashboard.html` in any browser. No server needed — the data is baked in.
On the page you also get **live sliders** (min/max drop, 52-week vs all-time high,
search) to explore beyond your saved criteria without re-fetching.

## Change your criteria
Edit **`config.yaml`** — it's commented and plain-English. You can change:
- `reference_high` — measure the discount from the `52w` (52-week) or `ath` (all-time) high
- `min_drawdown_pct` / `max_drawdown_pct` — the "fire sale" band (e.g. 40–100)
- `min_assets_usd` — only show big funds
- `universe` — the list of funds to watch (add/remove tickers freely)

The cron job reads `config.yaml` fresh on every run, so changes are picked up
automatically on the next update. To refresh immediately:
```bash
./update.sh
```

## The automatic update (cron)
A job runs **weekdays at 6:30 PM local time** (after US market close, once fund NAVs
settle) and rebuilds the dashboard.

- Install / refresh it:  `./setup_cron.sh`
- See it:                `crontab -l`
- Logs:                  `cron.log` and `update.log`
- Remove it:             `crontab -l | grep -v fire-sale-watch | crontab -`

To change the schedule, edit the time in `setup_cron.sh` and re-run it.

## Files
| File | What it is |
|------|------------|
| `config.yaml` | **Your settings** — criteria + fund list (edit this) |
| `dashboard.html` | The dashboard (generated; open this) |
| `fetch_data.py` | Fetches data, computes drawdowns, builds the dashboard |
| `update.sh` | Runs one refresh (used by cron) |
| `setup_cron.sh` | Installs the daily schedule |
| `open.sh` | Opens the dashboard in your browser |
| `data.json` | Latest computed data (generated) |
| `.venv/` | Python environment with yfinance |

## Notes
- Data source: Yahoo Finance via the `yfinance` library. Free, no API key.
- Drawdowns use dividend-adjusted closing prices.
- This is an educational tool, **not investment advice.** A fund can be cheap for a
  reason — do your own homework before being greedy.
