# Context for AI assistants: the ListenBrainz extract (Data Mining exam project)

Paste this file into your AI chat before asking questions about our data. It describes the FULL extract that Hans has on his machine. Teammates normally only have the small sample (`sample_2023_600users.csv`) and `cohort_users.csv`. Anything not stated here is unknown: say so instead of guessing.

## 1. Project in one paragraph
Group exam project in "Data Mining and Machine Learning KSD" (ITU, autumn 2026). We build a music-listening dataset from the full ListenBrainz listens dump (plus MusicBrainz metadata) and study long-term listeners. The report is 8-15 pages (ITU LaTeX template), the code must be in commented Python scripts or notebooks, and we must use at least two preprocessing techniques and algorithms from at least two categories (supervised, unsupervised, data mining such as association rules or anomaly detection). Course libraries: pandas, numpy, scikit-learn. Deadlines: 17 Dec 2026 (Assignment #02) and 4 Jan 2027 13:59 (exam).

Draft research directions (not final): (1) can long-term listeners be grouped into 3-6 interpretable types (clustering on genre mix, artist loyalty, discovery, volume), (2) which genres are played by the same listeners, (3) "The superfan is dead": does listening become more varied over the years, (4) optional: predict the listener type from behaviour as validation.

## 2. Source
- ListenBrainz full listens dump no. 2758, dated 2026-11-01 (about 267 GB compressed, 2,990,440,915 lines, one JSON listen per line).
- Extract built with `extract.py` from a cohort defined by `build_cohort.py` (on Hans's machine, in `Reports/03_Cohort` and `Reports/04_Extract`, each step with its own report). Verified with `--check`: all checks passed (see section 6).

## 3. The cohort (who is in the extract)
Rule: a user is in if they have at least 5 consecutive calendar years in which each year has 2,000-40,000 raw listens (UTC years; for 2026 the limits are scaled by 10/12 to about 1,667-33,333 because the dump ends 1 Nov). A user with any year above the maximum anywhere in their history is excluded completely. The 2,000 minimum only applies inside the 5-year window. The user's whole listening history is kept (also years outside the window, including years below 2,000). No sampling, no cap on rows.

Result: **13,515 users, 1,462,060,308 listens** (rows in the extract, including 12.7 M rows flagged as duplicates).
Why others are excluded (of 101,881 users in the dump, counted with the same rule code): 3,604 users (3.5%) have a year above 40,000 listens; they hold 1,047,858,853 listens, 35.0% of all listens in the dump. 84,762 users (83.2%) have no 5 consecutive years within the limits (history too short, gaps or too few listens). The cohort is 13.3% of the users and 48.9% of the listens. Cohort share of each year's listens: about 65% in 2005-2016, falling to 19% in 2026 (many new users).

Consequences to remember: the extract describes long-term, moderate-volume users (survivors), not all ListenBrainz users. Many listens come from imported histories (e.g. from Last.fm/Spotify), so "listen time" is not always when the music was actually played in ListenBrainz; upload date is not available.

## 4. Extract layout
- Folder `Extract/extract/year=YYYY/part-NNNNNN.parquet` (zstd), years 2002-2026, 755 files, about 126 GB. Partitioned by `year` (UTC year of `ts`). Query with DuckDB or pyarrow; do not load everything into pandas.
- `Extract/cohort_users.csv` (13,515 rows): `user_id`, `window_start`, `window_end` (first qualifying 5+ year run), `first_year`, `last_year` (first/last year with any listen), `n_runs` (number of separate qualifying runs, 968 users have more than one), `total_listens` (raw, incl. duplicates), `bucket` (0-99 = md5(user_id) mod 100, used for repeatable user splits, planned 10% development / 10% validation / 80% final).
- `Extract/cohort_year_counts.csv` (170,653 rows): `user_id`, `year`, `listens` (raw listens per user and year).
- `Extract/config.json`: the cohort rule parameters.

## 5. Columns in the Parquet files (verified from the files)
| Column | Type | Meaning |
|---|---|---|
| user_id | int64 | pseudonymous user number (username removed) |
| ts | int64 | Unix timestamp of the listen, UTC |
| year | int16 | UTC year of ts (partition) |
| artist_name, track_name, release_name | string | as submitted by the user's client (free text, can be messy) |
| recording_msid | string | ListenBrainz's own recording ID |
| recording_mbid, release_mbid, artist_mbid | string | MusicBrainz IDs, only when present (from ListenBrainz mapping or the client); artist_mbid is the first artist |
| spotify_id, origin_url, isrc | string | extra identifiers when the client gave them |
| source | string | submitting client (submission_client) |
| music_service | string | streaming service if reported |
| tracknumber | int32 | values outside the int32 range were set to empty |
| duration_ms, ms_played | int64 | reported track length / time played; mostly empty |
| is_dup | bool | true if same user, same second, same artist and track as another row (12,684,853 rows, 0.87%) |
| extra_json | string | the remaining `additional_info` fields as JSON |

Not in the data: genre, tags, release year, artist details, listener type, any features. Those come from the later linking and feature steps. Hour of day and weekday should NOT be used as features because the user's time zone/location is unknown (timestamps are UTC); year and differences between timestamps are fine.

## 6. What we know about the content (measured on the full extract)
Listens and users per year (all rows, including duplicates). Shares are the fraction of rows with a value.

| Year | Rows (M) | Users | has recording_mbid | has source | has ms_played |
|---|---|---|---|---|---|
| 2005 | 6.2 | 1,015 | 3% | 79% | 0% |
| 2008 | 32.5 | 3,866 | 26% | 55% | 0% |
| 2010 | 43.5 | 5,151 | 26% | 56% | 1% |
| 2012 | 48.1 | 6,312 | 25% | 57% | 3% |
| 2014 | 55.2 | 7,523 | 24% | 57% | 8% |
| 2016 | 60.0 | 8,655 | 18% | 61% | 18% |
| 2018 | 80.9 | 9,941 | 12% | 70% | 26% |
| 2020 | 101.1 | 10,904 | 2% | 79% | 29% |
| 2022 | 117.2 | 11,777 | 1% | 89% | 30% |
| 2023 | 120.2 | 11,529 | 1% | 95% | 30% |
| 2024 | 113.4 | 11,183 | 2% | 96% | 31% |
| 2025 | 103.3 | 10,671 | 4% | 95% | 29% |
| 2026 (to 1 Nov) | 77.0 | 10,556 | 9% | 96% | 13% |

Listens by period: 2005-2010 about 11%, 2011-2015 17%, 2016-2020 27%, 2021-2026 44%; peak year 2023 (about 8%). Per user over the whole history: mean 108,000 listens, median 90,000, maximum 630,000. Listens per user-year: median 6,700, maximum 39,994. Artist and track names are (practically) never empty. Overall about 10.9% of rows have a recording_mbid (the share varies a lot by year, see table), 76% have a source, 26.7% duration_ms, 20.3% ms_played. Duplicate share is about 0.3-1.9% per year (2005 onwards).

Not yet done (do not assume): a full high-level report with top artists/sources, distinct songs per slice, genre linking of the full extract, cleaning rules agreed by the group.

## 7. Planned layers (how we work from here)
1. Extract (done, raw, no cleaning).
2. Clean: remove `is_dup`, handle outliers, agree rules together (prefer a DuckDB view; materialise subsets only).
3. Link: build a match key (lowercase, accent-stripped letters and digits of artist + title), match distinct songs to the MusicBrainz canonical lookup (`musicbrainz-canonical-dump-20261103`, about 69-72% of distinct songs match), then add genre (main genre = most-voted official genre of the song, fallback the artist's top genre), tags, release year, artist info from the MusicBrainz tables.
4. Features designed together by the group (nothing is assumed in advance), then clustering and classification on user or user-year rows.
Typical working units: a user-year or a user sample (for example the 10% bucket), not all 1.46 billion rows.

## 8. Known limitations (state them in answers and in the report)
- Only long-term, moderate-volume users; heavy uploaders (above 40,000 listens/year) are excluded.
- Imported histories: timestamps may reflect the original source; there is no upload date.
- MusicBrainz genres/tags/country describe the artist or song today, not at the time of listening; some release years are anachronistic (reissues).
- About 29% of listens did not get a recording id when linked by name (600-user sample); about 39% of listens end up without a genre (in the 600-user sample 61.1% of listens have a genre). The unlinked part is not random (obscure, user-made and streaming-style titles with "feat." or "Remastered" link less).
- MBIDs in the raw data are heavily year-dependent (25% in 2006-2014, about 1% in 2020-2023).
- AcousticBrainz audio features ended in June 2022 and are not part of the extract.
- Privacy: user ids are pseudonymous numbers; usernames were dropped. Do not try to re-identify users.

## 9. Related files
- `test_data/sample_2023.csv` plus its README: 600 cohort users from 2023 (the 600 with the smallest hash of seed 2023 and user id, from the 10,558 cohort users with 2,000-40,000 listens in 2023), 200,007 listens (each user keeps about 3.0% of their 2023 listens, exact repeats removed first), already linked to MusicBrainz (about 70% of the distinct songs with a match key are matched in the canonical dump). Made on 12 Nov 2026 with scripts that can be repeated from the extract (`Reports/05_Test_Sample`); a first version from 11 Nov was replaced and has different users. When a song has several genres with equal votes, the first alphabetically is used. Columns: user_id, listen_time_utc, player_duration_ms, song, artist, album, release_year, genre, artist_tags, song_tags, song_length_ms, artist_begin_year, artist_end_year, artist_type, artist_country, recording_id, matchkey.
- `AI_pakke/cohort_users.csv`, `AI_pakke/per_year_overview.csv` (the table in section 6 with all columns).
- On Hans's machine the whole history is documented step by step in `Reports/` (00 downloading, 01 count pass, 02 profile pass, 03 cohort, 04 extract, 05 test sample), each with scripts, output, figures and a report.
