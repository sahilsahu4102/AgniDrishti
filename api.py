import csv
import re
import time
from datetime import datetime
from typing import Literal

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

import config as c
import score
import store

app = FastAPI(title='AgniDrishti')
app.add_middleware(GZipMiddleware, minimum_size=2000)
ID = re.compile(r'^\d{4}-\d{2}-\d{2}_\d{4}_-?\d{1,3}\.\d{4}_-?\d{1,3}\.\d{4}$')
LIST = ['id', 'latitude', 'longitude', 'tier', 'p', 'r', 'why', 't', 'village_name', 'village_km']
cache = {}


def table(path):
    """A CSV as a DataFrame, re-read only when the file changes on disk."""
    mtime = path.stat().st_mtime if path.exists() else None
    if cache.get(path, (0,))[0] != mtime:
        cache[path] = (mtime, pd.read_csv(path) if mtime else pd.DataFrame())
    return cache[path][1]


def version():
    return {p.name: p.stat().st_mtime for p in (c.SCORED, c.BURNS) if p.exists()}


def rows(df, window):
    if df.empty:
        return []
    d = df[LIST].assign(window=window)
    d = d.round({'latitude': 5, 'longitude': 5, 'p': 2, 'village_km': 2})
    return d.astype(object).where(d.notna(), None).values.tolist()


def latest_outcomes():
    o = table(c.OUTCOMES)
    if o.empty:
        return {}
    o = o.sort_values('ts').drop_duplicates('id', keep='last')
    return {r.id: {'result': r.result, 'src': r.src, 'ts': float(r.ts)} for r in o.itertuples()}


def sent():
    """Alerts whose CAP file exists, i.e. Telegram accepted the message (D4)."""
    return {p.stem[4:]: p.stat().st_mtime for p in c.DATA.glob('cap_*.xml')}


@app.get('/api/alerts')
def alerts():
    replay = table(c.SCORED)
    window = replay.acq_date.lt('2026-03-01').map({True: 'A', False: 'B'}) if not replay.empty else 'A'
    return {'version': version(), 'cols': LIST + ['window'],
            'rows': rows(replay, window) + rows(table(c.LIVE_SCORED), 'live')}


@app.get('/api/live')
def live():
    """Polled every few seconds: live alerts, outcomes, sent markers, and file versions."""
    return {'version': version(), 'cols': LIST + ['window'], 'live': rows(table(c.LIVE_SCORED), 'live'),
            'outcomes': latest_outcomes(), 'sent': sent(), 'now': time.time()}


@app.get('/api/alerts/{aid}')
def alert(aid: str):
    if not ID.match(aid):
        raise HTTPException(404, 'not an alert id')
    for path in (c.LIVE_SCORED, c.SCORED):
        df = table(path)
        hit = df[df.id == aid] if not df.empty else df
        if len(hit):
            a = hit.iloc[0].to_dict()
            break
    else:
        raise HTTPException(404, 'unknown alert id')
    ledger = score.ledger(a)
    p_sum = round(min(1.0, max(0.0, c.P_START + sum(d for _, d in ledger))), 2)
    o = table(c.OUTCOMES)
    history = [] if o.empty else o[o.id == aid].sort_values('ts')[['result', 'src', 'ts']].to_dict('records')
    image = history[-1]['result'] if history else None
    cap = c.DATA / f'cap_{aid}.xml'
    clean = {k: (None if isinstance(v, float) and v != v else v) for k, v in a.items()}
    return {'alert': clean, 'ledger': [{'text': t, 'delta': d} for t, d in ledger], 'p_start': c.P_START, 'p_sum': p_sum,
            'image': image, 'image_p': round(score.image_p(p_sum, image), 2) if image else None,
            'risk': [{'text': t, 'points': n} for t, n in score.risk(a)], 'history': history,
            'thresholds': {'verify': c.VERIFY_P, 'risky': c.DISPATCH_P_RISKY, 'dispatch': c.DISPATCH_P, 'risky_r': c.DISPATCH_R},
            'sent': cap.stat().st_mtime if cap.exists() else None,
            'map': f"https://maps.google.com/?q={a['latitude']:.5f},{a['longitude']:.5f}"}


class Burn(BaseModel):
    lat: float = Field(ge=c.BOX[1], le=c.BOX[3])
    lon: float = Field(ge=c.BOX[0], le=c.BOX[2])
    r_km: float = Field(gt=0, le=50)
    start: datetime  # UTC
    end: datetime
    note: str = Field(default='', max_length=200)

    @model_validator(mode='after')
    def ordered(self):
        if self.end <= self.start:
            raise ValueError('end must be after start')
        return self


@app.get('/api/burns')
def burns():
    b = table(c.BURNS)
    return [] if b.empty else b.astype(object).where(b.notna(), None).to_dict('records')


@app.post('/api/burns', status_code=201)
def add_burn(b: Burn):
    taken = set(table(c.BURNS).get('id', []))
    stamp = int(time.time())
    while f'B{stamp}' in taken:  # two entries in one second
        stamp += 1
    row = {'id': f'B{stamp}', 'lat': round(b.lat, 5), 'lon': round(b.lon, 5), 'r_km': b.r_km,
           'start': b.start.strftime('%Y-%m-%d %H:%M'), 'end': b.end.strftime('%Y-%m-%d %H:%M'),
           'note': b.note.replace('\n', ' ').strip()}
    with open(c.BURNS, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(row.values())
    return row


def known(aid):
    return any(not t.empty and (t.id == aid).any() for t in (table(c.LIVE_SCORED), table(c.SCORED)))


@app.get('/todo')
def todo(node: str):
    """Camera node work list (§12.1): up to 10 DISPATCH or VERIFY alerts with no outcome yet, newest first (D3)."""
    df = pd.concat([t for t in (table(c.SCORED), table(c.LIVE_SCORED)) if not t.empty] or [pd.DataFrame(columns=LIST)])
    open_ = df[df.tier.isin(['DISPATCH', 'VERIFY']) & ~df.id.isin(latest_outcomes().keys())]
    return [{'id': r.id, 'lat': r.latitude, 'lon': r.longitude} for r in open_.sort_values('t', ascending=False).head(10).itertuples()]


class Seen(BaseModel):
    id: str = Field(pattern=ID.pattern)
    node: str = Field(min_length=1, max_length=40, pattern=r'^[\w-]+$')
    result: Literal['smoke', 'nosmoke']


@app.post('/seen')
def seen(s: Seen):
    if not known(s.id):
        raise HTTPException(404, 'unknown alert id')
    store.record(s.id, s.node, s.result)
    return {'ok': True}


@app.get('/cap/{aid}.xml')
def cap(aid: str):
    path = c.DATA / f'cap_{aid}.xml'
    if not ID.match(aid) or not path.exists():
        raise HTTPException(404, 'no CAP file for this alert')
    return FileResponse(path, media_type='application/xml')


app.mount('/', StaticFiles(directory=c.ROOT / 'web', html=True), name='web')
