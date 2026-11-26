from pathlib import Path

# columns kept from the extract (dropped: year, tracknumber, origin_url, extra_json)
KEEP = ["user_id", "ts", "artist_name", "track_name", "release_name",
        "recording_mbid", "artist_mbid", "release_mbid", "recording_msid",
        "spotify_id", "isrc", "duration_ms", "ms_played", "source", "music_service"]


def drop_duplicate_listens(con, extract_path, users_path, year=2023, table="listens"):
    """Step 2A: load the listens of the picked users and drop the exact repeats.

    Reads every listen of the users in users_path from the extract into the DuckDB table `table`,
    then drops the listens the extract flagged as is_dup (same user, second, artist and track).

    con           an open DuckDB connection; the following steps (2B-2D) work on the same table
    extract_path  folder holding year=YYYY/part-*.parquet (e.g. "Extract/extract")
    users_path    csv with a user_id column (from pick_users)

    Returns (listens before, listens removed).
    """
    # only part-*.parquet: skips the macOS '._part-*' metadata files that sit next to them
    src = (Path(extract_path) / f"year={year}" / "part-*.parquet").as_posix()
    con.execute(f"""create or replace table {table} as
        select {', '.join(KEEP)}, is_dup
        from read_parquet('{src}')
        semi join (select user_id from read_csv('{Path(users_path).as_posix()}')) using (user_id)""")
    before = con.execute(f"select count(*) from {table}").fetchone()[0]

    con.execute(f"delete from {table} where is_dup")
    con.execute(f"alter table {table} drop column is_dup")
    after = con.execute(f"select count(*) from {table}").fetchone()[0]

    print(f"2A  loaded {before:,} listens, removed {before - after:,} exact repeats (is_dup), {after:,} left")
    return before, before - after
