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
| Stream the phone camera to the laptop (decided 3 Oct: phone, no Pi, no servo). Run the IP Webcam app on the phone, on the same Wi-Fi as the laptop. Set `CAMERA_SOURCE` to `http://<phone-ip>:8080/video`. | Frames show in a window on the laptop. |
| Flush buffered frames before every read (§19). | Cover the lens, uncover it, grab a frame: it shows the uncovered view. |

There is no servo, so the camera knobs in `config` are:

- **`NODE_HEADING`:** the compass bearing the phone faces. Measure it with a second phone's compass app.
- **`NODE_FOV_DEG`:** the phone's horizontal field of view, about 60° for a main camera. The node skips alerts outside heading ± FOV/2.

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

- [x] Window A pulled and clipped, row count printed. Geo; pasted output.
- [x] WorldCover tiles, DEM tiles, villages and history cells ready. Geo; file and row counts.
- [x] One alert has every feature plus p, r, tier and reasons. Scoring; pasted alert.
- [x] Full Window A scored to `data/scored.csv`, tier counts printed. Scoring; pasted counts.
- [ ] Camera streams to the laptop (servo dropped, decided 3 Oct). Hardware + bot; stream URL and fps.
- [ ] Dashboard map shows scored alerts. Product; `docs/img/phase-1-dashboard.png`.
- [x] Pyronear model detects smoke on a test clip. Vision; `docs/img/phase-1-smoke.png`.
- [ ] Added by this plan: the score self-check passes, D1–D5 are recorded, and the labelling guide is at v1.

---

## Completion report: Gate 1

