"""Shared fixtures. The API tests run against small CSV files in a temp folder, never the real data/ or burns.csv."""
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import config
import score

# A quiet, ordinary alert: p 0.5, VERIFY. Tests change one feature at a time.
FEATURES = dict(veg=0.8, tree=0.5, farm=0.1, burn='', recur=0, seen=0, confidence='n', frp=5.0,
                village_km=10.0, village_name='Sitarganj', slope=10.0, wind=5.0, rh=50.0)


def make_alert(date, hhmm, lat, lon, **features):
    """One scored alert row, with p, r, tier and why computed by the real scoring code."""
    a = {**FEATURES, **features, 'acq_date': date, 'latitude': lat, 'longitude': lon}
    a['id'] = f'{date}_{hhmm}_{lat:.4f}_{lon:.4f}'
    a['t'] = f'{date} {hhmm[:2]}:{hhmm[2:]}:00+00:00'
    a['p'], a['r'], a['tier'], a['why'] = score.score_one(a)
    return a


@pytest.fixture
def alerts():
    return {
        'dispatch': make_alert('2025-12-10', '0830', 30.1, 78.5, confidence='high', seen=2),  # 0.5 + 0.30 + 0.10 = 0.9
        'verify': make_alert('2026-04-12', '0645', 30.2, 78.6),
        'log': make_alert('2026-04-13', '1210', 30.3, 78.7, veg=0.05, farm=0.9),
        'live': make_alert('2026-10-09', '1955', 30.095, 78.2),
    }


@pytest.fixture
def client(tmp_path, monkeypatch, alerts):
    pd.DataFrame([alerts['dispatch'], alerts['verify'], alerts['log']]).to_csv(tmp_path / 'scored.csv', index=False)
    pd.DataFrame([alerts['live']]).to_csv(tmp_path / 'live_scored.csv', index=False)
    (tmp_path / 'burns.csv').write_text('id,lat,lon,r_km,start,end,note\n', encoding='utf-8')
    for name, file in {'SCORED': 'scored.csv', 'LIVE_SCORED': 'live_scored.csv', 'OUTCOMES': 'outcomes.csv', 'BURNS': 'burns.csv'}.items():
        monkeypatch.setattr(config, name, tmp_path / file)
    monkeypatch.setattr(config, 'DATA', tmp_path)
    import api
    api.cache.clear()
    return TestClient(api.app)
