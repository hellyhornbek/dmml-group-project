#!/usr/bin/env python3
"""Measures the finished extract: one pass over the Parquet files with DuckDB, no sampling.
Usage: python3 extract_overview.py --extract "<folder with year=YYYY>" --out "<output folder>"
Writes in the output folder:
  extract_per_year.csv      per year: rows, users, repeated rows (is_dup), and the share of rows that have each field
  extract_top_sources.csv   the 30 most common submitting clients (source), with rows and share, over all years
  extract_per_user.csv      per user: total rows and active years (not shared outside the group)
Needs: pip install duckdb. The year loop keeps memory low (one year at a time).
Resumable: the result of each finished step is saved in <out>/_cache and skipped on the next run.
Use --budget SECONDS to stop cleanly after that time (run the same command again to continue).
The _cache folder can be deleted when the three csv files exist.
"""
import argparse, os, csv, json, time, duckdb

ap = argparse.ArgumentParser(); ap.add_argument('--extract', required=True); ap.add_argument('--out', required=True); ap.add_argument('--budget', type=float, default=1e9)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
CACHE = os.path.join(a.out, '_cache'); os.makedirs(CACHE, exist_ok=True); T0 = time.time()
def cached(name, fn):
    p = os.path.join(CACHE, name + '.json')
    if os.path.exists(p): return json.load(open(p))
    if time.time() - T0 > a.budget: print('time budget used, run the same command again'); raise SystemExit(0)
    v = fn(); json.dump(v, open(p, 'w')); return v
con = duckdb.connect(); con.execute('PRAGMA threads=4'); con.execute("PRAGMA memory_limit='2GB'")
FIELDS = ['recording_mbid', 'artist_mbid', 'release_mbid', 'release_name', 'source', 'music_service', 'spotify_id', 'isrc',
          'tracknumber', 'duration_ms', 'ms_played']
years = sorted(int(d.split('=')[1]) for d in os.listdir(a.extract) if d.startswith('year='))

# ---- per year (one year at a time) ----
head = ['year', 'rows', 'users', 'dup_rows'] + ['share_' + f for f in FIELDS] + ['share_missing_artist', 'share_missing_track', 'dup_share']
def one_year(y):
    src = "read_parquet('%s/year=%d/*.parquet')" % (a.extract, y)
    q = ("select count(*), count(distinct user_id), sum(is_dup::int), " + ', '.join('count(%s)' % f for f in FIELDS) +
         ", sum((artist_name is null or artist_name = '')::int), sum((track_name is null or track_name = '')::int) from " + src)
    r = con.execute(q).fetchone(); print('year', y, r[0], flush=True); return [int(x) for x in r]
res = {y: cached('year_%d' % y, lambda y=y: one_year(y)) for y in years}
with open(os.path.join(a.out, 'extract_per_year.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(head)
    for y in years:
        r = res[y]; n = r[0]
        w.writerow([y, n, r[1], r[2]] + [round(c / n, 4) for c in r[3:3 + len(FIELDS)]] +
                   [round(r[3 + len(FIELDS)] / n, 4), round(r[4 + len(FIELDS)] / n, 4), round(r[2] / n, 4)])

# ---- top sources, all years ----
allp = "read_parquet('%s/year=*/*.parquet')" % a.extract
rows = cached('sources', lambda: [list(r) for r in con.execute("select coalesce(source, '(none)') s, count(*) n from %s group by 1 order by n desc limit 30" % allp).fetchall()])
total = sum(r[0] for r in res.values())
with open(os.path.join(a.out, 'extract_top_sources.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['source', 'rows', 'share_of_all_rows'])
    for s, n in rows: w.writerow([s, n, round(n / total, 4)])

# ---- per user ----
with open(os.path.join(a.out, 'extract_per_user.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['user_id', 'rows', 'active_years'])
    for r in cached('users', lambda: [list(r) for r in con.execute("select user_id, count(*), count(distinct year) from %s group by 1 order by 1" % allp).fetchall()]): w.writerow(r)
print('done: %d rows in %d years' % (total, len(years)))
