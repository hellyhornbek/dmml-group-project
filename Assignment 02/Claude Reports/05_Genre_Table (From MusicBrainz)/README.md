# 05 Genre table: all official MusicBrainz genres

`Results/genres_overview.csv` lists every official MusicBrainz genre (2,221 rows) and how much each one is used as a tag across MusicBrainz.
It is made by `Scripts/01_official_genres.py` and contains no listening data and no ListenBrainz users.

## What the data represents

- **Official genres.** MusicBrainz keeps a short curated list of genre names (the `genre` table). This is the only list we treat as genres.
- **Tags.** Users also put free-text tags on artists and songs (the `tag` table, roughly 245,000 different tags). Most are used once and are not genres. A tag counts as a genre in our project only if its name is on the official list.
- **1,924 of the 2,221 official genres have been used as a tag** (`in_tag_table = true`). The other 297 have never been used, so all their counts are 0.
- **Why it matters.** Our genre for a listen comes from this list: the most voted official genre of the song, or of the artist if the song has none. So this file is the full set of genres that can possibly appear in our data. The extract can only contain a subset.

## Columns

| Column | Meaning |
|---|---|
| `genre_id` | MusicBrainz internal id of the genre |
| `mbid` | MusicBrainz permanent id (gid) of the genre |
| `genre` | The genre name |
| `comment` | Disambiguation note from MusicBrainz (mostly empty) |
| `in_tag_table` | `true` if a tag with this exact name exists |
| `tag_uses` | `ref_count` of the tag as stored by MusicBrainz: how often the tag is used on any kind of item (artists, songs, albums and others). It is not a count of songs |
| `recording_votes` | Total user votes for this tag on songs (recordings) |
| `recordings` | Number of different songs carrying the tag |
| `artist_votes` | Total user votes for this tag on artists |
| `artists` | Number of different artists carrying the tag |

The file is sorted by `tag_uses`, highest first (rock, electronic, pop, jazz, hip hop ...).

## How to read it

- Use `recordings` and `artists` to compare genres as labels for songs and artists. `tag_uses` also includes albums and other items, so it is larger (rock: 1,598,768 uses, but 664,493 songs and 18,723 artists).
- A vote is one user agreeing with a tag on one item, so `recording_votes` is higher than `recordings`.
- Only a small part of MusicBrainz is tagged (about 40.8 million songs in total), so these numbers describe how popular a label is, not how much music exists in each genre.
- **All counts are for the whole of MusicBrainz, not for our 13,515 users.** They say how well established a genre is, not how much our listeners play it.

## Not in this file yet

- Counts from our extract (listens, users, songs per genre). They need the whole extract linked to MusicBrainz first.
- Heavily used tags that are not official genres (for example indie, soundtrack). Planned rule: add tags above a usage threshold in the extract, merge synonyms (vgm = video game music, score = soundtrack), use them only for songs with no official genre, and keep an `official` / `added` column so we can run the analysis both ways.
- The genre families. We decide them after looking at the full overview.

## Run

```
python3 Scripts/01_official_genres.py --mb "<path to MusicBrainz Full>/tables/mbdump" --out Results/genres_overview.csv
```

Needs Python with `duckdb`. It reads the `genre`, `tag`, `recording_tag` and `artist_tag` tables.
