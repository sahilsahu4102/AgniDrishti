import csv
import time

import pandas as pd

import config


def load():
    """Replay and live scored alerts as one table."""
    parts = [pd.read_csv(p) for p in (config.SCORED, config.LIVE_SCORED) if p.exists()]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def record(aid, src, result):
    """Append an image or field outcome (§8: append-only, the latest row per id wins)."""
    new = not config.OUTCOMES.exists()
    with open(config.OUTCOMES, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['id', 'src', 'result', 'ts'])
        w.writerow([aid, src, result, round(time.time(), 3)])
