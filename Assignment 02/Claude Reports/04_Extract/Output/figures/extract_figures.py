#!/usr/bin/env python3
"""Draws the figures for the extract from the three csv files made by ../../Scripts/extract_overview.py.

Reads:  ../extract_per_year.csv, ../extract_top_sources.csv, ../extract_per_user.csv  (this script sits in Output/figures)
Writes: 01_...png to 06_...png in the same folder.
The script stops with an error if the totals are not 1,462,060,308 rows and 13,515 users.
Needs: matplotlib, numpy.   Run from anywhere:  python3 extract_figures.py
"""
import os, csv
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__)); IN = os.path.join(HERE, '..'); OUT = HERE
rd = lambda n: list(csv.DictReader(open(os.path.join(IN, n), encoding='utf8')))
py, src, pu = rd('extract_per_year.csv'), rd('extract_top_sources.csv'), rd('extract_per_user.csv')
assert sum(int(r['rows']) for r in py) == 1462060308, 'rows per year do not add up'
assert len(pu) == 13515 and sum(int(r['rows']) for r in pu) == 1462060308, 'per-user table does not add up'
print('checks passed')

BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
INK, MUTE, GRID = '#0b0b0b', '#52514e', '#e1e0d9'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': '#c3c2b7', 'axes.labelcolor': MUTE,
    'xtick.color': MUTE, 'ytick.color': MUTE, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 200,
    'axes.facecolor': 'white', 'figure.facecolor': 'white', 'axes.titlesize': 12, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left'})
def style(ax, grid='y'): ax.grid(axis=grid, color=GRID, linewidth=0.8); ax.set_axisbelow(True)
def save(fig, name, note=None):
    if note: fig.text(0.01, 0.005, note, fontsize=7.5, color=MUTE, ha='left', va='bottom')
    fig.tight_layout(rect=(0, 0.03 if note else 0, 1, 1)); fig.savefig(os.path.join(OUT, name)); plt.close(fig); print('wrote', name)
PART = '2026 is partial (the dump ends on 1 Nov 2026)'
ys = [int(r['year']) for r in py if int(r['year']) >= 2005]
get = lambda col, f=float: [f(r[col]) for r in py if int(r['year']) >= 2005]

# 01 rows and users per year
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.5, 6), sharex=True)
style(a1); a1.bar(ys, get('rows', int), color=BLUE, width=0.72); a1.yaxis.set_major_formatter(FuncFormatter(lambda v, p: '%g' % (v / 1e6)))
a1.set_ylabel('Listens (millions)'); a1.set_title('Listens and users per year in the extract')
style(a2); a2.plot(ys, get('users', int), color=ORANGE, lw=2.4, marker='o', ms=4); a2.set_ylabel('Users'); a2.set_ylim(0, 13500)
a2.set_xticks(ys[::2]); a2.axhline(13515, color=MUTE, lw=0.8, ls='--'); a2.text(2005.2, 12600, 'all 13,515 cohort users', fontsize=8, color=MUTE)
save(fig, '01_listens_and_users_per_year.png', PART + '. All rows, including repeated rows.')

# 02 field coverage by year
fig, ax = plt.subplots(figsize=(8.5, 4.2)); style(ax)
ys2 = [y for y in ys if y >= 2006]; sel = lambda col: [float(r[col]) * 100 for r in py if int(r['year']) in ys2]
for col, name, c in [('share_recording_mbid', 'Has a MusicBrainz recording id', BLUE), ('share_duration_ms', 'Has a song length', ORANGE), ('share_ms_played', 'Has time played', AQUA)]:
    ax.plot(ys2, sel(col), color=c, lw=2.4, marker='o', ms=3.5)
ax.text(2006.3, 30, 'MusicBrainz recording id', color=BLUE, fontsize=8.5)
ax.text(2021.2, 44, 'Song length', color=ORANGE, fontsize=8.5, ha='right'); ax.text(2024.6, 8, 'Time played', color=AQUA, fontsize=8.5, ha='right')
ax.set_ylim(0, 60); ax.set_ylabel('% of listens in that year'); ax.set_title('Which fields are filled in, by year')
ax.set_xticks(ys2[::2])
save(fig, '02_field_coverage_per_year.png', 'Share of rows with a value, all rows of the extract. ' + PART + '.')

