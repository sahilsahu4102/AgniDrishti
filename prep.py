import json

import numpy as np
import pandas as pd
import shapely
from shapely.geometry import shape

import config


def state():
    for f in json.load(open(config.STATE, encoding='utf-8'))['features']:
        if f['properties'].get('shapeISO') == config.STATE_ISO:
            poly = shape(f['geometry'])
            shapely.prepare(poly)
            return poly
    raise SystemExit(f'{config.STATE_ISO} not found in {config.STATE}')


def clip(name, poly):
    df = pd.read_csv(config.DATA / f'{name}.csv')
    inside = shapely.contains_xy(poly, df.longitude.values, df.latitude.values)
    df[inside].to_csv(config.DATA / f'{name}_uk.csv', index=False)
    print(f'{name}: {len(df)} rows in the box, {inside.sum()} inside Uttarakhand -> {name}_uk.csv')


def villages():
    els = json.load(open(config.DATA / 'villages.json', encoding='utf-8'))['elements']
    df = pd.DataFrame({'name': [e.get('tags', {}).get('name', 'unnamed') for e in els],
                       'lat': [e['lat'] for e in els], 'lon': [e['lon'] for e in els]})
    df.to_csv(config.VILLAGES, index=False, encoding='utf-8')
    print(f'villages: {len(df)} places ({(df.name == "unnamed").sum()} unnamed) -> {config.VILLAGES.name}')


def cells():
    h = pd.read_csv(config.DATA / 'hist_uk.csv')
    c = pd.DataFrame({'cy': np.floor(h.latitude / config.CELL_DEG).astype(int),
                      'cx': np.floor(h.longitude / config.CELL_DEG).astype(int)})
    c = c.value_counts().rename('n').reset_index()
    c.to_csv(config.CELLS, index=False)
    print(f'cells: {len(c)} cells from {len(h)} history detections, largest n {c.n.max()} -> {config.CELLS.name}')


if __name__ == '__main__':
    poly = state()
    for name in config.WINDOWS:
        clip(name, poly)
    villages()
    cells()
