import json
import math
import time
from functools import lru_cache

import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.windows import Window
from sklearn.neighbors import BallTree

import config
import geo


@lru_cache(maxsize=None)
def tile(path):
    return rasterio.open(path)


def prepare(df):
    """Alert time t (UTC) and the stable alert id (§9); drops duplicate ids."""
    hhmm = df.acq_time.astype(int).astype(str).str.zfill(4)
    df = df.assign(t=pd.to_datetime(df.acq_date + ' ' + hhmm, format='%Y-%m-%d %H%M', utc=True),
                   id=df.acq_date + '_' + hhmm + '_' + df.latitude.map('{:.4f}'.format) + '_' + df.longitude.map('{:.4f}'.format))
    return df.drop_duplicates('id').reset_index(drop=True)


def landcover(lat, lon, scan, track):
    """Shares of vegetation (10-30), tree cover (10) and farm or built-up (40, 50) inside the pixel footprint."""
    t = tile(config.WORLDCOVER / f'ESA_WorldCover_10m_2021_v200_N{math.floor(lat / 3) * 3:02d}E{math.floor(lon / 3) * 3:03d}_Map.tif')
    dlat, dlon = track / 111 / 2, scan / (111 * math.cos(math.radians(lat))) / 2
    r0, c0 = t.index(lon - dlon, lat + dlat)
    r1, c1 = t.index(lon + dlon, lat - dlat)
    r0, c0, r1, c1 = max(r0, 0), max(c0, 0), min(r1, t.height - 1), min(c1, t.width - 1)  # one tile is enough (§19)
    a = t.read(1, window=Window(c0, r0, c1 - c0 + 1, r1 - r0 + 1))
    a = a[a > 0]
    if a.size == 0:
        return np.nan, np.nan, np.nan
    return np.isin(a, (10, 20, 30)).mean(), (a == 10).mean(), np.isin(a, (40, 50)).mean()


def slope(lat, lon):
    """Degrees, from a 3x3 DEM window centred on the alert."""
    t = tile(config.DEM / f'Copernicus_DSM_COG_10_N{math.floor(lat):02d}_00_E{math.floor(lon):03d}_00_DEM.tif')
    r, c = t.index(lon, lat)
    r, c = min(max(r, 1), t.height - 2), min(max(c, 1), t.width - 2)  # clamp at tile edges
    z = t.read(1, window=Window(c - 1, r - 1, 3, 3)).astype(float)
    dy = abs(t.res[1]) * 111320
    dx = t.res[0] * 111320 * math.cos(math.radians(lat))
    return math.degrees(math.atan(math.hypot((z[1, 2] - z[1, 0]) / (2 * dx), (z[0, 1] - z[2, 1]) / (2 * dy))))


def burns():
    """Planned-burn register, read fresh on every pass so new entries apply at once."""
    b = pd.read_csv(config.BURNS)
    return b.assign(start=pd.to_datetime(b.start, utc=True), end=pd.to_datetime(b.end, utc=True))


def burn(lat, lon, t, register):
    for b in register.itertuples():
        if b.start <= t <= b.end and geo.km(lat, lon, b.lat, b.lon) <= b.r_km:
            return b.id
    return ''


def seen(df):
    """Other alerts within SEEN_KM in the SEEN_HOURS up to and including each alert's time (D2)."""
    order = df.t.sort_values(kind='stable').index
    t = df.t[order].values.astype('datetime64[s]').astype(np.int64)
    lat, lon = df.latitude[order].values, df.longitude[order].values
    lo = np.searchsorted(t, t - config.SEEN_HOURS * 3600, side='left')
    hi = np.searchsorted(t, t, side='right')
    n = [(geo.km(lat[i], lon[i], lat[lo[i]:hi[i]], lon[lo[i]:hi[i]]) <= config.SEEN_KM).sum() - 1 for i in range(len(t))]
    return pd.Series(n, index=order).reindex(df.index)


