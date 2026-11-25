# 06 Artist table: all artists in MusicBrainz

How many artists exist in MusicBrainz, and how many of them carry genre information. Made by `Scripts/01_artists.py`.
It contains no listening data and no ListenBrainz users, so it says nothing yet about the artists our listeners play.

## Files

- `Results/artists_summary.csv`: small table of counts (`measure`, `n`).
- `Results/artists_genre.parquet`: one row per artist **that has at least one tag** (271,562 artists, about 10 MB). The other artists are only counted in the summary, to keep the file small enough for the repository.

## The main numbers

| | Artists | Share of all |
|---|---|---|
| All artists in MusicBrainz | 3,032,671 | 100% |
| With at least one tag (vote above 0) | 271,562 | 9.0% |
| With at least one official genre | 218,964 | 7.2% |
| With two or more official genres | 102,947 | 3.4% |
| With six or more official genres | 14,771 | 0.5% |
| With a begin year | 608,509 | 20.1% |
| With an area | 1,506,390 | 49.7% |

By type: person 1,627,005, group 669,091, no type 688,473, character 18,246, orchestra 12,058, choir 11,051, other 6,747.

Most artists in MusicBrainz have no genre at all. Only about 1 in 14 has an official genre. Our listens still get a genre for about 64% of them, because listening is concentrated on a small number of well-known, well-tagged artists.

## Columns in `artists_genre.parquet`

| Column | Meaning |
|---|---|
| `artist_id`, `mbid` | MusicBrainz internal id and permanent id |
| `name`, `artist_type`, `area` | Name, type (person, group ...) and area |
| `begin_year`, `end_year`, `ended` | Active period as registered in MusicBrainz (often empty) |
| `n_tags`, `tag_votes` | Number of different tags on the artist, and the votes on them |
| `n_genres`, `genre_votes` | The same, counting only official genres (the list in `05_Genre_Table`) |
| `top_genre`, `top_genre_votes` | The official genre with most votes on the artist, ties broken alphabetically |

## Rules and cautions

- Only tag votes above 0 are counted.
- `top_genre` is the artist's most voted official genre. It is the same rule as our fallback when a song has no genre of its own.
- Some artists have unusually many genres (one has 102). Treat very high `n_genres` with care before using it as a feature.
- Everything is across all of MusicBrainz and not our extract. It tells us how well described the artists are, not which ones our listeners play.

## Run

```
python3 Scripts/01_artists.py --mb "<path to MusicBrainz Full>/tables/mbdump" --out-dir Results
```

Needs Python with `duckdb` and about 3 minutes. It reads `artist`, `artist_type`, `area`, `genre`, `tag` and `artist_tag`.
