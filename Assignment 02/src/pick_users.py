import duckdb
import pandas as pd
from pathlib import Path


def pick_users(extract_path, min_listens=2000, max_listens=40000, n_users=600, seed=2023,
               users_path=None, year=2023):
    """Pick the users to work with from the ListenBrainz extract (same rule as the 600-user sample).

    1. Pool: users with min_listens to max_listens listens in `year`, exact repeats (is_dup) not counted.
    2. From the pool, the n_users with the smallest hash of (user_id, seed). Same seed, same users.
       n_users=None keeps the whole pool.

    extract_path  folder holding year=YYYY/part-*.parquet (e.g. "Extract/extract")
    users_path    optional output csv with the picked users (user_id, n_listens). If the file already
                  exists, it is compared with the new pick first, and a warning is printed when they
                  differ (e.g. after a DuckDB upgrade changed hash(), or other arguments were used).

    With the defaults this gives exactly the 600 users of Samples/01_Test_Sample (checked with DuckDB 2.0.1).
    Returns a DataFrame with user_id and n_listens, sorted by user_id.
    """
    # only part-*.parquet: skips the macOS '._part-*' metadata files that sit next to them
    src = Path(extract_path) / f"year={year}" / "part-*.parquet"

    con = duckdb.connect()
    con.execute(f"""create table pool as
        select user_id, count(*) as n_listens
        from read_parquet('{src.as_posix()}')
        where not is_dup
        group by user_id
        having count(*) between {int(min_listens)} and {int(max_listens)}""")
    n_pool, listens_pool = con.execute("select count(*), sum(n_listens) from pool").fetchone()

    limit = "" if n_users is None else f"limit {int(n_users)}"
    users = con.execute(f"""
        select user_id, n_listens from pool
        order by hash(user_id::varchar || '-{int(seed)}'), user_id
        {limit}""").df().sort_values("user_id").reset_index(drop=True)
    con.close()

    print(f"Pool: {n_pool:,} users with {min_listens:,}-{max_listens:,} listens in {year} "
          f"({listens_pool:,} listens)")
    print(f"Picked {len(users):,} users (seed {seed}) with {users['n_listens'].sum():,} listens")

    if users_path is not None:
        users_path = Path(users_path)
        if users_path.exists():
            old = pd.read_csv(users_path)
            if set(old["user_id"]) != set(users["user_id"]):
                print(f"WARNING: the picked users differ from the ones already in {users_path} "
                      f"({len(set(old['user_id']) & set(users['user_id'])):,} of {len(old):,} the same). "
                      f"The file is overwritten with the new pick.")
        users_path.parent.mkdir(parents=True, exist_ok=True)
        users.to_csv(users_path, index=False)

    return users
