import duckdb
import pandas as pd
from pathlib import Path

# columns kept from the extract (dropped: year, is_dup, tracknumber, origin_url, extra_json)
KEEP = ["user_id", "ts", "artist_name", "track_name", "release_name",
        "recording_mbid", "artist_mbid", "release_mbid", "recording_msid",
        "spotify_id", "isrc", "duration_ms", "ms_played", "source", "music_service"]


def clean_listens(extract_path, users_path, listens_path, year=2023,
                  max_same_second=5, min_ms_played=None):
    """Clean all listens of the picked users and write them to one parquet file.

    Rules, in this order:
      1. keep only the users in users_path (the output of pick_users)
      2. drop exact repeats flagged by the extract (is_dup: same user, second, artist, track)
      3. drop listens without an artist or track name
      4. drop repeats that only differ in upper/lower case (same user, second, artist, track);
         the copy with a recording_mbid is kept when there is one
      5. drop bulk-import clusters: seconds where one user has more than max_same_second listens
         (no one plays 6+ tracks in one second; they would make fake zero-gap sessions).
         None switches the rule off.
      6. optional: drop listens with ms_played below min_ms_played (only ~30% of rows have
         ms_played; rows without it are always kept). None (default) switches the rule off.

    extract_path  folder holding year=YYYY/part-*.parquet (e.g. "Extract/extract")
    users_path    csv with a user_id column (from pick_users)
    listens_path  output parquet, one row per listen, ordered by user_id, ts.
                  Adds listen_time_utc (timestamp, UTC) next to ts (Unix seconds).

    Returns a small DataFrame with the number of listens removed by each rule.
    """
    src = (Path(extract_path) / f"year={year}" / "part-*.parquet").as_posix()  # skips macOS '._' files
    listens_path = Path(listens_path)
    listens_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    steps = []

    def count(table):
        return con.execute(f"select count(*) from {table}").fetchone()[0]

    # 1. users
    con.execute(f"create view users as select user_id from read_csv('{Path(users_path).as_posix()}')")
    con.execute(f"""create table l as
        select {', '.join(KEEP)}, is_dup
        from read_parquet('{src}') semi join users using (user_id)""")
    n = count("l")
    steps.append(("listens of the picked users", n, None))

    # 2. flagged exact repeats
    con.execute("delete from l where is_dup")
    steps.append(("exact repeats (is_dup)", count("l"), n - count("l"))); n = count("l")

    # 3. missing names
    con.execute("delete from l where trim(coalesce(artist_name, '')) = '' or trim(coalesce(track_name, '')) = ''")
    steps.append(("no artist or track name", count("l"), n - count("l"))); n = count("l")

    # 4. case-only repeats
    con.execute("""create or replace table l as
        select * exclude (rn) from (
            select *, row_number() over (
                partition by user_id, ts, lower(artist_name), lower(track_name)
                order by recording_mbid is null, artist_mbid is null) as rn
            from l)
        where rn = 1""")
    steps.append(("repeats differing only in case", count("l"), n - count("l"))); n = count("l")

    # 5. bulk-import clusters
    if max_same_second is not None:
        con.execute(f"""create or replace table l as
            select * from l anti join (
                select user_id, ts from l group by user_id, ts having count(*) > {int(max_same_second)}
            ) as clusters using (user_id, ts)""")
        steps.append((f"clusters of > {max_same_second} listens in one second", count("l"), n - count("l")))
        n = count("l")

    # 6. short plays
    if min_ms_played is not None:
        con.execute(f"delete from l where ms_played is not null and ms_played < {int(min_ms_played)}")
        steps.append((f"ms_played < {min_ms_played:,} ms", count("l"), n - count("l"))); n = count("l")

    con.execute(f"""copy (
        select user_id, ts, to_timestamp(ts) as listen_time_utc, * exclude (user_id, ts, is_dup)
        from l order by user_id, ts, artist_name, track_name
    ) to '{listens_path.as_posix()}' (format parquet, compression zstd)""")
    n_users = con.execute("select count(distinct user_id) from l").fetchone()[0]
    con.close()

    report = pd.DataFrame(steps, columns=["step", "listens_left", "removed"])
    print(report.to_string(index=False))
    print(f"\nWrote {n:,} listens of {n_users:,} users to {listens_path}")
    return report
