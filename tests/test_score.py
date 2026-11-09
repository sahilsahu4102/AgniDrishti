from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import check
import config as c
import score
from conftest import FEATURES, make_alert

ROOT = Path(__file__).parent.parent


def test_inline_selftest_still_passes():
    """score.py carries its own asserts for every rule; keep them in the suite."""
    score.selftest()


@pytest.mark.parametrize('p, r, expected', [
    (0.90, 0, 'DISPATCH'),  # sure enough on its own
    (0.80, 2, 'DISPATCH'),  # a lower bar once the risk is high
    (0.80, 1, 'VERIFY'),
    (0.65, 7, 'VERIFY'),    # one repeat detection no longer dispatches, whatever the risk
    (0.35, 0, 'VERIFY'),
    (0.34, 7, 'LOG'),
])
def test_tier_thresholds(p, r, expected):
    assert score.tier(p, r) == expected


def test_threshold_settings_are_ordered():
    assert 0 < c.VERIFY_P < c.DISPATCH_P_RISKY < c.DISPATCH_P <= 1


def random_alerts(n=500):
    rng = np.random.default_rng(0)
    for _ in range(n):
        weather = rng.random() > 0.1  # some alerts have no weather
        yield dict(veg=rng.random(), tree=rng.random(), farm=rng.random(), burn='B1' if rng.random() < 0.2 else '',
                   recur=int(rng.integers(0, 20)), seen=int(rng.integers(0, 6)),
                   confidence=rng.choice(['n', 'l', 'nominal', 'high', 'h']), frp=rng.random() * 40,
                   village_km=rng.random() * 15, village_name='V', slope=rng.random() * 40,
                   wind=rng.random() * 30 if weather else float('nan'), rh=rng.random() * 90 + 5 if weather else float('nan'))


def test_every_alert_gets_a_valid_score_and_a_consistent_tier():
    for a in random_alerts():
        p, r, tier, why = score.score_one(a)
        assert 0.0 <= p <= 1.0 and 0 <= r <= 7
        assert tier == score.tier(p, r)
        assert why  # every alert carries its reasons
        if tier == 'DISPATCH':
            assert p >= c.DISPATCH_P_RISKY
        if tier == 'LOG':
            assert p < c.VERIFY_P


def test_every_reason_that_moves_p_is_shown_to_the_officer():
    for a in random_alerts():
        why = score.score_one(a)[3]
        for text, _ in score.ledger(a):
            assert text in why


@pytest.mark.parametrize('p', [0.0, 0.2, 0.5, 0.85, 1.0])
def test_image_outcomes_override_the_summed_p(p):
    assert score.image_p(p, 'smoke') >= p and score.image_p(p, 'smoke') >= c.SMOKE_P
    assert score.image_p(p, 'nosmoke') <= p
    assert score.image_p(p, 'fire') == 1.0
    assert all(score.image_p(p, o) == c.NOFIRE_P for o in ['none', 'farm', 'burn'])


def test_camera_smoke_turns_a_verify_alert_into_dispatch():
    a = {**FEATURES}
    assert score.score_one(a)[2] == 'VERIFY'
    assert score.score_one(a, 'smoke')[2] == 'DISPATCH'
    assert score.score_one(a, 'smoke')[3].startswith('image check: smoke')


def test_latest_outcome_per_alert_wins(tmp_path, monkeypatch):
    path = tmp_path / 'outcomes.csv'
    path.write_text('id,src,result,ts\nx,node,smoke,1.0\nx,bot,none,2.0\ny,node,smoke,1.5\n', encoding='utf-8')
    monkeypatch.setattr(c, 'OUTCOMES', path)
    assert score.outcomes() == {'x': 'none', 'y': 'smoke'}


def test_alert_ids_match_what_the_api_accepts():
    """check.prepare builds the id; api.ID decides which ids the API will look up. They must agree."""
    from api import ID
    df = check.prepare(pd.DataFrame({'acq_date': ['2026-04-10'], 'acq_time': [754], 'latitude': [30.12341], 'longitude': [78.56781]}))
    assert df.id[0] == '2026-04-10_0754_30.1234_78.5678'
    assert ID.match(df.id[0])
    assert make_alert('2026-04-10', '0754', 30.12341, 78.56781)['id'] == df.id[0]


@pytest.mark.skipif(not (ROOT / 'data' / 'scored.csv').exists(), reason='data/scored.csv is not in git; run `python score.py` to create it')
def test_readme_replay_numbers_reproduce_from_the_data():
    """The README's headline results, recomputed from the scored replay and the committed hand labels."""
    scored = pd.read_csv(ROOT / 'data' / 'scored.csv')
    assert len(scored) == 10314
    assert (scored.tier == 'DISPATCH').sum() == 3751  # 64% fewer than dispatching every alert

    labels = pd.read_csv(ROOT / 'data' / 'labels.csv')
    labels = labels[labels.labeller == 'final']  # metrics use final labels only
    sample = pd.read_csv(ROOT / 'data' / 'sample.csv')[['id', 'half']]
    test = labels.merge(sample, on='id').merge(scored[['id', 'tier']], on='id')
    test = test[test.half == 'test']
    fires = test[test.label == 'forest_fire']
    assert len(fires) == 19 and fires.tier.isin(['DISPATCH', 'VERIFY']).all()  # no real forest fire sent to LOG
    sent = test[test.tier == 'DISPATCH']
    assert (sent.label == 'forest_fire').sum() == 9 and (sent.label == 'unclear').sum() == 2 and len(sent) == 11
