# Phase 2: End to end (hours 8–20)

**Goal:**

- both replay windows scored;
- the live path working once: inject → VERIFY → camera smoke → DISPATCH → Telegram + CAP → field outcome;
- the burn register working;
- 80 alerts sampled, with at least 40 labelled.

**Spec:** §5, §10.2 image outcomes, §10.6, §11.2–§11.3, §12, §13.
**Exit:** pass Gate 2, then push the completion report with tag `phase-2`.

## Plan

### Tasks by role

**Geo data**

| Task | Done when |
| --- | --- |
| Hand-check land cover, slope and weather for 5 alerts against the WorldCover viewer, the terrain and Open-Meteo. | Table filled in the report. |
| Pull Window B (if not done in Phase 0) and clip it. | `data/win_b_uk.csv` written and its rows printed. |
| Score A and B together into `data/scored.csv`, with Scoring. | Tier counts printed per window. |
| If time allows, start `s2` (§11.4), moved up from Phase 3 (R5). | One alert returns a dNBR. |

**Scoring**

| Task | Done when |
| --- | --- |
| Image outcomes: read `data/outcomes.csv`, where the latest row per id wins. Apply the §10.2 overrides after clipping, and put "image check: <outcome>" first. | The self-check covers all four overrides. |
| `api` (FastAPI, port 8000, §12.1). `/todo` returns up to 10 DISPATCH or VERIFY alerts with no outcome, newest first (D3). `/seen` accepts only `smoke` or `nosmoke` for a known id, appends `id, src=<node>, result, ts`, and returns ok. Anything else gets a 4xx. | Both endpoints work from `http://localhost:8000/docs`. |
| `send`: §10.6 text, §12.3 CAP and Telegram `sendMessage`, for DISPATCH only and once per id (D4). In replay, pick the top 3 by p first, then skip ids already sent, so a second run sends nothing. | Run it twice: 3 messages, then 0. |
| `live` (owner per R3): every 10 s, rescore `data/live.csv` into `data/live_scored.csv` and push each new DISPATCH once. | An injected row appears within 10 s. |
| Live weather: recent alerts use the forecast API's current values (§7). A failed lookup scores no wind or RH points, adds "weather unavailable" and never stops the loop. | With the network off, the loop keeps scoring. |

**Vision**

| Task | Done when |
| --- | --- |
| Node check: 6 frames about 2 s apart, flushing before each. Run Pyronear at 1024 / 0.25 and save an annotated snapshot to `data/snaps/` when smoke is found. Return `smoke` if 4 or more of the 6 frames have a box. The model's only class is named `item`, so count boxes; don't filter on the name "smoke". | `smoke` on a smoke clip, `nosmoke` on a sky clip. |
| Make the frame source a config value: camera index, stream URL or video file. | The same code runs on the camera and on a clip. Phase 3's false-alarm test needs this. |
| Photo model in the bot: YOLO11n trained on D-Fire, conf 0.40. If training isn't finished, use the best checkpoint; failing that, the Pyronear model. | The bot replies to a test photo. |

**Hardware + bot** (wiring moved up from Phase 3, R2)

| Task | Done when |
| --- | --- |
| Node loop (§11.2):<br>1. Poll `/todo` every 5 s and skip alerts beyond range.<br>2. Compute the bearing, then relative angle = ((bearing − heading + 540) mod 360) − 180.<br>3. Apply the sign, clamp to ±90°, wait 2 s.<br>4. Run the check and `POST /seen`. | The node pans to an injected alert. |
| Network errors don't kill the loop: log, wait and retry. | Cut the laptop's network for 10 s; the node recovers. |
| Bot (§11.3), python-telegram-bot v20, private chat:<br>- remember each user's last location in memory;<br>- on a photo, run the model, reply, and show the 4 buttons;<br>- on a tap, find the nearest non-LOG alert within 3 km of that location, append `id, src=field, result, ts`, and confirm. If none is found, say so. | Run 3 below passes. |

**Product + pitch**

| Task | Done when |
| --- | --- |
| Dashboard per §12.4. **Built early on 3 Oct** as the FastAPI page (`api.py` plus `web/`). It polls `/api/live` every 3 s, so new alerts, tier flips, outcomes and sent markers appear with no refresh. | Its live markers behave correctly during Runs 2–4. |
| Planned-burn form (R6). **Built 3 Oct** into the dashboard (`POST /api/burns`). Clicking the map sets the centre, and the server rejects lat/lon outside the box, an `r_km` ≤ 0 or > 50, or an end ≤ start. | Run 4 passes. |
| Draw the 80-alert sample as described in [labelling-guide.md](labelling-guide.md): fixed seed, halves assigned before anyone labels. | `data/sample.csv` committed. |
| Label the first 40. Two labellers each, blind to tier. | 40 ids with two first-pass labels each. |

### Integration runs (in order; each one is a Gate 2 item)

