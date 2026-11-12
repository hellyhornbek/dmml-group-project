"""Builds the match key for every distinct artist + track in the sample.
Key = lowercase letters and digits of artist, then of title (accents removed), e.g. 'massiveattackunfinishedsympathy'.
Run inside a work folder that holds sample_listens.parquet. Writes song_keys.parquet and keys.txt there.
Usage: cd <work folder> && python3 make_keys.py
"""
import duckdb, unicodedata, re
import pandas as pd
def key(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]', '', s.lower())
con = duckdb.connect()
d = con.sql("select distinct artist_name, track_name from 'sample_listens.parquet'").fetchall()
rows = [(a, t, key(a) + key(t) if key(a) and key(t) else None) for a, t in d]
pd.DataFrame(rows, columns=['artist_name', 'track_name', 'matchkey']).to_parquet('song_keys.parquet')
keys = {r[2] for r in rows if r[2]}
open('keys.txt', 'w').write('\n'.join(sorted(keys)))
print('distinct songs', len(rows), 'distinct keys', len(keys), 'without key', sum(1 for r in rows if not r[2]))
