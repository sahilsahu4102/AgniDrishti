# AgniDrishti: Implementation Plan

The source of truth is [AgniDrishti_CONTEXT.md](../AgniDrishti_CONTEXT.md), and section numbers (§) in these docs point there. The spec says what to build. These docs add who builds it, when, how to check it, and what to record when each phase ends.

Like the spec, these docs contain no project code, because the event may restrict pre-written code (§4). They contain only download queries, shell and git commands, and acceptance checks.

## Phases

| Phase | When | Goal | Exit | Document |
| --- | --- | --- | --- | --- |
| 0 Before day one | Done by 3 Oct 2026 | Accounts, data, hardware and open questions sorted | Phase 0 checklist | [phase-0-before-day-one.md](phase-0-before-day-one.md) |
| 1 Foundations | 4 Oct | One alert scored end to end, then all of Window A | Gate 1 | [phase-1-foundations.md](phase-1-foundations.md) |
| 2 End to end | 5–6 Oct | Full replay plus one live camera confirmation | Gate 2 | [phase-2-end-to-end.md](phase-2-end-to-end.md) |
| 3 Prove it | 7 Oct | Labels, tuned weights, metrics, false-alarm test | Gate 3: code freeze | [phase-3-prove-it.md](phase-3-prove-it.md) |
| 4 Freeze and demo | 8–9 Oct | Rehearsals, recorded demo, README, slides; **submit by 9 Oct** | Gate 4: demo-ready | [phase-4-freeze-and-demo.md](phase-4-freeze-and-demo.md) |

**Changes decided on 3 Oct 2026** (details in the Phase 0 report):
- **Submission:** code and demo are submitted by 9 Oct 2026, and pre-written code is allowed. The "hours" in the phase docs map to the dates above.
- **Camera:** an Android phone is the camera (§11.2 option C). There is no Pi and no servo, so skip the servo tasks. The node checks only alerts inside the phone's field of view, and inference runs on the laptop.
- **Window B:** uses NOAA-20, because S-NPP had no data from 28 Apr to early June 2026.
- **Dashboard:** a custom page served by FastAPI (`api.py` plus `web/`) replaces the spec's Streamlit dashboard, which was the team lead's choice. Its visual direction is the "Toposheet" world, recorded in `PRODUCT.md` and `.impeccable/surfaces/web-index-html.md`. It updates itself every 3 s, so the four live demo moments need no refresh, and it already includes the planned-burn form.

Supporting document: [labelling-guide.md](labelling-guide.md), finished in Phase 1 and used in Phases 2–3.

There are no separate architecture, API or test-plan documents on purpose. The spec already covers them (§5, §6, §8, §12, §15.3), and copies would drift.

## Owners

| Role | Owner | Modules (§6) | Also owns |
| --- | --- | --- | --- |
| Geo data | | pull, prep, s2, data parts of check | Second labeller |
| Scoring | | config, geo, store, check, score, api, send, live | Hour-0 contracts, freeze |
| Vision | | model parts of node and bot | False-alarm test |
| Hardware + bot | | node, bot | Latency measurement |
| Product + pitch | | app | Labels, metrics, slides, runbook, README |

With four people, Vision merges into Hardware + bot (§15.1). The spec gives no owner for config, geo and store. They go to Scoring because everyone needs them at hour 0.

## Critical path

```
Phase 0 downloads
  └─> pull, prep ─> *_uk.csv, villages.csv, cells.csv
        └─> check + score  (+ config, geo, burns.csv, outcomes.csv) ─> data/scored.csv
              └─> store  (+ data/live_scored.csv, written by live every 10 s)
                    ├─> app ........................................... Gate 1
                    ├─> api ─> node ─> POST /seen ─> outcomes.csv ...... Gate 2
                    ├─> send ─> Telegram + CAP ........................ Gate 2
                    └─> bot ─> outcomes.csv ........................... Gate 2
sample.csv ─> two labellers ─> tune on one half ─> metrics on the other ... Gate 3
```