**Run 1, replay.** Score A + B and check that the dashboard shows both. Run `send`: expect 3 Telegram messages and 3 `data/cap_<id>.xml` files. Run it again: expect nothing new.

**Run 2, live camera confirmation.**

1. Start `api`, `live`, `bot` and `app` on the laptop, and `node` on the Pi.
2. Pick the demo point (rule below) and append its row to `data/live.csv`.

Write down the clock time at each of these steps:

1. VERIFY appears in `data/live_scored.csv` and on the dashboard, within 10 s.
2. The node fetches the alert, pans to its bearing, grabs 6 frames of the smoke clip and posts `smoke`.
3. On the next `live` pass, p ≥ 0.9 → DISPATCH: the Telegram message reaches the group and `data/cap_<id>.xml` is written.

**Run 3, field outcome.**

1. A teammate opens a private chat with the bot and shares a location. Use "send selected location" and drop the pin on the alert: the phone's own GPS is at the venue, not in Uttarakhand.
2. They send a smoke photo and tap "Real forest fire".

Expect an outcome row with `src = field` and `result = fire`. On the next pass, p = 1.0 with "image check: fire" first.

**Run 4, burn register.** Inject a second row that follows the demo-point rule (p = 0.5). Then register a burn through the form that covers its location and the current time. On the next pass, p = 0.1 → LOG, with the reason "inside planned burn B…".

**Demo-point rule.** The injected row must reach the camera before it reaches DISPATCH. Copy a Window B row and change only lat, lon, date and time (§13). The row needs:

- confidence that isn't high (`n` or `l`), and FRP under 10 MW;
- a footprint that is mostly tree, shrub or grass (`veg` ≥ 0.30, `farm` ≤ 0.50);
- `recur` under 8, and no planned burn. `seen` is 0, because `live.csv` holds only this row.

That gives p = 0.5, which is VERIFY whatever r is, and then p = 0.9 → DISPATCH after `smoke`. The point must also be within 10 km of the node and within ±90° of its heading. No open replay alert may lie within the node's range (D3).

### Gotchas

- OpenCV buffers frames, so flush before each read (§19).
- Put the SG90 on its own 5 V supply, with its ground tied to the Pi's ground. If a Pi 5 jitters, use the PCA9685 (§18).
- Only `bot` polls Telegram. A second poller on the same token gets a 409 Conflict.
- Field users talk to the bot in private, because group privacy mode hides other messages (§11.3). Use the location share, never photo EXIF.
- CAP `sent` needs a numeric offset. Python's UTC isoformat gives `+00:00`, but CAP wants `-00:00` (or use `+05:30`). XML-escape the description, and keep `status` at `Exercise`.
- The Pi can reach the laptop only if all three hold:
  - `uvicorn` binds to `0.0.0.0`;
  - the laptop firewall allows port 8000;
  - the Wi-Fi doesn't isolate clients.

  If any of these fails, use a phone hotspot.
- Window B: limit `seen` to a 12 h time window and don't build an n×n matrix.

## Gate 2 checklist (§15.3)

