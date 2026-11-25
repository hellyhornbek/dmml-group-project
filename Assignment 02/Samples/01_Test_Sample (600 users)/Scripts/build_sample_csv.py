"""Assembles the test CSV: the sample listens plus song and artist details from the linked MusicBrainz tables.
Run inside the work folder after link_musicbrainz.py. Writes sample_2023_600users.csv into OUT (default: the project's Samples folder).
Genre = most voted official MusicBrainz genre of the recording, else of the artist (ties: alphabetical, so a rerun gives the same file). Tags = up to 10 most voted.
"""
import duckdb, os
OUT = os.environ.get('SAMPLE_OUT', os.path.expanduser('~/mnt/Projects/Data Mining project/Samples'))
os.makedirs(OUT, exist_ok=True)
con = duckdb.connect('link.duckdb'); con.execute("PRAGMA memory_limit='2GB'")
con.execute("""
create or replace table top_genre_rec as
  select recording_id, (array_agg(tag order by votes desc, tag))[1] genre from recording_tags where is_genre group by 1;
create or replace table top_genre_art as
  select artist_id, (array_agg(tag order by votes desc, tag))[1] genre from artist_tags where is_genre group by 1;
create or replace table tags_rec as
  select recording_id, string_agg(tag, '; ' order by votes desc, tag) tags from (
    select *, row_number() over (partition by recording_id order by votes desc, tag) rn from recording_tags) where rn <= 10 group by 1;
create or replace table tags_art as
  select artist_id, string_agg(tag, '; ' order by votes desc, tag) tags from (
    select *, row_number() over (partition by artist_id order by votes desc, tag) rn from artist_tags) where rn <= 10 group by 1;
create or replace table final as
select l.user_id as user_id,
       strftime(to_timestamp(l.ts) at time zone 'UTC', '%Y-%m-%d %H:%M:%S') || ' UTC' as listen_time_utc,
       l.ms_played as player_duration_ms,
       l.track_name as song,
       l.artist_name as artist,
       l.release_name as album,
       rgy.rel_year as release_year,
       coalesce(tgr.genre, tga.genre) as genre,
       ta.tags as artist_tags,
       tr.tags as song_tags,
       r.length_ms as song_length_ms,
       a.begin_year as artist_begin_year,
       a.end_year as artist_end_year,
       aty.name as artist_type,
       ar.name as artist_country,
       s.recording_mbid as recording_id,
       s.matchkey as matchkey
from 'sample_listens.parquet' l
left join songs s on s.artist_name = l.artist_name and s.track_name = l.track_name
left join artist a on a.gid = s.artist_mbid
left join atype aty on aty.id = a.type_id
left join area ar on ar.id = a.area_id
left join recording r on r.gid = s.recording_mbid
left join rel on rel.gid = s.release_mbid
left join rgy on rgy.rg = rel.rg
left join top_genre_rec tgr on tgr.recording_id = r.id
left join top_genre_art tga on tga.artist_id = a.id
left join tags_art ta on ta.artist_id = a.id
left join tags_rec tr on tr.recording_id = r.id
order by l.user_id, l.ts
""")
n = con.execute("select count(*) from final").fetchone()[0]
print('rows', n)
cols = [c[0] for c in con.sql("describe final").fetchall()]
fill = con.sql("select " + ", ".join(f"round(100.0*count({c})/count(*),1) as {c}" for c in cols) + " from final").df().T
print(fill.to_string(header=False))
con.execute(f"copy final to '{OUT}/sample_2023_600users.csv' (header, delimiter ',')")
print(con.sql("select count(distinct user_id), min(listen_time_utc), max(listen_time_utc) from final").fetchall())
