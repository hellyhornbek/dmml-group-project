#!/usr/bin/env python3
"""Draws the figures for the test sample from the csv files made by ../../Scripts/sample_overview.py.

Reads:  ../sample_song_linking.csv, ../sample_linking_coverage.csv, ../sample_per_user.csv  (this script sits in Output/figures)
Writes: 01_...png to 03_...png in the same folder. Stops with an error if the files do not agree (600 users, same number of listens everywhere).
Needs: matplotlib, numpy.   Run from anywhere:  python3 sample_figures.py
"""
import os, csv
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); IN = os.path.join(HERE, '..'); OUT = HERE
rd = lambda n: list(csv.DictReader(open(os.path.join(IN, n), encoding='utf8')))
sl, cov, pu = rd('sample_song_linking.csv'), rd('sample_linking_coverage.csv'), rd('sample_per_user.csv')
NL = sum(int(r['listens_in_sample']) for r in pu)
assert len(pu) == 600 and int(cov[0]['listens_with_value']) == NL
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

# 01 how many distinct songs get ids
names = ['All distinct songs', 'With a match key', 'Matched in the canonical dump', 'With a recording id', 'With an artist id', 'With a release id']
v = [int(r['songs']) for r in sl]
fig, ax = plt.subplots(figsize=(8.5, 3.8)); style(ax, 'x'); yy = np.arange(len(v))[::-1]
ax.barh(yy, [x / v[0] * 100 for x in v], color=[MUTE] + [BLUE] * 5, height=0.62)
for y, x in zip(yy, v): ax.text(x / v[0] * 100 + 1.2, y, '%s (%.1f%%)' % (format(x, ','), x / v[0] * 100), va='center', fontsize=8.5, color=INK)
ax.set_yticks(yy); ax.set_yticklabels(names); ax.set_xlim(0, 125); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xlabel('% of distinct songs')
ax.set_title('How many songs could be linked to MusicBrainz')
save(fig, '01_songs_linked.png', 'A song is one artist + title pair. Recording ids come from ListenBrainz first, then from the canonical match.')

# 02 fill rate per column
rows = [r for r in cov if r['column'] not in ('user_id', 'listen_time_utc', 'song', 'artist', 'matchkey')]
rows.sort(key=lambda r: float(r['share']))
lab = {'player_duration_ms': 'Time played', 'album': 'Album', 'release_year': 'Release year', 'genre': 'Genre', 'artist_tags': 'Artist tags', 'song_tags': 'Song tags',
       'song_length_ms': 'Song length', 'artist_begin_year': 'Artist begin year', 'artist_end_year': 'Artist end year', 'artist_type': 'Artist type',
       'artist_country': 'Artist country', 'recording_id': 'Recording id'}
fig, ax = plt.subplots(figsize=(8.5, 4.6)); style(ax, 'x'); yy = np.arange(len(rows))
ax.barh(yy, [float(r['share']) * 100 for r in rows], color=BLUE, height=0.64)
for y, r in zip(yy, rows): ax.text(float(r['share']) * 100 + 1.2, y, '%.1f%%' % (float(r['share']) * 100), va='center', fontsize=8.5, color=INK)
ax.set_yticks(yy); ax.set_yticklabels([lab[r['column']] for r in rows]); ax.set_xlim(0, 100); ax.set_xlabel('%% of the %s listens with a value' % format(NL, ','))
ax.set_title('Which columns are filled in')
save(fig, '02_column_fill_rate.png', 'Empty means not linked or no data, not that the song has no genre. Artist end year is empty for artists that are still active.')

# 03 listens per user
n = [int(r['listens_in_sample']) for r in pu]
fig, ax = plt.subplots(figsize=(8.5, 3.8)); style(ax)
ax.hist(n, bins=np.logspace(np.log10(min(n)), np.log10(max(n)), 31), color=BLUE, edgecolor='white', linewidth=0.5)
ax.set_xscale('log'); ax.set_xlabel('Listens of a user in the sample (log scale)'); ax.set_ylabel('Users'); ax.set_title('How many listens does each sample user have?')
ax.text(0.98, 0.9, 'median %d, largest %s' % (np.median(n), format(max(n), ',')), transform=ax.transAxes, ha='right', fontsize=8.5, color=MUTE)
save(fig, '03_listens_per_user.png', '600 users, %s listens. Each user keeps the same share (about 3%%) of their 2023 listens, so the shape follows the full year.' % format(NL, ','))
