# Running the cohort step

Needs only Python 3. Run from the `Data Mining project` folder. Takes seconds.

    python3 "Reports/03_Cohort/Scripts/build_cohort.py" --profile "Reports/02_ListenBrainz User and Year/Output/user_year_profile.csv" --out "Extract"

Must print: `cohort: 13,515 users, 1,462,060,308 listens`.
Writes `cohort_users.csv`, `cohort_year_counts.csv` and `config.json` into `Extract/` (copies are in `../Output/`).

`cohort_overview.py` counts how many users each rule removes (needs the same profile file):

    python3 "Reports/03_Cohort/Scripts/cohort_overview.py" --profile "Reports/02_ListenBrainz User and Year/Output/user_year_profile.csv" --out "Reports/03_Cohort/Output"

The rule (agreed 11 Nov 2026): at least 5 consecutive calendar years with 2,000 to 40,000 listens each (2026 scaled by 10/12),
no year above the maximum anywhere in the history, whole history kept.
