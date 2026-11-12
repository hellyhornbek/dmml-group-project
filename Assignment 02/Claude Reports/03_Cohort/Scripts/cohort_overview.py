#!/usr/bin/env python3
"""Counts how the cohort was selected and how much of the dump it covers.

Reads:  user_year_profile.csv (columns user_id, year, listens only) and ../Output/cohort_users.csv
Writes: cohort_funnel.csv  (how many users are left after each rule)
        cohort_per_year.csv (listens and users per year: whole dump vs cohort)
Uses the same rule code as build_cohort.py, so the numbers cannot drift from the real selection.
Usage:  python3 cohort_overview.py --profile ../../02_ListenBrainz\ User\ and\ Year/Output/user_year_profile.csv --out ../Output
"""
import argparse, collections, csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_cohort import DEFAULTS, limits, qualifying_runs

ap = argparse.ArgumentParser(); ap.add_argument('--profile', required=True); ap.add_argument('--out', required=True)
a = ap.parse_args(); cfg = dict(DEFAULTS)
counts = collections.defaultdict(dict)
with open(a.profile, newline='') as fh:
    r = csv.reader(fh); next(r)
    for row in r:
        counts[int(row[0])][int(row[1])] = int(row[2])
cohort = {int(r['user_id']) for r in csv.DictReader(open(os.path.join(a.out, 'cohort_users.csv')))}

n_all = len(counts); too_big = no_run = 0; listens = collections.Counter(); f = collections.Counter()
dump_y, dump_u, coh_y, coh_u = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
for uid, c in counts.items():
    runs = qualifying_runs(c, cfg)
    if runs is None: f['too_big'] += 1; f['too_big_listens'] += sum(c.values())
    elif not runs: f['no_run'] += 1; f['no_run_listens'] += sum(c.values())
    else: f['in'] += 1; f['in_listens'] += sum(c.values())
    assert (bool(runs)) == (uid in cohort)
    for y, n in c.items():
        dump_y[y] += n; dump_u[y] += 1
        if uid in cohort: coh_y[y] += n; coh_u[y] += 1
assert f['in'] == len(cohort) == 13515 and f['in_listens'] == 1462060308
tot = sum(dump_y.values()); assert tot == 2990440915 and n_all == 101881
with open(os.path.join(a.out, 'cohort_funnel.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['step', 'users', 'listens'])
    w.writerow(['all users in the dump', n_all, tot])
    w.writerow(['removed: a year above the maximum', f['too_big'], f['too_big_listens']])
    w.writerow(['removed: no 5 years in a row within the limits', f['no_run'], f['no_run_listens']])
    w.writerow(['cohort', f['in'], f['in_listens']])
with open(os.path.join(a.out, 'cohort_per_year.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['year', 'dump_listens', 'dump_users', 'cohort_listens', 'cohort_users'])
    for y in sorted(dump_y): w.writerow([y, dump_y[y], dump_u[y], coh_y[y], coh_u[y]])
print(dict(f)); print('written to', a.out)
