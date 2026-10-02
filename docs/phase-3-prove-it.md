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

- [ ] All 80 alerts labelled by two people; first-pass agreement recorded. Product, Geo.
- [ ] Weights tuned on one half; metrics computed on the other. Scoring.
- [ ] Camera false-alarm test done (30 minutes of cloud, fog and haze). Vision.
- [ ] End-to-end latency measured. Hardware + bot.
- [ ] Metrics slide and demo script drafted with the final numbers. Product.
- [ ] Requirements pinned; `phase-3` tag pushed. Scoring.

---

## Completion report: Gate 3

> Fill this in, then push it with tag `phase-3` ([how](implementation-plan.md#documents-and-pushing)). This tag is the code freeze.

**Gate passed at:** hour __ (YYYY-MM-DD HH:MM IST) · **Filled by:** · **Commit:**

### Labelling

- Labellers:
- First-pass agreement: __ / 80 (__%)
- Disagreements (label pair → count):
- Final labels:

| Window | forest_fire | outside_forest | recurring_source | unclear |
| --- | --- | --- | --- | --- |
| A | | | | |
| B | | | | |

- dNBR hints: computed for __ / 80; __ of them ≥ 0.10

### Tuning (tune half only)

| Setting | Spec value | Tuned value | Why (the errors it fixed on the tune half) |
| --- | --- | --- | --- |
| | | | |

### Results on the test half

| | Spec weights | Tuned weights |
| --- | --- | --- |
| Real fires kept (Y of Z) | | |
| DISPATCH precision (N of M) | | |
| `unclear` alerts in DISPATCH | | |

Tier × final label, tuned weights, test half:

| | forest_fire | outside_forest | recurring_source | unclear |
| --- | --- | --- | --- | --- |
| DISPATCH | | | | |
| VERIFY | | | | |
| LOG | | | | |

### Full-window numbers

| Window | Alerts | DISPATCH | Dispatch reduction |
| --- | --- | --- | --- |
| A | | | |
| B | | | |
| A + B | | | |

Cross-check: Window A outside-forest share __% vs the department's 39%.

### Camera

- Source (camera at monitor / file) __, minutes __, checks __, false confirmations __, frames with a box __
- Smoke clips confirmed: __ / 10
- Locked values: confidence __, frames needed __ of 6

### Latency (3 runs)

| Run | Inject → VERIFY | → `smoke` posted | → DISPATCH | → Telegram |
| --- | --- | --- | --- | --- |
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| Median | | | | |

### Slide numbers (final wording)

- Staff sent to __% fewer alerts
- Kept __ of __ real fires
- __ of __ dispatches were real
- __ false confirmations in __ min
- Confirmed in __ seconds

### Known limitations (for Q&A)

- Sample size.
- WorldCover dates from 2021.
- dNBR is only a hint.
- This is a replay of public FIRMS data, not FSI's live alerts (§18).

### Changes to thresholds and spec

| What | From → To | Why | Who |
| --- | --- | --- | --- |
| | | | |

### Carry-overs (only demo-blocking items may cross the freeze)

| Item | Owner | Due hour |
| --- | --- | --- |
| | | |
