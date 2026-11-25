#!/usr/bin/env python3
"""Step 1 of the test sample: pick users and thin their listens. Reads the 2023 part of the extract.

  1. Pool: users with 2,000 to 40,000 listens in 2023, exact repeats (is_dup) not counted.
  2. 600 users from the pool: the 600 with the smallest hash of (seed, user_id). Same seed, same users.
  3. Thinning: each listen of those users is kept when the hash of (seed, user, time, artist, title, row number) is below
     the fraction f = target / (all non-repeat listens of the 600 users in 2023). Same seed, same listens.
     Exact repeats are removed first. The result has about 200,000 rows.
Writes sample_listens.parquet (the input of make_keys.py) into --work.

The first version of the group sample (11 Nov 2026) was made with an earlier script that was not saved. On 12 Nov 2026 the sample was made again
with this script (seed 2023), so the whole chain from the extract to the csv can be repeated.

Usage: python3 make_sample_listens.py --extract "<project>/Extract/extract" --work <work folder> [--seed 2023] [--target 200000]
"""
import argparse, os, duckdb
ap = argparse.ArgumentParser()
ap.add_argument('--extract', required=True); ap.add_argument('--work', required=True)
ap.add_argument('--seed', type=int, default=2023); ap.add_argument('--target', type=int, default=200000)
ap.add_argument('--users', type=int, default=600)
a = ap.parse_args(); os.makedirs(a.work, exist_ok=True)
con = duckdb.connect(); con.execute("PRAGMA threads=4")
src = os.path.join(a.extract, 'year=2023', '*.parquet')
con.execute(f"create table pool as select user_id, count(*) n from '{src}' where not is_dup group by 1 having count(*) between 2000 and 40000")
print('pool', con.sql('select count(*) from pool').fetchone()[0], 'users')
con.execute(f"create table picked as select user_id, n from pool order by hash(user_id::varchar || '-{a.seed}'), user_id limit {a.users}")
total = con.sql('select sum(n) from picked').fetchone()[0]; f = a.target / total
print('picked', a.users, 'users with', total, 'listens in 2023; fraction', round(f, 6))
con.execute(f"""create table sample as
  select user_id, ts, artist_name, track_name, release_name, recording_mbid, release_mbid, artist_mbid, ms_played, duration_ms, n as user_listens_2023
  from (select e.*, p.n, row_number() over (partition by e.user_id, e.ts, e.artist_name, e.track_name) rn
        from '{src}' e join picked p using(user_id) where not e.is_dup)
  where (hash(user_id::varchar || '-' || ts || '-' || coalesce(artist_name, '') || '-' || coalesce(track_name, '') || '-' || rn || '-{a.seed}') % 1000000) / 1000000.0 < {f}""")
con.execute(f"copy (select * from sample order by user_id, ts) to '{os.path.join(a.work, 'sample_listens.parquet')}' (format parquet)")
print('rows', con.sql('select count(*) from sample').fetchone()[0], 'users', con.sql('select count(distinct user_id) from sample').fetchone()[0])
