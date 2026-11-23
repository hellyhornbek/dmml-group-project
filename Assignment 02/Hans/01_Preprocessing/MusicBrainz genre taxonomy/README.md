# MusicBrainz genre taxonomy

How MusicBrainz's official genres relate to each other (subgenre of ...). Built by `03_MusicBrainz_genre_taxonomy.ipynb` (in this folder).

| File | What it is |
|---|---|
| `l_genre_genre` | The MusicBrainz table of relationships between two genres, copied unchanged from `mbdump.tar.bz2` (3,538 rows). Tab-separated, no header. Columns: id, link, entity0, entity1, edits_pending, last_updated, link_order, entity0_credit, entity1_credit. `link` points to the MusicBrainz `link` table, which says the type: subgenre, fusion of, or influenced by. For a subgenre relationship `entity0` is the parent. |
| `genre_hierarchy.csv` | One row per official genre (2,221). `parent` (the first one alphabetically if there are several), `all_parents`, `n_parents`, `family` (the top genre above it; the genre itself if it has no parent), `depth` (steps to the top, 0 = no parent), `n_children` (direct subgenres). |
| `taxonomy_coverage.csv` | For every year: how many of our genres, and how many listens, have a parent / are a top-level genre with subgenres / have no relationships. Made by matching the genre counts from notebook 02 to `genre_hierarchy.csv`. |

Only the subgenre relationships are used for the hierarchy. A few genres have more than one parent (8 of them); they use the first parent alphabetically for their family.
