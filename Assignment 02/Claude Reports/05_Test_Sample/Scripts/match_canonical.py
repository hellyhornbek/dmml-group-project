#!/usr/bin/env python3
"""Finds the MusicBrainz canonical row for every song key of the sample.

The canonical dump (7.7 GB csv inside a .tar.zst) is streamed, never unpacked. Each line ends with
combined_lookup,score. A line is kept when its combined_lookup is one of our song keys (keys.txt, made by make_keys.py).
If a key occurs several times, the row with the highest score wins.
Writes matches.json: {matchkey: [score, artist_mbids, release_mbid, recording_mbid]}.
Can be stopped and run again (progress.json holds the byte offset), e.g. when a call must stay under a time limit.

Usage: python3 match_canonical.py --tar <canonical dump .tar.zst> --work <folder with keys.txt> [--budget 150]
"""
import argparse, csv, json, os, subprocess, sys, time

ap = argparse.ArgumentParser()
ap.add_argument('--tar', required=True); ap.add_argument('--work', required=True); ap.add_argument('--budget', type=float, default=150)
a = ap.parse_args(); t0 = time.time()
W = a.work; keys = set(open(os.path.join(W, 'keys.txt')).read().split('\n'))
pf, mf = os.path.join(W, 'progress.json'), os.path.join(W, 'matches.json')
P = json.load(open(pf)) if os.path.exists(pf) else {'offset': 0, 'lines': 0, 'done': False}
M = json.load(open(mf)) if os.path.exists(mf) else {}
if P['done']: sys.exit('already done: %d keys matched' % len(M))
MEMBER = 'canonical/canonical_musicbrainz_data.csv'
name = subprocess.run('zstd -dc "%s" | tar -tf - | grep %s' % (a.tar, MEMBER), shell=True, capture_output=True, text=True).stdout.split('\n')[0]
cmd = 'zstd -dc "%s" | tar -xOf - "%s"' % (a.tar, name)
proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
pos = 0; skip = P['offset']; n = 0; finished = True
for raw in proc.stdout:
    pos += len(raw)
    if pos <= skip: continue
    n += 1
    line = raw.decode('utf-8', 'replace').rstrip('\n')
    p = line.rsplit(',', 2)
    if len(p) == 3 and p[1] in keys:
        try: score = int(p[2])
        except ValueError: score = 0
        old = M.get(p[1])
        if old is None or score > old[0]:
            try: r = next(csv.reader([line]))
            except Exception: continue
            if len(r) >= 10: M[p[1]] = [score, r[2], r[4], r[6]]
    if n % 200000 == 0 and time.time() - t0 > a.budget:
        finished = False; break
if not finished: proc.kill()
P['offset'] = pos; P['lines'] += n; P['done'] = finished
json.dump(M, open(mf, 'w')); json.dump(P, open(pf, 'w'))
print('lines this run %d, total %d, matched keys %d, done=%s' % (n, P['lines'], len(M), finished))
