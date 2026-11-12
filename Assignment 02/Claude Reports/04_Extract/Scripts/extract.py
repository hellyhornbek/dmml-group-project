#!/usr/bin/env python3
"""Extract: one streaming pass over the full dump; keeps only cohort users; writes Parquet per year.
Resumable (progress.json). Run again with the same command to continue after a stop.

Extract:  python3 extract.py --dump "<dump>.tar.zst" --out "../../../Extract"
Check:    python3 extract.py --check --out "../Extract"
Options:  --workers N   --max-lines N (test)   --no-extra (leave out the extra_json column)
          --expected FILE (user_id,year,listens; default OUT/cohort_year_counts.csv)
"""
import argparse, collections, csv, glob, json, os, sys, time, itertools
from multiprocessing import Pool
import pyarrow as pa, pyarrow.parquet as pq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lbstream import iter_lines, year_of, LINE_RE

TOTAL_LINES = 2990440915          # lines in the full dump (from the count pass), used only for the ETA
BATCH = 40000                     # cohort lines per task
FLUSH_ROWS = 2000000              # rows kept in memory before writing parts

FIELDS = [('user_id', pa.int64()), ('ts', pa.int64()), ('year', pa.int16()),
          ('artist_name', pa.string()), ('track_name', pa.string()), ('release_name', pa.string()),
          ('recording_msid', pa.string()), ('recording_mbid', pa.string()), ('release_mbid', pa.string()),
          ('artist_mbid', pa.string()), ('spotify_id', pa.string()), ('origin_url', pa.string()),
          ('source', pa.string()), ('music_service', pa.string()), ('tracknumber', pa.int32()),
          ('isrc', pa.string()), ('duration_ms', pa.int64()), ('ms_played', pa.int64()),
          ('is_dup', pa.bool_()), ('extra_json', pa.string())]
SCHEMA = pa.schema(FIELDS)
USED_AI = {'submission_client', 'duration_ms', 'duration', 'ms_played', 'tracknumber', 'isrc', 'music_service',
           'origin_url', 'spotify_id', 'recording_mbid', 'artist_mbids', 'release_mbid', 'recording_msid'}
COHORT = set()


def _init(cohort):
    global COHORT
    COHORT = cohort


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if v != v or v in (float('inf'), float('-inf')):
        return None
    v = int(v)
    # values outside int64 cannot be stored; treat them as missing
    return v if -2**63 <= v < 2**63 else None


def num32(x):
    # track numbers are stored as int32; junk such as 4294967295 is treated as missing
    v = num(x)
    return v if v is not None and -2**31 <= v < 2**31 else None


def as_str(x):
    if x is None or x == '':
        return None
    return x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)


def first(x):
    if isinstance(x, list):
        return as_str(x[0]) if x else None
    return as_str(x)


def clean(x):
    return x.encode('utf-8', 'surrogatepass').decode('utf-8', 'replace') if isinstance(x, str) else x


