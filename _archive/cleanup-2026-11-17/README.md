# Workspace cleanup — 17 November 2026

All existing changes were committed and pushed **before** this cleanup:

| Repository | Published checkpoint |
| --- | --- |
| Parent | `f5c4a0a27a53a814b21d0289369527ce027c6dab` |
| Backend | `4b27b2084256cff4d52344ed9b978e853bc2dcc7` |
| Frontend | `6e6bb63406d9d0bfc15bce69de1042fecff877ba` |
| NLP_Service | `06cdbd6ed5bd3ea8cb2497a60ca8e67b79191241` |

## Layout and decisions

An original path such as `Backend/scripts/update_contract.py` is preserved at
`_archive/cleanup-2026-11-17/Backend/scripts/update_contract.py`. Moves preserve
file bytes, permissions and symlinks. Nothing was permanently deleted.

The [manifest](manifest.json) records every moved root, its reason, distribution
policy, file count, byte count and recursive SHA-256 fingerprint. Fingerprints
include names, contents, permissions and symlink targets without following links.

This cleanup moved **48 entries containing 89,000 files/symlinks**, approximately
**2.23 GB of logical file content**. Most are files inside the three legacy Python
environments. Ten source/document files are versioned; local-only artifacts remain
excluded from GitHub.

| Original location | Why it was archived | Git distribution |
| --- | --- | --- |
| `Backend/scripts/update_contract.py` | One-off contract text replacement; no runtime caller | Versioned |
| `Backend/database/seeders/ForecastTestSeeder.php` | Random, unauthenticated-era synthetic fixture; current demo commands prepare isolated, owned research workspaces | Versioned |
| `NLP_Service/experiments/` | Five one-off Holt/Mann–Kendall probes; maintained models and tests now cover actual behavior | Versioned |
| `docs/PROJECT_GUIDE.md` | Initial planning guide contains superseded startup, dataset and prediction milestones | Versioned |
| `docs/FILE_MOVES.json` | Frozen October reorganization ledger, retained as historical provenance | Versioned |
| `Backend/dev-docs/` | Old manual forecast instructions and payload; instructions refer to the earlier authentication and seeding workflow | Local only |
| `Scraper/data/archive/` | Failed collection pilots and superseded verification replays | Local only |
| Selected `.logs/` artifacts | Old screenshots, scripts, captures, verification records and pre-migration/repair backups | Local only |
| Three temporary `business_backtest/` runs | Smoke/reproduction copies; cited studies and latest report inputs stay active | Local only |
| `.venv-py39/`, `NLP_Service/.venv/`, `NLP_Service/.venv311/` | Earlier unused environments; launcher and documented commands use root `.venv/` | Local only |
| Report `work/` PNGs, SVGs and two rendering directories | Intermediate figures and visual QA; final DOCX and build sources stay accessible | Local only |
| Finder `.DS_Store` files | Local file-manager metadata | Local only |

The archive consolidates material; it does not reclaim disk space. Archived
virtual environments contain absolute installation paths and must be restored to
their original locations before attempting to use them. Some old scripts remain
historical evidence and depend on superseded application behavior even if restored.

## What stays active

- Frontend pages, styles, chart interactions, examples and asset-versioning utility.
- Laravel routes, authentication, migrations, framework resources and real demo commands.
- All runtime forecasting modules, including `forecasting.py`, `business_prediction.py`,
  `automatic_forecast.py`, `outlook.py`, `commercial_baseline.py` and `olist_forecasting.py`.
  Several earlier research modules are dependencies of the current commercial API.
- Maintained scoring, evaluation, data-preparation and reproduction scripts, fixed
  protocols, release evidence, independent sentiment benchmarks and CBN inputs.
- Successful Jumia, Olist, open-startup and RePro collections; original cited study
  results and the latest forecast comparison inputs.
- Root `.venv/`, installed Composer dependencies, pinned model caches, databases,
  `.env` files, IDE settings and current service logs. These are local runtime state.
- The final Word report and its builder, rasterizer, build manifest and local Node
  dependency link under `outputs/forecast-comparison-2026-11-17/`.

The current setup guide is [Testing the app](../../docs/TESTING_THE_APP.md).
Commercial behavior and research limitations are documented in
[Commercial release](../../docs/COMMERCIAL_RELEASE.md). Older design/results
documents retain their original dates and are historical evidence.

## Inspect and restore

Run these commands from the project root; the helper uses only Python's standard library:

```sh
# List paths and reasons.
python3 scripts/restore_archive.py

# Verify all payloads against the manifest (can take time for old environments).
python3 scripts/restore_archive.py --verify --all

# Preview one exact restoration without changing anything.
python3 scripts/restore_archive.py Backend/scripts/update_contract.py

# Restore it to the original path, with no overwrite permitted.
python3 scripts/restore_archive.py --apply Backend/scripts/update_contract.py

# Preview the complete restoration; add --apply only when wanted.
python3 scripts/restore_archive.py --all
```

The helper checks the whole selected set before moving files. A changed checksum,
missing payload, symlink parent or existing destination stops restoration. An
already-restored entry is checked in its original location. There is no force or
overwrite flag. Restoration into component repositories creates normal Git working
tree changes for review; it does not alter commit history or publish changes.

GitHub contains the versioned payloads and manifest. Private/local artifacts are
preserved only in this workspace and its private backups. On a fresh clone,
verification reports those payloads as unavailable; select specific versioned paths
or restore the local archive backup before requesting `--all`.

## Validation after cleanup

- All 48 archive entries passed their fingerprints; all ten archived source/document
  files also match the published checkpoint's Git blobs byte for byte.
- `python3 scripts/restore_archive.py Backend/scripts/update_contract.py` previews
  the original restoration path without moving anything.
- Root `.venv/bin/python -m pytest -q`: **145 passed, 2 optional browser tests skipped**.
  This includes seven restoration checks for preview behavior, conflicts, modified
  payloads, unsafe paths, symlink parents, directory/link preservation and missing files.
- From `Backend/`, `php artisan test --compact`: **73 passed, 516 assertions**.
- Frontend `main.js` and `commercial.js` passed Node syntax checks. Application
  source and maintained research model behavior were not changed by this cleanup.
- Local-only archive paths are ignored by Git. The final Word report, its dependency
  link, active data/model paths and current service log locations remain available.

These are filesystem and software checks, not a new model accuracy evaluation.
