# Phase 4: Freeze and demo (hours 32–36)

**Goal:** the demo works three times in a row, and a backup video exists in case it fails on stage.
**Spec:** §13, §15.2 (Freeze row), §17, §18.
**Rule:** no code changes after the `phase-3` tag, except demo-blocking fixes. List each one in the report.
**Exit:** pass Gate 4 (demo-ready; added by this plan, R4), then push the completion report with tag `phase-4`.

## Plan

| Role | Task |
| --- | --- |
| Geo data | Freeze the data: copy `data/` (scored files, tiles, villages, cells, clips) to a USB stick or a second laptop. |
| Scoring | Produce the final `scored.csv` from the frozen weights, and confirm `live` and `api` run from the `phase-3` tag. |
| Vision | Confirm the node runs the locked thresholds. |
| Hardware + bot | Mount the camera on the tripod facing the monitor and tape down the cables. Pack the spare SG90, spare power and a power bank. Have the hotspot ready. |
| Product + pitch | Run three timed rehearsals with the runbook below and record the backup video. Finalise the slides, prepare the Q&A (§17) and write the root `README.md`. |

The root `README.md` is for judges and anyone who opens the repo. It should cover:

- what AgniDrishti is (§1);
- how to run it (the startup steps below);
- the results, copied from the Gate 3 report;
- the limitations;
- the licences: Ultralytics is AGPL-3.0 (§11.1), and the Pyronear model and Pyro-SDIS are Apache-2.0. List the data sources from §7 as well.

## Demo runbook

This is a draft. Replace the suggested commands with the real ones during rehearsal 1.

### T−30 minutes

1. **Network.** Put the laptop, the Pi and the phones on one network. Use the hotspot if the venue Wi-Fi blocks Telegram or isolates clients. Check: the Pi can open `http://<LAPTOP_IP>:8000/docs`.
2. **Reset the demo state by renaming files, not deleting them.**
   - Move `data/outcomes.csv`, `data/live_scored.csv` and the rehearsal `data/cap_*.xml` files into `data/rehearsal-<n>/`.
   - Cut `data/live.csv` back to its header.
   - Restore the clean register with `git checkout burns.csv`.

   Without this reset, the demo alert's id already has an outcome and a CAP file. `/todo` would skip it and `send` wouldn't push it.
3. **Start the services in this order**, one terminal each (suggested commands):
   1. `uvicorn api:app --host 0.0.0.0 --port 8000`. This serves both the camera API and the dashboard at http://localhost:8000.
   2. `python live.py`
   3. `python bot.py`
   4. `python node.py`, with the phone camera stream as `CAMERA_SOURCE`.
4. **Dashboard:** open http://localhost:8000 with the tier filter on DISPATCH + VERIFY. Live changes appear by themselves; nothing needs refreshing.
5. **Camera:** have the smoke video ready on the monitor, in the direction of the demo point (§13).
6. **Phones:**
   - Judges join "Range staff" through the invite-link QR code on the slides.
   - A teammate's phone is mirrored on screen as a backup.
   - The field teammate shares the demo point with the bot now, as a selected location. The bot keeps the last location, so on stage they only need to send the photo and tap.
7. **Demo row:** have it ready in `demo_row.csv`. It must follow the demo-point rule from Phase 2, with today's date and a time just before your slot.
8. **Backup video:** open it on the desktop.

### On stage (§17)

| Time | Operator does | Expected |
| --- | --- | --- |
| 0:00–1:00 | Slides | |
| 1:00–2:15 | Toggle LOG on and off in the dashboard; read 2–3 reasons aloud | Farmland pixel, planned burn, recurring cell |
| 2:15 | Append `demo_row.csv` to `data/live.csv` | VERIFY within 10 s |
| 2:15–3:30 | Open `data/cap_<id>.xml` in the browser once it appears | The servo turns, the node posts `smoke`, the alert goes DISPATCH and the judges' phones buzz |
| 3:30–4:15 | The field teammate sends a photo and taps "Real forest fire" | Within about 13 s, the dashboard's live strip announces the field report, and the alert shows p 1.0 with "Field: real forest fire" |
| 4:15–5:00 | Metrics slide, then the ask | |

### If something fails on stage (§18)

| Symptom | Do this |
| --- | --- |
| Telegram message doesn't arrive | Switch to the hotspot. If still nothing, show the dashboard turning red and open the CAP file. |
| Servo jitters or doesn't move | Say "fixed camera" and aim the camera by hand. The node still checks and posts. |
| No `smoke` within 30 s | Switch to the backup video and narrate over it. Never post an outcome by hand. |
| The Pi can't reach the laptop | Use the hotspot. If that fails, run `node` on the laptop with the USB webcam. |
| Anything else | Backup video. |

**Safety (§18):** no open flame indoors without the organisers' permission. If incense is allowed, keep water nearby and stay at least 2 m from cables and paper.

## Gate 4 checklist (demo-ready)

- [ ] Three full rehearsals with this runbook, each under 5:00. Product + pitch.
- [ ] Backup video of a full successful run, saved on two devices. Product + pitch.
- [ ] Slides final, with numbers that match the Gate 3 report exactly. Product + pitch.
- [ ] Data frozen and copied. Geo data.
- [ ] Demo runs from the `phase-3` tag plus the listed fixes; thresholds locked. Scoring, Vision.
- [ ] Camera mounted, cables taped, spares packed. Hardware + bot.
- [ ] Root `README.md` written. Product + pitch.

---

## Completion report: Gate 4

> Fill this in, then push it with tag `phase-4` ([how](implementation-plan.md#documents-and-pushing)). After the event, add the judges' feedback and push again.

**Demo-ready at:** hour __ (YYYY-MM-DD HH:MM IST) · **Filled by:** · **Commit:**

### Rehearsals

| # | Start (IST) | Duration | Inject → Telegram (s) | What went wrong | Fix |
| --- | --- | --- | --- | --- | --- |
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

### Backup video

File, length, and the two places it's stored:

### Final slide numbers (must match the Gate 3 report)

- Staff sent to __% fewer alerts
- Kept __ of __ real fires
- __ of __ dispatches were real
- __ false confirmations in __ min
- Confirmed in __ seconds

### Changes after the freeze

| Change | Why it was demo-blocking | Commit |
| --- | --- | --- |
| | | |

### Data snapshot

Location, files and sizes:

### After the event

- Judges' feedback:
- Contacts made (forest division, faculty):
- Next steps, from the backlog in [implementation-plan.md](implementation-plan.md#after-the-event):
