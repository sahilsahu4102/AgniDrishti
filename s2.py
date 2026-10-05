import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from html import escape

import cv2
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

import config as c

STAC = 'https://earth-search.aws.element84.com/v1'
OUT = c.DATA / 'labelling'
DNBR_BOX, CHIP_BOX, DAYS, CLOUD = 0.002, 0.01, 20, 20  # §11.4: ±0.002° (~400 m) for dNBR; chips show ~2 km of context


def scenes(cat, lat, lon, start, end):
    """Least-cloudy first, cloud under 20% (§11.4)."""
    items = cat.search(collections=['sentinel-2-c1-l2a'], intersects={'type': 'Point', 'coordinates': [lon, lat]},
                       datetime=f'{start:%Y-%m-%d}/{end:%Y-%m-%d}', query={'eo:cloud_cover': {'lt': CLOUD}}).item_collection()
    return sorted(items, key=lambda i: i.properties['eo:cloud_cover'])


def read(item, key, lat, lon, half, shape=None):
    """Reflectance in a lat/lon box: scale and offset from raster:bands (C1 offset is -0.1), 0 is nodata."""
    asset = item.assets[key]
    band = (asset.extra_fields.get('raster:bands') or [{}])[0]
    with rasterio.open(asset.href) as src:
        xs, ys = Transformer.from_crs('EPSG:4326', src.crs, always_xy=True).transform([lon - half, lon + half], [lat - half, lat + half])
        window = from_bounds(min(xs), min(ys), max(xs), max(ys), src.transform)
        a = src.read(1, window=window, out_shape=shape, resampling=Resampling.bilinear, boundless=True, fill_value=0).astype('float32')
    a = np.where(a == 0, np.nan, a * band.get('scale', 0.0001) + band.get('offset', 0))
    return a


def nbr(item, lat, lon):
    nir = read(item, 'nir', lat, lon, DNBR_BOX)
    swir = read(item, 'swir22', lat, lon, DNBR_BOX, shape=nir.shape)  # 20 m SWIR resampled to the 10 m NIR grid
    v = (nir - swir) / (nir + swir)
    return float(np.nanmean(v)) if np.isfinite(v).any() else None


def chip(item, lat, lon, keys, path, top):
    """An 8-bit composite (reflectance 0..top stretched) with the dNBR box drawn on it."""
    first = read(item, keys[0], lat, lon, CHIP_BOX)
    bands = [first] + [read(item, k, lat, lon, CHIP_BOX, shape=first.shape) for k in keys[1:]]
    img = np.dstack([np.nan_to_num(np.clip(b / top, 0, 1)) for b in bands[::-1]])  # BGR for OpenCV
    img = cv2.resize((img * 255).astype('uint8'), (300, 300), interpolation=cv2.INTER_NEAREST)
    k = 150 * DNBR_BOX / CHIP_BOX
    cv2.rectangle(img, (int(150 - k), int(150 - k)), (int(150 + k), int(150 + k)), (255, 255, 255), 1)
    cv2.imwrite(str(path), img)


def label_one(cat, aid, lat, lon, t):
    """Before/after scenes, dNBR, and four chips for one alert. Returns a dict for the gallery."""
    row = {'id': aid, 'lat': lat, 'lon': lon, 't': t, 'dnbr': None, 'before': None, 'after': None}
    pairs = {}
    for side, start, end in [('before', t - timedelta(days=DAYS), t - timedelta(days=1)), ('after', t + timedelta(days=1), t + timedelta(days=DAYS))]:
        for item in scenes(cat, lat, lon, start, end):
            v = nbr(item, lat, lon)
            if v is not None:
                pairs[side] = (item, v)
                row[side] = f"{item.datetime:%d %b %Y}, cloud {item.properties['eo:cloud_cover']:.0f}%"
                for keys, kind, top in ((['red', 'green', 'blue'], 'tc', 0.2), (['swir22', 'nir', 'red'], 'swir', 0.35)):
                    if not (OUT / f'{aid}_{side}_{kind}.jpg').exists():  # resumable: chips from an interrupted run stay
                        chip(item, lat, lon, keys, OUT / f'{aid}_{side}_{kind}.jpg', top)
                break
    if len(pairs) == 2:
        row['dnbr'] = round(pairs['before'][1] - pairs['after'][1], 3)
    return row


