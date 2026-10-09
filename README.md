# GitHub Open Source Radar

A lightweight, locally hosted open-source growth leaderboard. Five rolling windows: **7d, 30d, 90d, 6m (182 days), 1y (365 days)**. Ranking by newly-added stars, **not lifetime star totals**.

**Important:** The leaderboard ranks a sampled candidate pool, **not all GitHub repositories**. Never label this as a complete/global Top 20 until coverage is independently audited. API buckets measure star additions, not net change after unstars; growth rate uses current stars minus added stars as an approximation.

## Run (Python 3.10+, no pip install required)

```bash
# PowerShell, Linux, macOS: set GITHUB_TOKEN in your shell or environment first.
python -m radar.sync --limit 30
python -m radar.server
# Open http://127.0.0.1:8765
```

Windows PowerShell:
```powershell
$env:GITHUB_TOKEN = 'YOUR_TOKEN' # do NOT commit the token
py -m radar.sync --limit 30
py -m radar.server
```

Run offline tests:
```bash
python -m unittest discover -s tests -v
```

## Routes

- `GET /` — responsive web page
- `GET /api/rankings?window=30d&language=Python` — ordered JSON results, sampled coverage disclosure, run metadata

## Data pipeline

1. GitHub Repository Search chooses a diversified sample (global popular, created in the past year, recently pushed, agent-tagged).
2. Fetch official `GET /repos/{owner}/{repo}/stargazers/history` weekly/daily buckets.
3. Aggregate daily counts into five fixed windows; cache repository metadata and metrics in SQLite.
4. The browser reads rankings from local JSON API, never calls GitHub directly.

Known limitations: candidate sampling biases popular repositories ; for better longitudinal coverage diversify search strata, paginate and persist candidate pool. Current UI has no project detail chart or scheduled jobs. Rate limits matter for large candidate sets; no aggressive API retries. The 1-year window requires about 54 weeks of data to cover boundary variation. Current daily bucket dates follow GitHub week timestamps and are UTC approximations; GitHub cautions that its week/day boundaries may not align with UTC.

## Research and API sources

- [Official GitHub star history endpoint](https://docs.github.com/en/rest/activity/starring)
- [GitHub API launch announcement (2026-09-04)](https://github.blog/changelog/2026-09-04-new-api-endpoint-provides-privacy-safe-star-history-data/)
- [Star History OSS](https://github.com/star-history/star-history)

## Next phases

- Phase B: better discovery including fresh breakout projects, cursor/pagination, checkpointed jobs, configurable snapshot date, API cost quota guard, historical quality audit, language/topic filters.
- Phase C: repository detail trend chart, watchlists, AI summary, scheduled jobs, Docker and deployment.