def parse_batch(args):
    lines, keep_extra = args
    import json as _json
    per_year = {}
    seen = {}
    bad = kept = 0
    for line in lines:
        try:
            d = _json.loads(line)
            uid = int(d['user_id']); ts = int(d['timestamp'])
        except Exception:
            bad += 1
            continue
        if uid not in COHORT:
            continue
        t = d.get('track_metadata') or {}
        ai = t.get('additional_info') or {}
        mm = t.get('mbid_mapping') or {}
        art = t.get('artist_name'); trk = t.get('track_name')
        k = (uid, ts); pair = (art, trk)
        s = seen.get(k)
        if s is None:
            seen[k] = {pair}; dup = False
        elif pair in s:
            dup = True
        else:
            s.add(pair); dup = False
        dur = num(ai.get('duration_ms'))
        if dur is None:
            dd = num(ai.get('duration'))
            dur = dd * 1000 if dd is not None else None
        extra = None
        if keep_extra:
            ex = {kk: v for kk, v in ai.items() if kk not in USED_AI}
            if ex:
                extra = _json.dumps(ex, separators=(',', ':'), ensure_ascii=False)
        row = (uid, ts, year_of(ts), art, trk, t.get('release_name'),
               as_str(d.get('recording_msid') or ai.get('recording_msid')),
               as_str(mm.get('recording_mbid') or ai.get('recording_mbid')),
               as_str(mm.get('release_mbid') or ai.get('release_mbid')),
               first(mm.get('artist_mbids') or ai.get('artist_mbids')),
               as_str(ai.get('spotify_id')), as_str(ai.get('origin_url')),
               as_str(ai.get('submission_client')), as_str(ai.get('music_service')),
               num32(ai.get('tracknumber')), as_str(ai.get('isrc')), dur, num(ai.get('ms_played')),
               dup, extra)
        per_year.setdefault(row[2], []).append(row); kept += 1
    out = {}
    for y, rows in per_year.items():
        cols = list(zip(*rows))
        try:
            arrays = [pa.array(c, type=t) for c, (_, t) in zip(cols, FIELDS)]
        except (pa.ArrowInvalid, UnicodeEncodeError, ValueError):
            arrays = [pa.array([clean(v) for v in c], type=t) for c, (_, t) in zip(cols, FIELDS)]
        out[y] = pa.Table.from_arrays(arrays, schema=SCHEMA)
    return out, kept, bad


def atomic_json(path, obj):
    tmp = path + '.tmp'
    with open(tmp, 'w') as fh:
        json.dump(obj, fh)
    os.replace(tmp, path)


