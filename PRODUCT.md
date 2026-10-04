# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

A FastAPI app (Python 3.11+) serves one custom HTML/CSS/JS dashboard page with a Leaflet map. Chosen by the team lead on 3 Oct 2026; it replaces the spec's Streamlit dashboard (§12.4 of `AgniDrishti_CONTEXT.md`). The same FastAPI app serves the camera-node endpoints (§12.1). Storage stays CSV files (`data/scored.csv`, `data/live_scored.csv`, `burns.csv`, `data/outcomes.csv`); there is no database.

## Users

Primary user: a forest department control-room officer at a laptop (division or range level). They triage satellite fire alerts before anyone is sent out:

- scan the ranked alert queue;
- read why each alert is ranked where it is;
- register the department's own planned burns;
- watch live alerts, and camera and field confirmations, arrive.

Other audiences don't use the dashboard directly. Field staff receive DISPATCH messages and send photos through the Telegram bot. Hackathon judges see the dashboard in a recorded 5-minute demo.

## Product Purpose

AgniDrishti checks every satellite fire alert before anyone is sent out, so staff only go to alerts that are likely to be real, dangerous forest fires. It does not detect fires. It scores existing alerts and sorts each into one of three tiers:

- **p**, 0–1: how likely the alert is a real forest fire;
- **r**, 0–7: how dangerous it would be.

The tiers are:

- **DISPATCH:** message field staff now.
- **VERIFY:** point a camera at it and ask for a photo first.
- **LOG:** keep it on the dashboard and send nothing.

Every alert carries plain-language reasons. Success means staff are sent to fewer alerts while the real forest fires stay in the top two tiers.

## Positioning

A verification and prioritisation layer between existing satellite alerts (NASA FIRMS now, FSI's feed later) and the state's dispatch app. It complements both and replaces neither. FSI detects; AgniDrishti decides which alerts deserve a person, and shows why.

## Operating Context

- **Input:** NASA FIRMS VIIRS alerts for Uttarakhand. Replay windows cover Nov 2025 – Jan 2026 (S-NPP) and Apr – May 2026 (NOAA-20); live mode uses NOAA-20 and NOAA-21.
- **Data checks per alert:** land cover in the satellite pixel, the planned-burn register, recurrence over 2023–2025, multi-pass agreement, distance to the nearest village, slope, wind and humidity.
- **Image checks:**
  - a phone camera node, which confirms smoke across 6 frames;
  - field staff photos with outcome buttons sent through the Telegram bot.
- **Outputs:** a Telegram message and a CAP 1.2 XML file for each DISPATCH alert, plus the dashboard.
- **Demo flow:**
  1. An injected live alert lands in VERIFY.
  2. The camera sees smoke.
  3. The alert turns DISPATCH, and a Telegram message is sent.
  4. A field confirmation brings it to p 1.0.
- **Deadline:** code and demo are submitted by 9 Oct 2026.

## Capabilities and Constraints

- **Terminology:** alert, tier (DISPATCH / VERIFY / LOG), p, r (risk 0–7), reasons ("why"), planned burn (register id `B<unix time>`), outcome (`smoke`, `nosmoke`, `fire`, `none`, `farm`, `burn`), image check, CAP.
- **Required dashboard functions (spec §12.4):**
  - counters for alerts in, DISPATCH and VERIFY;
  - a map with a tier filter defaulting to DISPATCH + VERIFY, tier-coloured markers (DISPATCH red, VERIFY orange, LOG grey), and popups showing tier, p and reasons;
  - a table of id, tier, p, r and reasons, sorted DISPATCH → VERIFY → LOG, then by p descending;
  - a planned-burn form (latitude, longitude, radius km, start and end in UTC, note) that appends to `burns.csv` with id `B<unix time>`;
  - replay and live alerts shown together.
- **Scale:** about 10,300 replay alerts, plus a few live ones.
- **Rules:**
  - times are UTC internally, IST only in user-facing text;
  - nothing is deleted, and LOG alerts stay visible;
  - thresholds live in `config.py`;
  - alert ids are stable: `<acq_date>_<HHMM>_<lat 4dp>_<lon 4dp>`.
- **Open:** Hindi labels are a stretch goal, not required.

## Brand Commitments

The name is AgniDrishti (Agni = fire, Drishti = sight). No logo, colours or other brand assets exist; the identity is designed from scratch.

## Evidence on Hand

- **Primary-source problem numbers:** ETV Bharat, 30 Jan 2026. From 1 Nov 2025 to 20 Jan 2026 there were **1,952** alerts in Uttarakhand: 132 real forest fires, 766 false, 754 outside forest and about 300 controlled burns. Use 1,952, not the secondary figure 1,957.
- **Replay data:** 10,314 scored alerts in `data/scored.csv`. Window A (S-NPP) has 3,434 and Window B (NOAA-20) has 6,880.
- **Models:**
  - Pyronear YOLO11s, the camera smoke model;
  - a D-Fire YOLO11n photo model with test mAP50 of 0.802 for smoke and 0.682 for fire.
- **Not yet available:**
  - validation metrics (the 80-alert labelled sample is Phase 3, 7 Oct);
  - field pilots, deployments or user testimonials.

  Never claim more than the sample shows. Say "replay of public FIRMS data", never "FSI's live alerts".
- **Current weights:** the spec's starting weights put 61% of replay alerts in DISPATCH; tuning happens in Phase 3. Don't present the current split as the product's result.

## Product Principles

1. Every alert explains itself. The reasons are the product, not a detail behind a click.
2. Nothing is deleted. LOG alerts stay one toggle away.
3. Risk keeps alerts visible. An alert near a village stays prominent even when p is modest.
4. Be honest about the evidence: name the data source and its limits on screen.
5. The officer's next action is obvious: DISPATCH first, then VERIFY.
