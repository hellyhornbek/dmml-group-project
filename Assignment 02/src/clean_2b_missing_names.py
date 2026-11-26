def drop_missing_names(con, table="listens"):
    """Step 2B: drop listens without an artist or track name (empty or only spaces counts as missing).

    Works on the DuckDB table made in step 2A. Returns the number of listens removed.
    """
    before = con.execute(f"select count(*) from {table}").fetchone()[0]
    con.execute(f"""delete from {table}
        where trim(coalesce(artist_name, '')) = '' or trim(coalesce(track_name, '')) = ''""")
    after = con.execute(f"select count(*) from {table}").fetchone()[0]

    print(f"2B  removed {before - after:,} listens without an artist or track name, {after:,} left")
    return before - after
