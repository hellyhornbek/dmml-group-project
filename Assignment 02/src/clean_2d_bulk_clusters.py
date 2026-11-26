def drop_bulk_clusters(con, max_same_second=5, table="listens"):
    """Step 2D: drop bulk-import clusters.

    A second in which one user has more than max_same_second listens is a bulk import, not real
    listening: no one plays 6+ tracks in one second, and the cluster would make a fake session with
    zero gaps. All listens of such a second are dropped. Pairs (and up to max_same_second) are kept.

    Works on the DuckDB table from steps 2A-2C. Returns the number of listens removed.
    """
    before = con.execute(f"select count(*) from {table}").fetchone()[0]
    n_clusters = con.execute(f"""select count(*) from (
        select 1 from {table} group by user_id, ts having count(*) > {int(max_same_second)})""").fetchone()[0]
    con.execute(f"""create or replace table {table} as
        select * from {table} anti join (
            select user_id, ts from {table} group by user_id, ts having count(*) > {int(max_same_second)}
        ) as clusters using (user_id, ts)""")
    after = con.execute(f"select count(*) from {table}").fetchone()[0]

    print(f"2D  removed {before - after:,} listens in {n_clusters:,} seconds with more than "
          f"{max_same_second} listens, {after:,} left")
    return before - after