def gallery(rows):
    """A blind labelling page: chips, dNBR hint, links. No tier, p or reasons."""
    cards = []
    for r in rows:
        hint = 'no scenes on both sides' if r['dnbr'] is None else \
            f"dNBR {r['dnbr']:+.3f}: {'likely burned' if r['dnbr'] >= 0.10 else 'no visible scar (unclear, not false)'}"
        imgs = ''.join(f'<figure><img src="{escape(r["id"])}_{s}_{k}.jpg" alt="{s} {k}" loading="lazy" onerror="this.replaceWith(\'no scene\')">'
                       f'<figcaption>{s} · {"true colour" if k == "tc" else "SWIR"}<br>{escape(str(r[s] or "none"))}</figcaption></figure>'
                       for s in ('before', 'after') for k in ('tc', 'swir'))
        cards.append(f'<section><h2>{escape(r["id"])}</h2><p>{r["t"]:%d %b %Y %H:%M} UTC · {r["lat"]:.4f}, {r["lon"]:.4f} · '
                     f'<a href="https://maps.google.com/?q={r["lat"]:.5f},{r["lon"]:.5f}&t=k" target="_blank">satellite map</a> · <b>{hint}</b></p>'
                     f'<div class="row">{imgs}</div></section>')
    (OUT / 'index.html').write_text(
        '<!doctype html><meta charset="utf-8"><title>AgniDrishti labelling sheet</title><style>'
        'body{font:14px/1.4 system-ui;margin:24px;background:#f6f8f3;color:#221c15}section{border-top:1px solid #c2cab4;padding:12px 0}'
        'h2{font:600 14px ui-monospace,Consolas,monospace;margin:0 0 4px}.row{display:flex;gap:10px;flex-wrap:wrap}'
        'figure{margin:0}img{width:220px;height:220px;display:block;background:#dfe6d3}figcaption{font-size:12px;color:#5a4a3a}</style>'
        '<h1>Labelling sheet: Sentinel-2 before and after</h1><p>The white square is the dNBR box (about 400 m). Label from what you see, '
        'following docs/labelling-guide.md. dNBR is a hint only. Shuffled order; tiers are hidden on purpose.</p>' + ''.join(cards),
        encoding='utf-8')


if __name__ == '__main__':
    # python s2.py            -> every alert in data/labels_template.csv
    # python s2.py <alert id> -> one alert
    OUT.mkdir(parents=True, exist_ok=True)
    ids = sys.argv[1:] or pd.read_csv(c.DATA / 'labels_template.csv').id.tolist()

    def work(aid):  # each thread gets its own GDAL environment and STAC client
        date, hhmm, lat, lon = aid.split('_')
        t = datetime.strptime(date + hhmm, '%Y-%m-%d%H%M')
        saved = OUT / f'{aid}.json'
        if saved.exists():  # resumable: finished alerts are skipped
            return {**json.loads(saved.read_text()), 't': t}
        try:
            with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif', AWS_NO_SIGN_REQUEST='YES'):
                r = label_one(Client.open(STAC), aid, float(lat), float(lon), t)
        except Exception as e:  # one bad scene must not stop the batch
            r = {'id': aid, 'lat': float(lat), 'lon': float(lon), 't': t, 'dnbr': None, 'before': None, 'after': f'error: {e}'}
            print(f"{aid}: dNBR None ({e})", flush=True)
            return r  # errors are retried on the next run
        saved.write_text(json.dumps({k: v for k, v in r.items() if k != 't'}))
        print(f"{aid}: dNBR {r['dnbr']}", flush=True)
        return r

    with ThreadPoolExecutor(8) as pool:  # the time is network reads, so threads help
        rows = list(pool.map(work, ids))
    gallery(rows)
    if not sys.argv[1:]:
        tpl = pd.read_csv(c.DATA / 'labels_template.csv')
        tpl['dnbr'] = tpl.id.map({r['id']: r['dnbr'] for r in rows})
        tpl.to_csv(c.DATA / 'labels_template.csv', index=False)
    done = [r for r in rows if r['dnbr'] is not None]
    print(f"dNBR for {len(done)} of {len(rows)} alerts; {sum(r['dnbr'] >= 0.10 for r in done)} at or above 0.10; sheet: {OUT / 'index.html'}")
