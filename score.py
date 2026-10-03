import math
import sys

import pandas as pd

import check
import config as c


def outcomes():
    """Latest image or field outcome per alert id (§8: append-only, latest row wins)."""
    if not c.OUTCOMES.exists():
        return {}
    o = pd.read_csv(c.OUTCOMES).sort_values('ts')
    return dict(zip(o.id, o.result))


def tier(p, r):
    if p >= c.DISPATCH_P or (p >= c.DISPATCH_P_RISKY and r >= c.DISPATCH_R):
        return 'DISPATCH'
    return 'VERIFY' if p >= c.VERIFY_P else 'LOG'


def score_one(a, image=None):
    """p (0-1), r (0-7), tier and reasons for one alert's features (§10.2-10.4)."""
    p, why = c.P_START, []
    if a['veg'] < c.VEG_MIN:
        p -= c.VEG_PENALTY
        why.append(f"pixel only {a['veg']:.0%} vegetation")
    if a['farm'] > c.FARM_MAX:
        p -= c.FARM_PENALTY
        why.append(f"pixel {a['farm']:.0%} farmland or built-up")
    if a['burn']:
        p -= c.BURN_PENALTY
        why.append(f"inside planned burn {a['burn']}")
    if a['recur'] >= c.RECUR_MIN:
        p -= c.RECUR_PENALTY
        why.append(f"same cell fired {a['recur']} times since 2023")
    if a['seen'] > 0:
        p += min(c.SEEN_STEP * a['seen'], c.SEEN_CAP)
        why.append(f"seen {a['seen'] + 1} times in 12 h")
    if str(a['confidence']).lower().startswith('h'):
        p += c.CONF_BONUS
        why.append('high confidence')
    if a['frp'] >= c.FRP_MIN:
        p += c.FRP_BONUS
        why.append(f"FRP {a['frp']:.0f} MW")
    p = min(1.0, max(0.0, p))
    if image:  # image outcomes override the sum (§10.2)
        p = {'smoke': max(p, c.SMOKE_P), 'nosmoke': max(0.0, p - c.NOSMOKE_DROP), 'fire': c.FIRE_P}.get(image, c.NOFIRE_P)
        why.insert(0, f'image check: {image}')
    p = round(p, 2)  # 0.5 + 0.1 + 0.3 is 0.8999999999999999 in floating point

    r = 2 if a['village_km'] < c.VILLAGE_NEAR_KM else 1 if a['village_km'] < c.VILLAGE_KM else 0
    r += (a['slope'] > c.SLOPE_STEEP) + (a['tree'] > c.TREE_DENSE) + (a['wind'] > c.WIND_STRONG)
    r += (a['rh'] < c.RH_DRY) + (a['seen'] >= c.SEEN_EVENT)
    weather = 'weather unavailable' if math.isnan(a['wind']) else f"wind {a['wind']:.0f} km/h, RH {a['rh']:.0f}%"
    why.append(f"{a['village_km']:.1f} km from {a['village_name']}, slope {a['slope']:.0f}°, {weather}")
    return p, int(r), tier(p, r), '; '.join(why)


def score_csv(paths, out):
    df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    if df.empty:
        df.to_csv(out, index=False)
        print(f'{out.name}: no alerts')
        return df
    df = check.features(df)
    img = outcomes()
    df['p'], df['r'], df['tier'], df['why'] = zip(*[score_one(a, img.get(a['id'])) for a in df.to_dict('records')])
    df.to_csv(out, index=False)
    counts = df.tier.value_counts()
    print(f"{out.name}: {len(df)} alerts | DISPATCH {counts.get('DISPATCH', 0)} | VERIFY {counts.get('VERIFY', 0)} | LOG {counts.get('LOG', 0)}")
    return df


def selftest():
    base = dict(veg=0.8, tree=0.5, farm=0.1, burn='', recur=0, seen=0, confidence='n', frp=5.0,
                village_km=10.0, village_name='X', slope=10.0, wind=5.0, rh=50.0)
    s = lambda image=None, **kw: score_one({**base, **kw}, image)
    assert s()[:3] == (0.5, 0, 'VERIFY') and s()[3] == '10.0 km from X, slope 10°, wind 5 km/h, RH 50%'
    assert s(veg=0.09)[0] == 0.2 and s(veg=0.09)[3].startswith('pixel only 9% vegetation')
    assert s(farm=0.62)[0] == 0.2 and 'pixel 62% farmland or built-up' in s(farm=0.62)[3]
    assert s(burn='B-12')[:3] == (0.1, 0, 'LOG') and 'inside planned burn B-12' in s(burn='B-12')[3]
    assert s(recur=14)[0] == 0.25 and 'same cell fired 14 times since 2023' in s(recur=14)[3]
    assert s(seen=1)[0] == 0.65 and s(seen=3)[0] == 0.8  # +0.15 each, capped at +0.30
    assert s(confidence='high')[0] == 0.6 and s(frp=18)[0] == 0.6 and 'FRP 18 MW' in s(frp=18)[3]
    assert s(confidence='h', seen=2)[:3] == (0.9, 1, 'DISPATCH')  # float sum must still reach 0.9
    assert s(veg=0.1, farm=0.9, burn='B', recur=9)[0] == 0.0  # clipped at 0
    assert (tier(0.9, 0), tier(0.6, 2), tier(0.6, 1), tier(0.35, 0), tier(0.34, 7)) == ('DISPATCH', 'DISPATCH', 'VERIFY', 'VERIFY', 'LOG')
    assert s('smoke')[:3] == (0.9, 0, 'DISPATCH') and s('smoke')[3].startswith('image check: smoke')
    assert s('nosmoke')[0] == 0.4 and s('fire')[0] == 1.0 and s('farm')[:3] == (0.05, 0, 'LOG') and s('none')[0] == 0.05
    assert s(village_km=1.4)[1] == 2 and s(village_km=4.0)[1] == 1 and s(village_km=6.0)[1] == 0
    assert s(village_km=1, slope=27, tree=0.7, wind=18, rh=22, seen=2)[1] == 7
    assert 'weather unavailable' in s(wind=float('nan'), rh=float('nan'))[3]
    a = pd.DataFrame({'acq_date': ['2026-04-10'] * 3, 'acq_time': [754, 854, 2154],
                      'latitude': [30.12341, 30.1270, 30.12341], 'longitude': [78.56781, 78.5678, 78.56781]})
    a = check.prepare(a)
    assert a.id[0] == '2026-04-10_0754_30.1234_78.5678' and str(a.t[0]) == '2026-04-10 07:54:00+00:00'
    assert list(check.seen(a)) == [0, 1, 0]  # past-only: the later 0.4 km pass counts the earlier one; 14 h later counts none
    print('score self-test ok')


if __name__ == '__main__':
    if sys.argv[1:] == ['--selftest']:
        selftest()
    elif len(sys.argv) == 3:  # e.g. python score.py data/live.csv data/live_scored.csv
        from pathlib import Path
        score_csv([sys.argv[1]], Path(sys.argv[2]))
    else:
        score_csv([c.DATA / 'win_a_uk.csv', c.DATA / 'win_b_uk.csv'], c.SCORED)
