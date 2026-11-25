# Running the test sample step

Needs Python 3. Install the packages with `python -m pip install -r requirements.txt` (duckdb, pandas, pyarrow, matplotlib, numpy). Work in an empty work folder (it gets big intermediate files, so keep it outside the project).

    S="<project>/Reports/05_Test_Sample/Scripts"
    python3 "$S/make_sample_listens.py" --extract "<project>/Extract/extract" --work work    # picks the users and thins the listens (seed 2023)
    cd work
    python3 "$S/make_keys.py"
    python3 "$S/match_canonical.py" --tar "<project>/Raw data/MusicBrainz Canonical/musicbrainz-canonical-dump-20261103-080003.tar.zst" --work .
    for step in ids artist recording release; do python3 "$S/link_musicbrainz.py" $step; done
    SAMPLE_OUT=out python3 "$S/build_sample_csv.py"
    python3 "$S/sample_overview.py" --csv out/sample_2023_600users.csv --out "<project>/Reports/05_Test_Sample/Output"

Every step is repeatable: the same commands give the same csv. The first command writes `sample_listens.parquet` into the work folder; it can be made again, so it is not kept in the project.
Run the `link_musicbrainz.py` steps one at a time if your machine limits how long a command may run; `match_canonical.py` can be stopped and run again.
