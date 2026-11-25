# define variables
import pandas as pd
from pathlib import Path



# read the listens of sample_2023_600users.csv, ordered by user, then timestamp
df = df.sort_values(["user_id", "listen_time_utc"], kind="stable").reset_index(drop=True)

# new session at each user's first listen, or when the gap to the previous listen exceeds MIN_GAP
gap = df.groupby("user_id")["listen_time_utc"].diff()
df["session_id"] = (gap.isna() | (gap > MIN_GAP)).cumsum()

# drop sessions shorter than MIN_LEN listens
session_size = df.groupby("session_id")["session_id"].transform("size")
sessions = df[session_size >= MIN_LEN].copy()

# give session new ids, and number / id the listens inside each session
sessions["session_id"] = sessions.groupby("session_id", sort=False).ngroup()
sessions["position_in_session"] = sessions.groupby("session_id").cumcount() + 1

# truncate long sessions: keep only the first MAX_LEN listens (the rest is dropped)
n_truncated = (sessions.groupby("session_id").size() > MAX_LEN).sum()
sessions = sessions[sessions["position_in_session"] <= MAX_LEN]

# write to the new sessions.csv: one row per listen, grouped by user and session
sessions.to_csv(SESSIONS_PATH, index=False)

# print the summery: 
n_all = df["session_id"].nunique()
n_kept = sessions["session_id"].nunique()
print(f"{n_all:,} sessions found, {n_kept:,} kept (>= {MIN_LEN} listens), "
      f"{n_truncated:,} truncated to the first {MAX_LEN} listens")

check = pd.read_csv(SESSIONS_PATH)
print(f"Total samples in {SESSIONS_PATH}: {check['session_id'].nunique():,} sessions, "
      f"{len(check):,} listens, {check['user_id'].nunique():,} users")