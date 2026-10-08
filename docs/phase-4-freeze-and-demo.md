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
| Hardware + bot | Put the camera phone (IP Webcam) on a stand facing the monitor, with its charger plugged in. Tape down the cables. Pack a power bank. Have the hotspot ready. |
| Product + pitch | Run three timed rehearsals with the runbook below and record the backup video. Finalise the slides, prepare the Q&A (§17) and write the root `README.md`. |

The root `README.md` is for judges and anyone who opens the repo. It should cover:

- what AgniDrishti is (§1);
- how to run it (the startup steps below);
- the results, copied from the Gate 3 report;
- the limitations;
- the licences: Ultralytics is AGPL-3.0 (§11.1), and the Pyronear model and Pyro-SDIS are Apache-2.0. List the data sources from §7 as well.

## Demo runbook

Real commands as of 8 Oct. Correct anything that rehearsal 1 shows to be wrong. Run everything from `F:\PROJECTS\Agnidrishti` in PowerShell, after `.venv\Scripts\activate`.

### T−30 minutes

1. **Network.** Put the laptop and the camera phone on one network. Use the phone's hotspot if the venue Wi-Fi blocks Telegram or isolates devices.
   - Start the IP Webcam server on the phone and note the IP it shows.
   - Check that the laptop can read the stream. This should print `True`:

     ```powershell
     python -c "import cv2; ok, f = cv2.VideoCapture('http://<phone-ip>:8080/video').read(); print(ok)"
     ```
2. **Reset the demo state.** Do this before **every** rehearsal and before the real demo, and move files rather than delete them. Set `$n` to the rehearsal number:

   ```powershell
   $n = 1; $d = "data\rehearsal-$n"; New-Item -ItemType Directory -Force $d | Out-Null
   Move-Item data\outcomes.csv, data\live_scored.csv $d -ErrorAction SilentlyContinue
   Get-ChildItem data\cap_2026-10-*.xml | Move-Item -Destination $d
   Copy-Item data\live.csv $d; (Get-Content data\live.csv -TotalCount 1) | Set-Content data\live.csv -Encoding ascii
   git checkout burns.csv
   ```

   **Why each line matters:**
   - **CAP files:** the reset moves only the October CAP files, which are the live alerts. The three `cap_2026-05-27_*` replay files must stay, because a CAP file is what marks an alert as sent, and `send.py` would otherwise re-send them.
   - **`live.csv`:** cutting it back to its header stops old test alerts at the same spot from counting as repeat detections. Without that, the demo alert can jump straight to DISPATCH and skip the camera.
   - **`burns.csv`:** `git checkout` removes the two Gate 2 test burns.
3. **Start the services in this order**, one terminal each:
   1. `uvicorn api:app --host 0.0.0.0 --port 8000`. This serves both the camera API and the dashboard at http://localhost:8000.
   2. `python live.py`
   3. `python bot.py`. Only one copy may run per bot token.
   4. `$env:CAMERA_SOURCE="http://<phone-ip>:8080/video"; python node.py`. If the phone fails, use the clip file `data\clips\smoke\hpwren_20160604_FIRE_rm-n-mobo-c_smoke.mp4` as `CAMERA_SOURCE` instead.
4. **Dashboard:** open http://localhost:8000 with the tier filter on DISPATCH + VERIFY. Live changes appear by themselves; nothing needs refreshing.
5. **Camera:**
   - Play `data\clips\smoke\hpwren_20160604_FIRE_rm-n-mobo-c_smoke.mp4` full screen and on repeat, with the monitor bright.
   - Put the phone in landscape, 0.5–1 m from the screen.
   - The node faces north (`NODE_HEADING` 0). The demo alert is injected 5 km north of the node, at 30.0950, 78.2000.
6. **Phones:**
   - Judges join "Range staff" through the invite-link QR code on the slides.
   - A teammate's phone is mirrored on screen as a backup.
   - The field teammate shares the demo point with the bot now, as a selected location: 30.0950, 78.2000. The bot keeps the last location, so on stage they only need to send the photo and tap.
   - Use the photo that rehearsal showed the bot answers with "Smoke or fire seen": a close-up smoke photo, not a photo of the monitor.
7. **Demo alert:** nothing to prepare. `python live.py --inject 5` stamps the current time.
   - It should print `first pass p 0.5 ... VERIFY`.
   - A `WARNING: not VERIFY` means the reset was skipped.
8. **Backup video:** open it on the desktop.

### On stage (§17)

| Time | Operator does | Expected |
| --- | --- | --- |
| 0:00–1:00 | Slides | |
| 1:00–2:15 | Toggle LOG on and off in the dashboard; read 2–3 reasons aloud | Farmland pixel, planned burn, recurring cell |
| 2:15 | Run `python live.py --inject 5` | VERIFY within 10 s |
| 2:15–3:30 | Open `data/cap_<id>.xml` in the browser once it appears | The node checks 6 frames and posts `smoke`, the alert goes DISPATCH, and the judges' phones buzz (about 1 minute; Run 2 took 53 s) |
| 3:30–4:15 | The field teammate sends a photo and taps "Real forest fire" | Within about 13 s, the dashboard's live strip announces the field report, and the alert shows p 1.0 with "Field: real forest fire" |
| 4:15–5:00 | Metrics slide, then the ask | |

### If something fails on stage (§18)

| Symptom | Do this |
| --- | --- |
| Telegram message doesn't arrive | Switch to the hotspot. If still nothing, show the dashboard turning red and open the CAP file. |
| The phone stream drops (the node prints errors, or the alert sits in VERIFY) | Check that the phone is awake and that its IP hasn't changed, then restart `node.py`. If the phone is lost, restart `node.py` with the clip file as `CAMERA_SOURCE`. |
| No `smoke` within 60 s | Switch to the backup video and narrate over it. Never post an outcome by hand. |
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
