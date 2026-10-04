---
version: 1
slug: "web-index-html"
primary_target: "web/index.html"
related_targets: ["web/app.js","web/style.css","api.py"]
---

# Surface brief: alert dashboard

- **Scope:** `web/index.html`, the AgniDrishti dashboard served by FastAPI (`api.py`), with `web/app.js` and `web/style.css`.
- **Visitor mode:** Operate.
- **Audience:** a control-room officer at a laptop; also judges seeing it in the recorded demo.
- **Job:** triage satellite fire alerts.
  - See what to act on first: DISPATCH, then VERIFY, ordered by p.
  - Read why without clicking.
  - See where each alert sits on the terrain.
  - Register planned burns.
  - Watch live changes arrive.
- **Content:** about 10,300 replay alerts (public FIRMS data) plus live injected alerts. Each has p, r, tier, reasons, features, image and field outcomes, and a CAP file when sent.
- **Constraints:**
  - spec §12.4 functions;
  - nothing deleted, with LOG one toggle away;
  - UTC internally, IST on screen;
  - these four show up within about 5 s with no refresh: a new live alert, a camera result flipping VERIFY to DISPATCH, a field confirmation taking p to 1.0, and dispatch sent (Telegram plus CAP).
- **Must not:** hide the reasons behind clicks, show only a map, or look like generic SaaS analytics.
- **Memorable moment:** the injected alert lands in the margin queue, the leader line draws to its symbol, then the camera result turns it carmine and the dispatch mark appears.
- **Unresolved:** Hindi labels (a stretch goal).

## Direction contract

THESIS: The dashboard is a fire-alert sheet read like a Survey of India toposheet: alerts plotted on terrain, with the ranked queue set in the sheet's margin as its legend. It refuses both the neon command-centre map and the KPI-card dashboard.

OWN-WORLD: The ground is sheet paper.
- Contour brown carries rules and secondary ink.
- Vegetation-tint green is used for the land.
- Water blue carries links and focus.
- Tier symbols are flat toposheet colour, each with its own shape: DISPATCH carmine, VERIFY ochre, LOG slate grey.
- Figures are tabular; coordinates are in degrees, minutes and seconds.
- The boundary is a dash-dot line.
- No gradients and no glow.

STORY: The officer sees the top DISPATCH, reads its reasons in place, finds it on the terrain, and watches live changes land on the sheet.

FIRST VIEWPORT:
- **Top bar (title block):** name, data source, live clock in IST, counts by tier, tier and window filters, and "Register burn".
- **Left margin (about 34%):** the ranked queue with reasons inline.
- **Right:** the terrain sheet of Uttarakhand with plotted symbols and the state boundary.
- **Evidence panel:** docks at the lower right of the sheet, with a reason ledger (each reason and its effect on p), the lifecycle strip and a CAP link.

SIGNATURE MOVE: margin-to-map leader. Selecting or hovering a queue entry draws a fine carmine leader line from the entry to its plotted symbol, labelled with its coordinates, the way toposheet marginalia point into the map.

FORM: Toposheet (Impeccable's pick), position 1 on the ordered list; seed key 22b6a051.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
