#!/usr/bin/env python3
"""Draws one figure per table of user_counts_overview.txt (the output of user_counts.py).

Reads:  ../user_counts_overview.txt   (this script sits in Output/figures)
Writes: 01_...png to 12_...png in the same folder (one png per table)

All numbers are read from the overview file, nothing is typed by hand. The script stops with an
error if the parsed numbers do not add up to the totals in the file (2,990,440,915 listens, 101,881 users).
Needs: matplotlib. Run from anywhere:  python3 user_counts_figures.py
"""
import os, re
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'user_counts_overview.txt')   # this script sits in Output/figures
OUT = HERE
os.makedirs(OUT, exist_ok=True)
txt = open(SRC, encoding='utf8').read()
num = lambda s: int(s.replace(',', ''))

# ---------- colours (blue, orange, aqua; blue steps for ordered levels) ----------
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
STEPS = ['#9ec5f4', '#5598e7', '#2a78d6', '#1c5cab', '#0d366b']
INK, MUTE, GRID = '#0b0b0b', '#52514e', '#e1e0d9'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': '#c3c2b7',
    'axes.labelcolor': MUTE, 'xtick.color': MUTE, 'ytick.color': MUTE, 'axes.spines.top': False,
    'axes.spines.right': False, 'figure.dpi': 200, 'axes.facecolor': 'white', 'figure.facecolor': 'white',
    'axes.titlesize': 12, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left'})

def style(ax, grid='y'):
    ax.grid(axis=grid, color=GRID, linewidth=0.8); ax.set_axisbelow(True)
def save(fig, name, note=None):
    if note: fig.text(0.01, 0.005, note, fontsize=7.5, color=MUTE, ha='left', va='bottom')
    fig.tight_layout(rect=(0, 0.03 if note else 0, 1, 1)); fig.savefig(os.path.join(OUT, name)); plt.close(fig); print('wrote', name)
M = FuncFormatter(lambda v, p: '%g' % (v / 1e6))
K = FuncFormatter(lambda v, p: '{:,.0f}'.format(v / 1e3) if v >= 1000 else '%g' % v)
PART = '2026 is partial (the dump ends on 1 Nov 2026)'

def section(title_start):
    """Text block that starts with the heading line and runs to the next blank line."""
    i = txt.index(title_start); j = txt.find('\n\n', i)
    return txt[i:j if j > 0 else len(txt)]

TOTAL_LISTENS = num(re.search(r'Listens read: (\d+)', txt).group(1))
TOTAL_USERS = num(re.search(r'Users: (\d+)', txt).group(1))

# ---------- parse ----------
b = re.findall(r'^\s+([\d,]+\+?(?:-[\d,]+)?) listens: (\d+) users \(([\d.]+)%\), holding ([\d.]+)% of all listens', txt, re.M)
buckets = [(x[0], int(x[1]), float(x[2]), float(x[3])) for x in b]
top = re.search(r'top 0\.1% of users: ([\d.]+)%, top 1%: ([\d.]+)%, top 10%: ([\d.]+)%', txt)
top = [float(top.group(i)) for i in (1, 2, 3)]
pct = re.search(r'median (\d+), 90th pct (\d+), 99th pct (\d+), 99\.9th pct (\d+), largest (\d+)', txt)
py = {int(y): (num(u), num(l)) for y, u, l in re.findall(r'^\s+(\d{4}): ([\d,]+) users, ([\d,]+) listens', section('Per year (users'), re.M)}
ya = {int(k): num(u) for k, u in re.findall(r'^\s+(\d+) years: ([\d,]+) users', section('Users by number of different years'), re.M)}
sk = {int(m[0]): [num(x) for x in m[2:5]] + [float(m[5]), float(m[6])] for m in
      re.findall(r'^\s+(\d{4}): ([\d,]+) users \| median (\d+) \| 90th pct (\d+) \| 99th pct (\d+) \| top 1% hold ([\d.]+)% \| top 10% hold ([\d.]+)%', txt, re.M)}
sk_users = {int(m[0]): num(m[1]) for m in re.findall(r'^\s+(\d{4}): ([\d,]+) users \| median', txt, re.M)}
lv_names = ['under 100', '100-999', '1,000-4,999', '5,000-14,999', '15,000+']
lv = {}
for line in section('Users per year by number of listens').splitlines()[1:]:
    m = re.match(r'\s+(\d{4}) \|', line)
    if m: lv[int(m.group(1))] = [int(re.search(re.escape(n) + r': ([\d,]+) \(', line).group(1).replace(',', '')) for n in lv_names]
