# Running the extract step

Needs Python 3, `zstd` (`brew install zstd`) and `pip install pyarrow duckdb`. Run from the `Data Mining project` folder.
The cohort files must already be in `Extract/` (see `03_Cohort`).

## Extract the listens (2 to 4 hours, can be resumed)

    caffeinate -i python3 "Reports/04_Extract/Scripts/extract.py" --dump "Raw data/ListenBrainz Full/listenbrainz-listens-dump-2758-20261101-000003-full.tar.zst" --out "Extract"

Prints progress every 20 s. If it stops, run the same command again.
Output: `Extract/extract/year=YYYY/part-*.parquet`, `progress.json`, `run_info.json`.

## Check the result

    python3 "Reports/04_Extract/Scripts/extract.py" --check --out "Extract"

Compares the extract with the profile (rows per user and year, totals, users, the rule) and writes `Extract/check_report.txt`.
It must end with: RESULT: ALL CHECKS PASSED.

## Overview tables and figures

    python3 "Reports/04_Extract/Scripts/extract_overview.py" --extract "Extract/extract" --out "Reports/04_Extract/Output"
    python3 "Reports/04_Extract/Scripts/extract_user_year_buckets.py"
    python3 "Reports/04_Extract/Output/figures/extract_figures.py"

`extract_overview.py` can be stopped and run again (it keeps a cache and has a `--budget` time limit in seconds).
