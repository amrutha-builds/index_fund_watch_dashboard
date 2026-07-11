# Contributing to Fire-Sale Watch

Thanks for helping improve Fire-Sale Watch! This is a small, self-contained Python
project — no server, no database, no build step. Contributions of all sizes are
welcome, from adding a ticker to reworking the dashboard UI.

## Ground rules

- **Be kind and constructive.** Assume good intent in reviews and issues.
- **Keep it simple.** This tool deliberately has few moving parts. Prefer the
  smallest change that solves the problem over a clever one.
- **Not investment advice.** Nothing here should present itself as financial
  advice. Keep the educational framing.

## Getting set up for development

See the **Setup from scratch** section of [`README.md`](README.md) to create the
virtualenv and install dependencies. In short:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Development workflow

1. **Fork** the repo and create a branch off `main`:
   ```bash
   git checkout -b my-change
   ```
2. **Make your change.** Keep commits focused — one logical change per commit.
3. **Test it end-to-end** by running a real refresh and opening the dashboard:
   ```bash
   ./update.sh      # fetches data, rebuilds dashboard.html
   ./open.sh        # opens it in the browser
   ```
   Check `update.log` for warnings and confirm the funds you touched render
   correctly.
4. **Commit** with a clear message (see below).
5. **Push** your branch and open a **pull request** against `main`, describing
   what changed and why.

## What lives where

| File | Edit this when… |
|------|-----------------|
| `config.yaml` | Adding/removing tickers or changing default criteria |
| `fetch_data.py` | Changing what data is fetched or how metrics are computed |
| `dashboard_template.html` | Changing the dashboard's look, layout, or sliders |
| `update.sh` / `setup_cron.sh` / `open.sh` | Changing how it runs or schedules |
| `requirements.txt` | Adding/upgrading a Python dependency |

**Do not commit generated files.** `data.json`, `dashboard.html`, and the `*.log`
files are produced by running the tool and are `.gitignore`d. If you change the
template, commit `dashboard_template.html`, not the rendered `dashboard.html`.

## Adding a fund to the default universe

Add the US-listed ticker to the appropriate section of `config.yaml`, with an
inline comment naming its industry/sector — the fetcher reads that comment as the
fund's label:

```yaml
  - SCHD     # Dividend equity
```

Run `./update.sh` and confirm it fetches cleanly (Yahoo Finance occasionally rate-
limits; the fetcher already retries a dropped ticker once).

## Commit messages

- Use the imperative mood: "Add SCHD to universe", not "Added" / "Adds".
- Keep the summary line under ~72 characters.
- Add a body if the *why* isn't obvious from the summary.

## Code style

- Python targets **3.10+** (the code uses `X | None` type hints). Match the
  existing style: type hints on function signatures, short docstrings explaining
  intent, and `log(...)` for anything worth seeing in `update.log`.
- No formatter is enforced, but keep lines readable and imports tidy.

## Reporting bugs / ideas

Open a GitHub issue with:
- What you expected vs. what happened.
- Relevant lines from `update.log` (redact anything private).
- Your OS and Python version (`python --version`).

## Data source note

Data comes from Yahoo Finance via the free `yfinance` library — no API key, but no
uptime or accuracy guarantee. If a fund stops fetching, it's usually an upstream
Yahoo change; check whether the ticker symbol still resolves on finance.yahoo.com.
