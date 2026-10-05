import time

import cv2
import requests
from ultralytics import YOLO

import config as c
import geo

API = f'http://{c.LAPTOP_IP}:{c.API_PORT}'
SNAPS = c.DATA / 'snaps'


def in_view(a):
    """Within range and inside the phone's field of view: there is no servo to pan (§11.2 option C)."""
    if geo.km(c.NODE_LAT, c.NODE_LON, a['lat'], a['lon']) > c.NODE_RANGE_KM:
        return False
    rel = (geo.bearing(c.NODE_LAT, c.NODE_LON, a['lat'], a['lon']) - c.NODE_HEADING + 540) % 360 - 180
    return abs(rel) <= c.NODE_FOV_DEG / 2


def grab(cap):
    """A fresh frame: OpenCV buffers frames, so drop the stale ones first (§19)."""
    for _ in range(4):
        cap.grab()
    ok, frame = cap.read()
    return frame if ok else None


def check(cap, model, aid):
    """'smoke', 'nosmoke', or None when the scene is too dark to judge (night: no verdict either way)."""
    hits, luma = 0, []
    for i in range(c.FRAMES):
        frame = grab(cap)
        if frame is not None:
            luma.append(float(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).mean()))
            r = model.predict(frame, imgsz=c.CAMERA_IMGSZ, conf=c.CAMERA_CONF, iou=c.CAMERA_IOU, verbose=False)[0]
            if len(r.boxes):  # the model's only class is 'item': count boxes, never filter on a name
                hits += 1
                cv2.imwrite(str(SNAPS / f'{aid}_{i}.jpg'), r.plot())
        if i < c.FRAMES - 1:
            time.sleep(c.FRAME_GAP_S)
    if not luma or sorted(luma)[len(luma) // 2] < c.DARK_LUMA:
        return None, hits
    return ('smoke' if hits >= c.FRAMES_NEEDED else 'nosmoke'), hits


def main():
    SNAPS.mkdir(parents=True, exist_ok=True)
    model = YOLO(c.CAMERA_MODEL)
    cap = cv2.VideoCapture(c.CAMERA_SOURCE)
    print(f'{c.NODE_ID} at {c.NODE_LAT},{c.NODE_LON} facing {c.NODE_HEADING}°, camera {c.CAMERA_SOURCE}, API {API}')
    dark_until = {}  # alert id -> time to look again after a too-dark check
    while True:
        try:
            for a in filter(in_view, requests.get(f'{API}/todo', params={'node': c.NODE_ID}, timeout=10).json()):
                if dark_until.get(a['id'], 0) > time.time():
                    continue
                if not cap.isOpened() or grab(cap) is None:  # stream dropped or clip ended: reopen
                    cap.release()
                    cap = cv2.VideoCapture(c.CAMERA_SOURCE)
                result, hits = check(cap, model, a['id'])
                if result is None:
                    dark_until[a['id']] = time.time() + 600
                    print(f"{a['id']}: too dark to judge; trying again in 10 min")
                    continue
                requests.post(f'{API}/seen', json={'id': a['id'], 'node': c.NODE_ID, 'result': result}, timeout=10).raise_for_status()
                print(f"{a['id']}: {result} ({hits} of {c.FRAMES} frames)")
        except requests.RequestException as e:
            print(f'API unreachable, retrying: {e}')
        time.sleep(5)


if __name__ == '__main__':
    main()
