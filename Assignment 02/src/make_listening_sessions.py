import pandas as pd
from pathlib import Path


def make_sessions(min_len, max_len, min_gap, sample_path, sessions_path):
    """Split listens into sessions and write them to sessions_path.

    min_len       sessions with fewer listens are dropped
    max_len       longer sessions keep only their first max_len listens
    min_gap       pd.Timedelta; a gap longer than this starts a new session
    sample_path   input csv of cleaned listens (listens_cleaned.csv from the preprocessing notebook)
    sessions_path output csv, one row per listen

    Returns the sessions DataFrame.
    """
    sample_path, sessions_path = Path(sample_path), Path(sessions_path)

    # read the listens, ordered by user, then timestamp
    df = pd.read_csv(sample_path)
    df["listen_time_utc"] = pd.to_datetime(df["listen_time_utc"], utc=True)
    df = df.sort_values(["user_id", "listen_time_utc"], kind="stable").reset_index(drop=True)

    # new session at each user's first listen, or when the gap to the previous listen exceeds min_gap
    gap = df.groupby("user_id")["listen_time_utc"].diff()
    df["session_id"] = (gap.isna() | (gap > min_gap)).cumsum()

    # drop sessions shorter than min_len listens
    session_size = df.groupby("session_id")["session_id"].transform("size")
    sessions = df[session_size >= min_len].copy()

    # give sessions new ids, and number the listens inside each session
    sessions["session_id"] = sessions.groupby("session_id", sort=False).ngroup()
    sessions["position_in_session"] = sessions.groupby("session_id").cumcount() + 1

    # truncate long sessions: keep only the first max_len listens (the rest is dropped)
    n_truncated = (sessions.groupby("session_id").size() > max_len).sum()
    sessions = sessions[sessions["position_in_session"] <= max_len]

    # write sessions.csv: one row per listen, grouped by user and session
    sessions_path.parent.mkdir(parents=True, exist_ok=True)
    sessions.to_csv(sessions_path, index=False)

    # print the summary
    n_all = df["session_id"].nunique()
    n_kept = sessions["session_id"].nunique()
    print(f"{n_all:,} sessions found, {n_kept:,} kept (>= {min_len} listens), "
          f"{n_truncated:,} truncated to the first {max_len} listens")
    print(f"Total samples in {sessions_path}: {n_kept:,} sessions, "
          f"{len(sessions):,} listens, {sessions['user_id'].nunique():,} users")

    return sessions
