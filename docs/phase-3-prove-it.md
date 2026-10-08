# Phase 3: Prove it (hours 20–32)

**Goal:** evidence for every number on the metrics slide, then a code freeze.
**Spec:** §10.5, §11.4, §14, §18.
**Exit:** pass Gate 3 (code freeze), then push the completion report with tag `phase-3`. The demo runs from that tag.

## Plan

### Tasks by role

| Role | Task | Done when |
| --- | --- | --- |
| Geo data | The `s2` dNBR helper (§11.4) fills the `dnbr` hint for all 80 sample alerts. Take scale and offset from each asset's `raster:bands`. Collection 1 uses an offset of −0.1, not the default 0 in §11.4 (Phase 0), and NBR changes if the offset is skipped. | 80 values, or a reason for each gap (cloud, no scene). |
| Geo data, Product | Finish labelling. Two people label all 80 independently, record first-pass agreement, then resolve the rest together. | A `final` row for each of the 80 ids. |
| Scoring | Tune once on the tune half, then compute metrics on the test half (procedure below). | Tables filled in the report. |
| Vision | Run the false-alarm test, then lock the thresholds. | 0 false confirmations, or the real number. |
| Hardware + bot | Harden `node`, `bot` and `live` so they survive network blips, and write down the restart commands. Measure latency 3 times (R7). | Median time from inject to Telegram recorded. |
| Product + pitch | Build the metrics slide with the final numbers, and draft the demo script in [phase-4-freeze-and-demo.md](phase-4-freeze-and-demo.md). | Ready for rehearsal 1. |
| Scoring | Freeze: run `pip freeze > requirements.txt` and produce the final `scored.csv`. | `phase-3` tag pushed. |

### Validation procedure (§14)

1. `data/sample.csv` already puts each alert in the tune half or the test half (Phase 2). Never move an alert between halves.
2. Each of the 80 alerts is labelled twice. First-pass agreement = ids where both labels match ÷ 80. Record it **before** resolving.
3. Resolve disagreements together and write one `final` row per id (see the labelling guide). Metrics use `final` labels only.
4. **Tune on the tune half only.** Look at forest fires that landed in LOG and at non-fires that landed in DISPATCH. Change at most 2–3 numbers in `config`, each with a reason. With about 40 alerts, any more knobs than that will fit noise.
5. Rescore with the tuned weights and compute the test-half metrics once. Don't go back to tuning after seeing them. If you do, say so on the slide.
6. Report test-half metrics for both the spec weights and the tuned weights.
7. Compute dispatch reduction over the full windows, not the sample.
8. Cross-check Window A's outside-forest share against the department's 39%. Present it as a cross-check, not as accuracy (§14).

| Metric | Formula | Slide wording |
| --- | --- | --- |
| Dispatch reduction | 1 − DISPATCH ÷ all alerts, full window | "Staff sent to X% fewer alerts" |
| Real fires kept | `forest_fire` in DISPATCH or VERIFY ÷ all `forest_fire`, test half | "Kept Y of Z real fires" |
| DISPATCH precision | `forest_fire` in DISPATCH ÷ DISPATCH alerts with a clear label, test half. Report `unclear` separately. | "N of M dispatches were real" |
| Camera false alarms | `smoke` results during ≥ 30 min of cloud, fog and haze | "0 false confirmations in 30 min" |
| Time to confirm | Inject → camera result → Telegram, median of 3 runs | "Confirmed in N seconds" |

Keep the numbers honest:

- `unclear` alerts count neither as fires nor as false alarms (§11.4).
- The sample is stratified by tier, so "Y of Z" describes the sample only. For a population estimate, weight each alert by its tier's count in the window ÷ its tier's count in the sample, and label the result as an estimate.
- When a denominator is small, use counts ("7 of 8") rather than percentages. Call the results preliminary and give the sample size (§18).

### False-alarm test (Vision)

- Feed the 30+ minutes of negative clips through the node's 6-frame check, back to back (about 150 checks). Pointing the camera at a monitor is more realistic; feeding the file directly is faster. Record which you used.
- Count the `smoke` results (false confirmations) and the frames with any box.
- Run the 10 smoke clips through the same check. This shows whether a stricter threshold has quietly stopped detecting smoke.
- If there are false confirmations, raise the confidence threshold, or fine-tune with your own negatives (§11.1, optional). Then re-run both sets and lock the final values in `config`.

## Gate 3 checklist (code freeze)

This is §15.3 Gate 3, minus the rehearsal items that moved to Gate 4 (R4).