def run_extract(a):
    out = a.out; ext = os.path.join(out, 'extract')
    cohort = set()
    with open(os.path.join(out, 'cohort_users.csv'), newline='') as fh:
        r = csv.reader(fh); next(r)
        for row in r:
            cohort.add(int(row[0]))
    print('cohort users: %s' % format(len(cohort), ','), flush=True)
    os.makedirs(ext, exist_ok=True)
    pp = os.path.join(out, 'progress.json')
    st = dict(ckpt=0, lines_done=0, rows=0, cohort_lines=0, bad=0, regex_miss=0, done=False)
    if os.path.exists(pp):
        st = json.load(open(pp))
        for f in glob.glob(os.path.join(ext, 'year=*', 'part-*.parquet*')):
            n = os.path.basename(f).split('.')[0].split('-')[1]
            if int(n) > st['ckpt']:
                os.remove(f)
        if st.get('done') and a.max_lines is None:
            print('Already finished (progress.json says done). Nothing to do.'); return
        print('Resuming after %s lines (%s rows already written)' % (format(st['lines_done'], ','), format(st['rows'], ',')), flush=True)
    else:
        info = dict(dump=os.path.basename(a.dump), dump_bytes=os.path.getsize(a.dump), started=time.strftime('%Y-%m-%d %H:%M:%S'))
        md5 = a.dump + '.md5'
        if os.path.exists(md5):
            info['md5_file'] = open(md5).read().split()[0]
        atomic_json(os.path.join(out, 'run_info.json'), info)
    buf = collections.defaultdict(list); buf_rows = [0]; last_end = [st['lines_done'] - 1]

    def flush():
        if not buf_rows[0]:
            return
        st['ckpt'] += 1
        for y, tbls in buf.items():
            d = os.path.join(ext, 'year=%d' % y); os.makedirs(d, exist_ok=True)
            p = os.path.join(d, 'part-%06d.parquet' % st['ckpt'])
            pq.write_table(pa.concat_tables(tbls), p + '.tmp', compression='zstd', compression_level=3)
            os.replace(p + '.tmp', p)
        st['rows'] += buf_rows[0]; st['lines_done'] = last_end[0] + 1
        buf.clear(); buf_rows[0] = 0
        atomic_json(pp, st)

    pool = Pool(a.workers, initializer=_init, initargs=(cohort,))
    inflight = collections.deque(); window = a.workers * 3
    t0 = time.time(); last_print = [t0]; lines_start = st['lines_done']

    def collect():
        res, end_idx = inflight.popleft()
        tables, kept, bad = res.get()
        st['cohort_lines'] += kept; st['bad'] += bad
        for y, t in tables.items():
            buf[y].append(t); buf_rows[0] += t.num_rows
        last_end[0] = end_idx
        if buf_rows[0] >= FLUSH_ROWS:
            flush()

    def submit(batch, end_idx):
        while len(inflight) >= window:
            collect()
        inflight.append((pool.apply_async(parse_batch, ((batch, not a.no_extra),)), end_idx))

    stream = iter_lines([a.dump])
    if st['lines_done']:
        stream = itertools.islice(stream, st['lines_done'], None)
    i = st['lines_done'] - 1
    batch, batch_ts, stopped = [], None, False
    for line in stream:
        i += 1
        if a.max_lines is not None and i >= a.max_lines:
            stopped = True; break
        m = LINE_RE.match(line)
        if m:
            if int(m.group(1)) not in cohort:
                ts = None
            else:
                ts = int(m.group(2))
            if ts is None:
                if time.time() - last_print[0] > 20:
                    last_print[0] = time.time(); el = last_print[0] - t0; done = i - lines_start + 1
                    print('%sM lines (%.0f%% of the dump), %sM rows written, %.0fk lines/s, about %.0f min left' % (
                        format(i / 1e6, ',.0f'), 100 * i / TOTAL_LINES, format(st['rows'] / 1e6, ',.1f'), done / el / 1e3,
                        (TOTAL_LINES - i) / max(done / el, 1) / 60), flush=True)
                continue
        else:
            st['regex_miss'] += 1; ts = -1      # unusual line: let the worker decide
        if len(batch) >= BATCH and ts != batch_ts:
            submit(batch, i - 1); batch = []
        batch.append(line); batch_ts = ts
    if batch:
        submit(batch, i if not stopped else i - 1)
    while inflight:
        collect()
    flush()
    pool.close(); pool.join()
    st['done'] = not stopped
    if not stopped:
        st['lines_done'] = i + 1
    st['finished'] = time.strftime('%Y-%m-%d %H:%M:%S')
    atomic_json(pp, st)
    print('%s. Lines read: %s. Rows written: %s. Unparsable cohort lines: %d. Lines the quick filter could not read: %d.' % (
        'Finished' if st['done'] else 'Stopped at max-lines', format(st['lines_done'], ','), format(st['rows'], ','), st['bad'], st['regex_miss']), flush=True)


