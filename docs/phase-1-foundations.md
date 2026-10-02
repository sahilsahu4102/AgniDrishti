# Phase 1: Foundations (hours 0–8)

**Goal:** one alert scored end to end, then all of Window A. The camera, servo, smoke model and dashboard each work on their own.
**Spec:** §5.1, §6, §8–§10, §11.1–§11.2, §12.4, §19.
**Exit:** pass Gate 1, then push the completion report with tag `phase-1`.

## Plan

### Hour 0 (everyone, 45 minutes)

1. Settle decisions D1–D5 and the hour-0 contracts in [implementation-plan.md](implementation-plan.md#open-decisions), and write the answers into this report.
2. Scoring writes `config` and `geo` (30 minutes at most) and pushes; everyone else pulls.
   - `config` holds:
     - the box, windows and history range;
     - the sources: S-NPP for replay, NOAA-20 and NOAA-21 for live;
     - paths, and every §10 threshold and weight;
     - the camera model path and settings (imgsz 1024, conf 0.2, iou 0.01; see the Phase 0 report);
     - the replay dispatch limit of 3, and port 8000;
     - the node settings: id, lat, lon, heading at servo centre, range of 10 km, servo sign and servo pulse widths.

     Secrets come from `.env`.
   - `geo` holds haversine distance in km (R = 6371) and initial bearing. Self-check: 1° of latitude ≈ 111.19 km, due north is 0°, and due east on the equator is 90°.
3. `requirements.txt` lists the §20 libraries, unpinned until Gate 3.
4. `burns.csv` starts with only its header: `id,lat,lon,r_km,start,end,note`.

### Tasks by role

**Geo data**

| Task | Output | Done when |
| --- | --- | --- |
| `pull` (re-run at the event if the rules require it) | `data/win_a.csv`, `data/hist.csv` | It prints the row count. |
| `prep`: clip each CSV to the state polygon | `data/win_a_uk.csv`, `data/hist_uk.csv` | It prints rows before and after. On a map, no points fall in Nepal, Himachal, UP or Tibet. |
| `prep`: villages table | `data/villages.csv` with `name, lat, lon`; a missing name becomes "unnamed" | It prints the count. |
| `prep`: history cells from `hist_uk.csv` | `data/cells.csv` with `cy, cx, n` | It prints the cell count and the largest `n`. |
| Raster reads for `check`: the WorldCover footprint window and the DEM 3×3 window | functions in `check` | For one alert, `veg`/`tree`/`farm` match the WorldCover viewer and the slope matches the terrain. |

**Scoring**

| Task | Output | Done when |
| --- | --- | --- |
| `check`: every §10.1 feature | functions | One alert prints all of them. |
| Weather with a cache (§10.1, §19) | cache under `data/` | A second run makes no HTTP calls. |
| `score` v1: p, r, tier and reasons (§10.2–§10.4, R1) | `score` | The self-check below passes. |
| Score Window A | `data/scored.csv` | It prints tier counts, and ids are unique. |
| `store` | `store` | It returns `scored.csv`, plus `live_scored.csv` when present. |

The `score` self-check is one small `__main__` block of asserts, with no test framework. It covers:

- `acq_time` 754 becomes `0754`, and the id matches §9.
- Each p rule fires on its own with the §10.2 reason text. `seen` = 3 adds +0.30, the cap.
- Tier edges:
  - p 0.9 → DISPATCH
  - p 0.6 with r 2 → DISPATCH
  - p 0.6 with r 1 → VERIFY
  - p 0.35 → VERIFY
  - p 0.34 → LOG
- `0.5 + 0.1 + 0.3` must reach DISPATCH. In floating point it evaluates to `0.8999999999999999`, so round p to 2 dp before comparing it to a threshold.
- Risk: a village at 1.4 km adds +2, at 4 km +1, and at 6 km 0. r never goes above 7.

**Vision**

| Task | Done when |
| --- | --- |
| Run the pinned Pyronear model (`data/models/pyronear/yolo11s_rapid-raccoon_v8.1.0/best.pt`) on a smoke test clip at imgsz 1024, conf 0.2, iou 0.01, the settings on its model card. Phase 0 found that the spec's model is no longer published. | Smoke frames get boxes; an annotated frame is saved as `docs/img/phase-1-smoke.png`. |
| Time one inference on the laptop, and on the Pi if NCNN is planned. | ms per frame recorded. This decides where inference runs. |
| D-Fire training | Running, or finished with the weights saved. |

**Hardware + bot**

| Task | Done when |
| --- | --- |
| Stream the camera to the laptop: a USB webcam through OpenCV, or an ESP32 at `http://<ip>:81/stream`. The Pi Camera Module needs Picamera2. | Frames show in a window. |
| Flush buffered frames before every read (§19). | Cover the lens, uncover it, grab a frame: it shows the uncovered view. |
| Sweep the servo on command. | −90°, 0° and +90° look right by eye; calibration recorded below. |

Keep the servo calibration knobs in `config`:

- **Pulse widths:** gpiozero's default 1–2 ms pulses move an SG90 through only part of its range. Widen them to about 0.5–2.5 ms and adjust until −90/0/+90 look right.
- **Sign:** set it to ±1 so that a positive angle turns clockwise.
- **Heading:** measure the compass heading at 0° with a phone. That value is the node heading.

**Product + pitch**

| Task | Done when |
| --- | --- |
| Dashboard shell through `store`: map, counters and table (§12.4) | It shows the stub, then the real `scored.csv`. Screenshot saved as `docs/img/phase-1-dashboard.png`. |
| Turn [labelling-guide.md](labelling-guide.md) from v0 into v1. | Both labellers have read it and labelled 3 practice alerts together (not from the sample). |

### Gotchas (§19)

- Pad `acq_time` to four digits before building `t` and the id.
- FIRMS: a valid response starts with `latitude`. Drop rows past the end date, and always clip to the polygon.
- State polygon: select it with `shapeISO == 'IN-UT'`. In `data/state.geojson` the name is `Uttarākhand` (with ā), so neither spelling in §7 matches, and a match on "Uttar" also catches Uttar Pradesh.
- WorldCover: the tile is floor(lat / 3) × 3 and floor(lon / 3) × 3. Round read windows to whole pixels. Reading one tile at an edge is fine.
- Footprint in degrees: lat = km / 111; lon = km / (111 × cos(lat)).
- DEM: the x pixel size in metres uses cos(lat). Skip or clamp 3×3 windows at a tile edge.
- Open-Meteo: one archive request per 0.25° cell covering the whole window fills the cache for every date, about 150 requests per window.
- `seen` excludes the alert itself and uses the D2 window. Don't build an n×n matrix, because Window B is much bigger.

## Gate 1 checklist (§15.3)

- [ ] Window A pulled and clipped, row count printed. Geo; pasted output.
- [ ] WorldCover tiles, DEM tiles, villages and history cells ready. Geo; file and row counts.
- [ ] One alert has every feature plus p, r, tier and reasons. Scoring; pasted alert.
- [ ] Full Window A scored to `data/scored.csv`, tier counts printed. Scoring; pasted counts.
- [ ] Camera streams to the laptop and the servo sweeps on command. Hardware + bot; calibration values.
- [ ] Dashboard map shows scored alerts. Product; `docs/img/phase-1-dashboard.png`.
- [ ] Pyronear model detects smoke on a test clip. Vision; `docs/img/phase-1-smoke.png`.
- [ ] Added by this plan: the score self-check passes, D1–D5 are recorded, and the labelling guide is at v1.

---

## Completion report: Gate 1

> Fill this in, then push it with tag `phase-1` ([how](implementation-plan.md#documents-and-pushing)).

**Gate passed at:** hour __ (YYYY-MM-DD HH:MM IST) · **Filled by:** · **Commit:**

### Decisions made at hour 0

| # | Decision | Chosen |
| --- | --- | --- |
| D1 | VERIFY messages | |
| D2 | `seen` window | |
| D3 | `/todo` order | |
| D4 | Sent marker | |
| D5 | Labels in git | |

### Data counts (paste the printed output)

```
win_a.csv rows:          win_a_uk.csv rows:
hist.csv rows:           hist_uk.csv rows:
cells.csv rows:          largest n:
villages.csv rows:
WorldCover tiles: _/6    DEM tiles: _/20
```

### Window A tiers

| DISPATCH | VERIFY | LOG | Total |
| --- | --- | --- | --- |
| | | | |

Early cross-check (optional): the share of Window A with `veg` < 0.30 or `farm` > 0.50 is __%. The department reported 39%; expect a higher share here (§14).

### One alert, end to end (paste)

```
id, veg, tree, farm, burn, recur, seen, village_km, village_name, slope, wind, rh, image
p, r, tier
why
```

### Self-check output

```
```

### Camera, servo, model

- Camera option, stream URL or index, fps:
- Flush test:
- Servo: sign __, min pulse __ ms, max pulse __ ms, heading at 0° = __°
- Pyronear: weights __, test clip __, smoke frames __ of __, ms per frame on laptop __ / on Pi __
- D-Fire status:

### Changes to thresholds and spec

| What | From → To | Why | Who |
| --- | --- | --- | --- |
| | | | |

### Carry-overs

| Item | Owner | Due hour |
| --- | --- | --- |
| | | |