Some tracks don't wait for scoring until Phase 2: camera and servo, the Pyronear model, D-Fire training and the dashboard. Build the dashboard against a 5-row hand-made `data/scored.csv` (§8 columns) until the real file lands.

## Hour-0 contracts

Freeze these before anyone splits off. To change one, tell everyone and log it in the current phase report.

- File names and columns exactly as in §8.
- Alert id as in §9: `<acq_date>_<HHMM>_<lat 4 dp>_<lon 4 dp>`, with `acq_time` zero-padded.
- Every threshold and weight lives in `config` (§9, §10).
- API endpoints `GET /todo?node=<id>` and `POST /seen` (§12.1).
- Outcome values: `smoke`, `nosmoke`, `fire`, `none`, `farm`, `burn`.
- UTC everywhere. IST only in user-facing text.

## Where the spec disagrees with itself

§20 says to build in gate order. So where the phase table (§15.2) schedules work later than a gate (§15.3) needs it, this plan moves the work earlier.

| # | Conflict | This plan |
| --- | --- | --- |
| R1 | §15.2 puts tiers and reasons in Phase 2, but Gate 1 needs both. | Score v1 with tiers and reasons ships in Phase 1. Phase 2 adds image outcomes. |
| R2 | §15.2 wires the node and bot to the API, and builds the live loop, in Phase 3. Gate 2 tests all three. | Moved to Phase 2. Phase 3 hardware work becomes hardening and latency measurement. |
| R3 | §15.2 gives the live loop to Hardware + bot, but §15.1 gives `live` to Scoring. | Scoring owns `live`. |
| R4 | Gate 3 (hour 32) needs three rehearsals and a backup video, but §15.2 schedules them for hours 32–36. | Gate 3 becomes code freeze only. Rehearsals, backup video and final slides form a new Gate 4 at hour 36. |
| R5 | The Sentinel-2 helper is scheduled for Phase 3, but labelling starts in Phase 2. | Labelling doesn't wait, since dNBR is only a hint. Geo starts `s2` in Phase 2 if Window B is done early. |
| R6 | Gate 2 tests the planned-burn form, but no phase schedules it. | Product + pitch builds it in Phase 2. |
| R7 | Gate 3 needs end-to-end latency, but nobody owns it. | Hardware + bot owns it. |

## Open decisions

Settle these at hour 0 and record the answers in the Phase 1 report.

| # | Question | Why it matters | Recommendation |
| --- | --- | --- | --- |
| D1 | Do VERIFY alerts get a Telegram photo request? §11.3 says a VERIFY message lands in the group, but §12.2 sends only DISPATCH. | Replay has many VERIFY alerts, and the demo (§13) expects one message, at DISPATCH. | Send only DISPATCH. The bot already accepts outcomes for any non-LOG alert within 3 km, so VERIFY photos still work. |
| D2 | Does `seen` look 12 h both ways, or only back? (§10.1) | Looking both ways lets a replay alert count passes that came later, which live mode can't know. That flatters the replay metrics. | Count alerts from 12 h before up to the same time, inclusive, so neighbours in the same pass still count. |
| D3 | In what order does `/todo` return its 10 alerts? (§12.1) | Open replay alerts can fill all 10 slots, so the injected demo alert never reaches the node. | Newest first by `t`, which keeps the injected alert on top. Also place the node where no open replay alert lies within its range. |
| D4 | How does `live` know it already pushed an alert? (§6, "exactly once") | A restart must not resend. | Treat `data/cap_<id>.xml` as the marker, and write it only after Telegram returns ok. No extra file. |
| D5 | Labels live in git-ignored `data/`. | One dead laptop loses hours of labelling. | Already done: `.gitignore` uses `data/*` with `!data/labels*.csv` and `!data/sample.csv`, so both get committed. |

