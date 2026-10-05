# Design

The AgniDrishti dashboard is a fire-alert sheet read like a Survey of India 1:50,000 toposheet. Alerts are plotted on terrain, and the ranked queue sits in the sheet's margin as its legend. Source of truth: `web/style.css` (tokens) and `web/app.js` (symbol styles and map colours, in `INK` and `STYLE`). Surface strategy: `.impeccable/surfaces/web-index-html.md`.

## Colour

| Token | Value | Job |
| --- | --- | --- |
| `--paper` | `#f6f8f3` | Map-paper ground: page, margin, panels |
| `--paper-2` / `--paper-3` | `#ebefe4` / `#dfe6d3` | Hover / selected row and pressed states |
| `--shell` | `#d4e4bc` | Forest-tint green: title block and filter band. This is the toposheet's signature colour |
| `--ink` | `#221c15` | Text, neatlines, the boundary, the selection ring |
| `--ink-2` | `#5a4a3a` | Contour-brown secondary text (7.4:1 on paper, 6.3:1 on the shell) |
| `--rule` | `#c2cab4` | Hairlines |
| `--contour` | `#8e5428` | Planned-burn circles |
| `--water` | `#2c67a0` | Links and the focus ring (5.1:1) |
| `--dispatch` | `#c21e2e` | DISPATCH symbol and text, and the leader line (5.2:1) |
| `--verify` / `--verify-ink` | `#c9741a` / `#8a4b0b` | VERIFY symbol stroke / VERIFY text (5.9:1) |
| `--log` / `--log-ink` | `#7c8083` / `#565a5c` | LOG symbol / LOG text (6.1:1) |

Rules:

- **Tier colour:** always flat and unmodulated. No gradients, glow or tinted halos.
- **Tiers never rely on colour alone.** Every tier also has a shape and its word: DISPATCH a filled triangle, VERIFY an open diamond, LOG a dot.
- **Terrain tiles** sit under `filter: saturate(.34) contrast(.8) brightness(1.1)` so the symbols lead.

## Type

- **Faces:** Noto Sans, self-hosted as a variable font (`web/fonts/`, weight 100–900, width 62.5–100%, real tabular figures). Ids and coordinates use the system monospace stack, as data.
- **Map labels** (tier words, group headers, ticks, chips) are condensed: `font-stretch: 75%` and letter-spacing 0.04–0.06em.
- **Scale:** 22 px title (750, 87.5% width); 16 px panel headings; 14 px body; 12–13 px rows and fields; 10.5–11.5 px labels.
- **Numbers:** always `font-variant-numeric: tabular-nums`. Indian digit grouping (`en-IN`).
- **Times:** IST on screen (`09 Nov 2025 12:27 IST`); UTC only as a secondary reading.
- **Coordinates:** degrees, minutes and seconds (`31°12′17″N`).

## Layout

- **Desktop:** title block, then filter band, then a two-column body.
  - Margin: `clamp(360px, 33vw, 520px)`.
  - Sheet: the rest.
- **The sheet:**
  - a frame inset 30/22/22/62 px, with a double neatline (1.5 px border plus a 1 px outline 6 px out);
  - graticule ticks outside it;
  - a dash-dot state boundary cased in paper.
- **Docked panels** (evidence, burn register) share the sheet's lower right: 372 px wide, a 1 px ink border, no shadow.
- **At 760 px and below:** one column. The margin is capped at `min(62vh, 640px)`, the frame at `min(62vh, 560px)`, the dock flows below the map, and the leader line hides.

## Components

- **Queue row:** symbol; place and distance; `p · risk`; the reasons inline (never hidden); a meta line with time, window and marks.
- **Group header:** sticky, a 1 px ink rule under it, with tier, count and gloss.
- **Marks:** small outlined capsules, reserved for live state:
  - `New` in water blue;
  - `VERIFY → DISPATCH` in carmine;
  - `Camera: smoke` in ochre;
  - `Field: …` in green;
  - `Sent` in ink, with a flag icon.

  A mark stays until the officer opens the alert.
- **Live strip:** an ink band at the top of the margin, holding the latest live event and a Show button.
- **p scale:** a toposheet scale bar from 0 to 1, in alternating ink and paper segments. Ticks mark VERIFY (0.35), 0.6 and DISPATCH (0.9); a tier-coloured pointer marks p.
- **Reason ledger:** the starting value, then each reason with its signed effect (minus sign `−`), then the total; an image override is a bold final line. Risk is listed the same way, with +1/+2 points.
- **Controls:** standard web controls only. Pill chips are checkboxes for the tiers; then a select, a search input, and buttons (outline by default, solid ink for submit). No modals: the burn register is a docked panel.

## Signature move and motion

- **Leader line:** selecting a queue entry draws a 1.25 px carmine line from the entry's right edge, elbowing to its plotted symbol, with a coordinate tag. Hover draws a dashed brown preview.
- **Motion:** the leader draw is the only authored motion (0.42 s, `cubic-bezier(.16, 1, .3, 1)`). Reduced motion turns it off.

## Not done in this run

The impeccable finish review has no verdict. Its first attempt asked for a valid phone capture, which was then made; the full re-review was interrupted by a usage limit and then stopped, and the team lead chose not to run review agents. `.impeccable/design.json` was not generated.