# 03 source known + repeated rows
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.5, 5.4), sharex=True)
style(a1); a1.plot(ys, [v * 100 for v in get('share_source')], color=BLUE, lw=2.4, marker='o', ms=3.5); a1.set_ylim(0, 100); a1.set_ylabel('% of listens'); a1.set_title('Listens with a known source (submitting app)')
style(a2); a2.bar(ys, [v * 100 for v in get('dup_share')], color=ORANGE, width=0.72); a2.set_ylabel('% of listens'); a2.set_title('Listens flagged as exact repeats (same user, second, artist, track)')
a2.set_xticks(ys[::2])
save(fig, '03_source_and_repeats_per_year.png', PART + '.')

# 04 top sources
fig, ax = plt.subplots(figsize=(8.5, 4.8)); style(ax, 'x')
top = src[:12][::-1]; labs = [r['source'] if len(r['source']) < 48 else r['source'][:45] + '...' for r in top]
vals = [float(r['share_of_all_rows']) * 100 for r in top]
ax.barh(labs, vals, color=[ORANGE if r['source'] == '(none)' else BLUE for r in top], height=0.65)
for i, v in enumerate(vals): ax.text(v + 0.5, i, '%.1f%%' % v, va='center', fontsize=8.5)
ax.set_xlim(0, 44); ax.set_xlabel('% of all rows'); ax.set_title('Which apps sent the listens')
save(fig, '04_top_sources.png', 'Top 12 of the 30 in extract_top_sources.csv. "(none)" = no source recorded (orange).')

# 05 listens per user
fig, ax = plt.subplots(figsize=(8.5, 4)); style(ax)
v = np.array([int(r['rows']) for r in pu]); ax.hist(np.log10(v), bins=40, color=BLUE, edgecolor='white', linewidth=0.5)
ax.set_xticks([3, 4, 5, 6]); ax.set_xticklabels(['1,000', '10,000', '100,000', '1,000,000']); ax.set_xlabel('Listens of a user over their whole history (log scale)')
ax.set_ylabel('Users'); ax.set_title('How many listens does each user have?')
ax.text(0.98, 0.9, 'median %s\nlargest %s' % ('{:,.0f}'.format(np.median(v)), '{:,.0f}'.format(v.max())), transform=ax.transAxes, ha='right', va='top', fontsize=9, color=MUTE)
save(fig, '05_listens_per_user.png', '13,515 users. Each user is counted once.')

# 06 active years per user
fig, ax = plt.subplots(figsize=(8.5, 3.9)); style(ax)
ay = np.array([int(r['active_years']) for r in pu]); ks = sorted(set(ay))
ax.bar(ks, [int((ay == k).sum()) for k in ks], color=BLUE, width=0.75); ax.set_xlabel('Number of different years with at least one listen'); ax.set_ylabel('Users')
ax.set_title('How many years does each user appear in?'); ax.set_xticks(range(min(ks), max(ks) + 1, 2))
save(fig, '06_active_years_per_user.png', 'The cohort rule needs 5 years in a row, so no user has fewer than 5.')

# 07 how many users in each listening-amount group, per year
BK = ['under 2,000', '2,000-4,000', '4,000-8,000', '8,000-16,000', '16,000-32,000', '32,000-40,000']
BC = ['#d9d8cf', '#9ec5f4', '#5598e7', '#2a78d6', '#1c5cab', '#0d366b']
ub = rd('extract_user_year_buckets.csv')
assert sum(int(r['users']) for r in ub) == 170653, 'user-years do not add up'
yb = sorted({int(r['year']) for r in ub if int(r['year']) >= 2005})
M = {(int(r['year']), r['bucket']): int(r['users']) for r in ub}
tot = [sum(M[(y, b)] for b in BK) for y in yb]
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.5, 7), sharex=True)
for ax, share in ((a1, False), (a2, True)):
    style(ax); bottom = np.zeros(len(yb))
    for b, c in zip(BK, BC):
        v = np.array([M[(y, b)] for y in yb], float)
        if share: v = v / np.array(tot) * 100
        ax.bar(yb, v, bottom=bottom, color=c, width=0.72, label=b, edgecolor='white', linewidth=0.4); bottom += v
a1.set_ylabel('Users'); a1.set_title('Users per year by number of listens in that year')
a1.legend(title='Listens in the year', frameon=False, fontsize=8, title_fontsize=8, loc='upper left', ncol=2)
a2.set_ylabel('% of users in that year'); a2.set_title('Same, as a share of the year\'s users'); a2.set_ylim(0, 100); a2.set_xticks(yb[::2])
save(fig, '07_users_by_listens_per_year.png', 'Each user-year counted once, raw listens including repeats. 2026 is partial (10 of 12 months), so its users sit in lower groups.')
