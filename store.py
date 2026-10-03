import pandas as pd

import config


def load():
    """Replay and live scored alerts as one table."""
    parts = [pd.read_csv(p) for p in (config.SCORED, config.LIVE_SCORED) if p.exists()]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
