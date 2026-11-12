#!/usr/bin/env python3
"""Pass 1: counts listens per user (and per user and year) and writes an overview.
Usage: python3 user_counts.py OUT_FOLDER dump1.tar.zst [dump2.tar.zst ...]
Writes OUT_FOLDER/user_counts.csv (stays on your computer) and OUT_FOLDER/user_counts_overview.txt (aggregates only).
"""
import sys, os, csv, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lbstream import iter_lines, LINE_RE, year_of

out = sys.argv[1]; files = sys.argv[2:]
if not files: sys.exit(__doc__)
os.makedirs(out, exist_ok=True)
# Fast parsing: the user id is the first number, the timestamp follows the user name.
# We count per (user, year) with integer keys, which keeps memory small even for billions of listens.
per_user_year = collections.Counter()   # key = user_id * 10000 + year
YEAR_BY_DAY = [year_of(d * 86400) for d in range(0, 47000)]   # day number since 1970 -> year (up to 2098)
n = 0; bad = 0; t0 = time.time()
find = bytes.find; index = bytes.index
for line in iter_lines(files):
    j = find(line, b',"timestamp":')
    if j < 0 or not line.startswith(b'{"user_id":'): bad += 1; continue
    try:
        ts = int(line[j + 13:index(line, b',', j + 13)])
        per_user_year[int(line[11:index(line, b',', 11)]) * 10000 + YEAR_BY_DAY[ts // 86400]] += 1
    except (ValueError, IndexError):
        bad += 1; continue
    n += 1
    if n % 20000000 == 0:
        print('%d million listens read, %d user-years, %.0f s' % (n // 1000000, len(per_user_year), time.time() - t0), flush=True)

users = collections.defaultdict(lambda: [0, 9999, 0, 0])   # total, first_year, last_year, years_active
year_users = collections.Counter(); year_listens = collections.Counter()
for k, c in per_user_year.items():
    u, y = divmod(k, 10000)
    r = users[u]; r[0] += c; r[1] = min(r[1], y); r[2] = max(r[2], y); r[3] += 1
    year_users[y] += 1; year_listens[y] += c
with open(os.path.join(out, 'user_counts.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['user_id', 'total_listens', 'first_year', 'last_year', 'years_active'])
    for u in sorted(users): w.writerow([u] + users[u])

tot = sorted((r[0] for r in users.values()), reverse=True)
U = len(tot); S = sum(tot)
def pct(p): return tot[min(U - 1, int(U * (1 - p / 100)))]
def share(top_frac):
    k = max(1, int(U * top_frac)); return 100.0 * sum(tot[:k]) / S
buckets = [(1, 9), (10, 99), (100, 999), (1000, 9999), (10000, 99999), (100000, 10 ** 12)]
lines = []
lines.append('Listens read: %d (lines that could not be read: %d)' % (n, bad))
lines.append('Users: %d' % U)
lines.append('')
lines.append('Users by number of listens in total')
for a, b in buckets:
    cnt = sum(1 for t in tot if a <= t <= b)
    lines.append('  %s%s listens: %d users (%.1f%%), holding %.1f%% of all listens' % (
        '{:,}'.format(a), ('-' + '{:,}'.format(b)) if b < 10 ** 12 else '+', cnt, 100.0 * cnt / U,
        100.0 * sum(t for t in tot if a <= t <= b) / S))
lines.append('')
lines.append('Listens per user: median %d, 90th pct %d, 99th pct %d, 99.9th pct %d, largest %d' % (pct(50), pct(90), pct(99), pct(99.9), tot[0]))
lines.append('Share of all listens held by the top 0.1%% of users: %.1f%%, top 1%%: %.1f%%, top 10%%: %.1f%%' % (share(0.001), share(0.01), share(0.10)))
lines.append('')
lines.append('Per year (users with at least one listen that year, listens)')
for y in sorted(year_users): lines.append('  %d: %d users, %d listens' % (y, year_users[y], year_listens[y]))
lines.append('')
lines.append('Users by number of different years with listens')
ya = collections.Counter(r[3] for r in users.values())
for k in sorted(ya): lines.append('  %d years: %d users' % (k, ya[k]))

# ---------- extra sections: worked out from the counts above, no extra reading of the dump ----------
WIN_A, WIN_B = 2016, 2025            # window for the filter table
comma = '{:,}'.format
ycounts = collections.defaultdict(list)      # year -> listens per user in that year
user_years = collections.defaultdict(dict)   # user -> {year: listens}
for k, c in per_user_year.items():
    u, y = divmod(k, 10000)
    ycounts[y].append(c)
    user_years[u][y] = c
maxy = max(year_users) if year_users else 0

def pct_of(s, p):
    return s[min(len(s) - 1, int(len(s) * (1 - p / 100.0)))]

lines.append('')
lines.append('Skew per year (counted per user and year)')
for y in sorted(ycounts):
    s = sorted(ycounts[y], reverse=True); m = len(s); t = sum(s)
    lines.append('  %d: %s users | median %d | 90th pct %d | 99th pct %d | top 1%% hold %.1f%% | top 10%% hold %.1f%%' % (
        y, comma(m), pct_of(s, 50), pct_of(s, 90), pct_of(s, 99),
        100.0 * sum(s[:max(1, int(m * 0.01))]) / t, 100.0 * sum(s[:max(1, int(m * 0.10))]) / t))

levels = [(1, 99, 'under 100'), (100, 999, '100-999'), (1000, 4999, '1,000-4,999'),
          (5000, 14999, '5,000-14,999'), (15000, 10 ** 12, '15,000+')]
lines.append('')
lines.append('Users per year by number of listens that year: users (% of users / % of listens)')
for y in sorted(ycounts):
    s = ycounts[y]; t = sum(s); m = len(s); parts = []
    for a, b, name in levels:
        sel = [c for c in s if a <= c <= b]
        parts.append('%s: %s (%.0f%%/%.0f%%)' % (name, comma(len(sel)), 100.0 * len(sel) / m, 100.0 * sum(sel) / t))
    lines.append('  %d | ' % y + ' | '.join(parts))

first = collections.Counter(r[1] for r in users.values()); last = collections.Counter(r[2] for r in users.values())
lines.append('')
lines.append('Users by first year seen and by last year seen')
for y in sorted(set(first) | set(last)):
    lines.append('  %d: %s users first seen, %s users last seen' % (y, comma(first[y]), comma(last[y])))

cohort = collections.defaultdict(list)
for u, r in users.items(): cohort[r[1]].append(u)
lines.append('')
lines.append('Of the users first seen in a year, how many also have listens 1, 3 and 5 years later')
for y0 in sorted(cohort):
    if y0 < 2005 or y0 > maxy - 1: continue
    c = cohort[y0]
    def ret(off):
        if y0 + off > maxy: return 'n/a'
        return '%.0f%%' % (100.0 * sum(1 for u in c if (y0 + off) in user_years[u]) / len(c))
    lines.append('  first seen %d (%s users): +1 year %s, +3 years %s, +5 years %s' % (y0, comma(len(c)), ret(1), ret(3), ret(5)))

def longest_run(ys):
    best = run = 0; prev = None
    for y in sorted(ys):
        run = run + 1 if prev is not None and y == prev + 1 else 1
        best = max(best, run); prev = y
    return best
runs = collections.Counter(longest_run(d) for d in user_years.values())
lines.append('')
lines.append('Users by longest run of consecutive years with listens (any years)')
for K in (2, 3, 5, 8, 10):
    lines.append('  at least %d years in a row: %s users' % (K, comma(sum(v for k, v in runs.items() if k >= K))))

Ks = (3, 5, 8, 10); Ms = (10, 50, 100, 500, 1000)
for WIN_A, WIN_B in ((2016, 2025), (2006, 2015)):
    tab = {(K, M): 0 for K in Ks for M in Ms}
    for d in user_years.values():
        sc = sorted((c for y, c in d.items() if WIN_A <= y <= WIN_B), reverse=True)
        for K in Ks:
            if len(sc) >= K:
                kth = sc[K - 1]
                for M in Ms:
                    if kth >= M: tab[(K, M)] += 1
    lines.append('')
    lines.append('Users who would pass a filter in %d-%d: at least K years (not necessarily in a row), each with at least M listens' % (WIN_A, WIN_B))
    lines.append('  columns: M = ' + ' | '.join(str(M) for M in Ms))
    for K in Ks:
        lines.append('  at least %d years: ' % K + ' | '.join(comma(tab[(K, M)]) for M in Ms))

text = '\n'.join(lines)
open(os.path.join(out, 'user_counts_overview.txt'), 'w').write(text + '\n')
print(text)