def villages(df):
    v = pd.read_csv(config.VILLAGES)
    d, i = BallTree(np.radians(v[['lat', 'lon']].values), metric='haversine').query(np.radians(df[['latitude', 'longitude']].values))
    return d[:, 0] * geo.R, v.name.values[i[:, 0]]


now_cache = {}  # live alerts: current weather per cell, kept 15 minutes


def weather(df):
    """Hourly wind (km/h) and humidity (%) at the acquisition hour, cached per 0.25 degree cell. NaN when unavailable."""
    config.WEATHER.mkdir(parents=True, exist_ok=True)
    cell = config.WEATHER_CELL_DEG
    df = df.assign(cy=np.floor(df.latitude / cell).astype(int), cx=np.floor(df.longitude / cell).astype(int),
                   hour=df.t.dt.strftime('%Y-%m-%dT%H:00'))
    recent = df.t >= pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=config.LIVE_WEATHER_DAYS)
    wind, rh = pd.Series(np.nan, index=df.index), pd.Series(np.nan, index=df.index)
    for (cy, cx), g in df.groupby(['cy', 'cx']):
        lat, lon = (cy + 0.5) * cell, (cx + 0.5) * cell
        path = config.WEATHER / f'{cy}_{cx}.json'
        cache = json.loads(path.read_text()) if path.exists() else {}
        old = g[~recent[g.index]]
        if not old.hour.isin(set(cache)).all():
            try:
                h = requests.get('https://archive-api.open-meteo.com/v1/archive', timeout=60, params={
                    'latitude': lat, 'longitude': lon, 'start_date': old.t.min().strftime('%Y-%m-%d'),
                    'end_date': old.t.max().strftime('%Y-%m-%d'), 'hourly': 'wind_speed_10m,relative_humidity_2m',
                    'timezone': 'UTC'}).json()['hourly']
                cache.update({k: [w, r] for k, w, r in zip(h['time'], h['wind_speed_10m'], h['relative_humidity_2m'])})
                path.write_text(json.dumps(cache))
            except (requests.RequestException, KeyError, ValueError):
                pass
        for i, hr in zip(old.index, old.hour):
            wind[i], rh[i] = cache.get(hr, [np.nan, np.nan])
        new = g[recent[g.index]]
        if len(new):
            if time.time() - now_cache.get((cy, cx), (0, None))[0] > 900:
                try:
                    c = requests.get('https://api.open-meteo.com/v1/forecast', timeout=30, params={
                        'latitude': lat, 'longitude': lon, 'current': 'wind_speed_10m,relative_humidity_2m',
                        'timezone': 'UTC'}).json()['current']
                    now_cache[(cy, cx)] = (time.time(), [c['wind_speed_10m'], c['relative_humidity_2m']])
                except (requests.RequestException, KeyError, ValueError):
                    pass
            wr = now_cache.get((cy, cx), (0, [np.nan, np.nan]))[1]
            wind[new.index], rh[new.index] = wr[0], wr[1]
    return wind.astype(float).values, rh.astype(float).values


def features(df):
    """Every §10.1 feature except the image outcome, for a whole table of FIRMS rows."""
    df = prepare(df)
    lc = [landcover(a.latitude, a.longitude, a.scan, a.track) for a in df.itertuples()]
    reg, cells = burns(), pd.read_csv(config.CELLS)
    cells = dict(zip(zip(cells.cy, cells.cx), cells.n))
    df['veg'], df['tree'], df['farm'] = zip(*lc) if lc else ([], [], [])
    df['burn'] = [burn(a.latitude, a.longitude, a.t, reg) for a in df.itertuples()]
    df['recur'] = [cells.get((math.floor(a.latitude / config.CELL_DEG), math.floor(a.longitude / config.CELL_DEG)), 0)
                   for a in df.itertuples()]
    df['seen'] = seen(df)
    df['village_km'], df['village_name'] = villages(df)
    df['slope'] = [slope(a.latitude, a.longitude) for a in df.itertuples()]
    df['wind'], df['rh'] = weather(df)
    return df
