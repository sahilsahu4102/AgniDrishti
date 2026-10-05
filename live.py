import sys
import time
from datetime import datetime, timezone

import pandas as pd
import shapely

import check
import config as c
import geo
import prep
import pull
import score
import send


def read_live():
    return pd.read_csv(c.LIVE) if c.LIVE.exists() and c.LIVE.stat().st_size else pd.DataFrame()


def tick(last):
    """Rescore live.csv and push each new DISPATCH exactly once."""
    df = score.score_csv([c.LIVE], c.LIVE_SCORED, log=False) if c.LIVE.exists() else pd.DataFrame()
    counts = df.tier.value_counts().to_dict() if len(df) else {}
    if counts != last:
        print(f'live: {len(df)} alerts {counts}')
    for a in df[df.tier == 'DISPATCH'].to_dict('records') if len(df) else []:
        if send.push(a):
            print(f"dispatched {a['id']}")
    return counts


def poll_firms(poly):
    """Live mode (§3.1): the latest NOAA-20 and NOAA-21 detections inside Uttarakhand, appended to live.csv."""
    new = pd.concat([pull.chunk(s, 1) for s in c.LIVE_SOURCES], ignore_index=True)
    new = new[shapely.contains_xy(poly, new.longitude.values, new.latitude.values)]
    both = pd.concat([read_live(), new], ignore_index=True).drop_duplicates(['latitude', 'longitude', 'acq_date', 'acq_time'])
    both.to_csv(c.LIVE, index=False)
    print(f'firms: {len(new)} detections in Uttarakhand now; live.csv holds {len(both)}')


def inject(dist_km=5.0):
    """Demo alert (§13): a Window B row moved onto the camera's line of sight, stamped with the current time."""
    lat, lon = geo.offset(c.NODE_LAT, c.NODE_LON, c.NODE_HEADING, dist_km)
    b = pd.read_csv(c.DATA / 'win_b_uk.csv')
    row = b[~b.confidence.astype(str).str.startswith('h') & (b.frp < c.FRP_MIN)].iloc[[0]].copy()  # p stays 0.5
    now = datetime.now(timezone.utc)
    row[['latitude', 'longitude', 'acq_date', 'acq_time']] = [round(lat, 5), round(lon, 5), now.strftime('%Y-%m-%d'), int(now.strftime('%H%M'))]
    f = check.features(row.copy()).iloc[0].to_dict()
    p, r, tier, _ = score.score_one(f)
    pd.concat([read_live(), row], ignore_index=True).to_csv(c.LIVE, index=False)
    print(f"injected {f['id']} at {lat:.5f},{lon:.5f}, {dist_km} km from {c.NODE_ID}: first pass p {p}, risk {r}, {tier}")
    if tier != 'VERIFY':
        print('WARNING: not VERIFY, so the camera step would be skipped. Move the node or change the distance.')


if __name__ == '__main__':
    if '--inject' in sys.argv:
        inject(*[float(x) for x in sys.argv[sys.argv.index('--inject') + 1:][:1]])
        sys.exit()
    firms = '--firms' in sys.argv  # off by default, so a real alert can't fire into the group mid-demo
    poly, last, next_firms = prep.state() if firms else None, None, 0
    print(f"live loop: rescoring {c.LIVE.name} every 10 s{' and polling FIRMS every 10 min' if firms else ''}")
    while True:
        try:
            if firms and time.time() >= next_firms:
                poll_firms(poly)
                next_firms = time.time() + 600
            last = tick(last)
        except Exception as e:  # keep running through network blips and half-written files
            print(f'live pass failed: {e}')
        time.sleep(10)