> Fill this in, then push it with tag `phase-1` ([how](implementation-plan.md#documents-and-pushing)).

**Gate status (3 Oct 2026):** every item passes except two that need the team lead's laptop and phone: the phone camera stream, and the dashboard screenshot. Tag `phase-1` waits for both. · **Filled by:** Claude Code · **Code:** `config.py`, `geo.py`, `pull.py`, `prep.py`, `check.py`, `score.py`, `store.py`, `app.py`

### Decisions made at hour 0

Recommended defaults adopted on 3 Oct; the team lead didn't override them.

| # | Decision | Chosen |
| --- | --- | --- |
| D1 | VERIFY messages | Only DISPATCH is sent to Telegram; the bot accepts photos for any non-LOG alert |
| D2 | `seen` window | Earlier alerts only: the 12 h up to and including the alert's own time (`check.seen`) |
| D3 | `/todo` order | Newest first (Phase 2) |
| D4 | Sent marker | `data/cap_<id>.xml` exists only after Telegram returns ok (Phase 2) |
| D5 | Labels in git | `.gitignore` keeps `data/labels*.csv` and `data/sample.csv` |

### Data counts (printed by `prep.py`)

```
win_a: 4692 rows in the box, 3434 inside Uttarakhand -> win_a_uk.csv
win_b: 9968 rows in the box, 6880 inside Uttarakhand -> win_b_uk.csv   (NOAA-20)
hist: 54587 rows in the box, 33570 inside Uttarakhand -> hist_uk.csv
villages: 23165 places (3303 unnamed) -> villages.csv
cells: 25119 cells from 33570 history detections, largest n 8 -> cells.csv
WorldCover tiles: 6/6    DEM tiles: 20/20
```

### Window A tiers

`score.py` scores Windows A and B together in 2 min 25 s; the first run also fills the weather cache.

| | DISPATCH | VERIFY | LOG | Total |
| --- | --- | --- | --- | --- |
| Window A | 1,919 | 1,243 | 272 | 3,434 |
| Window B | 4,325 | 2,222 | 333 | 6,880 |
| Both (`data/scored.csv`) | 6,244 | 3,465 | 605 | 10,314 |

Early cross-check: **8.2%** of Window A has `veg` < 0.30 or `farm` > 0.50, against the department's 39%. The spec expected a higher share. The likely reason: the department splits alerts by **Reserve Forest boundary**, and its own document says "Only RF boundaries are there". WorldCover sees vegetation, not legal boundaries, so fires in vegetated land outside Reserve Forest look like forest. This is the limitation the spec accepts (§3.3); say so in the pitch.

### Findings for Phase 3: the spec's starting weights barely discriminate here

With the §10 weights, **61% of alerts are DISPATCH**. Nothing here is a bug; the features look right. The thresholds just don't separate alerts in Uttarakhand:

- **Village distance:** 83% of alerts are within 2 km of an OSM place (17,392 of the 23,165 are hamlets), so nearly every alert gets the +2 for a village under 2 km.
- **Slope:** the median is 31°, so most alerts also get +1.
- **Result:** 96% of alerts have r ≥ 2, so "p ≥ 0.6 and r ≥ 2" collapses to "p ≥ 0.6". 5,852 of the 6,244 DISPATCH alerts got there that way.
- **`seen`:** 62% of alerts have at least one other detection within 1 km and 12 h, which already makes p 0.65.
- **Recurrence:** the busiest 500 m cell fired only 8 times in 3 years, so the `recur` ≥ 8 rule almost never fires.
- **Land cover:** only 5% of alerts have `veg` < 0.30 and 6% have `farm` > 0.50.

Per §10.5 and §20, none of these were changed. Candidates to tune on the tune half of the labels in Phase 3:

- the village distances, or counting villages and towns only, without hamlets;
- the DISPATCH risk bar;
- the step for `seen`;
- the `recur` threshold.

### One alert, end to end (from `data/scored.csv`)

```
id 2025-11-09_0657_31.2046_78.4332
veg 0.13, tree 0.00, farm 0.00, burn none, recur 0, seen 2
village_km 12.6 (Seema), slope 43.7°, wind 8.0 km/h, rh 30%, confidence h, frp 49.34 MW, image none
p 0.70 (0.5 − 0.30 low vegetation + 0.30 seen + 0.10 high confidence + 0.10 FRP), r 2 (slope + seen ≥ 2), DISPATCH
why: pixel only 13% vegetation; seen 3 times in 12 h; high confidence; FRP 49 MW; 12.6 km from Seema, slope 44°, wind 8 km/h, RH 30%
```

### Self-check output

```
$ python geo.py
geo ok
$ python score.py --selftest
score self-test ok
```

The self-test covers each p rule with its reason text; the `seen` cap; clipping at 0; the 0.5 + 0.1 + 0.3 float case; all tier edges; the four image overrides; every risk point (village 1.4 / 4 / 6 km, all seven); "weather unavailable"; the alert-id format; and `seen` counting earlier alerts only.

### Dashboard

Superseded on 3 Oct. The team lead chose a custom FastAPI-served page (`api.py` plus `web/`), built with the impeccable design workflow, and `app.py` was removed. What follows records the Gate 1 check of the original Streamlit shell.

`app.py` (Streamlit + folium), checked with Streamlit's `AppTest`:

- no exceptions;
- counters show 10,314 / 6,244 / 3,465;
- the tier filter defaults to DISPATCH and VERIFY;
- the table has 9,709 rows sorted DISPATCH, then VERIFY, then LOG, and by p within each.

Load time: the first version drew one folium marker per alert and took 66 s per run. One GeoJSON layer brought that down to 5 s for the first load and 2 s for a rerun with LOG on (10,314 alerts). Headless Edge only captured Streamlit's loading skeleton, so the screenshot is a carry-over.

### Camera, model

- Camera option, stream URL or index, fps: option C (phone). Not tested yet; carry-over.
- Flush test: with the phone stream (carry-over).
- Phone camera: stream URL __, fps __, heading __°, field of view __°
- Pyronear: `yolo11s_rapid-raccoon_v8.1.0/best.pt`. On 3 labelled frames: 3 of 3 detected. On sample clips with the 6-frame rule: 3 of 3 smoke clips → smoke, 9 of 9 no-smoke clips → nosmoke. About 0.7 s per frame on the laptop CPU; no Pi.
- D-Fire status: done 3 Oct on Kaggle (YOLO11n, 640 px, 30 epochs, 76 min).
  - Test split (4,291 images, 5,166 boxes): **mAP50 smoke 0.802, fire 0.682, all 0.742** (precision 0.742, recall 0.674).
  - The class ids are right: the test set has more fire boxes than smoke boxes (2,868 vs 2,298), as in D-Fire.
  - Weights are at `data/models/dfire_yolo11n_best.pt`. The download arrived as `.zip`, which is the checkpoint itself (a `.pt` is a zip archive), so it was copied to `.pt` unchanged.
  - About 45 ms per photo on the laptop CPU.
  - On the 3 distant tower frames at conf 0.40 it boxed 1 (smoke 0.61). That's expected for a close-range photo model; distant plumes are the Pyronear camera model's job.

### Changes to thresholds and spec

| What | From → To | Why | Who |
| --- | --- | --- | --- |
| Thresholds and weights | none changed | They are tuned once in Phase 3 (§10.5); see the findings above | — |
| `scored.csv` columns | §8 list → §8 list plus the feature columns (`veg` … `rh`) | Phase 3 can re-tune and re-score without recomputing features | Claude Code |
| p before tiering | raw sum → rounded to 2 dp | `0.5 + 0.1 + 0.3` is `0.8999999999999999` and would miss DISPATCH | Claude Code |
| Dashboard markers | one folium marker per alert → one GeoJSON layer | 66 s → 5 s per run | Claude Code |
| Weather | one request per cell and date → one archive request per 0.25° cell covering its whole date range, cached in `data/weather/` | Same §10.1 values with far fewer calls; a failed lookup gives "weather unavailable" and never stops scoring | Claude Code |

### Carry-overs

| Item | Owner | Due |
| --- | --- | --- |
| Phone camera (IP Webcam) streams to the laptop; flush test; heading and field of view recorded | Team lead | 4 Oct |
| Dashboard screenshot saved as `docs/img/phase-1-dashboard.png` (open http://localhost:8501) | Team lead | 4 Oct |
| Both labellers read the labelling guide and label 3 practice alerts together | Product + pitch | 4 Oct |
| D-Fire weights saved to `data/models/dfire_yolo11n_best.pt`, with their test mAP | Team lead | **Done 3 Oct** (mAP50 0.742) |
