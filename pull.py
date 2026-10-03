import io
import sys
import time
from datetime import date, timedelta

import pandas as pd
import requests

import config

API = 'https://firms.modaps.eosdis.nasa.gov/api/area/csv'


def chunk(source, days, start=None):
    """One FIRMS area call: `days` (1-5) days from `start`, or the latest days if no start."""
    box = ','.join(map(str, config.BOX))
    url = f'{API}/{config.FIRMS_KEY}/{source}/{box}/{days}' + (f'/{start}' if start else '')
    for attempt in range(4):
        try:
            text = requests.get(url, timeout=180).text
            if text.startswith('latitude'):  # a bad key or limit returns plain text
                return pd.read_csv(io.StringIO(text))
        except requests.RequestException:
            pass
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(f'FIRMS returned no CSV for {source} {start}; check FIRMS_KEY and the rate limit')


def get(source, start, end):
    parts, d, last = [], date.fromisoformat(start), date.fromisoformat(end)
    while d <= last:
        parts.append(chunk(source, 5, d))
        d += timedelta(days=5)
        time.sleep(1)
    df = pd.concat(parts, ignore_index=True).drop_duplicates()
    return df[(df.acq_date >= start) & (df.acq_date <= end)]


if __name__ == '__main__':
    for name in sys.argv[1:] or config.WINDOWS:
        source, start, end = config.WINDOWS[name]
        df = get(source, start, end)
        df.to_csv(config.DATA / f'{name}.csv', index=False)
        print(f'{name}: {source} {start}..{end}: {len(df)} rows')
