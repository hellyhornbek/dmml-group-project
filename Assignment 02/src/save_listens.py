from pathlib import Path


def save_listens(con, listens_path, table="listens"):
    """Write the cleaned listens (after steps 2A-2D) to one parquet file.

    One row per listen, ordered by user_id, ts. Adds listen_time_utc (timestamp, UTC) next to ts
    (Unix seconds).
    """
    listens_path = Path(listens_path)
    listens_path.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"""copy (
        select user_id, ts, to_timestamp(ts) as listen_time_utc, * exclude (user_id, ts)
        from {table} order by user_id, ts, artist_name, track_name
    ) to '{listens_path.as_posix()}' (format parquet, compression zstd)""")
    n, n_users = con.execute(f"select count(*), count(distinct user_id) from {table}").fetchone()
    print(f"Wrote {n:,} listens of {n_users:,} users to {listens_path}")
