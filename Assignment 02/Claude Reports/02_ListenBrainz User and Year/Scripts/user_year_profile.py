#!/usr/bin/env python3
"""Profile pass: a deep profile of the whole dump. No filtering: every listen is counted.
Usage: python3 user_year_profile.py OUT_FOLDER dump1.tar.zst [dump2.tar.zst ...]
Writes in OUT_FOLDER:
  user_year_profile_overview.txt   aggregates only (sections 1-7, read this first)
  user_year_profile.csv            one row per user and year: listens per month, per hour (UTC), per weekday,
                                   and how long since the user's previous listen (all users)
Only user_id and timestamp are read from each line.
Assumes the dump is in time order. The report counts how many listens break that (section 1).
Note: the run in November 2026 also wrote a section 8 (a 1% user sample) and two sample files. That code was removed
from this copy because the sample is not used; the saved overview file still shows that section.
"""
import sys, os, csv, time, argparse, collections, datetime, resource
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lbstream import iter_lines

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('out'); ap.add_argument('dumps', nargs='+')
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)

ND = 47000; base = datetime.date(1970, 1, 1).toordinal()
DAY_Y = [0] * ND; DAY_M = [0] * ND
for d in range(ND):
    x = datetime.date.fromordinal(base + d); DAY_Y[d] = x.year - 2000; DAY_M[d] = x.month

dd0 = collections.defaultdict
C_um = dd0(int); C_h = dd0(int); C_w = dd0(int); C_gap = dd0(int)    # keys: uy*13+month, uy*24+hour, uy*7+weekday, uy*10+gap bucket
G_ywh = [0] * (40 * 7 * 24); G_day = [0] * ND; last = {}                # uy = user_id * 40 + (year - 2000)
GAPNAMES = ['first listen of the user', 'before the previous listen (out of order)', 'same second', '1-29 s', '30-119 s',
            '2-9 min', '10-59 min', '1-5 h', '6-23 h', '1 day or more']


