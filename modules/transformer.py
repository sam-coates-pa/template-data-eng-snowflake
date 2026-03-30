import pandas as pd
from datetime import datetime


def transform_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure timestamp formatting
    df["event_time"] = pd.to_datetime(df["event_time"], errors="coerce")

    # Filter out rows lacking key fields
    df = df.dropna(subset=["id", "event_time", "event_type"])

    # Normalise event_type into lowercase
    df["event_type"] = df["event_type"].str.lower()

    # Add processed timestamp
    df["processed_at"] = datetime.utcnow().isoformat()

    # Optional: sort rows for deterministic output
    df = df.sort_values("event_time").reset_index(drop=True)

    return df
