# Phase 0: Before day one

**When:** before the event. Do every S-NPP pull **before 1 Nov 2026**, when S-NPP data delivery ends (§2.2).
**Goal:** nothing at the event waits on an account, a download, a parcel or an unanswered question.
**Spec:** §4, §7, §16, §21, §22.
**Exit:** tick the checklist below, then push the completion report with tag `phase-0`.

## Plan

### Rules, venue, people (Product + pitch)

| # | Task | Done when |
| --- | --- | --- |
| 0.1 | Read the event rules. Is pre-written code allowed? Are data downloads and accounts allowed? | The answer is quoted in the report. If code isn't allowed, prepare only data, accounts and docs now. Then write `pull` and `prep` at hour 0 and re-run them. |
| 0.2 | Ask the organisers whether Telegram works on the venue Wi-Fi and whether incense is allowed (§21). | Answers recorded. If unknown, plan for a phone hotspot and a smoke video. |
| 0.3 | Contact one forest division office or forestry faculty member and ask the §22 questions. | Answers recorded. They feed the Q&A. |
| 0.4 | Draft five slides with the §2 numbers. | Link in the report. |

### Repo and accounts (Scoring, Hardware + bot)

| # | Task | Done when |
| --- | --- | --- |
| 0.5 | Create a private Git repo, add teammates, and push these docs with the `.gitignore` already in the folder. | Everyone can clone and push. |
| 0.6 | Get a FIRMS MAP_KEY (§7). | `https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/<KEY>/ALL` returns CSV. |
| 0.7 | Create the bot with @BotFather and a test group called "Range staff", then add the bot to the group. Send `/start@<bot_username>` in the group, open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `chat.id` (negative for groups). | A test message reaches the group: `curl.exe "https://api.telegram.org/bot<TOKEN>/sendMessage" -d chat_id=<CHAT_ID> -d text=test`. On Windows type `curl.exe`, because plain `curl` is a PowerShell alias for something else. |
| 0.8 | Create `.env` on every laptop that runs services, with `FIRMS_KEY`, `BOT_TOKEN`, `CHAT_ID` and `LAPTOP_IP`. | `git status` never lists `.env`. |

If Telegram upgrades the group to a supergroup (for example after a history-visibility change), the chat id changes to one that starts with `-100`. Re-send the test message after any change to the group's settings.

### Data (Geo data; everything goes in `data/`)

| # | Task | Done when |
| --- | --- | --- |
| 0.9 | Check FIRMS coverage with `/api/data_availability/csv/<KEY>/ALL`. For each range, use `_SP` if it covers the whole range, otherwise `_NRT`. If a range needs both, split it at the last `_SP` date. | Choice per range recorded (§21). |
| 0.10 | Pull S-NPP data for Window A (19 calls), Window B (13 calls) and history (207 calls), using the box `77.5,28.7,81.1,31.5`. Use 5-day chunks with a 1 s pause, check that each response starts with `latitude`, and drop rows past the end date. Save as `win_a.csv`, `win_b.csv` and `hist.csv`. | Row counts recorded, **before 1 Nov 2026**. |
| 0.11 | Make one 1-day call each to `VIIRS_NOAA20_NRT` and `VIIRS_NOAA21_NRT`. | Both start with `latitude` and have the same columns as the S-NPP files (live mode, §3.1). |
| 0.12 | Download the WorldCover tiles `N27E075`, `N27E078`, `N27E081`, `N30E075`, `N30E078` and `N30E081` into `data/worldcover/`. | All 6 files open. |
| 0.13 | For the Copernicus DEM, list the bucket first, e.g. `https://copernicus-dem-30m.s3.amazonaws.com/?list-type=2&prefix=Copernicus_DSM_COG_10_N28_00_E077`. Then download lat 28–31 × lon 077–081 into `data/dem/`. | All 20 files open and the names are confirmed (§21). |
| 0.14 | Run the Overpass query below and save the result as `data/villages.json`. | Element count recorded. |
| 0.15 | Download the state boundary (geoBoundaries IND ADM1 or DataMeet) as `data/state.geojson`. | Property name and value for Uttarakhand recorded, e.g. `shapeName` = `Uttarakhand`. Older files say "Uttaranchal". |
| 0.16 | Open one item from `https://earth-search.aws.element84.com/v1/collections/sentinel-2-c1-l2a/items?limit=1`. | `nir` and `swir22` carry `raster:bands` with `scale` and `offset` (§21). |