- [x] Windows A and B scored. Scoring, Geo; tier counts per window.
- [x] API answers `/todo` and accepts `/seen`. Scoring; responses pasted from `/docs`.
- [x] Node pans to an injected alert and posts `smoke` for a smoke clip (no servo: the alert is checked inside the phone's field of view). Hardware + bot, Vision; Run 2 times and snapshot.
- [x] Live loop flips that alert to DISPATCH and pushes Telegram plus CAP. Scoring; message screenshot and CAP path.
- [ ] Bot saves a field outcome and the alert updates on the next pass. Hardware + bot; Run 3 rows.
- [x] A burn registered in the form pushes an alert in its zone down to LOG. Product, Scoring; Run 4 before and after.
- [ ] 80 alerts sampled; at least 40 labelled. Product; `sample.csv` and `labels_*.csv` counts.

---

## Completion report: Gate 2

> Fill this in, then push it with tag `phase-2` ([how](implementation-plan.md#documents-and-pushing)).

**Status (5 Oct 2026):**
- **Passed:** Runs 1, 2 and 4.
- **Open:** Run 3 (the field confirmation needs the team lead on Telegram) and labelling (two people needed).

Tag `phase-2` waits for both. Code: `api.py` (`/todo`, `/seen`), `send.py`, `live.py`, `node.py`, `bot.py` and `store.record`. All commits are local only, by the team lead's choice.

### Replay tiers

| Window | DISPATCH | VERIFY | LOG | Total |
| --- | --- | --- | --- | --- |
| A (S-NPP) | 1,919 | 1,243 | 272 | 3,434 |
| B (NOAA-20) | 4,325 | 2,222 | 333 | 6,880 |

### Hand-check of 5 alerts

Not done yet (Geo data). Phase 0 and Phase 1 spot checks cover the same ground (land-cover landmarks, slopes and elevations), but this per-alert table is still owed.

| id | Land cover vs viewer | Slope plausible | Weather vs Open-Meteo | OK? |
| --- | --- | --- | --- | --- |
| | | | | |

### API and send

- **`/todo`:** returns up to 10 open DISPATCH/VERIFY alerts, newest first (D3). With no live alerts, the top entry is `2026-05-30_0734_30.7576_78.3548`.
- **`/seen` validation:** a result other than `smoke`/`nosmoke` gets 422; an unknown alert id gets 404; a node name like `../x` gets 422. None of these wrote an outcome.
- **Valid `/seen`:** posted by the camera node in Run 2, appending `2026-10-05_0628_30.0950_78.2000,AG-01,smoke,1791181743.581`.
- **Replay send:** run 1 sent 3 and wrote 3 CAP files (`cap_2026-05-27_0830_30.2509_78.7434.xml`, `…30.2732_79.3925`, `…30.3661_79.2938`); run 2 sent 0.

### Run 2 timeline

Camera: the node at 30.05°N 78.20°E facing north (field of view 60°, range 10 km), reading the HPWREN clip `smoke/hpwren_20160604_FIRE_rm-n-mobo-c_smoke.mp4` in place of the phone.

| Step | UTC time | Seconds since inject |
| --- | --- | --- |
| Row injected (`live.py --inject`): `2026-10-05_0628_30.0950_78.2000`, first pass p 0.5, risk 3 | 06:28:20 | 0 |
| VERIFY in `live_scored.csv` | next 10 s pass | ≤ 10 |
| Node took it from `/todo`: bearing 0°, inside the field of view, 5.0 km (no servo to move) | — | — |
| 6 frames done: **6 of 6** with smoke, annotated snapshots in `data/snaps/` | — | — |
| `smoke` posted | 06:29:03 | 43 |
| DISPATCH in `live_scored.csv`: p 0.9, "image check: smoke" first | next pass | ~50 |
| Telegram accepted (`sendMessage` ok) | 06:29:13 | 53 |
| CAP written: `data/cap_2026-10-05_0628_30.0950_78.2000.xml` | 06:29:13 | **53** |

CAP check:
- `sent` uses offset `-00:00` ☑
- `status` is Exercise ☑
- the description is escaped (`html.escape`) ☑
- the file parses as CAP 1.2 XML ☑

### Runs 3 and 4

- **Field outcome (Run 3):** pending. The bot is polling; the team lead sends a location near 30.0950, 78.2000, then a photo, then taps "Real forest fire".
- **Burn (Run 4), passed:**
  - Burn `B1791181874` (1 km round 29.94497, 78.25, from 05:31 to 11:31 UTC) was registered through `POST /api/burns`, the dashboard form's endpoint.
  - Alert `2026-10-05_0630_29.9450_78.2500` sits in Rajaji forest, 12.6 km from the camera, so outside its range and the camera couldn't override.
  - It went from **VERIFY p 0.5** to **LOG p 0.1** on the next pass, with "inside planned burn B1791181874" first.
  - An earlier attempt 15 km north landed on 51% farmland, so it was already LOG. The burn still took p from 0.2 to 0.0, but that didn't test a push down a tier.

### Labels so far

| Sampled | DISPATCH | VERIFY | LOG |
| --- | --- | --- | --- |
| Window A | 13 | 13 | 14 |
| Window B | 13 | 13 | 14 |

- **Seed:** 20261005.
- **Halves:** 42 tune and 38 test, fixed in `data/sample.csv` before labelling.
- **Labelling template:** `data/labels_template.csv`, in shuffled order with no tier.
- **Progress:** labelled by both, 0 / 80.

### Changes to thresholds and spec

| What | From → To | Why | Who |
| --- | --- | --- | --- |
| Thresholds and weights | none | Tuned in Phase 3 | — |
| Camera node (§11.2) | pan to the bearing → check only alerts within heading ± 30° and 10 km | Phone camera, no servo (decided 3 Oct) | Claude Code |
| Demo injection (§13) | hand-edited row → `python live.py --inject [km]`, which copies a nominal-confidence, low-FRP Window B row onto the camera's line of sight at the current time and warns unless the first pass is VERIFY | Makes the demo-point rule repeatable | Claude Code |
| Live FIRMS poll (§3.1) | always on → `python live.py --firms` | Off by default, so a real alert can't post to the group mid-demo | Claude Code |
| Bot callback data | trusted → only the four outcome values accepted | Telegram callback data comes from the client | Claude Code |

### Carry-overs

| Item | Owner | Due |
| --- | --- | --- |
| Run 3: field confirmation through the bot | Team lead | 5–6 Oct |
| Label 40+ alerts (two labellers, blind) | Product + pitch, Geo data | 6 Oct |
| Hand-check of 5 alerts | Geo data | 6 Oct |
| Run 2 with the real phone stream (`CAMERA_SOURCE=http://<phone-ip>:8080/video`) | Team lead | 6 Oct |
| Reset the demo state before rehearsals (runbook step 2), and remove the two test burns with `git checkout burns.csv` | Team lead | before Phase 4 |
