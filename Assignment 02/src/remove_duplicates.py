import pandas as pd
from pathlib import Path

# Clean data
# remove duplicate listens: same user id, track id, timestamp
# get genre data if not there already


def remove_duplicates(sample_path, cleaned_path=None):
    """Read the sample and remove duplicate listens (same user, track, timestamp).

    sample_path   input csv (e.g. sample_2023_600users.csv)
    cleaned_path  optional output csv; if given, the cleaned listens are written there

    Returns the cleaned DataFrame (with a parsed listen_time_utc and a track_key column).
    """
    df = pd.read_csv(Path(sample_path))
    df["listen_time_utc"] = pd.to_datetime(df["listen_time_utc"], utc=True)

    # track id: matchkey (97% filled); fall back to lowercased artist + song when it is missing
    df["track_key"] = df["matchkey"].fillna(df["artist"].str.lower() + " - " + df["song"].str.lower())

    n_before = len(df)
    df = df.drop_duplicates(subset=["user_id", "track_key", "listen_time_utc"]).reset_index(drop=True)
    print(f"Removed {n_before - len(df):,} duplicate listens, {len(df):,} left")

    if cleaned_path is not None:
        cleaned_path = Path(cleaned_path)
        cleaned_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cleaned_path, index=False)

    return df