n = 0; bad = 0; t0 = time.time(); find = bytes.find; index = bytes.index
for line in iter_lines(a.dumps):
    if not line.startswith(b'{"user_id":'): bad += 1; continue
    j = find(line, b',"timestamp":')
    try:
        uid = int(line[11:index(line, b',', 11)]); ts = int(line[j + 13:index(line, b',', j + 13)])
        d = ts // 86400; yi = DAY_Y[d]
    except (ValueError, IndexError): bad += 1; continue
    if d < 0 or yi < 0 or yi > 39: bad += 1; continue
    n += 1; uy = uid * 40 + yi; hour = ts // 3600 % 24; wd = (d + 3) % 7
    C_um[uy * 13 + DAY_M[d]] += 1; C_h[uy * 24 + hour] += 1; C_w[uy * 7 + wd] += 1
    G_ywh[(yi * 7 + wd) * 24 + hour] += 1; G_day[d] += 1
    p = last.get(uid); last[uid] = ts
    if p is None: b = 0
    else:
        g = ts - p
        b = 1 if g < 0 else 2 if g == 0 else 3 if g < 30 else 4 if g < 120 else 5 if g < 600 else 6 if g < 3600 else 7 if g < 21600 else 8 if g < 86400 else 9
    C_gap[uy * 10 + b] += 1
    if n % 50000000 == 0:
        print('%d million listens, %d users so far, %.0f s' % (n // 1000000, len(last), time.time() - t0), flush=True)
print('main pass done: %d listens, %d unreadable, %.0f s. Writing reports...' % (n, bad, time.time() - t0), flush=True)

# ---------- per user and year file ----------
prof = {}
for k, c in C_um.items():
    uy, m = divmod(k, 13); prof.setdefault(uy, [0] * 53)[m - 1] += c
for k, c in C_h.items(): uy, h = divmod(k, 24); prof[uy][12 + h] += c
for k, c in C_w.items(): uy, w = divmod(k, 7); prof[uy][36 + w] += c
for k, c in C_gap.items(): uy, b = divmod(k, 10); prof[uy][43 + b] += c
with open(os.path.join(a.out, 'user_year_profile.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['user_id', 'year', 'listens', 'active_months'] + ['m%02d' % i for i in range(1, 13)] +
               ['h%02d_utc' % i for i in range(24)] + ['weekday_%d_mon0' % i for i in range(7)] +
               ['gap_' + str(i) for i in range(10)])
    for uy in sorted(prof):
        r = prof[uy]; uid, yi = divmod(uy, 40)
        w.writerow([uid, 2000 + yi, sum(r[:12]), sum(1 for x in r[:12] if x)] + r)

# ---------- report ----------
L = []; comma = '{:,}'.format
L.append('PROFILE REPORT  (listens read: %s, unreadable lines: %d, time %.0f s)' % (comma(n), bad, time.time() - t0))
L.append('Peak memory: %.1f GB' % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 ** 3 if sys.platform == 'darwin' else 1024.0 ** 2)))
gy = dd0(lambda: [0] * 10); uyc = collections.Counter()
for k, c in C_gap.items(): uy, b = divmod(k, 10); gy[uy % 40][b] += c
for uy in prof: uyc[uy % 40] += 1
tot_gap = [sum(gy[y][b] for y in gy) for b in range(10)]
L += ['', '1. Order check: listens that come before the same user\'s previous listen in the file: %s (%.4f%% of listens)' % (comma(tot_gap[1]), 100.0 * tot_gap[1] / max(1, n)),
      '   (0 means the dump is in time order, so the gap numbers below are trustworthy)']
L += ['', '2. Active months per user and year (share of user-years with listens in this many months of the year)',
      '   year | user-years | 1 month | 2-3 | 4-6 | 7-11 | all 12']
am = dd0(lambda: [0] * 5)
for uy, r in prof.items():
    k = sum(1 for x in r[:12] if x); am[uy % 40][0 if k == 1 else 1 if k <= 3 else 2 if k <= 6 else 3 if k <= 11 else 4] += 1
for yi in sorted(am):
    t = sum(am[yi]); L.append('   %d | %s | ' % (2000 + yi, comma(t)) + ' | '.join('%.0f%%' % (100.0 * v / t) for v in am[yi]))
ym = dd0(lambda: [0] * 12)
for k, c in C_um.items(): uy, m = divmod(k, 13); ym[uy % 40][m - 1] += c
L += ['', '3. Listens by calendar month (millions)', '   year | ' + ' | '.join('%02d' % i for i in range(1, 13))]
for yi in sorted(ym): L.append('   %d | ' % (2000 + yi) + ' | '.join('%.1f' % (v / 1e6) for v in ym[yi]))
L += ['', '4. Share of listens by time of day (UTC, 3-hour blocks 00-02, 03-05, ... 21-23) and by weekday (Mon..Sun), per year']
yh = dd0(lambda: [0] * 24); yw = dd0(lambda: [0] * 7)
for k, c in C_h.items(): uy, h = divmod(k, 24); yh[uy % 40][h] += c
for k, c in C_w.items(): uy, w_ = divmod(k, 7); yw[uy % 40][w_] += c
for yi in sorted(yh):
    t = sum(yh[yi]); b3 = [sum(yh[yi][i:i + 3]) for i in range(0, 24, 3)]
    L.append('   %d | hours: ' % (2000 + yi) + ' '.join('%.0f%%' % (100.0 * v / t) for v in b3) + ' | weekdays: ' + ' '.join('%.0f%%' % (100.0 * v / t) for v in yw[yi]))
L += ['', '5. Weekday by 3-hour block, all listens 2016-2025 (share of those listens, UTC)', '   day | ' + ' | '.join('%02d-%02d' % (i, i + 2) for i in range(0, 24, 3))]
tt = sum(G_ywh[(yi * 7 + w_) * 24 + h] for yi in range(16, 26) for w_ in range(7) for h in range(24)) or 1
for w_, nm in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
    L.append('   %s | ' % nm + ' | '.join('%.1f%%' % (100.0 * sum(G_ywh[(yi * 7 + w_) * 24 + h] for yi in range(16, 26) for h in range(i, i + 3)) / tt) for i in range(0, 24, 3)))
L += ['', '6. Time since the same user\'s previous listen, share of listens per year', '   year | ' + ' | '.join(GAPNAMES[2:])]
for yi in sorted(gy):
    t = sum(gy[yi]) - gy[yi][0] - gy[yi][1] or 1
    L.append('   %d | ' % (2000 + yi) + ' | '.join('%.1f%%' % (100.0 * gy[yi][b] / t) for b in range(2, 10)))
L += ['   (same second = bulk uploads or duplicates; 30-119 s and 2-9 min is normal song-by-song listening)']
L += ['', '7. The 20 busiest days (all users together)']
for d in sorted(range(ND), key=lambda i: -G_day[i])[:20]:
    x = datetime.date.fromordinal(base + d); L.append('   %s: %s listens (%.2f%% of that year)' % (x, comma(G_day[d]), 100.0 * G_day[d] / max(1, sum(ym[x.year - 2000]))))
text = '\n'.join(L); open(os.path.join(a.out, 'user_year_profile_overview.txt'), 'w', encoding='utf-8').write(text + '\n'); print(text)
