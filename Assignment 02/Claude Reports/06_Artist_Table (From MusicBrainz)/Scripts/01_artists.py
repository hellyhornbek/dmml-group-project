#!/usr/bin/env python3
"""Step 1: overview of all artists in MusicBrainz (no listening data involved), with their official-genre tagging.
Writes two files:
  artists_summary.csv      small table of counts (how many artists, by type, how many have tags / official genres ...)
  artists_genre.parquet    one row per artist that has at least one tag (the other artists are only counted in the summary, to keep the file small): id, mbid, name, artist_type, area, begin_year, end_year, ended,
                           n_tags, tag_votes, n_genres, genre_votes, top_genre, top_genre_votes
Rules: only tag votes above 0 count. A genre is an official MusicBrainz genre (same list as 05_Genre_Table).
       top_genre = the official genre with most votes on the artist, ties broken alphabetically.
Usage: python3 01_artists.py --mb "<.../MusicBrainz Full/tables/mbdump>" --out-dir Results
"""
import argparse, os, duckdb
ap = argparse.ArgumentParser(); ap.add_argument('--mb', required=True); ap.add_argument('--out-dir', default='Results'); ap.add_argument('--tmp', default='/tmp/duck'); a = ap.parse_args()
D = a.mb.rstrip('/'); O = a.out_dir; os.makedirs(O, exist_ok=True); os.makedirs(a.tmp, exist_ok=True)
con = duckdb.connect(); con.execute("pragma memory_limit='1500MB'"); con.execute(f"pragma temp_directory='{a.tmp}'")
rd = lambda f, cols: f"read_csv('{D}/{f}', delim='\\t', header=false, columns={cols}, quote='', escape='', null_padding=true, all_varchar=true, nullstr='\\N')"
V = 'varchar'
con.execute(f"create view artist as select cast(c_id as bigint) as id, c_gid as gid, c_name as name, try_cast(c_byear as int) as begin_year, try_cast(c_eyear as int) as end_year, try_cast(c_type as int) as type_id, try_cast(c_area as bigint) as area_id, c_ended as ended from {rd('artist', {'c_id':V,'c_gid':V,'c_name':V,'c_sort':V,'c_byear':V,'c_bm':V,'c_bd':V,'c_eyear':V,'c_em':V,'c_ed':V,'c_type':V,'c_area':V,'c_gender':V,'c_comment':V,'c_edits':V,'c_upd':V,'c_ended':V,'c_barea':V,'c_earea':V})}")
con.execute(f"create view atype as select cast(id as int) id, name from {rd('artist_type', {'id':V,'name':V,'parent':V,'child_order':V,'description':V,'gid':V})}")
con.execute(f"create view area as select cast(id as bigint) id, name from {rd('area', {'id':V,'gid':V,'name':V,'type':V,'edits':V,'upd':V,'fdy':V,'fdm':V,'fdd':V,'ldy':V,'ldm':V,'ldd':V,'ended':V,'comment':V})}")
con.execute(f"create view genre as select name from {rd('genre', {'id':V,'gid':V,'name':V,'comment':V,'edits':V,'upd':V})}")
con.execute(f"create view tag as select cast(id as bigint) id, name from {rd('tag', {'id':V,'name':V,'ref_count':V})}")
con.execute(f"create view atag as select cast(artist as bigint) artist, cast(tag as bigint) tag, cast(count as bigint) cnt from {rd('artist_tag', {'artist':V,'tag':V,'count':V,'upd':V})}")
print('tables ready', flush=True)
con.execute("create table gtag as select t.id tag, t.name genre, row_number() over (order by t.name) gr from tag t join genre g on g.name = t.name")
con.execute("create table tagagg as select artist, count(*) n_tags, sum(cnt) tag_votes from atag where cnt > 0 group by artist")
print('tags aggregated', flush=True)
con.execute("""create table genagg as select a.artist, count(*) n_genres, sum(a.cnt) genre_votes,
  arg_max(g.genre, a.cnt * 10000 - g.gr) top_genre, max(a.cnt) top_genre_votes
  from atag a join gtag g on g.tag = a.tag where a.cnt > 0 group by a.artist""")
print('genres aggregated', flush=True)
con.execute(f"""copy (select a.id as artist_id, a.gid as mbid, a.name as name, t.name as artist_type, ar.name as area, a.begin_year as begin_year, a.end_year as end_year, (a.ended = 't') as ended,
  coalesce(x.n_tags,0) as n_tags, coalesce(x.tag_votes,0) as tag_votes, coalesce(g.n_genres,0) as n_genres, coalesce(g.genre_votes,0) as genre_votes, g.top_genre as top_genre, g.top_genre_votes as top_genre_votes
  from artist a left join atype t on t.id = a.type_id left join area ar on ar.id = a.area_id left join tagagg x on x.artist = a.id left join genagg g on g.artist = a.id where x.n_tags > 0 order by a.id)
  to '{O}/artists_genre.parquet' (format parquet, compression zstd)""")
P = f"read_parquet('{O}/artists_genre.parquet')"
rows = con.sql(f"""
 select 'artists_total' as measure, count(*) as n from artist
 union all select 'artists_with_begin_year', count(*) from artist where begin_year is not null
 union all select 'artists_with_area', count(*) from artist where area_id is not null
 union all select 'type_' || coalesce(t.name, 'none'), count(*) from artist a left join atype t on t.id = a.type_id group by t.name
 union all select 'artists_with_any_tag', count(*) from {P}
 union all select 'artists_with_official_genre', count(*) from {P} where n_genres > 0
 union all select 'artists_with_2plus_official_genres', count(*) from {P} where n_genres >= 2
 union all select 'artists_with_6plus_official_genres', count(*) from {P} where n_genres >= 6
 union all select 'distinct_top_genres', count(distinct top_genre) from {P}
 union all select 'top_genre_' || top_genre, count(*) from {P} where top_genre is not null group by top_genre""").df().sort_values('n', ascending=False)
rows.to_csv(f'{O}/artists_summary.csv', index=False)
print(rows.head(40).to_string()); print('size MB', round(os.path.getsize(f'{O}/artists_genre.parquet')/1e6,1))
