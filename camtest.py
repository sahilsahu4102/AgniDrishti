"""Camera false-alarm test (§14): the node's 6-frame rule over every clip in data/clips/manifest.csv.

Frames are taken 2 s apart in clip time and grouped into back-to-back checks of 6. A check is a
confirmation when 4 or more of its frames have a box, which is what node.py posts as 'smoke'.
Inference runs once at a low floor and stores each frame's top confidence, so any threshold can be
scored afterwards without re-running the model.
"""
import csv

import cv2
import pandas as pd
from ultralytics import YOLO

import config as c

# Labelled "before ignition" by HPWREN, but a smoke plume from another fire is plainly visible
# (checked by eye on 5 Oct 2026), so it is not a fair negative. Reported separately, never dropped silently.
VISIBLE_SMOKE = {'negative/hpwren_20201208_FIRE_om-s-mobo-c_pre.mp4'}
THRESHOLDS = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]


def frames(path):
    cap = cv2.VideoCapture(str(path))
    fps, n = cap.get(cv2.CAP_PROP_FPS) or 1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    for k in range(int(n / fps / c.FRAME_GAP_S)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(n - 1, int(k * c.FRAME_GAP_S * fps)))
        ok, f = cap.read()
        if ok:
            yield f


def top_conf(model, frame):
    r = model.predict(frame, imgsz=c.CAMERA_IMGSZ, conf=0.05, iou=c.CAMERA_IOU, verbose=False)[0]
    return float(r.boxes.conf.max()) if len(r.boxes) else 0.0


def score(confs, t, luma=None):
    """(checks judged, confirmations, checks skipped as too dark), mirroring node.check."""
    judged = conf = dark = 0
    for i in range(0, len(confs) - c.FRAMES + 1, c.FRAMES):
        if luma is not None and sorted(luma[i:i + c.FRAMES])[c.FRAMES // 2] < c.DARK_LUMA:
            dark += 1
            continue
        judged += 1
        conf += sum(x >= t for x in confs[i:i + c.FRAMES]) >= c.FRAMES_NEEDED
    return judged, conf, dark


if __name__ == '__main__':
    model = YOLO(c.CAMERA_MODEL)
    cache = c.DATA / 'camtest_frames.csv'  # one row per clip, written as each finishes, so a rerun resumes
    done = {r['file']: r for r in csv.DictReader(open(cache, encoding='utf-8'))} if cache.exists() else {}
    if not cache.exists():
        cache.write_text('kind,file,seconds,confs\n', encoding='utf-8')
    clips = []
    for m in csv.DictReader(open(c.DATA / 'clips' / 'manifest.csv', encoding='utf-8')):
        kind = 'visible smoke' if m['file'] in VISIBLE_SMOKE else m['kind']
        if m['file'] in done:
            confs = [float(v) for v in done[m['file']]['confs'].split()]
        else:
            confs = [top_conf(model, f) for f in frames(c.DATA / 'clips' / m['file'])]
            with open(cache, 'a', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([kind, m['file'], m['seconds'], ' '.join(f'{v:.3f}' for v in confs)])
            print(f"{kind:<13} {m['file'][:58]:<58} {len(confs):>3} frames, top conf {max(confs, default=0):.2f}", flush=True)
        luma = [float(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).mean()) for f in frames(c.DATA / 'clips' / m['file'])]  # cheap, not cached
        clips.append({'kind': kind, 'file': m['file'], 'seconds': float(m['seconds']), 'confs': confs, 'luma': luma})
    rows = []
    for t in THRESHOLDS:
        row = {'conf': t}
        for kind in ('smoke', 'negative', 'visible smoke'):
            g = [x for x in clips if x['kind'] == kind]
            judged, conf, dark = map(sum, zip(*[score(x['confs'], t, x['luma']) for x in g])) if g else (0, 0, 0)
            row[f'{kind} checks'], row[f'{kind} confirmed'], row[f'{kind} too dark'] = judged, conf, dark
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(c.DATA / 'camtest.csv', index=False)
    neg_min = sum(x['seconds'] for x in clips if x['kind'] == 'negative') / 60
    print(f'\nnegatives: {neg_min:.1f} min; CAMERA_CONF {c.CAMERA_CONF}, DARK_LUMA {c.DARK_LUMA}')
    print(df.to_string(index=False))
