# Test sample: 600 users, 2023 (200,314 listens)

File: `sample_2023_600users.csv` (UTF-8, comma-separated, one row per listen, sorted by user and time).
This is a TEST sample for getting started, not the analysis dataset.

## How it was made
- Source: our extract (`Extract/extract/year=2023`), i.e. ListenBrainz listens of the 13,515 cohort users.
- Pool: cohort users with 2,000-40,000 listens in 2023 (10,558 users). 600 picked at random (fixed hash seed, repeatable).
- Scaling: every listen of those users was kept with the same probability (3.08%), so the total is about 200k and each user's share of the volume is preserved. Exact repeats (`is_dup`) were removed first.
  Consequence: loyalty / new-artist / variety measures computed on this sample are noisier than on the full year.
- Linking: artist+title match key -> MusicBrainz canonical lookup (69% of distinct songs matched); MBIDs already in ListenBrainz were used first. Details from the MusicBrainz tables (full dump of Nov 2026).

## Columns
| Column | Meaning | Filled |
|---|---|---|
| user_id | pseudonymous ListenBrainz user | 100% |
| listen_time_utc | date and time of the listen, UTC (local time unknown) | 100% |
| player_duration_ms | milliseconds played, as reported by the player | 31.5% |
| song, artist, album | as submitted by the user's client | 100 / 100 / 98% |
| release_year | year of the album's (release group's) first release in MusicBrainz | 71% |
| genre | most-voted official MusicBrainz genre of the song; if none, the artist's most-voted genre (ties: first alphabetically) | 61% |
| artist_tags, song_tags | up to 10 MusicBrainz tags (all kinds, by votes), separated by `; ` | 61% / 32% |
| song_length_ms | length of the recording in MusicBrainz | 70% |
| artist_begin_year, artist_end_year | MusicBrainz life-span years (end year empty if still active) | 59% / 8% |
| artist_type | Person, Group, Orchestra, ... | 70% |
| artist_country | MusicBrainz "area" of the artist - usually a country, but sometimes a city or region | 68% |
| recording_id | MusicBrainz recording MBID (from ListenBrainz or the match) | 71% |
| matchkey | lowercase, accent-stripped letters and digits of artist + title | 98% |

## Caveats
- Empty genre/tags mean "not linked or no tags", not "no genre". Unlinked listens are not a random subset.
- Tags, country and genre describe the artist/song in MusicBrainz today, not at the time of listening.
- Some release years are later than 2023 (2,147 rows) because MusicBrainz release dates can come from reissues or later entries.
- Names and match keys with non-Latin scripts match less often.