## Documents and pushing

Every phase document has two parts:

- **Plan:** tasks, owners and done-when checks.
- **Completion report:** filled in at the gate.

A phase is done when:

1. every exit item is ticked, or listed as a carry-over with an owner and a due hour;
2. the completion report is filled with evidence. That means pasted terminal output (row counts, tier counts, timings), not "works on my laptop". Screenshots go in `docs/img/phase-<N>-<what>.png`;
3. the report is committed, tagged and pushed:

```
git pull --rebase
git add -A
git status            # no .env; nothing from data/ except labels*.csv and sample.csv
git commit -m "Phase <N> complete: <gate>"
git tag -a phase-<N> -m "<gate> passed"
git push --follow-tags
```

Documents due at each exit:

| Exit | Pushed with it |
| --- | --- |
| Phase 0 (`phase-0`) | Phase 0 report: data manifest, FIRMS source choice, §21 answers |
| Gate 1 (`phase-1`) | Gate 1 report, D1–D5 answers, labelling guide v1 |
| Gate 2 (`phase-2`) | Gate 2 report, `data/sample.csv`, first 40 labels |
| Gate 3 (`phase-3`) | Gate 3 report with the validation results, all labels, pinned `requirements.txt`. This tag is the code freeze. |
| Gate 4 (`phase-4`) | Gate 4 report with the rehearsal log, root `README.md`, final slides link |

Rules:

- Never paste secrets into a doc. That covers the MAP_KEY, the bot token and the chat id.
- Change a threshold or weight only in `config`, with a one-line comment, and add a row to the current report's "Changes to thresholds and spec" table (§20).
- Between gates, commit small and often to `main`, and run `git pull --rebase` before pushing. A 36-hour event has no time for branches.
- The demo runs from the `phase-3` tag plus any listed demo-blocking fixes.

## Risks found while planning

These add to the risks in §18.

| Risk | Mitigation | Phase |
| --- | --- | --- |
| S-NPP data delivery ends 1 Nov 2026 (§2.2), and replay depends on S-NPP. | Pull Windows A and B and the history before that date. | 0 |
| The injected demo alert lands straight in DISPATCH or LOG and skips the camera. | Demo-point rule: the first-pass p must be exactly 0.5. | 2 |
| A tier flips on float noise: `0.5 + 0.1 + 0.3` evaluates to `0.8999999999999999`. | Round p to 2 dp before comparing it to a threshold. | 1 |
| The burn test fails, because an alert with p ≥ 0.75 stays above LOG after the −0.40. | Test the form with a p = 0.5 alert. | 2 |
| Window B is peak season and likely much bigger than A. | No n×n matrix for `seen`; one Open-Meteo request per 0.25° cell per window. | 1–2 |
| Two processes poll Telegram with one token (409 Conflict). | Only `bot` polls. `send` and `live` only call `sendMessage`. | 2 |
| Venue Wi-Fi blocks Telegram or isolates the Pi from the laptop. | Phone hotspot; test at T−30 min. | 4 |
| The weather API is down during the live demo. | A missing lookup scores no wind or RH points and says so in the reasons. It never stops scoring. | 2 |
| Judges aren't in the Telegram group. | Invite-link QR code on a slide; mirror a phone on screen as backup. | 4 |

## After the event

The stretch goals from §3.2. None of them starts before Gate 4.

| Item | Start when |
| --- | --- |
| Event clustering (one message per fire) | First post-event iteration |
| Learned weights (logistic regression) | 150+ labels exist (§10.5) |
| Season-wide Sentinel-2 labels | After clustering |
| Hindi messages; WhatsApp | A forest division confirms the channel staff read (§22 Q5) |
| FSI WMS/WFS feed instead of FIRMS | Access agreed |
| Second camera node for triangulation | The first node is proven in the field |
| Distance to roads; Dynamic World land cover | When labels show land cover or access is the weak signal |
