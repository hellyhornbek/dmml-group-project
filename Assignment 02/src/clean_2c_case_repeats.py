def drop_case_repeats(con, table="listens"):
    """Step 2C: drop repeats that only differ in upper/lower case.

    Two listens of the same user at the same second whose artist and track names are equal after
    lower-casing (e.g. 'Daft Punk' / 'daft punk') are one listen. The copy with a recording_mbid
    (then artist_mbid) is kept when there is one.

    Works on the DuckDB table from steps 2A-2B. Returns the number of listens removed.
    """
    before = con.execute(f"select count(*) from {table}").fetchone()[0]
    con.execute(f"""create or replace table {table} as
        select * exclude (rn) from (
            select *, row_number() over (
                partition by user_id, ts, lower(artist_name), lower(track_name)
                order by recording_mbid is null, artist_mbid is null) as rn
            from {table})
        where rn = 1""")
    after = con.execute(f"select count(*) from {table}").fetchone()[0]

    print(f"2C  removed {before - after:,} repeats that only differ in case, {after:,} left")
    return before - after
