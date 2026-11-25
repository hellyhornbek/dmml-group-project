"""Links the sample songs to the MusicBrainz full database tables (in the work folder, into link.duckdb).
Run in this order, inside the work folder (needs sample_listens.parquet, song_keys.parquet, matches.json):
  python3 link_musicbrainz.py ids         # recording / artist / release id per song (ListenBrainz id first, else canonical match)
  python3 link_musicbrainz.py artist      # artist name details, area, type, tags
  python3 link_musicbrainz.py recording   # recording length and tags
  python3 link_musicbrainz.py release     # release year (from the release group)
Set MB_TABLES to the folder 'MusicBrainz Full/tables/mbdump/' if it is not at the default place.
"""
import duckdb, json, os, time, sys
MB = os.environ.get('MB_TABLES', os.path.expanduser('~/mnt/Projects/Data Mining project/Raw data/MusicBrainz Full/tables/mbdump/'))
con = duckdb.connect('link.duckdb'); con.execute("PRAGMA memory_limit='2GB'"); con.execute("PRAGMA threads=4")
t0 = time.time()
def log(m): print(f'[{time.time()-t0:5.0f}s] {m}', flush=True)
def tsv(name, cols):
    c = ', '.join(f"'{k}': 'VARCHAR'" for k in cols)
    return f"read_csv('{MB}{name}', delim='\\t', header=false, quote='', escape='', nullstr='\\N', columns={{{c}}}, auto_detect=false, strict_mode=false, ignore_errors=true)"
step = sys.argv[1]
if step == 'ids':
    M = json.load(open('matches.json'))
    con.execute("create or replace table canon(matchkey varchar, artist_mbid varchar, release_mbid varchar, recording_mbid varchar)")
    con.executemany("insert into canon values (?,?,?,?)", [(k, v[1].split(',')[0].strip('{} "'), v[2], v[3]) for k, v in M.items()])
    con.execute("""create or replace table songs as
      select k.artist_name, k.track_name, k.matchkey,
             coalesce(l.recording_mbid, c.recording_mbid) recording_mbid,
             coalesce(l.artist_mbid, c.artist_mbid) artist_mbid,
             coalesce(l.release_mbid, c.release_mbid) release_mbid,
             c.matchkey is not null as matched_canonical
      from 'song_keys.parquet' k
      left join canon c using(matchkey)
      left join (select artist_name, track_name, max(recording_mbid) recording_mbid, max(artist_mbid) artist_mbid, max(release_mbid) release_mbid
                 from 'sample_listens.parquet' group by 1,2) l using(artist_name, track_name)""")
    print(con.sql("select count(*), count(recording_mbid), count(artist_mbid), count(release_mbid), sum(matched_canonical::int) from songs").fetchall())
    log('ids done')
elif step == 'artist':
    con.execute("create or replace table need_artist as select distinct artist_mbid g from songs where artist_mbid is not null")
    con.execute(f"""create or replace table artist as select a.id::bigint id, a.gid, a.name, a.begin_y::int begin_year, a.end_y::int end_year, a.type::int type_id, a.area::int area_id
        from {tsv('artist', {'id':0,'gid':0,'name':0,'sort_name':0,'begin_y':0,'begin_m':0,'begin_d':0,'end_y':0,'end_m':0,'end_d':0,'type':0,'area':0,'gender':0,'comment':0})} a
        where a.gid in (select g from need_artist)""")
    log('artist ' + str(con.execute('select count(*) from artist').fetchone()))
    con.execute(f"create or replace table area as select id::bigint id, name from {tsv('area', {'id':0,'gid':0,'name':0})}")
    con.execute(f"create or replace table atype as select id::bigint id, name from {tsv('artist_type', {'id':0,'name':0})}")
    con.execute(f"create or replace table tag as select id::bigint id, name from {tsv('tag', {'id':0,'name':0})}")
    con.execute(f"create or replace table genre as select name from {tsv('genre', {'id':0,'gid':0,'name':0})}")
    con.execute(f"""create or replace table artist_tags as
        select x.artist::bigint artist_id, t.name tag, x.count::int votes, (t.name in (select name from genre)) is_genre
        from {tsv('artist_tag', {'artist':0,'tag':0,'count':0})} x join tag t on t.id = x.tag::bigint
        where x.artist::bigint in (select id from artist) and x.count::int > 0""")
    log('artist tags ' + str(con.execute('select count(*) from artist_tags').fetchone()))
elif step == 'recording':
    con.execute("create or replace table need_rec as select distinct recording_mbid g from songs where recording_mbid is not null")
    con.execute(f"""create or replace table recording as select r.id::bigint id, r.gid, r.length::bigint length_ms
        from {tsv('recording', {'id':0,'gid':0,'name':0,'ac':0,'length':0})} r where r.gid in (select g from need_rec)""")
    log('recording ' + str(con.execute('select count(*) from recording').fetchone()))
    con.execute(f"""create or replace table recording_tags as
        select rt.recording::bigint recording_id, t.name tag, rt.count::int votes, (t.name in (select name from genre)) is_genre
        from {tsv('recording_tag', {'recording':0,'tag':0,'count':0})} rt join tag t on t.id = rt.tag::bigint
        where rt.recording::bigint in (select id from recording) and rt.count::int > 0""")
    log('recording tags ' + str(con.execute('select count(*) from recording_tags').fetchone()))
elif step == 'release':
    con.execute("create or replace table need_rel as select distinct release_mbid g from songs where release_mbid is not null")
    con.execute(f"""create or replace table rel as select r.gid, r.rg::bigint rg from {tsv('release', {'id':0,'gid':0,'name':0,'ac':0,'rg':0})} r where r.gid in (select g from need_rel)""")
    con.execute(f"""create or replace table rgy as select m.id::bigint rg, m.y::int rel_year from {tsv('release_group_meta', {'id':0,'rc':0,'y':0})} m
        where m.id::bigint in (select rg from rel)""")
    log('release ' + str(con.execute('select count(*) from rel').fetchone()) + ' years ' + str(con.execute('select count(*) from rgy').fetchone()))
