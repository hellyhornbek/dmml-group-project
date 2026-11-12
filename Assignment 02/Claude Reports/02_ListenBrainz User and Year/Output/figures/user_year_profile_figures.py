#!/usr/bin/env python3
"""Draws one figure per table (sections 2-7) of user_year_profile_overview.txt (the output of user_year_profile.py).

Reads:  ../user_year_profile_overview.txt   (this script sits in Output/figures)
Writes: 01_...png to 07_...png in the same folder.
Section 1 (order check) is a single number and section 8 (a 1% user sample) is not used.

All numbers are read from the overview file, nothing is typed by hand. The script stops with an error if
the parsed tables do not look right (shares must add up to about 100%). Needs: matplotlib, numpy.
Run from anywhere:  python3 user_year_profile_figures.py
"""
import os, re
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'user_year_profile_overview.txt'); OUT = HERE
txt = open(SRC, encoding='utf8').read()
num = lambda s: float(s.replace(',', '').rstrip('%'))

BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
STEPS = ['#9ec5f4', '#5598e7', '#2a78d6', '#1c5cab', '#0d366b']
INK, MUTE, GRID = '#0b0b0b', '#52514e', '#e1e0d9'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': '#c3c2b7', 'axes.labelcolor': MUTE,
    'xtick.color': MUTE, 'ytick.color': MUTE, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 200,
    'axes.facecolor': 'white', 'figure.facecolor': 'white', 'axes.titlesize': 12, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left'})
def style(ax, grid='y'): ax.grid(axis=grid, color=GRID, linewidth=0.8); ax.set_axisbelow(True)
def save(fig, name, note=None):
    if note: fig.text(0.01, 0.005, note, fontsize=7.5, color=MUTE, ha='left', va='bottom')
    fig.tight_layout(rect=(0, 0.03 if note else 0, 1, 1)); fig.savefig(os.path.join(OUT, name)); plt.close(fig); print('wrote', name)
PART = '2026 is partial (the dump ends on 1 Nov 2026)'
SMALL = 'Years 2002-2004 have 5-7 users and are left out.'

def section(n):
    i = txt.index('\n%d. ' % n) + 1; j = txt.find('\n\n', i); return txt[i:j if j > 0 else len(txt)]

# ---------- 2: active months ----------
am = {}
for m in re.finditer(r'^\s+(\d{4}) \| ([\d,]+) \| (\d+)% \| (\d+)% \| (\d+)% \| (\d+)% \| (\d+)%', section(2), re.M):
    am[int(m.group(1))] = [num(m.group(i)) for i in range(3, 8)]
# ---------- 3: listens per calendar month ----------
mo = {}
for m in re.finditer(r'^\s+(\d{4}) \| ((?:[\d.]+ \| ){11}[\d.]+)\s*$', section(3), re.M):
    mo[int(m.group(1))] = [float(x) for x in m.group(2).split('|')]
# ---------- 4: hours and weekdays per year ----------
hw = {}
for m in re.finditer(r'^\s+(\d{4}) \| hours: ((?:\d+% ?){8}) \| weekdays: ((?:\d+% ?){7})', section(4), re.M):
    hw[int(m.group(1))] = ([float(x) for x in re.findall(r'\d+', m.group(2))], [float(x) for x in re.findall(r'\d+', m.group(3))])
# ---------- 5: weekday x 3-hour block ----------
wb = {}
for m in re.finditer(r'^\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun) \| ((?:[\d.]+% ?\|? ?){8})', section(5), re.M):
    wb[m.group(1)] = [float(x) for x in re.findall(r'[\d.]+', m.group(2))]
# ---------- 6: gaps ----------
gp = {}
for m in re.finditer(r'^\s+(\d{4}) \| ((?:[\d.]+% \| ){7}[\d.]+%)', section(6), re.M):
    gp[int(m.group(1))] = [float(x) for x in re.findall(r'[\d.]+', m.group(2))]
# ---------- 7: busiest days ----------
bd = [(m.group(1), int(m.group(2).replace(',', '')), float(m.group(3))) for m in
      re.finditer(r'^\s+(\d{4}-\d\d-\d\d): ([\d,]+) listens \(([\d.]+)% of that year\)', section(7), re.M)]

