#!/usr/bin/env python3
"""Step 1: overview of all official MusicBrainz genres (no listening data involved).
One row per official genre with how much it is used as a tag across MusicBrainz:
  tag_uses         tag.ref_count (all uses of the tag on any entity: artists, recordings, releases ...)
  recording_votes  sum of votes on recordings (recording_tag.count);  recordings = number of recordings tagged
  artist_votes     sum of votes on artists (artist_tag.count);        artists    = number of artists tagged
  in_tag_table   False if no tag with the genre's name exists (never used)
Usage: python3 01_official_genres.py --mb "<.../MusicBrainz Full/tables/mbdump>" --out genres_overview.csv
"""
import argparse, duckdb
ap = argparse.ArgumentParser(); ap.add_argument('--mb', required=True); ap.add_argument('--out', default='genres_overview.csv'); a = ap.parse_args(); D = a.mb.rstrip('/')
con = duckdb.connect(); con.execute("pragma memory_limit='1500MB'"); con.execute("pragma temp_directory='/tmp/duck'")
rd = lambda f, cols: f"read_csv('{D}/{f}', delim='\\t', header=false, columns={cols}, quote='', escape='', null_padding=true, all_varchar=true)"
con.execute(f"create view genre as select * from {rd('genre', {'id':'varchar','gid':'varchar','name':'varchar','comment':'varchar','edits':'varchar','upd':'varchar'})}")
con.execute(f"create view tag as select cast(id as bigint) id, name, cast(ref_count as bigint) ref_count from {rd('tag', {'id':'varchar','name':'varchar','ref_count':'varchar'})}")
con.execute(f"create view rt as select cast(tag as bigint) tag, cast(count as bigint) cnt from {rd('recording_tag', {'recording':'varchar','tag':'varchar','count':'varchar','upd':'varchar'})}")
con.execute(f"create view atg as select cast(tag as bigint) tag, cast(count as bigint) cnt from {rd('artist_tag', {'artist':'varchar','tag':'varchar','count':'varchar','upd':'varchar'})}")
con.execute("create table r as select tag, sum(cnt) votes, count(*) n from rt group by tag")
con.execute("create table ar as select tag, sum(cnt) votes, count(*) n from atg group by tag")
con.execute(f"""copy (select cast(g.id as int) genre_id, g.gid mbid, g.name genre, g.comment, t.id is not null in_tag_table,
  coalesce(t.ref_count,0) tag_uses, coalesce(r.votes,0) recording_votes, coalesce(r.n,0) recordings, coalesce(x.votes,0) artist_votes, coalesce(x.n,0) artists
  from genre g left join tag t on t.name=g.name left join r on r.tag=t.id left join ar x on x.tag=t.id order by tag_uses desc) to '{a.out}' (header, delimiter ',')""")
print(con.sql(f"select count(*) genres, sum(in_tag_table::int) in_tag, sum((tag_uses>0)::int) used from read_csv('{a.out}')").fetchall())