Overpass query (box order is south, west, north, east):

```
[out:json][timeout:180];
node["place"~"^(village|hamlet|town)$"](28.7,77.5,31.5,81.1);
out;
```

### Models and clips (Vision)

| # | Task | Done when |
| --- | --- | --- |
| 0.17 | Download the Pyronear YOLO11s snapshot (§7). | Weights filename recorded (§21). `yolo predict model=<weights> source=<smoke image> imgsz=1024 conf=0.25` draws a box. |
| 0.18 | Download D-Fire. If the rules allow, start YOLO11n training on Colab or Kaggle: 640 px, about 30 epochs, class 0 = smoke and class 1 = fire (§11.1). | Run started. Set `project=` to a Google Drive folder so a disconnect loses nothing; `resume=True` continues a stopped run. |
| 0.19 | Collect 10 smoke clips and 10 cloud, fog and haze clips into `data/clips/`. | The 10 negative clips add up to **at least 30 minutes**, which the false-alarm test needs (§14). |

### Hardware (Hardware + bot)

| # | Task | Done when |
| --- | --- | --- |
| 0.20 | Choose option A, B or C (§11.2). | Choice recorded. |
| 0.21 | Gather the parts (§16): Pi 4/5 or ESP32-CAM, USB webcam, SG90 and pan bracket, a separate 5 V supply for the servo, tripod, extension cord and A3 hillside backdrop. Spares: a second SG90, a PCA9685 board (§18), cables and a power bank. | Inventory ticked in the report. |
| 0.22 | Bench test: frames reach the laptop, and the servo moves to −90°, 0° and +90° on command. A throwaway script is fine. | Both work, and the servo supply's ground is tied to the Pi's ground. |

## Exit checklist

- [ ] Rules answer quoted (0.1) and venue answers recorded (0.2)
- [ ] Repo is up, everyone can push, `.gitignore` committed
- [x] FIRMS key works; a test message reached the Telegram group
- [x] `win_a.csv`, `win_b.csv` and `hist.csv` pulled before 1 Nov 2026; NOAA-20/21 checked
- [x] 6 WorldCover tiles, 20 DEM tiles, `villages.json` and `state.geojson` present
- [ ] Every §21 open item answered
- [ ] Pyronear model draws a box; D-Fire training started (or scheduled for hour 0)
- [ ] 10 smoke clips, plus negatives totalling at least 30 minutes
- [ ] Hardware in hand and bench-tested
- [ ] Five draft slides

---

## Completion report: Phase 0

