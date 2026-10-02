# AgniDrishti — Project Context

Forest fire alert verification and triage. Make-A-Thon theme: **Forest Fire Detection**. As of 1 October 2026.

This file is the full brief for building AgniDrishti: problem, evidence, scope, architecture, data sources, file formats, scoring rules, component behaviour, build plan, demo and risks. It contains no code on purpose. Implement from this spec, in Python, following the gates in section 15.

---

## 1. Summary

AgniDrishti checks every satellite fire alert before anyone is sent out, so forest staff only go to alerts that are likely to be real, dangerous forest fires.

It does not detect fires itself. It takes existing satellite alerts (NASA FIRMS VIIRS now, FSI's own feed later), runs four data checks and an image check on each one, scores it, and sorts it into one of three tiers with plain-language reasons:

- **DISPATCH**: message field staff now.
- **VERIFY**: point a camera at it and ask the nearest staff member for a photo first.
- **LOG**: keep it on the dashboard, send no message.

**Pitch line:** "In three winter months Uttarakhand got 1,957 fire alerts, and 132 were real forest fires. AgniDrishti tells staff which ones to run to, and shows them why."

**Positioning:** AgniDrishti sits between FSI/FIRMS alerts and the state's dispatch app. It complements both and replaces neither.

---

## 2. Problem and evidence

India does not lack fire detection. It lacks alerts that staff can trust.

### 2.1 Uttarakhand field check, November 2025 to January 2026 (1,957 FSI alerts)

| What the alert turned out to be | Alerts | Share | AgniDrishti check that targets it |
| --- | --- | --- | --- |
| Real forest fire | 132 | ~7% | Image confirmation, then risk ranking and dispatch |
| Fire outside the forest (farms, homes) | 754 | ~39% | Land cover inside the satellite pixel |
| Department's own controlled burn | ~300 | ~15% | Planned-burn register |
| Nothing found on the ground | 766 | ~39% | Recurring-source check, multi-pass agreement, image confirmation |

"Nothing found" can include small fires that burnt out before staff arrived. Treat it as wasted staff time, not proof that there was no fire.

### 2.2 Other facts for the pitch

- **Parliament (August 2026):** the standing committee report on Himalayan forest fires found only about 12.5% of FSI alerts in Uttarakhand matched actual fires. It warned of alert fatigue, asked for alerts to be prioritised, suggested linking FSI alerts to NDMA's cell broadcast system, and urged a dedicated geostationary fire satellite.
- **FSI today:** alerts at least six times a day from MODIS and S-NPP VIIRS, SMS down to beat level. FSI's dashboard shows an SMS going out about 25 minutes after a satellite pass. FSI's large-fire rule is 3 or more contiguous VIIRS pixels.
- **Detection already exists:**
  - Pench Tiger Reserve's "Pantera" (2024): a PTZ camera on a hilltop tower, 15 km range, 350+ sq km, camera plus satellite, alerts within 3 minutes.
  - Odisha: five AI/ML cameras in Similipal (2024), and more AI cameras and drones in 2026.
  - Uttarakhand's Forest Fire App: about 7,000 staff, live tracking of staff and vehicles, alert categorisation.
  - DASH pilot in Nallamala, Telangana: cameras, CO2 sensors and a LoRaWAN mesh.
- **Satellite sources are changing:**
  - S-NPP data delivery ends 1 November 2026.
  - NASA stops Terra MODIS in February 2027 and Aqua MODIS in September 2027.
  - Live mode must use the NOAA-20 and NOAA-21 VIIRS satellites.
- **Response capacity is stretched:**
  - Over 95% of India's forest fires are human-caused, mostly surface fires.
  - In May 2024 the Supreme Court found Uttarakhand had used ₹3.14 crore of ₹9 crore in central funds and named vacancies as the biggest hurdle.

**Implication:** another detector adds alerts to an overloaded system. The useful product is a verification and prioritisation layer on top of the alerts that already exist.

---

## 3. Scope

### 3.1 MVP (must ship)

1. **Alert feed:** NASA FIRMS VIIRS hotspots for Uttarakhand, cached as CSV.
   - Replay mode uses Window A and Window B.
   - Live mode polls every 10 minutes using NOAA-20 and NOAA-21.
2. **Checks per alert:** four data checks (land cover in the pixel, planned-burn register, recurring hotspot, multi-pass agreement), plus an image check when one is available.
3. **Scores and tiers:** p (0–1, likelihood of a real forest fire) and r (0–7, danger) put each alert in DISPATCH, VERIFY or LOG with reason text.
4. **Camera node:** pans toward an alert's bearing and confirms smoke across 6 frames.
5. **Telegram:** DISPATCH messages go to a staff group. A field bot takes back a location, a photo and an outcome button.
6. **Dashboard:**
   - Map, ranked list and counters.
   - Planned-burn register form.
   - CAP 1.2 XML for each DISPATCH alert.
7. **Validation:** about 80 hand-labelled alerts.

### 3.2 Stretch goals

- **Event clustering:** one message per fire instead of one per pixel.
- **Learned weights:** logistic regression on the same features once 150+ labels exist.
- **Season-wide labels:** Sentinel-2 burn-scar labelling for a whole season.
- **Channels:** Hindi messages, and WhatsApp instead of Telegram.
- **Official feed:** FSI's own WMS/WFS layer instead of FIRMS.
- **Triangulation:** a second camera node to locate the plume.
- **More risk inputs:** distance to roads.
- **Fresher land cover:** Dynamic World (near-real-time land cover).

### 3.3 Not building

- A new fire detector or satellite product.
- A fire-spread simulator.
- A replacement for FSI's system or for state dispatch apps.
- Anything that needs official forest boundaries. They are not public, so ESA WorldCover land cover stands in for them.

---

## 4. Assumptions and constraints

- **Event and team:**
  - 24–48 hour event; this plan assumes 36 hours.
  - 4–5 people, laptops, free Colab or Kaggle GPU, one camera node.
- **Event rules:** check the rules on pre-written code. Data downloads and account setup are usually allowed before the event.
- **Data and accounts:**
  - All data is public and free.
  - Accounts needed: a NASA FIRMS MAP_KEY and a Telegram bot token.

### 4.1 Demo region and time windows

| Item | Value |
| --- | --- |
| Region | Uttarakhand. Bounding box W 77.5, S 28.7, E 81.1, N 31.5 (FIRMS order west,south,east,north: `77.5,28.7,81.1,31.5`). Clip to the state polygon afterwards, because the box also covers parts of Himachal Pradesh, Uttar Pradesh, Nepal and Tibet. |
| Window A | 2025-11-01 to 2026-01-31. Matches Uttarakhand's published breakdown. |
| Window B | 2026-04-01 to 2026-05-31. Peak fire season. |
| History | 2023-01-01 to 2025-10-31. Used only for recurring-source counts; must not overlap Window A or B. |
| Replay sensor | VIIRS S-NPP (the sensor FSI lists). |
| Live sensors | VIIRS NOAA-20 and NOAA-21, near-real-time. |

---

## 5. System overview

```
FIRMS VIIRS alerts ──┐
                     ├──> 4 data checks ──> score (p, r) ──> tier ──┬── DISPATCH ──> Telegram to staff + CAP XML
Context data ────────┘                          ▲                   ├── VERIFY ────> camera node pans + photo request
 WorldCover, DEM, villages, weather,            │                   └── LOG ───────> dashboard only
 3-year history cells, planned-burn register    │
                                                │
            image outcomes (camera node, field bot) ── appended to outcomes, rescoring updates p and tier
```

### 5.1 Life of one alert

1. Pulled from FIRMS (or injected by hand for the live demo).
2. Clipped to the state polygon.
3. Features computed:
   - land-cover shares in its footprint
   - planned-burn match
   - recurrence count
   - agreement count
   - distance to the nearest village
   - slope
   - wind and humidity
4. Latest image outcome looked up, if any.
5. p and r computed, then the tier and the reason text.
6. The tier decides what happens next:
   - DISPATCH: Telegram message plus a CAP XML file.
   - VERIFY: the camera node pans to it and staff are asked for a photo.
   - LOG: dashboard only.
7. A camera or field outcome is appended to the outcomes file. The next scoring pass updates p and the tier.

---

## 6. Repository layout and module responsibilities

```
agnidrishti/
  config        constants: box, windows, thresholds, paths
  .env          secrets: FIRMS_KEY, BOT_TOKEN, CHAT_ID, LAPTOP_IP (git-ignored)
  geo           distance and bearing helpers
  store         loads replay + live scored alerts as one table
  pull          FIRMS download for any source and date range
  prep          clip to state, villages table, history cell counts
  check         feature functions
  score         p, r, tier, reasons; scores a whole CSV
  api           camera node endpoints
  node          camera node loop (runs on the Pi)
  bot           Telegram field bot
  send          dispatch message, CAP XML, Telegram push
  live          rescoring loop for the live demo
  s2            Sentinel-2 dNBR labeller
  app           Streamlit dashboard + planned-burn register
  burns.csv     planned-burn register
  data/         downloads and outputs (git-ignored)
```

| Module | Responsibility | Reads | Writes |
| --- | --- | --- | --- |
| config / .env | All constants and secrets in one place | — | — |
| geo | Haversine distance in km (Earth radius 6371 km); initial great-circle bearing in degrees clockwise from north | — | — |
| store | Load `data/scored.csv` and `data/live_scored.csv` (if present) as one table | scored CSVs | — |
| pull | Download a FIRMS area CSV for one source and date range in 5-day chunks, 1 s pause between calls, drop rows after the end date, print the row count | FIRMS API | `data/win_a.csv`, `data/win_b.csv`, `data/hist.csv` |
| prep | Clip each CSV to the state polygon; build the villages table from Overpass JSON; build history cell counts | raw CSVs, state GeoJSON, `data/villages.json` | `*_uk.csv`, `data/villages.csv`, `data/cells.csv` |
| check | Feature functions: land cover, planned burn, recurrence, agreement, nearest village, slope, weather | rasters, villages, cells, `burns.csv`, Open-Meteo | — |
| score | Score one alert (p, r, tier, reasons); score a whole CSV and write it out; print tier counts | `*_uk.csv` or `data/live.csv`, `data/outcomes.csv` | `data/scored.csv` or `data/live_scored.csv` |
| api | Endpoints the camera node uses (section 12.1) | store, outcomes | `data/outcomes.csv` |
| node | Camera node loop (section 11.2) | API, camera | API |
| bot | Telegram field bot (section 11.3) | store, photo model | `data/outcomes.csv` |
| send | Dispatch text, CAP XML, Telegram push; on its own, sends the top N DISPATCH alerts by p | store | Telegram, `data/cap_<id>.xml` |
| live | Every 10 s: rescore `data/live.csv`, push each new DISPATCH exactly once | `data/live.csv`, outcomes | `data/live_scored.csv` |
| s2 | Sentinel-2 dNBR for a lat, lon, date (section 11.4) | Earth Search STAC | `data/labels.csv` (hints) |
| app | Dashboard and planned-burn register (section 12.4) | store | `burns.csv` |

---

## 7. Data sources

| Source | Used for | Access | Auth and limits | Notes |
| --- | --- | --- | --- | --- |
| NASA FIRMS Area API | Alerts, history, agreement | `https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{west,south,east,north}/{DAY_RANGE}/{YYYY-MM-DD}` | Free MAP_KEY from `https://firms.modaps.eosdis.nasa.gov/api/map_key/`. 5,000 transactions per 10 minutes. DAY_RANGE 1–5. | Sources: `VIIRS_SNPP_NRT`, `VIIRS_SNPP_SP`, `VIIRS_NOAA20_NRT`, `VIIRS_NOAA20_SP`, `VIIRS_NOAA21_NRT`, `MODIS_NRT`, `MODIS_SP` (`_SP` = archive, `_NRT` = near-real-time). Check date coverage first at `https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/{MAP_KEY}/ALL`. A valid response starts with `latitude`. The country endpoint is reported dead; use area. |
| ESA WorldCover 2021 v200 (10 m) | Land cover in each pixel | `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{TILE}_Map.tif` | None | 3°×3° Cloud Optimized GeoTIFF tiles named by the south-west corner, e.g. `N30E078`. Uttarakhand needs `N27E075`, `N27E078`, `N27E081`, `N30E075`, `N30E078`, `N30E081`. Windowed reads are cheap. |
| Copernicus DEM GLO-30 | Slope | `https://copernicus-dem-30m.s3.amazonaws.com/{NAME}/{NAME}.tif`, with NAME = `Copernicus_DSM_COG_10_N{lat}_00_E{lon, 3 digits}_00_DEM` | None | 1° tiles named by the south-west corner. Uttarakhand needs lat 28–31 × lon 077–081 (20 tiles). Verify names by listing the bucket `s3://copernicus-dem-30m/` (public, no sign-in). It is a surface model including canopy, which is fine for slope. |
| OpenStreetMap via Overpass | Distance to nearest village | `https://overpass-api.de/api/interpreter` | None; download once | Nodes with `place` = village, hamlet or town inside the box. Overpass box order is south,west,north,east: `(28.7,77.5,31.5,81.1)`. JSON elements have `lat`, `lon`, `tags.name`. |
| Open-Meteo | Wind and humidity | Archive: `https://archive-api.open-meteo.com/v1/archive`; live: `https://api.open-meteo.com/v1/forecast` | None; cache responses | Hourly `wind_speed_10m` (km/h) and `relative_humidity_2m` (%), timezone UTC. The archive lags a few days, so live alerts use the forecast API's current values. |
| Sentinel-2 L2A, Collection 1 | Burn-scar labelling | Earth Search STAC `https://earth-search.aws.element84.com/v1`, collection `sentinel-2-c1-l2a` | None | Assets `nir` (B08, 10 m), `swir22` (B12, 20 m), `scl`. Apply each asset's `raster:bands` scale and offset; nodata is 0. |
| State boundary | Clip the box to Uttarakhand | geoBoundaries IND ADM1, or DataMeet state boundaries (GeoJSON) | None | Match the name "Uttarakhand" (older files: "Uttaranchal"). |
| Pyronear YOLO11s smoke model | Camera node | `https://huggingface.co/pyronear/yolo11s_colorful-chameleon_v3.0.0` | Apache-2.0 | The model card runs it at image size 1024, confidence 0.25. ONNX/NCNN runtimes are available through Pyronear's pyro-engine. |
| D-Fire dataset | Photo model | `https://github.com/gaiasd/DFireDataset` | Free | 21,527 images, YOLO format, class 0 = smoke, 1 = fire, 9,838 hard negatives (sunsets, glare, smoke-like cloud). |
| Pyro-SDIS / Pyro-SDIS-FINAL | Optional camera-model fine-tune | `https://huggingface.co/datasets/pyronear/pyro-sdis`; curated: `https://huggingface.co/datasets/copelandlaris/pyro-sdis-FINAL` | Apache-2.0 | 33,636 images; the curated version has 29,537 train and 4,099 val images, single class "smoke". |
| Telegram Bot API | Dispatch and field bot | Create a bot with @BotFather | Free | Needs the bot token and the staff group's chat id. |

**WorldCover classes:**

| Code | Class |
| --- | --- |
| 10 | Tree cover |
| 20 | Shrubland |
| 30 | Grassland |
| 40 | Cropland |
| 50 | Built-up |
| 60 | Bare / sparse vegetation |
| 70 | Snow and ice |
| 80 | Permanent water |
| 90 | Herbaceous wetland |
| 95 | Mangroves |
| 100 | Moss and lichen |

---

## 8. File formats

| File | Columns or content | Notes |
| --- | --- | --- |
| `data/win_a.csv`, `data/win_b.csv`, `data/hist.csv` | FIRMS VIIRS CSV as downloaded | Columns used: `latitude`, `longitude`, `scan`, `track`, `acq_date`, `acq_time`, `confidence`, `frp`, `satellite`, `daynight` |
| `data/*_uk.csv` | Same, clipped to Uttarakhand | |
| `data/villages.csv` | `name`, `lat`, `lon` | From Overpass; a missing name becomes "unnamed" |
| `data/cells.csv` | `cy`, `cx`, `n` | `cy` = floor(lat / 0.005), `cx` = floor(lon / 0.005), roughly 500 m cells; `n` = detections from 2023-01-01 to 2025-10-31 |
| `burns.csv` | `id`, `lat`, `lon`, `r_km`, `start`, `end`, `note` | `start` and `end` in UTC, "YYYY-MM-DD HH:MM". Read fresh on every scoring pass so new entries apply immediately. |
| `data/outcomes.csv` | `id`, `src`, `result`, `ts` | `src` = node id or "field". `result` is one of `smoke`, `nosmoke`, `fire`, `none`, `farm`, `burn`. `ts` = Unix seconds. Append-only; the latest row per id wins. |
| `data/scored.csv` | FIRMS columns + `t`, `id`, `seen`, `p`, `r`, `tier`, `why` | Replay output |
| `data/live.csv` | Same schema as a FIRMS CSV | One or a few hand-injected rows for the live demo |
| `data/live_scored.csv` | Same as `scored.csv` | Rewritten every 10 s by the live loop |
| `data/cap_<id>.xml` | CAP 1.2 alert | One per DISPATCH push |
| `data/labels.csv` | `id`, `label`, `labeller`, `dnbr`, `note` | `label` is one of `forest_fire`, `outside_forest`, `recurring_source`, `unclear` |

### 8.1 FIRMS column meanings

| Column | Meaning |
| --- | --- |
| `scan`, `track` | Pixel size in km along the scan (roughly east–west) and along the track (roughly north–south) |
| `acq_time` | HHMM in UTC; leading zeros may be missing (e.g. 754) |
| `confidence` | VIIRS gives `l`, `n` or `h`. Archive files may spell these out, so treat anything starting with "h" as high. |
| `frp` | Fire radiative power, in MW |

---

## 9. Conventions

- **Time:**
  - All times are UTC internally.
  - Build the alert time from `acq_date` plus `acq_time`, zero-padded to four digits.
  - Show IST only in user-facing text, if at all.
- **Alert id:** `<acq_date>_<HHMM>_<lat rounded to 4 dp>_<lon rounded to 4 dp>`. It must be stable across reruns.
- **Distances:** haversine, in km.
- **Bearing:** initial great-circle bearing from the camera node to the alert, in degrees clockwise from north.
- **Config:** every threshold in section 10 lives in the config module, not scattered through the code.
- **Logging:** every script prints row counts or tier counts when it finishes.

---

## 10. Verification and scoring specification

### 10.1 Features per alert

| Feature | Definition |
| --- | --- |
| `veg`, `tree`, `farm` | Read WorldCover inside the alert's footprint: a rectangle centred on the alert, `scan` km wide and `track` km tall. Convert km to degrees: latitude = km / 111; longitude = km / (111 × cos(latitude)). Pick the tile from floor(lat / 3) × 3 and floor(lon / 3) × 3. `veg` = share of classes 10, 20 and 30; `tree` = share of 10; `farm` = share of 40 and 50. |
| `burn` | Id of the first register entry where start ≤ alert time ≤ end and distance ≤ `r_km`; otherwise none. |
| `recur` | `n` for the alert's 500 m cell in `cells.csv`; 0 if absent. |
| `seen` | Number of other alerts in the same input set within 1 km and 12 hours. |
| `village_km`, `village_name` | Haversine distance to the nearest OSM place node, and its name. |
| `slope` | Degrees, from the gradient of a 3×3 DEM window centred on the alert. Convert pixel size to metres, using cos(latitude) for the x direction. |
| `wind`, `rh` | Open-Meteo hourly values at the acquisition hour (UTC). Cache per 0.25° grid cell and date. |
| `image` | Latest outcome for this alert id in `outcomes.csv`, if any. |

### 10.2 Probability p (is it a real forest fire?)

Start at 0.5, apply every matching adjustment, then clip to the range 0 to 1.

| Condition | Change | Reason text example |
| --- | --- | --- |
| `veg` < 0.30 | −0.30 | "pixel only 9% vegetation" |
| `farm` > 0.50 | −0.30 | "pixel 62% farmland or built-up" |
| Inside a planned burn | −0.40 | "inside planned burn B-12" |
| `recur` ≥ 8 | −0.25 | "same cell fired 14 times since 2023" |
| `seen` > 0 | +0.15 × seen, at most +0.30 | "seen 3 times in 12 h" |
| High confidence | +0.10 | "high confidence" |
| `frp` ≥ 10 MW | +0.10 | "FRP 18 MW" |

Image outcomes are applied after clipping and override the sum:

| Outcome | Source | Effect on p |
| --- | --- | --- |
| `smoke` | Camera | p = max(p, 0.90) |
| `nosmoke` | Camera | p = max(0, p − 0.10) |
| `fire` | Field | p = 1.0 |
| `none`, `farm`, `burn` | Field | p = 0.05 |

When an outcome applies, put "image check: <outcome>" first in the reasons.

### 10.3 Risk r (how dangerous would it be? 0 to 7)

| Condition | Points |
| --- | --- |
| Nearest village under 2 km (under 5 km: +1 instead) | +2 |
| Slope over 20° | +1 |
| `tree` over 0.6 | +1 |
| Wind over 15 km/h | +1 |
| Humidity under 30% | +1 |
| `seen` ≥ 2 (an event of 3+ pixels, FSI's large-fire rule) | +1 |

Always append a context reason, e.g. "1.4 km from <village>, slope 27°, wind 18 km/h, RH 22%".

### 10.4 Tiers

| Tier | Rule | Action |
| --- | --- | --- |
| DISPATCH | p ≥ 0.9, or (p ≥ 0.6 and r ≥ 2) | Telegram message to the staff group, CAP XML written |
| VERIFY | Otherwise, p ≥ 0.35 | Nearest camera node pans to it; staff asked for a photo |
| LOG | p < 0.35 | Dashboard only, no message |

### 10.5 Rules that do not change

- **Nothing is deleted.** LOG alerts stay visible.
- **Every alert has reasons.**
- **The weights are starting guesses:**
  - Tune them once on half of the labelled sample and report results on the other half.
  - After about 150 labels, replace them with logistic regression on the same features.
- **Risk keeps alerts visible.** An alert near a village keeps a high r even if p is modest.

### 10.6 Dispatch message format (plain text)

1. `<TIER>  p <p>  risk <r>`
2. Reasons joined with "; "
3. `Map: https://maps.google.com/?q=<lat>,<lon>` (5 decimal places)
4. `Alert <id>: share location, send a photo, then tap an outcome.`

---

## 11. Image components

### 11.1 Smoke models

| Model | Use | Settings |
| --- | --- | --- |
| Pyronear YOLO11s (pretrained, used as is) | Camera node, distant smoke plumes | Image size 1024, confidence 0.25. Confirmed only if smoke appears in 4 or more of 6 frames. |
| YOLO11n trained on D-Fire | Field photos, close-up smoke and flames | 640 px, about 30 epochs on a Colab T4; confidence 0.40; classes smoke and fire |
| Optional camera fine-tune | Fewer false alarms on local scenery | Pyro-SDIS-FINAL plus 200–500 of your own frames of cloud, fog, haze, dust and sun glare as negatives |

- **Pi export:** if inference runs on the Pi, export the models to NCNN.
- **Licence:** Ultralytics is AGPL-3.0. That is fine for a hackathon; check it before turning this into a product.

### 11.2 Camera node

**Hardware options**

| Option | Parts | Where inference runs |
| --- | --- | --- |
| A, recommended | Raspberry Pi 4 or 5, USB webcam (simplest with OpenCV) or Pi Camera Module 3, SG90 servo and pan bracket on GPIO 18, 5 V supply | Pi (NCNN) or laptop |
| B, cheapest | ESP32-CAM streaming MJPEG, SG90 servo on its own 5 V supply | Laptop |
| C, fallback | Old Android phone running an IP-camera app, no servo | Laptop |

**Config:** node id (e.g. `AG-01`), latitude, longitude, the compass heading the servo points at its centre position, and a range in km (10 for the demo).

**Behaviour:**

1. Every 5 seconds, ask the API for open alerts.
2. Skip any alert farther away than the node's range.
3. Compute the bearing from the node to the alert.
4. Convert it to a servo angle and turn:
   - Relative angle = ((bearing − heading + 540) mod 360) − 180.
   - Clamp it to ±90°, set the servo, then wait 2 seconds.
5. Grab 6 frames about 2 seconds apart, flushing buffered frames before each read.
6. Run the camera model on each frame and save an annotated snapshot whenever smoke is found.
7. Post the result: `smoke` if 4 or more frames contain a box, otherwise `nosmoke`.

**Notes:**

- **Servo:**
  - If it turns the wrong way, flip the sign of the relative angle.
  - An SG90 covers 180°, so one node sees half a circle.
  - Power it from its own 5 V supply.
  - Pi 5 software PWM can jitter; use a PCA9685 servo board if it does.
- **Camera hardware:**
  - The Pi Camera Module does not work through plain OpenCV capture on recent Pi OS; use Picamera2, or use a USB webcam.
  - ESP32-CAM streams at `http://<ip>:81/stream`. Control its servo through an HTTP endpoint on the board.
- **Demo setup:** set the node's configured location a few km from the injected demo alert so the pan means something, and say so in the pitch.

### 11.3 Field photo bot (Telegram)

1. A DISPATCH or VERIFY message lands in the staff group with a map link.
2. The staff member opens a private chat with the bot, shares their location, then sends a photo.
3. The bot runs the photo model and replies "Smoke or fire seen" or "No smoke or fire seen", then shows four buttons.
4. The staff member taps one button:

| Button | Saved as |
| --- | --- |
| Real forest fire | `fire` |
| Nothing found | `none` |
| Farm or village fire | `farm` |
| Our controlled burn | `burn` |

5. The backend finds the nearest non-LOG alert within 3 km of that user's last shared location and appends the outcome. If there is no such alert, the bot says so.

**Details:**

- **Location:** keep the last shared location per user in memory.
- **EXIF:** Telegram compresses photos and strips EXIF location, so always use the location share, never photo metadata.
- **Group privacy mode:** in group chats, bots only see commands unless privacy mode is turned off with @BotFather `/setprivacy`. A private chat avoids this.
- **Why these buttons:** they match Uttarakhand's own categories, so every reply is a training label.

### 11.4 Sentinel-2 burn-scar labeller

Use it to label alerts afterwards, not as a live signal. Sentinel-2 passes about every 5 days, and clouds block it.

1. **Pick scenes:** the least-cloudy scene (cloud under 20%) within 20 days before the alert, and the least-cloudy within 20 days after.
2. **Read bands:** in a ±0.002° box (about 400 m) around the alert, read `nir` and `swir22`.
   - Resample SWIR (20 m) to the NIR grid (10 m).
   - Reflectance = DN × scale + offset, from the asset's `raster:bands` metadata (default scale 0.0001, offset 0).
   - Treat 0 as nodata.
3. **NBR** = (NIR − SWIR2) / (NIR + SWIR2), averaged over the box.
4. **dNBR** = NBR before − NBR after.
   - 0.10 or more: likely burned (the usual low-severity cut-off).
   - Below 0.10: "no visible scar", which counts as unclear, not false.

Small ground fires under thick canopy often leave no visible scar. The labeller is a hint for human labellers, not the answer.

---

## 12. Interfaces

### 12.1 Camera node API (FastAPI on the laptop, port 8000)

| Endpoint | Input | Output |
| --- | --- | --- |
| `GET /todo?node=<id>` | Node id | Up to 10 alerts, each with `id`, `lat`, `lon`, drawn from replay and live scored alerts that are in DISPATCH or VERIFY and have no outcome yet |
| `POST /seen` | JSON body with `id`, `node`, `result` (`smoke` or `nosmoke`) | Appends a row to `data/outcomes.csv`; returns ok |

### 12.2 Telegram dispatch

- **What is sent:** a `sendMessage` to the staff group chat id with the text from section 10.6.
- **Which alerts:**
  - Only DISPATCH alerts are sent.
  - Each alert id is sent at most once.
  - In replay, send only the top 3 by p, to avoid flooding the group during the demo.

### 12.3 CAP 1.2 output (one XML file per DISPATCH push)

| Element | Value |
| --- | --- |
| `identifier` | `agni-<id>` (no spaces, commas, `<` or `&`) |
| `sender` | A project address, e.g. agnidrishti@example.org |
| `sent` | Current time with a numeric offset. CAP forbids "Z": write UTC as `-00:00`, or use IST `+05:30`. |
| `status` | `Exercise` (demo only; never `Actual`) |
| `msgType` | `Alert` |
| `scope` / `restriction` | `Restricted` / "Forest department field staff" |
| `info.category` | `Fire` |
| `info.event` | "Forest fire" |
| `info.urgency` / `severity` / `certainty` | `Immediate` / `Severe` / `Likely` |
| `info.headline` | "Likely forest fire, risk <r> of 7" |
| `info.description` | The reason text, XML-escaped |
| `info.area.areaDesc` | "Alert <id>" |
| `info.area.circle` | "<lat>,<lon> 1" (1 km radius) |

### 12.4 Dashboard (Streamlit + folium)

- **Counters:** alerts in, DISPATCH count, VERIFY count.
- **Map:**
  - Tier filter, defaulting to DISPATCH and VERIFY.
  - Markers coloured by tier: red DISPATCH, orange VERIFY, grey LOG.
  - Each marker's popup shows tier, p and reasons.
- **Table:** id, tier, p, r, reasons, sorted DISPATCH → VERIFY → LOG, then by p descending.
- **Planned-burn form:** latitude, longitude, radius in km, start and end in UTC, note. It appends to `burns.csv` with id `B<unix time>`.
- **Data:** reads replay and live scored alerts together.

---

## 13. Live demo flow

1. **Before going on stage:**
   - Window A replay is scored and the dashboard is open.
   - The API, bot and camera node are running.
   - The node's configured location is a few km from the demo point.
   - A smoke video on a monitor (or incense, if the venue allows it) sits in front of the camera, in the direction of the demo point.
2. **Inject an alert:** write one row to `data/live.csv` near the node. Copy a real Window B row and change latitude, longitude, date and time.
3. **First scoring:** the live loop scores it within 10 s. With no image check yet, it lands in VERIFY.
4. **Camera check:** the node picks it up from `/todo`, turns to its bearing, sees smoke in 4 of 6 frames and posts `smoke`.
5. **Dispatch:** on the next live pass p ≥ 0.9, so the alert becomes DISPATCH. A Telegram message reaches the judges' phones and a CAP XML file is written.
6. **Field confirmation:** a teammate playing field staff shares a location near the alert, sends a photo and taps "Real forest fire". p becomes 1.0.
7. **Result on screen:** the dashboard shows the alert in red with every reason listed.

---

## 14. Validation and metrics

The headline claim: "AgniDrishti cut staff dispatches by X% while keeping Y of Z real forest fires in the top two tiers", measured on a hand-labelled sample. Never claim more than the sample shows.

1. **Sample:** 80 alerts, 40 from Window A and 40 from Window B. Draw roughly a third from each tier, so every tier gets checked.
2. **Label:** two people label each alert independently in Copernicus Browser (true colour and SWIR, before and after) together with WorldCover.
   - Labels: forest fire, outside forest, recurring source, unclear.
   - The dNBR value is a hint only.
3. **Agree:** resolve disagreements together, and report how often the two labellers agreed at first.
4. **Tune and test:** tune the weights once on half the sample, and report metrics on the other half.

| Metric | How | Slide wording |
| --- | --- | --- |
| Dispatch reduction | 1 − (DISPATCH count ÷ all alerts), over the full window | "Staff sent to X% fewer alerts" |
| Real fires kept | Labelled forest fires in DISPATCH or VERIFY ÷ all labelled forest fires | "Kept Y of Z real fires" |
| DISPATCH precision | Labelled forest fires in DISPATCH ÷ labelled DISPATCH alerts | "N of M dispatches were real" |
| Camera false alarms | Confirmations during 30 minutes of cloud, fog and haze clips | "0 false confirmations in 30 min" |
| Time to confirm | Alert injected → camera result → Telegram message | "Confirmed in N seconds" |

**Rough cross-check against Uttarakhand's numbers:**

- Compare the share of Window A that the land-cover check tags as outside forest with the department's 39%.
- FIRMS includes detections that FSI's forest mask already drops, so expect a higher share.
- Present this as a cross-check, not as accuracy.

---

## 15. Build plan

### 15.1 Roles

| Role | Owns | Modules |
| --- | --- | --- |
| Geo data | Data pulls, rasters, villages, history, Sentinel-2 helper | pull, prep, s2, data parts of check |
| Scoring | Features, scores, tiers, reasons, API, dispatch, live loop | check, score, api, send, live |
| Vision | Camera and photo models, thresholds, false-alarm test | model parts of node and bot |
| Hardware + bot | Camera node, servo, Telegram bot | node, bot |
| Product + pitch | Dashboard, labels, metrics, demo, slides | app |

With four people, merge Vision into Hardware + bot.

### 15.2 Phases (36 hours)

| Phase | Hours | Geo data | Scoring | Vision | Hardware + bot | Product + pitch |
| --- | --- | --- | --- | --- | --- | --- |
| Foundations | 0–8 | FIRMS pulls, tiles, villages, history | Features and score v1 | Pyronear model running; start D-Fire training | Camera stream, servo sweeps | Dashboard shell, labelling rules |
| End to end | 8–20 | Land-cover, slope and weather checks verified; Window B | Tiers, reasons, outcomes, API, send | Node loop; photo model in bot | Pan to bearing; bot photo + buttons | Label the first 40 alerts |
| Prove it | 20–32 | Sentinel-2 helper for labellers | Tune weights on half the labels | False-alarm test on cloud and fog clips | Node and bot wired to the API; live loop | Finish labels; metrics slide; demo script |
| Freeze | 32–36 | Freeze data | Final scores | Lock thresholds | Mount, cables, spare power | Three rehearsals, backup video |

### 15.3 Gates (acceptance checklists)

**Gate 1, hour 8: one alert scored end to end**

- [ ] Window A pulled and clipped, row count printed
- [ ] WorldCover tiles, DEM tiles, villages and history cells ready
- [ ] One alert has every feature plus p, r, tier and reasons
- [ ] Full Window A scored to `data/scored.csv`, tier counts printed
- [ ] Camera streams to the laptop; servo sweeps on command
- [ ] Dashboard map shows scored alerts
- [ ] Pyronear model detects smoke on a test clip

**Gate 2, hour 20: full replay plus live camera confirmation**

- [ ] Windows A and B scored
- [ ] API answers `/todo` and accepts `/seen`
- [ ] Node pans to an injected alert and posts `smoke` for a smoke clip
- [ ] Live loop flips that alert to DISPATCH and pushes Telegram plus CAP
- [ ] Bot saves a field outcome and the alert updates on the next pass
- [ ] A burn registered in the form pushes an alert in its zone down to LOG
- [ ] 80 alerts sampled; at least 40 labelled

**Gate 3, hour 32: code freeze**

- [ ] All 80 alerts labelled by two people; first-pass agreement recorded
- [ ] Weights tuned on half; metrics computed on the other half
- [ ] Camera false-alarm test done (30 minutes of cloud, fog and haze)
- [ ] End-to-end latency measured
- [ ] Demo rehearsed three times; backup video recorded; slides final

---

## 16. Before day one

- [ ] Read the event rules: is pre-written code allowed? Data downloads and accounts usually are.
- [ ] Get a FIRMS MAP_KEY.
- [ ] Create the Telegram bot with @BotFather and a test "Range staff" group; note the group chat id.
- [ ] Download the 6 WorldCover tiles, the 20 DEM tiles, OSM villages and the state boundary.
- [ ] Pull FIRMS Window A, Window B and history to CSV (check data availability first).
- [ ] Download Pyronear's smoke model; start D-Fire training on Colab if the rules allow.
- [ ] Get hardware: Pi or ESP32-CAM, USB webcam, SG90 servo and pan bracket, 5 V supplies, tripod, extension cord.
- [ ] Collect 10 smoke clips and 10 cloud, fog and haze clips for the false-alarm test.
- [ ] Print an A3 hillside backdrop for the camera demo.
- [ ] Draft five slides using the numbers in section 2.
- [ ] Contact one forest division office or a forestry faculty member (questions in section 22).

---

## 17. Demo script (5 minutes) and Q&A

| Time | On screen | Say |
| --- | --- | --- |
| 0:00–0:30 | The Uttarakhand table from section 2.1 | "1,957 alerts in three winter months. 132 were real forest fires." |
| 0:30–1:00 | One slide: FSI alerts, Pench and Similipal cameras, Parliament's 12.5% | "Detection exists. Trust doesn't. Parliament asked for alerts to be prioritised." |
| 1:00–2:15 | Dashboard replay of Window A, toggling LOG on and off | Read two or three reasons aloud: farmland pixel, planned burn, recurring cell. |
| 2:15–3:30 | Inject an alert; the servo turns; smoke video; a judge's phone buzzes; open the CAP XML | "Before a single person moves, the camera has looked." |
| 3:30–4:15 | Teammate sends a photo and location and taps "Real forest fire"; the alert turns confirmed | "Every reply is a label, in the same categories Uttarakhand reports." |
| 4:15–5:00 | Metrics slide, then the ask | "One forest division, one season, their FSI feed, our filter." |

| Likely question | Answer |
| --- | --- |
| How is this different from FSI's system? | FSI detects; we decide which alerts deserve a person. FSI's alerts are our input. |
| Doesn't Uttarakhand's Forest Fire App do this? | It tracks staff and vehicles and categorises alerts. The January 2026 numbers show filtering before dispatch is still missing. We would feed it. |
| What if you filter out a real fire? | Nothing is deleted: LOG stays visible, risk near villages keeps alerts up, and we report how many labelled fires we kept. |
| Where is your ground truth? | 80 hand-labelled alerts checked against Sentinel-2. In a pilot, field labels arrive through the bot buttons. |
| Why not just more cameras? | Pench covers 350 sq km with one tower camera. We make every alert from any source worth a person's time. |
| What does it cost? | Software on public data; cameras are optional. |

---

## 18. Risks, fallbacks and safety

| Risk | Fallback |
| --- | --- |
| FIRMS limit, key problem or venue internet fails | Pull every window before day one; replay from CSV |
| No official forest boundaries | WorldCover stands in; say so. FSI's own feed already applies its forest mask. |
| WorldCover dates from 2021 | Land cover is one signal among five; Dynamic World is a stretch goal |
| Smoke model fires on cloud, fog or haze | 4-of-6 frame rule, confidence threshold, your own negatives |
| Servo jitter on Pi 5 | PCA9685 servo board, or drop the pan and show a fixed camera |
| Telegram blocked on venue Wi-Fi | Phone hotspot; dashboard highlight as backup |
| Too few labels for strong claims | Report sample size and method; call results preliminary |
| Overclaiming | Say "replay of public FIRMS data", never "FSI's live alerts" |

**Safety:** no open flame indoors without the organisers' permission. Default to a smoke video on a monitor. If incense is allowed, keep water nearby and stay at least 2 m from cables and paper.

---

## 19. Implementation gotchas

**FIRMS data**

- `acq_time` drops leading zeros, so pad it to four digits.
- A bad key returns plain text, not CSV, so check that the response starts with `latitude`.
- Each call covers at most 5 days. Loop over the range and drop rows past the end date.
- The bounding box is not the state, so always clip to the polygon.

**Raster reads**

- Round WorldCover read windows to whole pixels.
- A footprint can rarely straddle a tile edge; reading one tile is acceptable for the MVP.
- DEM 3×3 windows at a tile edge are rare; skip or clamp them.

**APIs and messaging**

- Open-Meteo's archive lags a few days, and the API is rate-limited, so cache by 0.25° cell and date.
- Telegram strips photo EXIF, and group privacy mode hides messages from bots.

**Camera node**

- OpenCV buffers frames, so flush a few before each read or you will analyse stale frames.

**Sentinel-2**

- Apply scale and offset from asset metadata.
- SWIR is 20 m and NIR is 10 m, so resample before computing NBR.

**Satellites**

- S-NPP data delivery ends 1 November 2026, so live mode uses NOAA-20 and NOAA-21.

**CAP**

- `sent` needs a numeric offset; "Z" is not allowed.
- XML-escape the reason text.

**Repository hygiene**

- Keep secrets and `data/` out of git.

---

## 20. Code style and working agreements

- **Language:** Python 3.11 or newer.
- **Libraries:**
  - Data and geo: pandas, numpy, requests, rasterio, pyproj, shapely, scikit-learn, pystac-client.
  - Models and camera: ultralytics, opencv-python, huggingface_hub; gpiozero on the Pi.
  - Services and UI: python-telegram-bot (v20+, async), fastapi, uvicorn, streamlit, folium, streamlit-folium.
- **Code style:**
  - Human-style code: short plain variable names, minimal comments.
  - Small single-purpose files; no unnecessary classes or abstraction layers.
- **Config and secrets:**
  - One config module for constants and thresholds.
  - `.env` for `FIRMS_KEY`, `BOT_TOKEN`, `CHAT_ID`, `LAPTOP_IP`.
- **Storage:**
  - CSV files are the storage layer for the MVP; no database.
  - `outcomes.csv` is append-only.
- **Output and time:**
  - Every script prints counts when it finishes.
  - UTC internally.
- **Build discipline:**
  - Build in gate order and keep a working end-to-end path at all times.
  - Do not change scoring thresholds silently; change them in config and note why.

---

## 21. Open items to verify early

- **Copernicus DEM:** confirm the tile naming and that the Uttarakhand tiles exist by listing the bucket.
- **State boundary:** confirm the name property and value for Uttarakhand in the boundary file.
- **FIRMS coverage:** confirm `_SP` versus `_NRT` coverage for each window via `data_availability`.
- **Pyronear model:** confirm the weights filename after downloading the repository snapshot.
- **Sentinel-2 metadata:** confirm `raster:bands` scale and offset are present on the Collection 1 assets.
- **Venue:** confirm that Telegram works on the venue network, and whether incense is allowed.

---

## 22. Questions for a forest division

1. In peak season, how many FSI alerts reach one range per day?
2. How do you decide which alerts to visit first?
3. Do you record outcomes in FSI's feedback system? Could we see one season's log?
4. Would staff log controlled burns a day ahead if it removed those alerts?
5. Which channel do field staff actually read: SMS, WhatsApp, or the state app?
6. What would make you trust an alert that the system puts in LOG?

---

## 23. Sources

**Problem and evidence**

- Uttarakhand false-alert breakdown, January 2026 (ETV Bharat): https://www.etvbharat.com/en/state/uttarakhand-forest-department-claims-that-most-of-fsi-forest-fire-alert-false-enn26013007036
- Total of 1,957 alerts (feuxdeforet.fr): https://feuxdeforet.fr/en/2026/01/31/ces-alertes-satellite-qui-rendent-fous-les-pompiers-en-inde-quand-la-techno-crie-au-feu-a-tort/
- Parliamentary committee report summary (PRS): https://prsindia.org/policy/report-summaries/forest-fires-in-the-himalayan-region-its-adverse-effects-and-mitigation-measures
- Committee coverage, alert fatigue and geostationary satellite (Swarajya): https://swarajyamag.com/news-brief/parliamentary-panel-pushes-for-dedicated-satellite-to-track-himalayan-forest-fires
- Supreme Court on Uttarakhand funds and vacancies (Swarajya): https://swarajyamag.com/amp/story/news-brief%2Funutilised-funds-vacant-posts-supreme-court-comes-down-heavily-on-uttarakhand-government-over-forest-fires
- Supreme Court order, 15 May 2024: https://api.sci.gov.in/supremecourt/2017/6141/6141_2017_3_106_53250_Order_15-May-2024.pdf
- Over 95% of fires human-caused (Mongabay India): https://india.mongabay.com/2020/01/most-forest-fires-in-india-on-account-of-human-activity/

**Existing systems in India**

- FSI fire alert dashboard: https://fsiforestfire.gov.in/
- FSI focus areas (alert frequency, large fires, WMS/WFS): https://fsi.nic.in/focus-areas?pgID=focus-areas
- FSI near-real-time monitoring: https://fsiforestfire.gov.in/Home/NRTDetails
- Pench Tiger Reserve AI system (Down To Earth): https://www.downtoearth.org.in/science-technology/pench-tiger-reserve-in-maharashtra-launches-first-advanced-ai-system-for-forest-fire-detection
- Pench system details (PW Only IAS): https://pwonlyias.com/current-affairs/pench-tiger-reserve-launches-ai-system/
- Odisha AI cameras and drones, 2026 (The Hawk): https://www.thehawk.in/news/india/odisha-enhances-forest-fire-preparedness-with-ai-cameras-and-drones
- Odisha Similipal cameras and OFMS app (Odisha government press note): https://inpr.odisha.gov.in/sites/default/files/2025-02/News-Forest_20022025EEEE.pdf
- Uttarakhand Forest Fire App (ETV Bharat): https://www.etvbharat.com/en/!bharat/uttarakhand-ifos-officer-develops-apps-to-mitigate-forest-fires-enn25021804429
- DASH pilot in Nallamala (APNIC Foundation): https://apnic.foundation/blog/project-complete-dash-ai-and-iot-powered-data-driven-wildfire-detection-and-prediction-system/

**Satellite changes**

- NASA MODIS to VIIRS transition: https://ladsweb.modaps.eosdis.nasa.gov/learn/modis-to-viirs-transition/
- NASA Earthdata notice on S-NPP data delivery ending 1 November 2026: https://www.earthdata.nasa.gov/news?page=124

**Data, models and APIs**

- FIRMS Area API: https://firms.modaps.eosdis.nasa.gov/api/area/
- ESA WorldCover datasets: https://github.com/ESA-WorldCover/esa-worldcover-datasets
- Copernicus DEM on AWS: https://registry.opendata.aws/copernicus-dem/
- Earth Search STAC: https://earth-search.aws.element84.com/v1
- Pyronear YOLO11s smoke model: https://huggingface.co/pyronear/yolo11s_colorful-chameleon_v3.0.0
- Pyro-SDIS: https://huggingface.co/datasets/pyronear/pyro-sdis
- Pyro-SDIS-FINAL: https://huggingface.co/datasets/copelandlaris/pyro-sdis-FINAL
- D-Fire: https://github.com/gaiasd/DFireDataset