- [x] All 80 alerts labelled; done as option B, not two people (see Labelling below). 7 Oct.
- [x] Weights tuned on one half; metrics computed on the other. Scoring. 8 Oct.
- [x] Camera false-alarm test done (30 minutes of cloud, fog and haze). Vision. 42.6 min; thresholds locked 6 Oct.
- [ ] End-to-end latency measured. Hardware + bot.
- [ ] Metrics slide and demo script drafted with the final numbers. Product.
- [ ] Requirements pinned; `phase-3` tag pushed. Scoring.

---

## Completion report: Gate 3

> Fill this in, then push it with tag `phase-3` ([how](implementation-plan.md#documents-and-pushing)). This tag is the code freeze.

**Gate passed at:** hour __ (YYYY-MM-DD HH:MM IST) · **Filled by:** · **Commit:**

### Labelling

- **Labellers (option B, chosen 7 Oct):** there was no second person, so §14's two independent labellers became the following.
  - Claude pre-labelled all 80 blind. It used only the before/after chips, the `dnbr` hint and the alert id, never the tier, p, reasons or landcover. Those are in `data/labels_claude.csv`, each with a note and a confidence: 31 high, 33 med, 16 low.
  - The user then checked every label, starting with the low-confidence ones.
- **First-pass agreement:** not measured, because there was only one human. Instead: **the user kept 80 of 80 AI pre-labels.** Slide wording: "AI pre-labels, every label human-verified".
- **Rule 1 reading:** an alert is `unclear` only when neither side has a usable image. The 12 alerts with a scene on one side only were labelled from that scene.
- **Final labels** (`final` rows in `data/labels.csv`):

| Window | forest_fire | outside_forest | recurring_source | unclear |
| --- | --- | --- | --- | --- |
| A | 15 | 14 | 0 | 11 |
| B | 16 | 13 | 0 | 11 |

- dNBR hints: computed for 68 / 80 by `python s2.py` on 6 Oct; 29 of them ≥ 0.10 (15 in Window A, 14 in Window B). The other 12 had no scene under 20% cloud within 20 days on one side. Values are in the `dnbr` column of `data/labels_template.csv`. Before and after chips (true colour and SWIR) are on the blind sheet `data/labelling/index.html`, which shows no tier, p or reasons.

### Tuning (tune half only)

The tune half has 42 alerts: 12 forest_fire, 13 outside_forest and 17 unclear. **The spec weights made no errors on it.** All 12 fires were in DISPATCH (7) or VERIFY (5), none in LOG, and all 13 outside-forest alerts were in LOG. So no change could fix an error. The one change below cuts workload instead, and it was chosen by the user on 8 Oct.

| Setting | Spec value | Tuned value | Why |
| --- | --- | --- | --- |
| `DISPATCH_P_RISKY` | 0.6 | 0.8 | 96% of alerts have r ≥ 2, so the risky rule meant "p ≥ 0.6". One repeat detection (p 0.65) was enough to dispatch, which sent 61% of all alerts. At 0.8, dispatch needs two repeats, or one repeat plus high confidence or FRP. Tune half: fires DISPATCH/VERIFY/LOG went from 7/5/0 to 5/7/0, and unclear dispatches fell from 7 to 4. No fire dropped to LOG. |

**Also tried on the tune half:** `DISPATCH_R` 3 and 4 had the same or a bigger cost to fires and cut fewer dispatches (41.1% and 47.7%, against 63.6%).

**Test half:** computed once, on 8 Oct, after the tuned value was fixed. Nothing was tuned after seeing it.

### Results on the test half

The test half has 38 alerts: 19 forest_fire, 14 outside_forest and 5 unclear.

| | Spec weights | Tuned weights |
| --- | --- | --- |
| Real fires kept (Y of Z) | 19 of 19 | 19 of 19 |
| Fires DISPATCH / VERIFY / LOG | 10 / 9 / 0 | 9 / 10 / 0 |
| DISPATCH precision (N of M) | 10 of 10 | 9 of 9 |
| `unclear` alerts in DISPATCH | 2 | 2 |

Tier × final label, tuned weights, test half:

| | forest_fire | outside_forest | recurring_source | unclear |
| --- | --- | --- | --- | --- |
| DISPATCH | 9 | 0 | 0 | 2 |
| VERIFY | 10 | 0 | 0 | 3 |
| LOG | 0 | 14 | 0 | 0 |

**What these numbers cover:**
- The sample was drawn as about a third from each tier, but LOG is only 6% of all alerts. So these counts describe the sample, not the population.
- "Real fires kept" counts DISPATCH and VERIFY together. Moving fires from DISPATCH to VERIFY doesn't change it, so the DISPATCH / VERIFY / LOG row is shown too.

### Full-window numbers

The table uses the tuned weights; spec values are in brackets. The rescored file is `data/scored.csv`. Features, p and r are unchanged; only 2,493 alerts moved, all from DISPATCH to VERIFY.

| Window | Alerts | DISPATCH | Dispatch reduction |
| --- | --- | --- | --- |
| A | 3,434 | 1,115 (1,919) | 67.5% (44.1%) |
| B | 6,880 | 2,636 (4,325) | 61.7% (37.1%) |
| A + B | 10,314 | 3,751 (6,244) | **63.6%** (39.5%) |

**Cross-check:** the land-cover check (`veg` < 0.30 or `farm` > 0.50) tags 283 of 3,434 Window A alerts as outside forest. That's 8.2%, against the department's 39%. The reason is in [phase-1-foundations.md](phase-1-foundations.md): the department splits alerts by Reserve Forest boundary, while WorldCover sees vegetation. Present this as a cross-check, not as accuracy.

### Camera

Run on 6 Oct with `python camtest.py`. Results are in `data/camtest.csv`, with per-frame confidences in `data/camtest_frames.csv`.

- **Source:** files fed directly, not a camera pointed at a monitor. Frames are 2 s apart in clip time, grouped into the node's 6-frame checks.
- **Footage:** 42.6 min of no-smoke clips (39 HPWREN before-ignition, 35 Wikimedia Commons cloud, fog and haze) and 10 HPWREN smoke clips.
- **Excluded clip:** `hpwren_20201208_FIRE_om-s-mobo-c_pre.mp4` is labelled before-ignition but shows a plainly visible plume from another fire, so it's scored separately as "visible smoke" (confirmed 3 of 3, which is correct).

| Setting | Smoke checks confirmed | Smoke clips caught | False confirmations (no-smoke footage) |
| --- | --- | --- | --- |
| conf 0.20, no guard (model card) | 25 / 29 | 9 / 10 | 10 in 182 checks |
| conf 0.30, no guard | 22 / 29 | 9 / 10 | 6 in 182 checks |
| **conf 0.30 + darkness guard (locked)** | **22 / 29** | **9 / 10** | **2 in 172 checks** (10 night checks given no verdict) |
| conf 0.40 + guard | 12 / 29 | — | 0 |

**What the false alarms were** (checked by eye):
- Night-time house lights (Franklin Fire camera, frame brightness about 21 of 255). No threshold fixed these; the darkness guard did.
- A hazy horizon (2019-10-06 camera).
- Jena at dusk (Commons).

**Locked values:**
- confidence 0.30;
- 4 of 6 frames;
- no verdict when a check's median brightness is under 30 (`DARK_LUMA`). The alert stays in VERIFY for a photo, and the node retries it after 10 min.

**Caveat:** the thresholds were chosen on the same clips they're scored on, with no held-out footage. On the slide, say "2 false confirmations in 43 minutes of test footage, at the chosen settings". Never say "0 false alarms".

### Latency (3 runs)

| Run | Inject → VERIFY | → `smoke` posted | → DISPATCH | → Telegram |
| --- | --- | --- | --- | --- |
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| Median | | | | |

### Slide numbers (final wording)

- Staff sent to 64% fewer alerts (10,314 alerts replayed, Nov 2025–Jan 2026 and Apr–May 2026)
- Kept 19 of 19 real fires (test half of a hand-checked sample; preliminary)
- 9 of 9 dispatches were real (test half; 2 more dispatches were `unclear` and are reported separately)
- 2 false confirmations in 43 min of test footage, at the chosen settings
- Confirmed in __ seconds (pending: needs 3 latency runs)

### Known limitations (for Q&A)

- Sample size: 38 test alerts. The sample is stratified by tier, so its counts describe the sample, not every alert.
- Labels are AI pre-labels checked by one person, not two independent labellers. No inter-rater agreement exists.
- `DISPATCH_P_RISKY` was raised to cut workload, not to fix an observed error. Both weight sets are reported.
- WorldCover dates from 2021.
- dNBR is only a hint.
- This is a replay of public FIRMS data, not FSI's live alerts (§18).

### Changes to thresholds and spec

| What | From → To | Why | Who |
| --- | --- | --- | --- |
| `DISPATCH_P_RISKY` (§10.4) | 0.6 → 0.8 | Spec weights dispatched 61% of alerts; see Tuning | User decision, Claude Code |
| Labelling (§14) | two independent labellers → AI pre-labels, every label checked by the user | No second labeller; deadline 9 Oct | User decision |

### Carry-overs (only demo-blocking items may cross the freeze)

| Item | Owner | Due hour |
| --- | --- | --- |
| | | |