fl = {int(y): (num(a), num(c)) for y, a, c in re.findall(r'^\s+(\d{4}): ([\d,]+) users first seen, ([\d,]+) users last seen', txt, re.M)}
ret = {}
for m in re.finditer(r'first seen (\d{4}) \(([\d,]+) users\): \+1 year (\S+), \+3 years (\S+), \+5 years (\S+)', txt):
    ret[int(m.group(1))] = [None if v == 'n/a' else float(v.rstrip('%')) for v in m.groups()[2:]]
runs = [(int(k), num(u)) for k, u in re.findall(r'at least (\d+) years in a row: ([\d,]+) users', txt)]
filt = {}
for m in re.finditer(r'filter in (\d{4})-(\d{4}).*?\n\s+columns: M = ([\d |]+)\n((?:\s+at least \d+ years: .*\n?)+)', txt):
    Ms = [int(x) for x in m.group(3).split('|')]
    rows = [(int(r[0]), [num(x) for x in r[1].split('|')]) for r in re.findall(r'at least (\d+) years: ([\d, |]+)', m.group(4))]
    filt[(m.group(1), m.group(2))] = (Ms, rows)

# ---------- checks: the parsed numbers must add up ----------
assert sum(l for u, l in py.values()) == TOTAL_LISTENS, 'listens per year do not add up'
assert sum(ya.values()) == TOTAL_USERS, 'users by years active do not add up'
assert sum(x[1] for x in buckets) == TOTAL_USERS, 'buckets do not add up'
assert all(sum(v) == sk_users[y] for y, v in lv.items()), 'levels per year do not add up'
assert sum(a for a, c in fl.values()) == TOTAL_USERS and sum(c for a, c in fl.values()) == TOTAL_USERS
print('checks passed:', TOTAL_LISTENS, 'listens,', TOTAL_USERS, 'users')

import numpy as np
yrs = sorted(py); yrs05 = [y for y in yrs if y >= 2005]

# 01 users by total number of listens
fig, ax = plt.subplots(figsize=(8, 4.2)); style(ax)
x = np.arange(len(buckets)); w = 0.38
ax.bar(x - w/2, [b[2] for b in buckets], w, color=BLUE, label='Share of users')
ax.bar(x + w/2, [b[3] for b in buckets], w, color=ORANGE, label='Share of all listens')
for i, bk in enumerate(buckets):
    ax.text(i - w/2, bk[2] + 1, '%.0f%%' % bk[2], ha='center', fontsize=8.5)
    ax.text(i + w/2, bk[3] + 1, '%.0f%%' % bk[3], ha='center', fontsize=8.5)
ax.set_xticks(x); ax.set_xticklabels([b[0].replace(',', ',​') + '\nlistens' for b in buckets], fontsize=8.5)
ax.set_ylabel('% of all'); ax.set_ylim(0, 75); ax.legend(frameon=False, loc='upper left')
ax.set_title('A few heavy users account for most listens')
save(fig, '01_users_by_total_listens.png', 'Source: user_counts_overview.txt, all %s users.' % '{:,}'.format(TOTAL_USERS))

# 02 concentration at the top
fig, ax = plt.subplots(figsize=(6.5, 3.6)); style(ax)
labs = ['Top 0.1%\nof users', 'Top 1%\nof users', 'Top 10%\nof users']
ax.bar(labs, top, color=BLUE, width=0.55)
for i, v in enumerate(top): ax.text(i, v + 1.5, '%.1f%%' % v, ha='center', fontsize=10)
ax.set_ylim(0, 85); ax.set_ylabel('% of all listens held'); ax.set_title('Share of all listens held by the heaviest users')
save(fig, '02_share_held_by_top_users.png', 'Median user: {:,} listens; largest user: {:,}.'.format(int(pct.group(1)), int(pct.group(5))))

# 03 listens per year
fig, ax = plt.subplots(figsize=(8.5, 3.9)); style(ax)
ax.bar([str(y) for y in yrs05], [py[y][1] for y in yrs05], color=BLUE, width=0.72)
ax.yaxis.set_major_formatter(M); ax.set_ylabel('Listens (millions)'); ax.set_title('Listens per year')
ax.set_xticks(range(0, len(yrs05), 2)); ax.set_xticklabels([str(y) for y in yrs05][::2])
ax.annotate('2005: first big\nhistory imports', (0, py[2005][1]), xytext=(1.2, 120e6), fontsize=8, color=MUTE, arrowprops=dict(arrowstyle='-', color=MUTE))
save(fig, '03_listens_per_year.png', PART + '. Years 2002-2004 have under 4,000 listens each and are left out.')

