#!/usr/bin/env python3
"""Counts how well the sample was linked. Run inside the work folder (needs link.duckdb and sample_listens.parquet).

Writes into --out:
  sample_linking_coverage.csv  share of listens with a value, per column of the sample csv
  sample_song_linking.csv      distinct songs: with a key, matched in the canonical dump, with ids, in the final csv
  sample_per_user.csv          listens per user in the sample and in 2023 before thinning
Usage: python3 sample_overview.py --csv "<Sample>/sample_2023_600users.csv" --out ../Output
"""
import argparse, os, duckdb
ap = argparse.ArgumentParser(); ap.add_argument('--csv', required=True); ap.add_argument('--out', required=True); a = ap.parse_args()
c = duckdb.connect('link.duckdb', read_only=True)
c.execute(f"create temp view f as select * from read_csv('{a.csv}', all_varchar=true)")
n = c.execute('select count(*) from f').fetchone()[0]; assert n == c.execute("select count(*) from 'sample_listens.parquet'").fetchone()[0]
cols = [r[0] for r in c.sql('describe f').fetchall()]
with open(os.path.join(a.out, 'sample_linking_coverage.csv'), 'w') as fh:
    fh.write('column,listens_with_value,share\n')
    for k in cols:
        v = c.execute(f'select count("{k}") from f').fetchone()[0]; fh.write('%s,%d,%.4f\n' % (k, v, v / n))
s = c.execute("""select count(*), count(matchkey), sum(matched_canonical::int), count(recording_mbid), count(artist_mbid), count(release_mbid) from songs""").fetchone()
lab = ['distinct songs (artist + title)', 'songs with a match key', 'songs matched in the canonical dump', 'songs with a recording id', 'songs with an artist id', 'songs with a release id']
with open(os.path.join(a.out, 'sample_song_linking.csv'), 'w') as fh:
    fh.write('step,songs\n')
    for l, v in zip(lab, s): fh.write('%s,%d\n' % (l, v))
c.execute("copy (select user_id, count(*) listens_in_sample, max(user_listens_2023) listens_2023_before_thinning from 'sample_listens.parquet' group by 1 order by 1) to '%s' (header)" % os.path.join(a.out, 'sample_per_user.csv'))
print(dict(zip(lab, s)))
