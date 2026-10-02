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
| Dashboard per §12.4: tier filter defaulting to DISPATCH + VERIFY, red/orange/grey markers, popups, a sorted table, and replay plus live data through `store`. A Refresh button is enough. | Screenshot saved. |
| Planned-burn form (R6): lat, lon, radius in km, start and end in UTC, and a note. It appends to `burns.csv` with id `B<unix time>`. Reject lat/lon outside the box, an `r_km` ≤ 0, or an end ≤ start. | Run 4 passes. |
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

- [ ] Windows A and B scored. Scoring, Geo; tier counts per window.
- [ ] API answers `/todo` and accepts `/seen`. Scoring; responses pasted from `/docs`.
- [ ] Node pans to an injected alert and posts `smoke` for a smoke clip. Hardware + bot, Vision; Run 2 times and snapshot.
- [ ] Live loop flips that alert to DISPATCH and pushes Telegram plus CAP. Scoring; message screenshot and CAP path.
- [ ] Bot saves a field outcome and the alert updates on the next pass. Hardware + bot; Run 3 rows.
- [ ] A burn registered in the form pushes an alert in its zone down to LOG. Product, Scoring; Run 4 before and after.
- [ ] 80 alerts sampled; at least 40 labelled. Product; `sample.csv` and `labels_*.csv` counts.

---

## Completion report: Gate 2

> Fill this in, then push it with tag `phase-2` ([how](implementation-plan.md#documents-and-pushing)).

**Gate passed at:** hour __ (YYYY-MM-DD HH:MM IST) · **Filled by:** · **Commit:**

### Replay tiers

| Window | DISPATCH | VERIFY | LOG | Total |
| --- | --- | --- | --- | --- |
| A | | | | |
| B | | | | |

### Hand-check of 5 alerts

| id | Land cover vs viewer | Slope plausible | Weather vs Open-Meteo | OK? |
| --- | --- | --- | --- | --- |
| | | | | |

### API and send

- `/todo` response (paste):
- `/seen` response and the row it appended:
- Replay send: ids sent __, CAP files __, second run sent __

### Run 2 timeline

| Step | UTC time | Seconds since inject |
| --- | --- | --- |
| Row injected | | 0 |
| VERIFY in `live_scored.csv` | | |
| Node fetched the alert | | |
| Servo at bearing (bearing __°, relative __°) | | |
| 6 frames done (__ of 6 with smoke) | | |
| `smoke` posted | | |
| DISPATCH in `live_scored.csv` | | |
| Telegram received | | |
| CAP written (path) | | |

CAP check: `sent` offset __ · `status` Exercise ☐ · description escaped ☐ · file opens in a browser ☐

### Runs 3 and 4

- Field outcome: nearest alert __ at __ km; row `id, src, result, ts`; p after __
- Burn: burn id __; alert __; p and tier before __ → after __

### Labels so far

| Sampled | DISPATCH | VERIFY | LOG |
| --- | --- | --- | --- |
| Window A | | | |
| Window B | | | |

Seed __. Labelled by both: __ / 80. First-pass agreement so far: __ / __.

### Changes to thresholds and spec

| What | From → To | Why | Who |
| --- | --- | --- | --- |
| | | | |

### Carry-overs

| Item | Owner | Due hour |
| --- | --- | --- |
| | | |
