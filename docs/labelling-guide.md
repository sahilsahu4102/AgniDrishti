# Labelling guide

Version 0. Product + pitch turns it into v1 in Phase 1.

**Who:** two labellers per alert, working independently. Suggested pair: Product + pitch and Geo data.
**When:** the sample is drawn in Phase 2. Label 40 alerts by Gate 2 and all 80 by Gate 3.
**Spec:** §8 (`labels.csv`), §11.4, §14.
**Time budget:** 3–5 minutes per alert, so 4–7 hours per labeller for all 80.

## 1. Draw the sample (once, in Phase 2)

- Draw 80 alerts from the scored replay: 40 from Window A and 40 from Window B.
- Within each window, take about 13 DISPATCH, 13 VERIFY and 14 LOG alerts. If a tier is short, take all of it and fill from the other tiers.
- Use a fixed random seed and record it in the Gate 2 report.
- Before anyone labels, split each window × tier group in half and set `half` to `tune` or `test`.
- Save the result as `data/sample.csv` with the columns `id, window, tier, half, lat, lon, t`. Git keeps this file.
- Give the labellers only `id`, `lat`, `lon` and `t`. **Never** show them the tier, p, r or reasons, so the score can't steer the label.
- Leave out the 3 practice alerts you labelled together in Phase 1.

## 2. Tools

- [Copernicus Browser](https://browser.dataspace.copernicus.eu/): Sentinel-2 L2A images in true colour and in a SWIR view, from before and after the alert date.
- [ESA WorldCover viewer](https://viewer.esa-worldcover.org/worldcover/): what the footprint is made of.
- Google Maps or Google Earth satellite view: look for kilns, factories, dumps, fields and houses.
- The `dnbr` value from `s2` (Phase 3). It is only a hint:
  - 0.10 or more means likely burned.
  - Below 0.10 means "no visible scar". Label that `unclear`, not "no fire".

Look at the whole footprint (`scan` × `track` km, roughly 0.4–0.8 km), not just the dot.

## 3. Labels

Apply the rules from the top; the first one that matches wins.

| # | If | Label |
| --- | --- | --- |
| 1 | There is no usable cloud-free image before or after the alert | `unclear` |
| 2 | There is a fixed industrial or waste site at the spot: brick kiln, factory, dump or flare | `recurring_source` |
| 3 | The fire or scar is on cropland, or in a village or town | `outside_forest` |
| 4 | There is a fresh scar or smoke in tree cover, shrubland or grassland | `forest_fire` |
| 5 | None of the above is clearly visible | `unclear` |

- From space, a controlled burn looks like a forest fire. Label what you see (`forest_fire`) and write "possible controlled burn" in `note`.
- A field that is burnt every season is `outside_forest`. Use `recurring_source` only for fixed sites.
- Small ground fires under thick canopy often leave no scar (§11.4). When unsure, label `unclear` and add a note. Never guess.

## 4. Recording

- Each labeller fills their own `data/labels_<initials>.csv` with the §8 columns `id, label, labeller, dnbr, note`. Put your initials in `labeller` and leave `dnbr` blank until `s2` fills it.
- Don't open the other labeller's file, or discuss alerts, until you have both finished the batch.
- After each batch:
  1. Count first-pass agreement: ids with the same label ÷ ids labelled by both.
  2. Resolve the disagreements together.
  3. Rebuild `data/labels.csv` from both first-pass files, plus one row per resolved id with `labeller` set to `final`.
  4. Commit. `.gitignore` keeps `labels*.csv` and `sample.csv` in git.

## 5. How the labels are used

- `forest_fire` is the only positive class, and the metrics use `final` rows only.
- `unclear` is left out of both "real fires kept" and "DISPATCH precision", and is reported as a separate count.
- The tune half is used once, to adjust the weights. The test half is used only to report results (Phase 3).
