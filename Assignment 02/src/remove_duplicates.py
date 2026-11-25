import pandas as pd
from pathlib import Path

# Clean data 
# remove duplicate listens: same user id, track id, timestamp
# get genre data if not there already

# Clean data: read the sample and remove duplicate listens (same user, track, timestamp)
df = pd.read_csv(SAMPLE_PATH)
df["listen_time_utc"] = pd.to_datetime(df["listen_time_utc"], utc=True)

# track id: matchkey (97% filled); fall back to lowercased artist + song when it is missing
df["track_key"] = df["matchkey"].fillna(df["artist"].str.lower() + " - " + df["song"].str.lower())

n_before = len(df)
df = df.drop_duplicates(subset=["user_id", "track_key", "listen_time_utc"])
print(f"Removed {n_before - len(df):,} duplicate listens, {len(df):,} left")