# 04 users per year, and new users
fig, ax = plt.subplots(figsize=(8.5, 3.9)); style(ax)
ax.plot(yrs05, [py[y][0] for y in yrs05], color=BLUE, lw=2.4, marker='o', ms=4)
ax.plot(yrs05, [fl[y][0] for y in yrs05], color=ORANGE, lw=2.4, marker='o', ms=4)
ax.yaxis.set_major_formatter(K); ax.set_ylabel('Users (thousands)'); ax.set_title('Users per year, and users seen for the first time')
ax.text(2005.4, 17000, 'Users with a listen that year', color=BLUE, fontsize=9)
ax.text(2009.5, 4000, 'Users whose first listen is that year', color=ORANGE, fontsize=9)
save(fig, '04_users_per_year.png', PART + '.')

# 05 users by number of different years
fig, ax = plt.subplots(figsize=(8.5, 3.9)); style(ax)
ks = sorted(ya)
ax.bar(ks, [ya[k] for k in ks], color=BLUE, width=0.75)
ax.yaxis.set_major_formatter(K); ax.set_ylabel('Users (thousands)'); ax.set_xlabel('Number of different years with at least one listen')
ax.set_title('Most users appear in only one or two years'); ax.set_xticks(range(1, 26, 2))
ax.text(1, ya[1] + 900, '{:,}'.format(ya[1]), ha='center', fontsize=8.5)
ax.text(2, ya[2] + 900, '{:,}'.format(ya[2]), ha='center', fontsize=8.5)
save(fig, '05_users_by_years_active.png')

# 06 listens per user and year: percentiles
fig, ax = plt.subplots(figsize=(8.5, 4.0)); style(ax)
ys = [y for y in yrs05]
for i, (name, col) in enumerate([('Median user', BLUE), ('90th percentile', ORANGE), ('99th percentile', AQUA)]):
    ax.plot(ys, [sk[y][i] for y in ys], color=col, lw=2.4, marker='o', ms=3.5)
    ax.text(2026.3, sk[2026][i], name, color=col, fontsize=8.5, va='center')
ax.set_yscale('log'); ax.set_xlim(2004.5, 2029.5); ax.set_ylabel('Listens in that year (log scale)')
ax.set_title('Listens per user and year')
save(fig, '06_listens_per_user_year_percentiles.png', PART + '. A user is counted once per year.')

# 07 skew per year: top 1% and top 10% share
fig, ax = plt.subplots(figsize=(8.5, 3.9)); style(ax)
ax.plot(ys, [sk[y][3] for y in ys], color=BLUE, lw=2.4, marker='o', ms=3.5)
ax.plot(ys, [sk[y][4] for y in ys], color=ORANGE, lw=2.4, marker='o', ms=3.5)
ax.text(2026.3, sk[2026][3], 'Top 1% of\nusers', color=BLUE, fontsize=8.5, va='center')
ax.text(2026.3, sk[2026][4], 'Top 10% of\nusers', color=ORANGE, fontsize=8.5, va='center')
ax.set_xlim(2004.5, 2030); ax.set_ylim(0, 75); ax.set_ylabel('% of that year\'s listens'); ax.set_title('Share of each year\'s listens held by the heaviest users')
save(fig, '07_skew_per_year.png', PART + '.')

# 08 users per year by listen level (share of users)
fig, ax = plt.subplots(figsize=(8.5, 4.4)); style(ax)
ys2 = [y for y in ys if y in lv]
tot = [sum(lv[y]) for y in ys2]; bottom = np.zeros(len(ys2))
for i, n in enumerate(lv_names):
    v = np.array([100.0 * lv[y][i] / sum(lv[y]) for y in ys2])
    ax.bar([str(y) for y in ys2], v, bottom=bottom, color=STEPS[i], width=0.8, edgecolor='white', linewidth=0.6, label=n + ' listens')
    bottom += v
