#!/usr/bin/env python3
"""Groups every user-year of the extract by how many listens the user has in that year.

Reads:  ../../03_Cohort/Output/cohort_year_counts.csv (user_id, year, listens). The extract check showed 0 user-years that differ from it.
Writes: ../Output/extract_user_year_buckets.csv  (year, bucket, users)
Buckets: under 2,000, then 2,000-4,000, 4,000-8,000, 8,000-16,000, 16,000-32,000 and 32,000-40,000 (the cohort maximum).
A listen count on a limit goes into the higher bucket. 2026 is partial (10 of 12 months).
"""
import csv, collections, os
H = os.path.dirname(os.path.abspath(__file__))
EDGES = [(0, 2000, 'under 2,000'), (2000, 4000, '2,000-4,000'), (4000, 8000, '4,000-8,000'), (8000, 16000, '8,000-16,000'),
         (16000, 32000, '16,000-32,000'), (32000, 40001, '32,000-40,000')]
cnt = collections.Counter(); n = 0
for r in csv.DictReader(open(os.path.join(H, '..', '..', '03_Cohort', 'Output', 'cohort_year_counts.csv'))):
    v = int(r['listens']); n += 1
    for lo, hi, name in EDGES:
        if lo <= v < hi: cnt[(int(r['year']), name)] += 1; break
    else: raise SystemExit('listens above 40,000: %d' % v)
assert sum(cnt.values()) == n == 170653
with open(os.path.join(H, '..', 'Output', 'extract_user_year_buckets.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['year', 'bucket', 'users'])
    for y in sorted({k[0] for k in cnt}):
        for _, _, name in EDGES: w.writerow([y, name, cnt[(y, name)]])
print('user-years', n)