def run_check(a):
    import duckdb
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import importlib.util
    spec = importlib.util.spec_from_file_location('bc', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '03_Cohort', 'Scripts', 'build_cohort.py'))
    bc = importlib.util.module_from_spec(spec); spec.loader.exec_module(bc)
    out = a.out; cfg = json.load(open(os.path.join(out, 'config.json')))
    exp_path = a.expected or os.path.join(out, 'cohort_year_counts.csv')
    rep = []; ok = True
    def line(s, good=None):
        nonlocal ok
        if good is False: ok = False
        rep.append(('PASS  ' if good else 'FAIL  ' if good is False else '      ') + s); print(rep[-1], flush=True)
    con = duckdb.connect(); con.execute("SET TimeZone='UTC'")
    con.execute("CREATE VIEW x AS SELECT * FROM read_parquet('%s', hive_partitioning=false)" % os.path.join(out, 'extract', 'year=*', '*.parquet'))
    con.execute("CREATE TEMP TABLE act AS SELECT user_id, year, count(*) AS n FROM x GROUP BY 1,2")
    con.execute("CREATE TEMP TABLE exp AS SELECT user_id, year, listens FROM read_csv('%s', header=true)" % exp_path)
    pj = os.path.join(out, 'progress.json')
    partial = False
    if os.path.exists(pj):
        p = json.load(open(pj)); partial = not p.get('done')
        line('progress.json: done=%s, lines read %s, unparsable cohort lines %d' % (p.get('done'), format(p.get('lines_done', 0), ','), p.get('bad', 0)), p.get('bad', 0) == 0)
    tot_a = con.execute('SELECT coalesce(sum(n),0) FROM act').fetchone()[0]
    tot_e = con.execute('SELECT coalesce(sum(listens),0) FROM exp').fetchone()[0]
    line('total rows %s, expected %s' % (format(tot_a, ','), format(tot_e, ',')), tot_a == tot_e)
    mism = con.execute('SELECT count(*) FROM act FULL OUTER JOIN exp USING (user_id, year) WHERE coalesce(act.n,-1) <> coalesce(exp.listens,-1)').fetchone()[0]
    line('user-years that differ from the profile: %d' % mism, mism == 0)
    if mism:
        for r in con.execute('SELECT user_id, year, act.n, exp.listens FROM act FULL OUTER JOIN exp USING (user_id, year) WHERE coalesce(act.n,-1) <> coalesce(exp.listens,-1) LIMIT 10').fetchall():
            line('   user %s year %s: extract %s, profile %s' % r)
    cohort = {int(r[0]) for r in csv.reader(open(os.path.join(out, 'cohort_users.csv'))) if r[0].isdigit()}
    outside = con.execute('SELECT count(DISTINCT user_id) FROM act').fetchone()[0]
    users_ex = {r[0] for r in con.execute('SELECT DISTINCT user_id FROM act').fetchall()}
    line('users in extract %s, outside cohort %d, cohort users missing %d%s' % (format(len(users_ex), ','), len(users_ex - cohort), len(cohort - users_ex), ' (not checked: run not finished)' if partial else ''), (not (users_ex - cohort)) and (partial or not (cohort - users_ex)))
    badyear = con.execute('SELECT count(*) FROM x WHERE year <> year(make_timestamp(ts * 1000000))').fetchone()[0]
    line('rows where year does not match the timestamp (UTC): %d' % badyear, badyear == 0)
    # rule recomputed from the extract itself
    counts = collections.defaultdict(dict)
    for u, y, n in con.execute('SELECT user_id, year, n FROM act').fetchall():
        counts[u][y] = n
    q = {u for u, c in counts.items() if bc.qualifying_runs(c, cfg)}
    if partial:
        line('rule recomputed from the extract: skipped, run not finished')
    else:
        line('rule recomputed from the extract: %s users pass, %d of the extract users fail' % (format(len(q), ','), len(users_ex - q)), len(users_ex - q) == 0 and len(q) == len(cohort))
    d = con.execute('SELECT count(*), sum(CASE WHEN is_dup THEN 1 ELSE 0 END) FROM x').fetchone()
    line('rows flagged as exact repeats (same user, second, artist, track): %s (%.2f%%)' % (format(d[1] or 0, ','), 100 * (d[1] or 0) / max(d[0], 1)))
    for col in ('recording_mbid', 'duration_ms', 'ms_played', 'source'):
        c = con.execute('SELECT count(%s) * 100.0 / count(*) FROM x' % col).fetchone()[0]
        line('share of rows with %s: %.1f%%' % (col, c or 0))
    rep.append(''); rep.append('RESULT: ' + ('ALL CHECKS PASSED' if ok else 'SOMETHING FAILED'))
    print(rep[-1])
    open(os.path.join(out, 'check_report.txt'), 'w').write('\n'.join(rep) + '\n')
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dump'); ap.add_argument('--out', required=True)
    ap.add_argument('--check', action='store_true'); ap.add_argument('--expected')
    ap.add_argument('--workers', type=int, default=max(2, (os.cpu_count() or 4) - 2))
    ap.add_argument('--max-lines', type=int, default=None); ap.add_argument('--no-extra', action='store_true')
    a = ap.parse_args()
    if a.check:
        run_check(a)
    else:
        if not a.dump:
            sys.exit('--dump is required')
        run_extract(a)


if __name__ == '__main__':
    main()
