# Part 1 - Genre popularity: what is where

## Code (run in this order)

| Notebook | What it does | Saves |
|---|---|---|
| `01_Data_and_users` | Shows how the extract is read, what the columns are, and which users we work with (development users = buckets 0-9). | nothing |
| `02_From_listens_to_genres` | For one `YEAR`: counts the songs, builds match keys, finds the songs in MusicBrainz, finds each song's genre, counts listens per genre. Set `DEV_ONLY = False` for all users. Leaves out duplicate listens (`is_dup`). `02.02_run_all_years.py` runs it for all years in a row. | the song table (parquet) and two small csv files, see below |
| `03_User_genre_table` | For every user and year: listens per genre and the share of the user's labelled listens. Also one row per user-year with total listens, labelled listens, `coverage_pct` and `bucket`. Needs the song tables from notebook 02. Checks that everything adds up to the genre counts of notebook 02. | `user_genre` and `user_year`, each as parquet and csv, see below |
| `MusicBrainz genre taxonomy/03_MusicBrainz_genre_taxonomy` | Reads which genres are subgenres of which in MusicBrainz, builds `genre_hierarchy.csv` (family and depth of every genre) and checks how many of our listens it covers. Not used by the other notebooks yet. | files in `MusicBrainz genre taxonomy/` |

## Input (not in git, too big)

### The extract: `Extract/extract/year=YYYY/part-*.parquet`

One row per **listen**. The 13,515 cohort users, 2002 to 31 Oct 2026. 2026 has 39 files, about 77 million listens.

A parquet file holds a table like a csv, but stored column by column, compressed and typed, so it is much smaller and much faster to read. It is read with DuckDB (`read_parquet`) without loading it into memory.

20 columns. The ones we use:

| column | meaning |
|---|---|
| `user_id` | the listener (anonymous number) |
| `ts` | time of the listen, seconds since 1 Jan 1970, UTC |
| `artist_name`, `track_name` | what ListenBrainz knows about the song |
| `recording_mbid`, `artist_mbid`, `release_mbid` | MusicBrainz ids; only about 5% of the listens have them |

Not used so far: `year`, `release_name`, `recording_msid`, `spotify_id`, `origin_url`, `source`, `music_service`, `tracknumber`, `isrc`, `duration_ms`, `ms_played`, `is_dup` (marks exact repeats), `extra_json`.

There is **no genre column**. Genres come from MusicBrainz tags.

### Small csv files next to the extract

- `cohort_users.csv`: one row per user, with `bucket` (0-99, fixed and random) and `total_listens`.
- `cohort_year_counts.csv`: listens per user per year. Used to check our counts.

## Output

### `Output_dev/data/parquets/songs/songs_genre_YEAR_dev.parquet` (big, not in git)

One row per **distinct song** of that year (not per listen). 2026, development users: 1,837,078 songs, 7,597,478 listens (the 7,761,058 listens of the year minus 163,580 duplicates).

| column | meaning |
|---|---|
| `artist_name`, `track_name` | the song as ListenBrainz writes it |
| `n_listens` | how many listens the song has, **without the duplicates the extract flags (`is_dup`)** (sums to the listens of the year minus those) |
| `matched_by` | how it was found in the MusicBrainz canonical table, tried in this order: `plain` key, `clean` key (after the feat./bracket/" - " rules), `collab` key (`A, B` written as `A feat B`), `title_feat` key (`(feat. B)` in the title moved to the artist), or `none` |
| `id_source` | whose id we use: `listenbrainz`, `canonical` or `none` |
| `recording_mbid`, `artist_mbid`, `release_mbid` | the MusicBrainz ids (empty if not found) |
| `genre` | the most-voted official MusicBrainz genre of the recording, otherwise of the artist; empty if none |
| `genre_source` | `recording`, `artist` or `none` |

### The small csv results (one per year, in `Output_dev/genre_counts/YEAR/`)

- `genre_counts_YEAR_dev.csv`: `year, genre, listens, songs`. One row per genre, only listens that have a genre. This is what the analysis and plots start from.
- `coverage_YEAR_dev.csv`: `year, category, songs, listens`. How many listens have a genre from the recording / the artist, were found in MusicBrainz but have no genre, or were not found.

These were summed from the song table, so they are a **summary**, not the same content: the parquet has one row per song, `genre_counts` one row per genre. Notebook 02 saves them in `Output_dev/genre_counts/YEAR/` (one folder per year), and a new run of the same year overwrites them.

### The user x genre tables (notebook 03)

| file | one row per | columns |
|---|---|---|
| `user_genre_dev.parquet` / `.csv` | user, year, genre | `year`, `user_id`, `genre`, `listens`, `share` (listens / the user's labelled listens that year; adds up to 1 per user-year) |
| `user_year_dev.parquet` / `.csv` | user, year | `year`, `user_id`, `total_listens`, `labelled_listens`, `coverage_pct`, `bucket` |

The parquet files are in `Output_dev/data/parquets/user_genre_tables/`, the csv files in `Output_dev/user_genre_tables/`. Both are sorted by year and user. The song tables are in `Output_dev/data/parquets/songs/`.

### `Output_dev/data/listens_2026_dev.csv` (old, not used any more)

One row per listen of the development users for 2026 (7,761,058 rows, 8 columns). It came from the earlier route that saved the listens first. Notebook 02 reads the parquet files directly and does not need it.
