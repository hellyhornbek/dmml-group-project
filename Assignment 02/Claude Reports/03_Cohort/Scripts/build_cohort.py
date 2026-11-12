#!/usr/bin/env python3
"""Cohort: build the cohort list from user_year_profile.csv (no pass over the dump needed).

Rule "A2" (agreed 11 Nov 2026):
  * at least 5 consecutive calendar years in which the user has between min and max listens
  * no year above max anywhere in the history (then the user is removed completely)
  * 2026 covers only 10 of 12 months, so both limits are scaled by 10/12 for 2026
Writes into --out:  cohort_users.csv, cohort_year_counts.csv, config.json

Usage:  python3 build_cohort.py --profile "../../02_ListenBrainz User and Year/Output/user_year_profile.csv" --out "../../../Extract"
"""
import argparse, collections, csv, hashlib, json, os

DEFAULTS = dict(min_listens=2000, max_listens=40000, min_run_years=5,
                partial_years={"2026": 10 / 12}, no_year_above_max=True, buckets=100)


def limits(y, cfg):
    f = cfg['partial_years'].get(str(y), 1.0)
    return round(cfg['min_listens'] * f), round(cfg['max_listens'] * f)


def bucket_of(uid, cfg):
    return int(hashlib.md5(str(uid).encode()).hexdigest(), 16) % cfg['buckets']


def qualifying_runs(counts, cfg):
    """counts: {year: listens}. Returns None if the user is removed for an abnormal year,
    else the list of (start, end) runs of consecutive qualifying years with length >= min_run_years."""
    if cfg['no_year_above_max']:
        for y, n in counts.items():
            if n > limits(y, cfg)[1]:
                return None
    runs, start, prev = [], None, None
    need = cfg['min_run_years']
    for y in sorted(counts):
        lo, hi = limits(y, cfg)
        ok = lo <= counts[y] <= hi
        if ok and start is not None and y == prev + 1:
            prev = y
            continue
        if start is not None and prev - start + 1 >= need:
            runs.append((start, prev))
        start = prev = y if ok else None
    if start is not None and prev - start + 1 >= need:
        runs.append((start, prev))
    return runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--profile', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    cfg = dict(DEFAULTS)
    os.makedirs(a.out, exist_ok=True)
    counts = collections.defaultdict(dict)
    with open(a.profile, newline='') as fh:
        r = csv.reader(fh); next(r)
        for row in r:
            counts[int(row[0])][int(row[1])] = int(row[2])
    print('users in profile: %s' % format(len(counts), ','))
    rows, per_year = [], collections.Counter()
    with open(os.path.join(a.out, 'cohort_year_counts.csv'), 'w', newline='') as fy:
        wy = csv.writer(fy); wy.writerow(['user_id', 'year', 'listens'])
        for uid in sorted(counts):
            runs = qualifying_runs(counts[uid], cfg)
            if not runs:
                continue
            c = counts[uid]
            rows.append([uid, runs[0][0], runs[0][1], min(c), max(c), len(runs), sum(c.values()), bucket_of(uid, cfg)])
            for y in sorted(c):
                wy.writerow([uid, y, c[y]]); per_year[y] += c[y]
    with open(os.path.join(a.out, 'cohort_users.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['user_id', 'window_start', 'window_end', 'first_year', 'last_year', 'n_runs', 'total_listens', 'bucket'])
        w.writerows(rows)
    cfg['n_users'] = len(rows); cfg['n_listens'] = sum(r[6] for r in rows)
    cfg['source_profile'] = os.path.basename(a.profile)
    with open(os.path.join(a.out, 'config.json'), 'w') as fh:
        json.dump(cfg, fh, indent=2)
    tot = cfg['n_listens']
    print('cohort: %s users, %s listens' % (format(len(rows), ','), format(tot, ',')))
    print('2026 limits: %d to %d' % limits(2026, cfg))
    print('listens by year (M):', {y: round(n / 1e6, 1) for y, n in sorted(per_year.items())})
    b = collections.Counter(r[7] for r in rows)
    print('users per bucket: min %d, max %d' % (min(b.values()), max(b.values())))
    print('written to', a.out)


if __name__ == '__main__':
    main()