ax.set_xticks(range(0, len(ys2), 2)); ax.set_xticklabels([str(y) for y in ys2][::2])
ax.set_ylabel('% of users that year'); ax.set_ylim(0, 100); ax.set_title('How much users listen in a year')
ax.legend(frameon=False, ncol=5, fontsize=7.5, loc='upper center', bbox_to_anchor=(0.5, -0.1))
save(fig, '08_users_by_listens_in_year.png', PART + '. Years 2002-2004 have 5-7 users and are left out.')

# 09 first seen / last seen
fig, ax = plt.subplots(figsize=(8.5, 3.9)); style(ax)
fy = [y for y in sorted(fl) if y >= 2005]
x = np.arange(len(fy)); w = 0.4
ax.bar(x - w/2, [fl[y][0] for y in fy], w, color=BLUE, label='First seen that year')
ax.bar(x + w/2, [fl[y][1] for y in fy], w, color=ORANGE, label='Last seen that year')
ax.set_xticks(x[::2]); ax.set_xticklabels([str(y) for y in fy][::2]); ax.yaxis.set_major_formatter(K)
ax.set_ylabel('Users (thousands)'); ax.legend(frameon=False, loc='upper left'); ax.set_title('When users first and last appear')
save(fig, '09_first_and_last_year_seen.png', PART + ': everyone active in 2026 counts as "last seen 2026".')

# 10 retention
fig, ax = plt.subplots(figsize=(8.5, 4.0)); style(ax)
ry = sorted(ret)
for i, (name, col) in enumerate([('1 year later', BLUE), ('3 years later', ORANGE), ('5 years later', AQUA)]):
    pts = [(y, ret[y][i]) for y in ry if ret[y][i] is not None]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=col, lw=2.4, marker='o', ms=3.5)
    dy = {0: 0, 1: -4, 2: -10}[i]   # label offsets so the labels do not sit on the lines
    ax.text(pts[-1][0] + 0.25, pts[-1][1] + dy, name, color=col, fontsize=8.5, va='center')
ax.set_xlim(2004.5, 2028.5); ax.set_ylim(0, 100); ax.set_xlabel('Year the user was first seen')
ax.set_ylabel('% of those users with a listen later'); ax.set_title('Do users come back? Share still listening')
save(fig, '10_retention.png', 'Note: users first seen in 2017 or earlier return much more often than those first seen from 2018. 2026 is partial.')

# 11 longest run of consecutive years
fig, ax = plt.subplots(figsize=(7.5, 3.6)); style(ax, 'x')
ax.barh([('%d+ years' % k) for k, u in runs][::-1], [u for k, u in runs][::-1], color=BLUE, height=0.6)
for i, (k, u) in enumerate(runs[::-1]): ax.text(u + 600, i, '{:,}'.format(u), va='center', fontsize=9)
ax.xaxis.set_major_formatter(K); ax.set_xlabel('Users (thousands)'); ax.set_xlim(0, 56000)
ax.set_title('Users with a long unbroken run of years')
save(fig, '11_longest_run_of_consecutive_years.png', 'Run = consecutive calendar years with at least one listen.')

# 12 filter tables (heatmaps)
fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
cmap = matplotlib.colors.LinearSegmentedColormap.from_list('b', ['#e8f1fc', '#2a78d6', '#0d366b'])
for ax, key in zip(axes, [('2006', '2015'), ('2016', '2025')]):
    Ms, rows = filt[key]; Z = np.array([r[1] for r in rows], float)
    ax.imshow(Z, cmap=cmap, aspect='auto', vmin=0, vmax=Z.max() * 1.15)
    for i in range(Z.shape[0]):
        for j in range(Z.shape[1]):
            ax.text(j, i, '{:,.0f}'.format(Z[i, j]), ha='center', va='center', fontsize=8.5, color='white' if Z[i, j] > Z.max() * 0.45 else INK)
    ax.set_xticks(range(len(Ms))); ax.set_xticklabels(Ms); ax.set_yticks(range(len(rows))); ax.set_yticklabels(['%d years' % r[0] for r in rows])
    ax.set_xlabel('at least this many listens in each of those years'); ax.set_title('%s-%s' % key); ax.spines[:].set_visible(False)
fig.suptitle('How many users would pass a filter (at least K years, each with at least M listens)', x=0.01, ha='left', fontsize=11, fontweight='bold')
save(fig, '12_users_passing_a_filter.png', 'Years need not be in a row. Our final cohort rule (5 years in a row, 2,000-40,000 listens each) is stricter.')
