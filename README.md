# 🔥 Fire-Sale Watch

A local dashboard that flags big index funds, ETFs, and mutual funds trading at a
deep discount from their highs — Buffett's *"be greedy when others are fearful"* moment.
A cron job refreshes it automatically; you open it anytime.

## Setup from scratch

You only need this the first time (or on a new machine). Requires **Python 3.10+**.

```bash
# 1. Get the code
git clone https://github.com/goatvram/index_fund_watch_dashboard.git
cd index_fund_watch_dashboard

# 2. Create an isolated Python environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Build the dashboard for the first time
./update.sh

# 5. Open it
./open.sh
```

That's it — `dashboard.html` is now generated and openable. To keep it fresh
automatically, install the cron job (see **The automatic update** below).

> **WSL / Windows note:** `open.sh` launches Chrome on Windows from WSL. On macOS
> or Linux, just open `dashboard.html` directly in any browser.

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
| `requirements.txt` | Python dependencies (`pip install -r`) |
| `data.json` | Latest computed data (generated, git-ignored) |
| `dashboard.html` | The rendered dashboard (generated, git-ignored) |
| `.venv/` | Python environment with yfinance (git-ignored) |

## Contributing

Contributions are welcome — adding tickers, improving the dashboard, or fixing
bugs. See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the dev setup, workflow, and
conventions. In short: fork, branch off `main`, run `./update.sh` to test your
change end-to-end, then open a pull request. Generated files (`data.json`,
`dashboard.html`, logs) are git-ignored — don't commit them.

## Notes
- Data source: Yahoo Finance via the `yfinance` library. Free, no API key.
- Drawdowns use dividend-adjusted closing prices.
- This is an educational tool, **not investment advice.** A fund can be cheap for a
  reason — do your own homework before being greedy.