# ---------- checks ----------
assert len(am) == 25 and len(mo) == 25 and len(hw) == 25 and len(gp) == 25 and len(wb) == 7 and len(bd) == 20, (len(am), len(mo), len(hw), len(gp), len(wb), len(bd))
assert all(abs(sum(v) - 100) <= 3 for v in am.values()), 'active months do not add up'
assert all(abs(sum(v) - 100) <= 1.5 for v in gp.values()), 'gaps do not add up'
assert all(abs(sum(v[0]) - 100) <= 3 and abs(sum(v[1]) - 100) <= 3 for v in hw.values()), 'hours/weekdays do not add up'
assert abs(sum(sum(v) for v in wb.values()) - 100) <= 1, 'weekday x block does not add up'
print('checks passed')
ys = [y for y in sorted(am) if y >= 2005]

# 01 active months per user and year
fig, ax = plt.subplots(figsize=(8.5, 4.4)); style(ax)
names = ['1 month', '2-3 months', '4-6 months', '7-11 months', 'all 12 months']; bottom = np.zeros(len(ys))
for i, n in enumerate(names):
    v = np.array([am[y][i] for y in ys]); ax.bar([str(y) for y in ys], v, bottom=bottom, color=STEPS[i], width=0.8, edgecolor='white', linewidth=0.6, label=n); bottom += v
ax.set_xticks(range(0, len(ys), 2)); ax.set_xticklabels([str(y) for y in ys][::2]); ax.set_ylim(0, 100)
ax.set_ylabel('% of user-years'); ax.set_title('In how many months of a year does a user listen?')
ax.legend(frameon=False, ncol=5, fontsize=7.5, loc='upper center', bbox_to_anchor=(0.5, -0.1))
save(fig, '01_active_months_per_user_year.png', PART + ': 2005 and 2026 cannot reach all 12 months. ' + SMALL)

# 02 listens per calendar month (continuous)
series = [(y, m + 1, mo[y][m]) for y in sorted(mo) for m in range(12) if y >= 2005 and not (y == 2005 and m == 0) and not (y == 2026 and m >= 10)]
fig, ax = plt.subplots(figsize=(8.5, 3.9)); style(ax)
xs = [y + (m - 1) / 12.0 for y, m, v in series]; vs = [v for y, m, v in series]
ax.plot(xs, vs, color=BLUE, lw=2.2); ax.set_ylabel('Listens in the month (millions)'); ax.set_title('Listens per calendar month')
ax.set_ylim(0, 50); ax.annotate('Feb 2005: first big\nhistory import', (2005.08, 2.6), xytext=(2007, 20), fontsize=8, color=MUTE, arrowprops=dict(arrowstyle='-', color=MUTE))
save(fig, '02_listens_per_month.png', 'Months with no data are left out (before Feb 2005, and Nov-Dec 2026). Values in the report are rounded to 0.1 million.')

# 03 time of day per year (UTC)
fig, ax = plt.subplots(figsize=(8.5, 4.6))
blocks = ['00-02', '03-05', '06-08', '09-11', '12-14', '15-17', '18-20', '21-23']
H = np.array([hw[y][0] for y in ys]).T
im = ax.imshow(H, aspect='auto', cmap=matplotlib.colors.LinearSegmentedColormap.from_list('b', ['#e8f1fc', '#2a78d6', '#0d366b']), vmin=0, vmax=20)
ax.set_yticks(range(8)); ax.set_yticklabels(blocks); ax.set_xticks(range(0, len(ys), 2)); ax.set_xticklabels([str(y) for y in ys][::2])
ax.set_ylabel('Hour of day (UTC)'); ax.set_title('When in the day do listens happen? (UTC)'); ax.spines[:].set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02); cb.set_label('% of that year\'s listens', color=MUTE)
save(fig, '03_time_of_day_per_year_utc.png', 'UTC mixes the time zones of all users, so this is not "local" time. ' + SMALL)

