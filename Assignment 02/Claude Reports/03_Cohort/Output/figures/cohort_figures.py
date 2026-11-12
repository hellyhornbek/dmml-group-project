#!/usr/bin/env python3
"""Draws the figures for the cohort step from csv files made by ../../Scripts/cohort_overview.py and build_cohort.py.

Reads:  ../cohort_funnel.csv, ../cohort_per_year.csv, ../cohort_users.csv  (this script sits in Output/figures)
Writes: 01_...png to 03_...png in the same folder. Stops with an error if the totals are not 101,881 users / 13,515 cohort users.
Needs: matplotlib, numpy.   Run from anywhere:  python3 cohort_figures.py
"""
import os, csv
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__)); IN = os.path.join(HERE, '..'); OUT = HERE
rd = lambda n: list(csv.DictReader(open(os.path.join(IN, n), encoding='utf8')))
fun, py, cu = rd('cohort_funnel.csv'), rd('cohort_per_year.csv'), rd('cohort_users.csv')
assert int(fun[0]['users']) == 101881 and int(fun[3]['users']) == 13515 == len(cu)
assert sum(int(r['dump_listens']) for r in py) == 2990440915 and sum(int(r['cohort_listens']) for r in py) == 1462060308
assert int(fun[1]['users']) + int(fun[2]['users']) + int(fun[3]['users']) == 101881
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

# 01 who is left after each rule (users and listens, share of the whole dump)
labels = ['Removed: a year above\n40,000 listens', 'Removed: no 5 years in a row\nwith 2,000 to 40,000', 'Cohort']
cols = [ORANGE, '#b9b8ae', BLUE]
us = [int(r['users']) for r in fun[1:]]; ls = [int(r['listens']) for r in fun[1:]]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
for ax, vals, tot, ttl in [(a1, us, 101881, 'Share of users'), (a2, ls, 2990440915, 'Share of listens')]:
    style(ax, 'x'); yy = np.arange(3)[::-1]
    ax.barh(yy, [v / tot * 100 for v in vals], color=cols, height=0.62)
    for y, v in zip(yy, vals): ax.text(v / tot * 100 + 1.5, y, '%s (%.1f%%)' % (format(v, ','), v / tot * 100), va='center', fontsize=8.5, color=INK)
    ax.set_xlim(0, 135); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_title(ttl)
a1.set_yticks(np.arange(3)[::-1]); a1.set_yticklabels(labels, fontsize=8.5)
save(fig, '01_users_and_listens_after_each_rule.png', 'All 101,881 users and 2,990,440,915 listens in the dump. Every user falls in exactly one of the three groups.')

# 02 share of the dump's listens that is in the cohort, per year
yrs = [int(r['year']) for r in py if int(r['year']) >= 2005]
sel = [r for r in py if int(r['year']) >= 2005]
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.5, 6), sharex=True)
style(a1); w = 0.72
a1.bar(yrs, [int(r['dump_listens']) / 1e6 for r in sel], color='#b9b8ae', width=w, label='Whole dump')
a1.bar(yrs, [int(r['cohort_listens']) / 1e6 for r in sel], color=BLUE, width=w, label='Cohort')
a1.set_ylabel('Listens (millions)'); a1.set_title('Listens per year: whole dump and cohort'); a1.legend(frameon=False, loc='upper left')
style(a2); a2.plot(yrs, [int(r['cohort_listens']) / int(r['dump_listens']) * 100 for r in sel], color=ORANGE, lw=2.4, marker='o', ms=4)
a2.set_ylim(0, 100); a2.set_ylabel('% of the year\'s listens'); a2.set_title('Share of each year that is in the cohort'); a2.set_xticks(yrs[::2])
save(fig, '02_cohort_share_of_dump_per_year.png', '2026 is partial (the dump ends on 1 Nov 2026).')

# 03 length of the qualifying window
ln = [int(r['window_end']) - int(r['window_start']) + 1 for r in cu]
v, c = np.unique(ln, return_counts=True)
fig, ax = plt.subplots(figsize=(8.5, 3.8)); style(ax); ax.bar(v, c, color=BLUE, width=0.72)
ax.set_xlabel('Years in the first run of consecutive qualifying years'); ax.set_ylabel('Users'); ax.set_title('How long is each user\'s qualifying run?')
ax.set_xticks(v[::2]); ax.text(0.98, 0.9, 'minimum allowed: 5', transform=ax.transAxes, ha='right', fontsize=8.5, color=MUTE)
save(fig, '03_length_of_qualifying_run.png', '13,515 users. Only the first run is counted; some users have more than one.')