> Fill this in, then push it with tag `phase-0` ([how](implementation-plan.md#documents-and-pushing)). Never paste secrets here.

**Completed:** YYYY-MM-DD · **Filled by:** · **Commit:**

### Rules and venue

| Question | Answer | Source (link or quote) |
| --- | --- | --- |
| Pre-written code allowed? | | |
| Data downloads and accounts allowed? | | |
| Telegram works on venue Wi-Fi? | | |
| Incense allowed? | | |

### Accounts

| Item | Status |
| --- | --- |
| FIRMS key works | Yes, in `.env`. Limit 5,000 transactions per 10 min; the full pull used about 2,100. `VIIRS_NOAA20_NRT` and `VIIRS_NOAA21_NRT` both answer with the S-NPP columns minus `type` (0 fires in the box on 2026-10-02). |
| Bot username | `@agnidrishtibot` (privacy mode on: in groups it sees only commands addressed to it) |
| Group created, bot added, test message received | Yes. Group "Range Staff" (basic group, chat id in `.env`); the test `sendMessage` succeeded on 2026-10-03. If the group is ever upgraded to a supergroup, the id changes. |
| `.env` present on (laptop names) | |

### FIRMS coverage and source choice

| Range | Dates | Source used | Why |
| --- | --- | --- | --- |
| Window A | 2025-11-01 to 2026-01-31 | VIIRS_SNPP_SP | `_SP` covers 2012-01-20 to 2026-06-30, the whole range |
| Window B | 2026-04-01 to 2026-05-31 | VIIRS_SNPP_SP | Same |
| History | 2023-01-01 to 2025-10-31 | VIIRS_SNPP_SP | Same |
| Live | now | VIIRS_NOAA20_NRT, VIIRS_NOAA21_NRT | §4.1 |

### Data manifest

| File | Source | Range or tiles | Rows or count | Size | Pulled on | By |
| --- | --- | --- | --- | --- | --- | --- |
| data/win_a.csv | FIRMS area API, VIIRS_SNPP_SP, box 77.5,28.7,81.1,31.5 (not clipped yet) | 2025-11-01 to 2026-01-31 | 4,692 (h 59, n 4,529, l 104) | 0.4 MB | 2026-10-02 | Claude Code |
| data/win_b.csv | Same, VIIRS_SNPP_SP | 2026-04-01 to 2026-05-31, **but data stops on 2026-04-27**: S-NPP has no detections from 28 Apr to early June 2026 | 4,304 (h 63, n 3,614, l 627) | 0.3 MB | 2026-10-02 | Claude Code |
| data/win_b_noaa20.csv | Same, VIIRS_NOAA20_SP | 2026-04-01 to 2026-05-30, complete | 9,968 (h 140, n 8,473, l 1,355) | 0.8 MB | 2026-10-02 | Claude Code |
| data/hist.csv | Same, VIIRS_SNPP_SP | 2023-01-01 to 2025-10-31 | 54,587 (h 748, n 48,123, l 5,716) | 4.1 MB | 2026-10-02 | Claude Code |
| data/worldcover/ | ESA WorldCover 2021 v200 (AWS S3) | N27E075, N27E078, N27E081, N30E075, N30E078, N30E081 | 6 tiles. All open (EPSG:4326, 36,000 × 36,000 px, uint8, deflate). Landmark samples are right: Dehradun built-up, Rajaji tree, Nanda Devi snow, Ramganga reservoir water, Nainital tree/built-up/water mix. | 550 MB | 2026-10-02 | Claude Code |
| data/dem/ | Copernicus DEM GLO-30 (AWS S3) | lat 28–31 × lon 077–081 | 20 tiles. All open (EPSG:4326, 3,600 × 3,600 px, 1 arc-second). Spot checks are right: Haridwar 278 m / 1.2°, Dehradun 673 m / 4.1°, Nainital 1,976 m / 26.5°, Nanda Devi 7,797 m. | 788 MB | 2026-10-02 | Claude Code |
| data/villages.json | Overpass, kumi.systems mirror (overpass-api.de timed out); OSM data as of 2026-07-24 | box 28.7,77.5,31.5,81.1; place = village, hamlet, town | 23,165 (5,632 village, 141 town, 17,392 hamlet; 3,303 unnamed) | 3.5 MB | 2026-10-02 | Claude Code |
| data/state.geojson | geoBoundaries gbOpen IND ADM1, commit 9469f09 (DataMeet / Election Commission of India, 2011; CC BY 2.5 IN) | all 36 states and UTs | 36 features | 45 MB | 2026-10-02 | Claude Code |
| data/models/pyronear/yolo11s_rapid-raccoon_v8.1.0/ | Hugging Face, Apache-2.0 | `best.pt`, `ncnn_cpu.tar.gz`, `onnx_cpu.tar.gz`, card, manifest | 5 files; `best.pt` sha256 matches the manifest | 85 MB | 2026-10-02 | Claude Code |
| data/clips/test/ | Pyro-SDIS val split (first rows), Apache-2.0 | 3 labelled tower-camera smoke frames (`sdis_val_0..2.jpg`) | 3 images | 0.2 MB | 2026-10-02 | Claude Code |
| data/clips/ | | 10 smoke clips + ≥ 30 min of negatives | | | | |

### Open items (§21)

| Item | Result | How checked |
| --- | --- | --- |
| Copernicus DEM tile names exist | Yes. All 20 exist as `Copernicus_DSM_COG_10_N{lat}_00_E{lon}_00_DEM/` plus the same name with `.tif`, as §7 says. | Bucket listing, then download and open all 20 |
| State boundary name property and value | `shapeName` = `Uttarākhand` (with ā), `shapeISO` = `IN-UT`. Select by `shapeISO`: neither §7 spelling matches, and "Uttar" also matches Uttar Pradesh. | Listed all 36 features of `data/state.geojson` |
| FIRMS `_SP` vs `_NRT` coverage per window | `VIIRS_SNPP_SP` covers 2012-01-20 to 2026-06-30, so all three ranges use `_SP` and nothing needs splitting. `_NRT` for S-NPP, NOAA-20 and MODIS starts 2026-07-01; `VIIRS_NOAA21_NRT` starts 2024-01-17. A request with day range 5 and date D returns D to D+4. `_SP` files add a `type` column (FIRMS's static-source flag), which `_NRT` files lack. | `/api/data_availability` on 2026-10-02, plus a probe request |
| Pyronear weights filename | The spec's repo `pyronear/yolo11s_colorful-chameleon_v3.0.0` is no longer published (Hugging Face returns 401). Pinned `pyronear/yolo11s_rapid-raccoon_v8.1.0`: `best.pt`, plus `ncnn_cpu.tar.gz` for the Pi. Card settings: imgsz 1024, conf 0.2, iou 0.01. | Hugging Face API listing of the `pyronear` org; sha256 checked against `manifest.yaml` |
| Sentinel-2 `raster:bands` scale and offset present | Present on `nir` and `swir22`: scale 0.0001, **offset −0.1** (processing baseline 05.13). §11.4's default offset of 0 is wrong for Collection 1, so always read it from the metadata. | Item `S2C_T43RGP_20260930T053540_L2A` from Earth Search |
| Venue: Telegram works, incense allowed | | |

### Models, clips, hardware

- Pyronear weights file: `data/models/pyronear/yolo11s_rapid-raccoon_v8.1.0/best.pt`. Its only class is named `item`, so count boxes rather than filtering on "smoke".
- Smoke check (task 0.17): at imgsz 1024, conf 0.2, iou 0.01, 3 of 3 labelled Pyro-SDIS frames got one box each on the labelled plume, with confidences 0.75, 0.26 and 0.47 (box centres within 0.03 of the labels). No box on the overcast sky. About 0.7 s per frame on the laptop CPU (ultralytics 8.x in `.venv`). Evidence: `docs/img/phase-0-smoke-check.jpg` (Pyro-SDIS, Apache-2.0).
- D-Fire run (where, epochs so far, mAP50 for smoke and fire):
- Clips: smoke __ (__ min); negatives __ (__ min)
- Camera option (A/B/C):
- Inventory: Pi or ESP32 ☐ webcam ☐ SG90 + bracket ☐ servo 5 V supply ☐ tripod ☐ extension cord ☐ backdrop ☐ spare SG90 ☐ PCA9685 ☐ power bank ☐
- Bench test result:

### Changes to the spec found in Phase 0

| What | Spec says | Found | Action |
| --- | --- | --- | --- |
| Camera smoke model (§7, §11.1) | `pyronear/yolo11s_colorful-chameleon_v3.0.0`, imgsz 1024, conf 0.25 | Not published any more. The latest versioned Pyronear YOLO11s is `yolo11s_rapid-raccoon_v8.1.0`, whose card uses imgsz 1024, conf 0.2, iou 0.01. The unversioned `pyronear/yolov11s` holds different, newer weights. | Pinned v8.1.0 so tests and the demo use the same weights. Phase 1 starts at conf 0.2; Phase 3 locks the final value. `yolov11s` is an optional comparison in Phase 3. |
| Selecting the state polygon (§7) | Match "Uttarakhand" or "Uttaranchal" | The name is `Uttarākhand` | `prep` selects `shapeISO == 'IN-UT'` |
| Sentinel-2 offset (§11.4) | Default scale 0.0001, offset 0 | Collection 1 carries offset −0.1 | `s2` reads scale and offset from `raster:bands` |
| Window B sensor (§4.1) | Replay uses VIIRS S-NPP | S-NPP recorded nothing over the box from 28 Apr to early June 2026. Over the same days NOAA-20, NOAA-21 and MODIS recorded plenty, e.g. NOAA-20 had 1,522 detections on 18–22 May. With S-NPP, Window B would lose May, the peak month. | **Decision needed.** Recommended: Window B from VIIRS_NOAA20_SP (`win_b_noaa20.csv`): full window, same VIIRS 375 m product, and the satellite live mode uses. Window A and the history stay on S-NPP. |

### Forest division contact (§22)

Who and when, plus short answers to Q1–Q6:

### Carry-overs

| Item | Owner | Due (event hour) |
| --- | --- | --- |
| | | |