# 04 weekday share per year
fig, ax = plt.subplots(figsize=(8.5, 3.9)); style(ax)
days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']; cols = [BLUE, BLUE, BLUE, BLUE, BLUE, ORANGE, ORANGE]
yy = [y for y in ys if y >= 2006]
Wd = np.array([hw[y][1] for y in yy])
ax.plot(yy, Wd[:, :5].mean(axis=1), color=BLUE, lw=2.4, marker='o', ms=3.5); ax.plot(yy, Wd[:, 5:].mean(axis=1), color=ORANGE, lw=2.4, marker='o', ms=3.5)
ax.text(2026.3, Wd[-1, :5].mean(), 'Mon-Fri\n(each day)', color=BLUE, fontsize=8.5, va='center'); ax.text(2026.3, Wd[-1, 5:].mean(), 'Sat-Sun\n(each day)', color=ORANGE, fontsize=8.5, va='center')
ax.set_xlim(2005.5, 2029.5); ax.set_ylim(10, 17); ax.set_ylabel('% of listens on one such day'); ax.set_title('Weekdays and weekends are close to equal')
save(fig, '04_weekday_share_per_year.png', 'Average of the daily shares in the report (a flat line would be 14.3%). ' + SMALL)

# 05 weekday x block, 2016-2025
fig, ax = plt.subplots(figsize=(7.5, 3.8))
Z = np.array([wb[d] for d in days]); ax.imshow(Z, aspect='auto', cmap=matplotlib.colors.LinearSegmentedColormap.from_list('b', ['#e8f1fc', '#2a78d6', '#0d366b']), vmin=0.8, vmax=2.6)
for i in range(7):
    for j in range(8): ax.text(j, i, '%.1f' % Z[i, j], ha='center', va='center', fontsize=8.5, color='white' if Z[i, j] > 2.0 else INK)
ax.set_xticks(range(8)); ax.set_xticklabels(blocks, fontsize=8.5); ax.set_yticks(range(7)); ax.set_yticklabels(days)
ax.set_xlabel('Hour of day (UTC)'); ax.set_title('Weekday and time of day, 2016-2025'); ax.spines[:].set_visible(False)
save(fig, '05_weekday_by_time_of_day.png', 'Each cell is the % of all listens in 2016-2025 (the 56 cells add up to 100%). UTC.')

# 06 time since the user's previous listen
fig, ax = plt.subplots(figsize=(8.5, 4.4)); style(ax)
G = {y: gp[y] for y in ys}; groups = [('Same second', [0]), ('1-29 s', [1]), ('30 s - 9 min (song after song)', [2, 3]), ('10 min - 23 h', [4, 5, 6]), ('1 day or more', [7])]
bottom = np.zeros(len(ys))
for i, (n, idx) in enumerate(groups):
    v = np.array([sum(G[y][k] for k in idx) for y in ys]); ax.bar([str(y) for y in ys], v, bottom=bottom, color=STEPS[i], width=0.8, edgecolor='white', linewidth=0.6, label=n); bottom += v
ax.set_xticks(range(0, len(ys), 2)); ax.set_xticklabels([str(y) for y in ys][::2]); ax.set_ylim(0, 100)
ax.set_ylabel('% of listens'); ax.set_title('Time since the same user\'s previous listen')
ax.legend(frameon=False, ncol=3, fontsize=7.5, loc='upper center', bbox_to_anchor=(0.5, -0.1))
save(fig, '06_time_since_previous_listen.png', 'Same second = bulk uploads or duplicates. ' + PART + '. ' + SMALL)

# 07 busiest days
fig, ax = plt.subplots(figsize=(8, 5.4)); style(ax, 'x')
labels = [d for d, n, p in bd][::-1]; vals = [n for d, n, p in bd][::-1]
ax.barh(labels, vals, color=[ORANGE if l == '2005-02-13' else BLUE for l in labels], height=0.7)
top = [p for d, n, p in bd if d == '2005-02-13'][0]
for i, (l, v) in enumerate(zip(labels, vals)):
    extra = '   = %.1f%% of all 2005 listens (history import)' % top if l == '2005-02-13' else ''
    ax.text(v + 20000, i, '{:,}'.format(v) + extra, va='center', fontsize=8, color=ORANGE if extra else INK)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: '%g' % (v / 1e6))); ax.set_xlabel('Listens on that day (millions)'); ax.set_xlim(0, 3.9e6)
ax.set_title('The 20 busiest days')
assert all(d.startswith('2026') for d, n, p in bd if d != '2005-02-13'), 'busiest days are not all in 2026'
save(fig, '07_busiest_days.png', 'All users together. The other 19 days are in 2026 (about 0.4% of that year each).')
