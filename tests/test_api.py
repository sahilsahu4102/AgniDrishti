"""The dashboard and camera-node API, run against small CSV files in a temp folder."""
import time

import pytest

# a burn that is valid for the Uttarakhand box in config.BOX
BURN = {'lat': 30.1, 'lon': 78.3, 'r_km': 2.0, 'start': '2026-10-05T05:00:00Z', 'end': '2026-10-05T11:00:00Z', 'note': 'test burn'}


def test_alert_list_has_replay_windows_and_live_alerts(client, alerts):
    body = client.get('/api/alerts').json()
    rows = [dict(zip(body['cols'], r)) for r in body['rows']]
    assert len(rows) == 4
    by_id = {r['id']: r for r in rows}
    assert by_id[alerts['dispatch']['id']]['window'] == 'A'   # before 2026-03-01
    assert by_id[alerts['verify']['id']]['window'] == 'B'
    assert by_id[alerts['live']['id']]['window'] == 'live'
    assert {r['tier'] for r in rows} == {'DISPATCH', 'VERIFY', 'LOG'}


def test_alert_detail_explains_how_p_was_reached(client, alerts):
    d = client.get(f"/api/alerts/{alerts['dispatch']['id']}").json()
    assert [row['text'] for row in d['ledger']] == ['seen 3 times in 12 h', 'high confidence']
    assert d['p_start'] == 0.5 and d['p_sum'] == 0.9
    assert d['thresholds'] == {'verify': 0.35, 'risky': 0.8, 'dispatch': 0.9, 'risky_r': 2}
    assert d['image'] is None and d['sent'] is None
    assert d['map'].startswith('https://maps.google.com/?q=30.10000,78.50000')


@pytest.mark.parametrize('bad', ['not-an-id', '..', '2026-04-12_0645_30.2000_78.6000.xml', "1' OR '1'='1"])
def test_malformed_ids_are_refused_before_any_lookup(client, bad):
    assert client.get(f'/api/alerts/{bad}').status_code == 404
    assert client.get(f'/cap/{bad}.xml').status_code == 404


def test_unknown_but_well_formed_id_is_404(client):
    r = client.get('/api/alerts/2026-01-01_0000_30.0000_78.0000')
    assert r.status_code == 404 and r.json()['detail'] == 'unknown alert id'


def test_burn_register_round_trip(client):
    r = client.post('/api/burns', json=BURN)
    assert r.status_code == 201 and r.json()['id'].startswith('B')
    listed = client.get('/api/burns').json()
    assert len(listed) == 1 and listed[0]['note'] == 'test burn' and listed[0]['r_km'] == 2.0


def test_two_burns_in_the_same_second_get_different_ids(client):
    ids = {client.post('/api/burns', json=BURN).json()['id'] for _ in range(3)}
    assert len(ids) == 3


def test_first_burn_in_a_missing_register_is_not_lost(client, tmp_path):
    """Regression: with no burns.csv, the first row used to be written without a header and read back as one."""
    (tmp_path / 'burns.csv').unlink()
    assert client.post('/api/burns', json=BURN).status_code == 201
    assert len(client.get('/api/burns').json()) == 1


@pytest.mark.parametrize('change', [
    {'end': '2026-10-05T04:00:00Z'},  # ends before it starts
    {'lat': 12.0},                     # outside Uttarakhand's search box
    {'lon': 90.0},
    {'r_km': 0},
    {'r_km': 51},
    {'note': 'x' * 201},
])
def test_invalid_burns_are_rejected_and_nothing_is_written(client, change):
    assert client.post('/api/burns', json={**BURN, **change}).status_code == 422
    assert client.get('/api/burns').json() == []


def test_camera_todo_lists_open_dispatch_and_verify_alerts_only(client, alerts):
    todo = client.get('/todo', params={'node': 'AG-01'}).json()
    ids = {t['id'] for t in todo}
    assert ids == {alerts['dispatch']['id'], alerts['verify']['id'], alerts['live']['id']}  # LOG is never sent to a camera
    assert [t['id'] for t in todo][0] == alerts['live']['id']  # newest first


def test_recorded_smoke_closes_the_alert_and_raises_p(client, alerts, tmp_path):
    vid = alerts['verify']['id']
    assert client.post('/seen', json={'id': vid, 'node': 'AG-01', 'result': 'smoke'}).json() == {'ok': True}
    assert vid not in {t['id'] for t in client.get('/todo', params={'node': 'AG-01'}).json()}
    d = client.get(f'/api/alerts/{vid}').json()
    assert d['image'] == 'smoke' and d['image_p'] == 0.9
    assert (tmp_path / 'outcomes.csv').read_text(encoding='utf-8').count('\n') == 2  # header plus one row


def test_latest_outcome_wins(client, alerts):
    vid = alerts['verify']['id']
    client.post('/seen', json={'id': vid, 'node': 'AG-01', 'result': 'nosmoke'})
    time.sleep(0.01)
    client.post('/seen', json={'id': vid, 'node': 'AG-01', 'result': 'smoke'})
    assert client.get('/api/live').json()['outcomes'][vid]['result'] == 'smoke'


@pytest.mark.parametrize('body', [
    {'id': '2026-01-01_0000_30.0000_78.0000', 'node': 'AG-01', 'result': 'smoke'},  # unknown alert -> 404
])
def test_outcome_for_an_unknown_alert_is_404(client, body):
    assert client.post('/seen', json=body).status_code == 404


def test_outcome_input_is_validated(client, alerts):
    vid = alerts['verify']['id']
    for bad in ({'node': 'AG 01; rm -rf'}, {'node': ''}, {'result': 'fire'}, {'id': 'nope'}):
        assert client.post('/seen', json={'id': vid, 'node': 'AG-01', 'result': 'smoke', **bad}).status_code == 422


def test_cap_file_is_served_and_marks_the_alert_as_sent(client, alerts, tmp_path):
    did = alerts['dispatch']['id']
    assert client.get(f'/cap/{did}.xml').status_code == 404  # nothing sent yet
    (tmp_path / f'cap_{did}.xml').write_text('<alert/>', encoding='utf-8')
    r = client.get(f'/cap/{did}.xml')
    assert r.status_code == 200 and r.headers['content-type'].startswith('application/xml')
    assert did in client.get('/api/live').json()['sent']
    assert client.get(f'/api/alerts/{did}').json()['sent'] is not None


def test_dashboard_page_is_served(client):
    r = client.get('/')
    assert r.status_code == 200 and 'AgniDrishti' in r.text
