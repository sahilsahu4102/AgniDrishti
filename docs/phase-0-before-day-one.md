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

- [x] Rules answer quoted (0.1) and venue answers recorded (0.2)
- [x] Repo is up, everyone can push, `.gitignore` committed (github.com/sahilsahu4102/AgniDrishti; add teammates as collaborators)
- [x] FIRMS key works; a test message reached the Telegram group
- [x] `win_a.csv`, `win_b.csv` and `hist.csv` pulled before 1 Nov 2026; NOAA-20/21 checked
- [x] 6 WorldCover tiles, 20 DEM tiles, `villages.json` and `state.geojson` present
- [x] Every §21 open item answered
- [x] Pyronear model draws a box; D-Fire training started (or scheduled for hour 0): notebook ready, the team lead is running it on Kaggle
- [x] 10 smoke clips, plus negatives totalling at least 30 minutes
- [ ] Hardware in hand and bench-tested: carried over. The phone camera replaces the Pi and servo; its stream test is the first Phase 1 task.
- [ ] Five draft slides: deferred to Phase 4 (team decision, 3 Oct)

---

## Completion report: Phase 0

> Fill this in, then push it with tag `phase-0` ([how](implementation-plan.md#documents-and-pushing)). Never paste secrets here.

**Completed:** 2026-10-03, with the carry-overs below · **Filled by:** Claude Code with the team lead · **Commit:** tagged `phase-0`

### Rules and venue

| Question | Answer | Source (link or quote) |
| --- | --- | --- |
| Pre-written code allowed? | Yes. Source code and demo are submitted by **9 Oct 2026** | Team lead, 2026-10-03 |
| Data downloads and accounts allowed? | Yes | Same |
| Telegram works on venue Wi-Fi? | Not applicable to a submitted demo; recheck if there is a live round | Same |
| Incense allowed? | Not needed: the demo uses a smoke video in front of a phone camera | Same |

### Accounts

| Item | Status |
| --- | --- |
| FIRMS key works | Yes, in `.env`. Limit 5,000 transactions per 10 min; the full pull used about 2,100. `VIIRS_NOAA20_NRT` and `VIIRS_NOAA21_NRT` both answer with the S-NPP columns minus `type` (0 fires in the box on 2026-10-02). |
| Bot username | `@agnidrishtibot` (privacy mode on: in groups it sees only commands addressed to it) |
| Group created, bot added, test message received | Yes. Group "Range Staff" (basic group, chat id in `.env`); the test `sendMessage` succeeded on 2026-10-03. If the group is ever upgraded to a supergroup, the id changes. |
| `.env` present on (laptop names) | Team lead's laptop: `FIRMS_KEY`, `BOT_TOKEN` and `CHAT_ID` set; `LAPTOP_IP` is needed only if the camera runs on another device |

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
| data/clips/ | HPWREN FIgLib (credit https://www.hpwren.ucsd.edu/ required) and Wikimedia Commons (CC0, PD, CC BY, CC BY-SA only). Each file's source, licence and credit is in `data/clips/manifest.csv`. | `smoke/`: 10 HPWREN tower-camera clips, from 5 min after the plume appears. `negative/`: 39 HPWREN before-ignition clips (same landscapes, no smoke) plus 35 Commons cloud, fog, mist and haze time-lapses. HPWREN frames are 1 per minute, played at 1 fps. | 10 smoke (6.0 min), 74 negative (43.3 min); every file decodes end to end | 1.4 GB with raw downloads | 2026-10-03 | Claude Code |

### Open items (§21)

| Item | Result | How checked |
| --- | --- | --- |
| Copernicus DEM tile names exist | Yes. All 20 exist as `Copernicus_DSM_COG_10_N{lat}_00_E{lon}_00_DEM/` plus the same name with `.tif`, as §7 says. | Bucket listing, then download and open all 20 |
| State boundary name property and value | `shapeName` = `Uttarākhand` (with ā), `shapeISO` = `IN-UT`. Select by `shapeISO`: neither §7 spelling matches, and "Uttar" also matches Uttar Pradesh. | Listed all 36 features of `data/state.geojson` |
| FIRMS `_SP` vs `_NRT` coverage per window | `VIIRS_SNPP_SP` covers 2012-01-20 to 2026-06-30, so all three ranges use `_SP` and nothing needs splitting. `_NRT` for S-NPP, NOAA-20 and MODIS starts 2026-07-01; `VIIRS_NOAA21_NRT` starts 2024-01-17. A request with day range 5 and date D returns D to D+4. `_SP` files add a `type` column (FIRMS's static-source flag), which `_NRT` files lack. | `/api/data_availability` on 2026-10-02, plus a probe request |
| Pyronear weights filename | The spec's repo `pyronear/yolo11s_colorful-chameleon_v3.0.0` is no longer published (Hugging Face returns 401). Pinned `pyronear/yolo11s_rapid-raccoon_v8.1.0`: `best.pt`, plus `ncnn_cpu.tar.gz` for the Pi. Card settings: imgsz 1024, conf 0.2, iou 0.01. | Hugging Face API listing of the `pyronear` org; sha256 checked against `manifest.yaml` |
| Sentinel-2 `raster:bands` scale and offset present | Present on `nir` and `swir22`: scale 0.0001, **offset −0.1** (processing baseline 05.13). §11.4's default offset of 0 is wrong for Collection 1, so always read it from the metadata. | Item `S2C_T43RGP_20260930T053540_L2A` from Earth Search |
| Venue: Telegram works, incense allowed | Not applicable: code and demo are submitted by 9 Oct. The demo films a phone camera watching a smoke video. | Team lead, 2026-10-03 |

### Models, clips, hardware

- Pyronear weights file: `data/models/pyronear/yolo11s_rapid-raccoon_v8.1.0/best.pt`. Its only class is named `item`, so count boxes rather than filtering on "smoke".
- Smoke check (task 0.17): at imgsz 1024, conf 0.2, iou 0.01, 3 of 3 labelled Pyro-SDIS frames got one box each on the labelled plume, with confidences 0.75, 0.26 and 0.47 (box centres within 0.03 of the labels). No box on the overcast sky. About 0.7 s per frame on the laptop CPU (ultralytics 8.x in `.venv`). Evidence: `docs/img/phase-0-smoke-check.jpg` (Pyro-SDIS, Apache-2.0).
- D-Fire run (where, epochs so far, mAP50 for smoke and fire): notebook `train_dfire.ipynb` is ready for Kaggle. It uses the Kaggle copy `sayedgamal99/smoke-fire-detection-yolo` and trains YOLO11n at 640 px for 30 epochs. Not run yet.
- Clips: smoke 10 (6.0 min); negatives 74 (43.3 min: 25.5 HPWREN, 17.8 Commons).
  - The first Commons pass saved Wikimedia error pages as video files, because the script didn't check responses. 38 files were re-fetched; 5 still failed and were dropped. Every remaining file was verified to decode to its last frame. One HPWREN video was corrupt and skipped.
  - 6-frame check (conf 0.2, smoke if ≥ 4 of 6): `smoke` on 3 of 3 sampled smoke clips (6, 5 and 4 of 6 frames). `nosmoke` on 9 sampled no-smoke clips: 0 of 6 frames on 7 of them (6 Commons cloud time-lapses, 1 HPWREN), 1 of 6 on one HPWREN clip. The full 30-minute test is Phase 3.
  - The demo credits must name HPWREN and the Commons authors listed in the manifest.
- Camera option (A/B/C): C, an Android phone running an IP-camera app, no servo, inference on the laptop
- Inventory: phone ☐ phone stand or tripod ☐ monitor or second screen for the smoke video ☐ charger ☐. No Pi, servo or PCA9685 needed.
- Bench test result: carried over to Phase 1 (phone stream test)

### Changes to the spec found in Phase 0

| What | Spec says | Found | Action |
| --- | --- | --- | --- |
| Camera smoke model (§7, §11.1) | `pyronear/yolo11s_colorful-chameleon_v3.0.0`, imgsz 1024, conf 0.25 | Not published any more. The latest versioned Pyronear YOLO11s is `yolo11s_rapid-raccoon_v8.1.0`, whose card uses imgsz 1024, conf 0.2, iou 0.01. The unversioned `pyronear/yolov11s` holds different, newer weights. | Pinned v8.1.0 so tests and the demo use the same weights. Phase 1 starts at conf 0.2; Phase 3 locks the final value. `yolov11s` is an optional comparison in Phase 3. |
| Selecting the state polygon (§7) | Match "Uttarakhand" or "Uttaranchal" | The name is `Uttarākhand` | `prep` selects `shapeISO == 'IN-UT'` |
| Sentinel-2 offset (§11.4) | Default scale 0.0001, offset 0 | Collection 1 carries offset −0.1 | `s2` reads scale and offset from `raster:bands` |
| Window B sensor (§4.1) | Replay uses VIIRS S-NPP | S-NPP recorded nothing over the box from 28 Apr to early June 2026. Over the same days NOAA-20, NOAA-21 and MODIS recorded plenty, e.g. NOAA-20 had 1,522 detections on 18–22 May. With S-NPP, Window B would lose May, the peak month. | **Decided 2026-10-03: Window B uses VIIRS_NOAA20_SP.** `data/win_b.csv` is now the NOAA-20 file (9,968 rows); the S-NPP partial is kept as `data/win_b_snpp.csv`. Window A and the history stay on S-NPP. |
| Camera node hardware (§11.2) | Option A (Pi + servo) recommended | Team chose a phone camera | Option C: an Android phone as an IP camera, no servo, inference on the laptop. The node does not pan; it only checks alerts inside the phone's field of view. |
| Schedule (§4, §15.2) | 36-hour event | Code and demo are submitted by 9 Oct 2026 | Phases dated in `implementation-plan.md`; pitch slides come last |

### Forest division questions (§22), from published sources only

No division was contacted. Each answer below is quoted or closely paraphrased from the source cited. Where nothing published answers a question, the table says so instead of guessing.

| # | Question | What published sources confirm | Source |
| --- | --- | --- | --- |
| 1 | Alerts per range per day in peak season? | No published per-range figure. State total: 1,952 alerts from 1 Nov 2025 to 20 Jan 2026. Our own FIRMS pull gives daily counts once Phase 1 clips it to the state. | [ETV Bharat, 30 Jan 2026](https://www.etvbharat.com/en/state/uttarakhand-forest-department-claims-that-most-of-fsi-forest-fire-alert-false-enn26013007036) |
| 2 | How are alerts prioritised? | No published "visit first" rule. Uttarakhand's IT cell (ITGC) enriches each alert with: inside or outside Reserve Forest, nearest crew station, nearest watch tower, nearest settlement (up to 2 km), and settlements within a 1 km buffer. FSI's own definition of a large fire is at least 3 neighbouring VIIRS pixels in one pass. | [Uttarakhand Forest Fire Management Model](https://uaoa.gov.in/sites/default/files/2025-08/Forest%20Forest%20Fire.pdf); [FSI forest fire activities (2022)](https://fsi.nic.in/uploads/documents/doc_8912_forest-fire-activities-1142022.pdf) |
| 3 | Are outcomes recorded in FSI's feedback system? | A feedback system exists: FSI's FAST 3.0 (launched January 2019) has "improved feedback system (via SMS and nodal officer page)", and FSI's SMS alerts carry a "Click … for feedback" link. No season's feedback log is published. | [FSI Technical Information Series Vol. I No. 2 (2019)](https://fsi.nic.in/uploads/documents/technical_information_series_vol1_no2.pdf); FSI forest fire activities (2022) |
| 4 | Would staff log controlled burns a day ahead? | No published answer; this needs a division. Related fact: about 300 of the 1,952 alerts were the department's own controlled burns for fire lines or dry-leaf disposal. | ETV Bharat, 30 Jan 2026 |
| 5 | Which channel do field staff read? | No published figure on what staff actually read. Channels in use: FSI sends alerts by SMS and email (beat level in 20 states, range level in 2), and Uttarakhand's ITGC passes fire locations to divisions "through SMS, email and WhatsApp Messenger". | FSI Technical Information Series (2019); Uttarakhand Forest Fire Management Model |
| 6 | What would make staff trust a LOG alert? | No published answer; this needs a division. | — |

Other confirmed facts for the pitch:

- **Alert count:** the spec's "1,957 alerts in three winter months" comes from a secondary source. The primary report says **1,952 alerts, 1 Nov 2025 to 20 Jan 2026**: 132 real forest fires, 766 false, 754 outside forest, about 300 controlled burns. Use these numbers on slides.
- **Officials quoted:** Forest Minister Subodh Uniyal said "only 6 to 7 per cent of the alerts turn out to be correct"; Chief Conservator Sushant Patnaik said the department has taken the issue up with FSI (ETV Bharat).
- **FSI already filters:** before sending, FSI removes fires outside forests using Recorded Forest Area boundaries plus forest cover, and applies an "industrial and volcanic fire filter mask" (FSI 2019, 2022). AgniDrishti's input (FIRMS) has none of this, so on slides say what AgniDrishti adds beyond FSI's filtering. Don't imply FSI has no filter.
- **Uttarakhand's stated weaknesses:** its own document lists "Only RF boundaries are there" and "Variation in number of fire points as compared to FIRMS" (Uttarakhand Forest Fire Management Model).
- **Crew stations:** they have "only wireless handsets, modern fire fighting tools and some 3 to 5 crew members" (same document).

### Carry-overs

| Item | Owner | Due |
| --- | --- | --- |
| Phone camera (IP-camera app) streams to the laptop | Hardware + bot | Phase 1, 4 Oct |
| D-Fire training on Kaggle finishes; `dfire_yolo11n_best.pt` saved to `data/models/` with its test mAP recorded | Vision (team lead) | Phase 2, 5 Oct |
| Teammates added as GitHub collaborators; Owners table filled | Team lead | 4 Oct |
| Five pitch slides (use 1,952, not 1,957) | Product + pitch | Phase 4, 8 Oct |
