# Figures from the extract

One figure per overview table, made from `../extract_per_year.csv`, `../extract_top_sources.csv` and `../extract_per_user.csv` (all 13,515 users, 1,462,060,308 rows).
Made by `extract_figures.py` in this folder, which checks the totals.

| Figure | Built from |
|---|---|
| 01_listens_and_users_per_year | extract_per_year.csv (rows, users) |
| 02_field_coverage_per_year | extract_per_year.csv (share of rows with recording id, song length, time played) |
| 03_source_and_repeats_per_year | extract_per_year.csv (share with source, share of exact repeats) |
| 04_top_sources | extract_top_sources.csv (top 12 of 30) |
| 05_listens_per_user | extract_per_user.csv (rows) |
| 06_active_years_per_user | extract_per_user.csv (active_years) |
| 07_users_by_listens_per_year | extract_user_year_buckets.csv (made by ../../Scripts/extract_user_year_buckets.py) |

2026 is partial (the dump ends on 1 Nov 2026).
