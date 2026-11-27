---
name: Efecto Gondola
description: Data journalism page on how wholesale prices reach the shelf, region by region, with a one-month forecast and its range.
colors:
  tinta: "#1A1A1A"
  tinta-2: "#595752"
  papel: "#FAF9F6"
  papel-2: "#F2F0E9"
  filete: "#DFDDD5"
  contraste: "#6B7280"
  no-significativo: "#A8A59C"
  region-gba: "#0072B2"
  region-pampeana: "#009E73"
  region-noroeste: "#D55E00"
  region-noreste: "#CC79A7"
  region-cuyo: "#E69F00"
  region-patagonia: "#56B4E9"
typography:
  display:
    fontFamily: "Source Serif 4 Variable, ui-serif, Georgia, serif"
    fontSize: "3.25rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.02em"
  figure:
    fontFamily: "Source Serif 4 Variable, ui-serif, Georgia, serif"
    fontSize: "2.75rem"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.025em"
    fontFeature: "tnum"
  headline:
    fontFamily: "Source Serif 4 Variable, ui-serif, Georgia, serif"
    fontSize: "2rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  figure-secondary:
    fontFamily: "Source Serif 4 Variable, ui-serif, Georgia, serif"
    fontSize: "1.75rem"
    fontWeight: 500
    lineHeight: 1.25
    fontFeature: "tnum"
  title:
    fontFamily: "Source Serif 4 Variable, ui-serif, Georgia, serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.375
    letterSpacing: "-0.01em"
  reading:
    fontFamily: "Source Serif 4 Variable, ui-serif, Georgia, serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.625
  body:
    fontFamily: "Public Sans, ui-sans-serif, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "tnum"
  label:
    fontFamily: "Public Sans, ui-sans-serif, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.43
    fontFeature: "tnum"
  note:
    fontFamily: "Public Sans, ui-sans-serif, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.375
    fontFeature: "tnum"
  chart:
    fontFamily: "Public Sans, ui-sans-serif, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    fontFeature: "tnum"
rounded:
  none: "0px"
  sm: "2px"
spacing:
  gutter: "16px"
  gutter-md: "32px"
  cell: "16px"
  cell-md: "20px"
  block: "32px"
  section: "40px"
  section-md: "56px"
  column-gap: "48px"
components:
  strip-cell:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta}"
    typography: "{typography.figure}"
    padding: "20px"
  region-select:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta}"
    typography: "{typography.figure-secondary}"
    rounded: "{rounded.none}"
    padding: "4px 24px 4px 20px"
  region-select-hover:
    backgroundColor: "{colors.papel-2}"
  region-list-item:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta}"
    typography: "{typography.label}"
    padding: "8px"
  region-list-item-active:
    backgroundColor: "{colors.papel-2}"
    textColor: "{colors.tinta}"
  segmented-toggle:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "4px 12px"
  segmented-toggle-active:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.papel}"
  energia-badge:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta-2}"
    rounded: "{rounded.sm}"
    padding: "2px 6px"
  region-swatch:
    backgroundColor: "{colors.region-gba}"
    rounded: "{rounded.sm}"
    size: "12px"
---

# Design System: Efecto Gondola

## Overview

**Creative North Star: "The Newsroom Instrument"**

A single page that reads like a data journalism piece and works like a measuring instrument. Warm paper, black ink, hairline rules and a serif for the numbers that matter. There are no cards, no shadows and no hero: the page is a grid of ruled cells and long columns, and the map of the six IPC regions sits at the top and drives everything under it.

Color is rationed. Ink does the talking, including the forecast. The Okabe-Ito palette exists only to tell regions apart and never carries text. Two grays carry meaning instead of decoration: a slate for energia (regulated tariff, shown as contrast) and a pale warm gray for estimates that cannot be told apart from zero. Uncertainty is always drawn, never implied.

Density is moderate and editorial: measured text columns (60 to 65ch), tabular figures everywhere, and charts that share one set of axes, fonts and halos so they read as one system.

**Key Characteristics:**
- Paper and ink, flat, square corners (2px at most).
- 1px rules as the only structure: ink for major breaks, filete for minor ones.
- Serif for headings and big figures, sans for interface, tables and axes.
- Tabular numerals on every number, including selects and chart tips.
- Region color for identity, ink for forecasts, gray for doubt.
- Interaction is dry: 150ms ease-out, color and opacity only.

## Colors

A warm paper-and-ink neutral base with one categorical palette reserved for regions and two meaningful grays.

### Primary
- **Newsprint Ink** (tinta): all body text, headings, major 1px rules, the forecast line and both forecast bands, significant estimates, focus outline, the active state of segmented toggles.

### Secondary
- **Region palette** (Okabe-Ito, colorblind safe): region-gba (deep blue), region-pampeana (bluish green), region-noroeste (vermillion), region-noreste (reddish purple), region-cuyo (amber), region-patagonia (sky). Used for map fills, region swatches, the bars of the region panel and the shelf (gondola) line in the rubro chart. Nothing else.

### Tertiary
- **Energia Slate** (contraste): the regulated-tariff series wherever it appears (bars, dashed lines, dashed ranges) and the dash in its badge.
- **Doubt Gray** (no-significativo): marks for estimates whose range crosses zero. Dots, range rules and bars only.

### Neutral
- **Paper** (papel): page background, halo behind chart labels, province boundaries on the map, hollow points, inset background.
- **Paper Shade** (papel-2): hover and selected background on rows, selects and toggles; scrollbar track.
- **Faded Ink** (tinta-2): secondary text, cell labels, notes, axis text, zero rules on line charts, reference rules.
- **Filete** (filete): minor 1px rules between cells, rows and blocks; chart gridlines; toggle and badge borders.

### Named Rules
**The Ink Forecast Rule.** The forecast is ink, never region color. Dashed ink line (3 3), hollow end point, and a fan opening from the last real value: 80% band in ink at fill-opacity 0.22, 90% band in ink at 0.10. No forecast number appears without its band.

**The Fill-Only Rule.** Region colors are fills and strokes, never text. Amber and sky fail AA as text on paper, so every label, value and caption stays in ink or faded ink.

**The Energia Flag Rule.** Energia is always slate with the 4 3 dash. Bars get a slate fill at 0.35 opacity with a 1.25px dashed slate outline; lines and ranges are dashed slate strokes; points are solid slate. Wherever energia shows up in a chart, table or selector it carries the badge "Tarifa regulada - referencia de contraste" plus a one-line plain explanation.

**The Gray Means Zero Rule.** An estimate that cannot be told apart from zero is drawn in Doubt Gray, never in ink or region color, and the prose says so.

## Typography

**Display Font:** Source Serif 4 Variable (optical sizing on, with ui-serif, Georgia)
**Body Font:** Public Sans 400, 600, 700 (with ui-sans-serif)

**Character:** A newspaper serif for what you read as a headline or a figure, and a plain civic sans for everything you operate or scan. The serif earns the big numbers; the sans keeps tables and axes quiet.

### Hierarchy
- **Display** (700, 2.5rem on mobile, 3.25rem from md, line-height 1, -0.02em): the masthead "Efecto Gondola" only.
- **Figure** (600, 2.25rem on mobile, 2.75rem from md, line-height 1, tight tracking): the headline numbers in the top strip (last data, forecast).
- **Headline** (600, 2rem, line-height 1.25): section titles and the region name. The revisions article steps up to 2.25 / 2.75rem.
- **Figure secondary** (500, 1.5rem on mobile, 1.75rem from md): the next-release date and the region select in the strip. Summary values in the update section use 600 at 1.375rem.
- **Title** (600, 1.25rem): block headings inside the region panel, chart captions, subsections.
- **Reading** (400, 1.125rem, line-height 1.625): long serif prose in the revisions article; the forecast explainer uses 1.0625rem. Max 65ch.
- **Body** (400, 1rem, line-height 1.55): Public Sans running text, max 60ch.
- **Label** (400, 0.875rem): cell labels (dt), table text, list buttons, toggles. Sentence case, faded ink, no uppercase, no letter-spacing.
- **Note** (400, 0.8125rem): source and caveat lines under figures and charts, faded ink, max 65ch.
- **Chart** (400, 12px, faded ink; 11px for in-plot annotations like "llega todo").

### Named Rules
**The Tabular Everywhere Rule.** font-variant-numeric: tabular-nums is set on html and repeated on selects, chart SVGs and chart tips. Numbers line up in every column and never jitter when the region changes.

**The Serif Holds the Number Rule.** Big figures and headings are serif; axis labels, tables, selects in body size and controls are sans. Don't set a data table in serif or a headline figure in sans.

## Layout

One centered column, max 1200px, 16px side gutter on mobile and 32px from md (768px). Sections stack full width, each opened by a 1px ink rule, with 40px vertical padding on mobile and 56px from md. Column gap is 48px wherever the page splits.

- **Header:** masthead and lede on the left, data date on the right, wrapping on mobile.
- **Strip:** four cells (last data, forecast with band, next INDEC release, region select) between two 1px ink rules, divided by 1px filete rules. Two by two on mobile, four across from md.
- **Map and panel:** 5fr / 6fr from md, with the map sticky at the top of its column. On mobile the map sits above the panel.
- **Lower sections:** asymmetric splits from lg (1024px): 7/5 for rubro and update, 5/7 for the forecast, 1/2 for the footer. Long-form revisions text is a single 65ch column.
- **Blocks inside a panel:** 32px apart, each opened by a 1px filete rule with 20px above the title.
- **Charts** take the column width, redraw on resize, reserve their height up front so nothing jumps, and switch to fewer ticks under 480px of chart width (420px for the forecast chart). The left label margin is computed from the longest category label (about 6.4px per character plus 14px, never more than half the chart), and under 480px long rubro names switch to short forms ("Electricidad y gas", "Verduras", "Medicamentos").

### Named Rules
**The Hairline Rule.** Structure comes from 1px rules only. Ink rules mark section breaks, the strip, table heads and totals, and the underline of selects. Filete rules divide cells, rows and blocks. No boxes around content.

**The Map Governs Rule.** Choosing a region on the map, the GBA inset, the list under the map or the strip select updates the strip, the panel, the rubro view and the forecast section in the same render. One state, many readers.

## Elevation & Depth

Flat. There are no shadows anywhere; depth comes from the paper shade on hover and selection, the ink rules, and opacity on the map. The only layered element is the GBA inset, a paper rectangle with a 1px ink border placed over the sea.

### Named Rules
**The Flat Paper Rule.** Nothing floats. A state change is a background shift to Paper Shade, a weight change or an ink fill, never a shadow or a lift.

## Shapes

Square by default. The only radius is 2px, used on region swatches (12px in lists and the strip, 16px next to the region name) and on the energia badge. Controls are open: selects are a bare 1px ink underline with a hand-drawn chevron, toggles are a 1px filete outline split by a filete rule.

Map shapes keep a round line join. The selected region gets a 1.2px ink outline; province boundaries are thin paper-colored lines (0.6px, 0.5px inside the inset) so they orient without competing.

### Named Rules
**The 2px Ceiling Rule.** No radius above 2px, on anything.

## Components

### Buttons and toggles
- **Shape:** square (0px), sans label size.
- **Segmented toggle:** two options inside a 1px filete border, 4px 12px padding, split by a filete rule. Active option is filled ink with paper text; inactive goes to Paper Shade on hover.
- **Region list button:** full-width row with swatch, name and value in faded ink, 8px padding, filete rule below. Active row gets Paper Shade and 600 weight.
- **Hover / Focus:** background-color transition 150ms ease-out. Focus is a 2px ink outline with 2px offset.

### Selects
- **Style:** transparent background, 1px ink underline, no box, native arrow removed (appearance none) and replaced by the same drawn chevron (12px wide, 1.5px stroke) on every select. The region select in the strip uses the serif figure-secondary size with the region swatch at its left; the rubro select uses serif 1.25rem; the series select in the forecast section uses sans label size.
- **Hover:** Paper Shade, 150ms ease-out.

### Links
- Underlined, 1px, offset 3px, underline in faded ink that turns ink on hover. No color change on the text.

### Strip cells
- Label (faded ink, 0.875rem) over a serif figure over a note. 16px padding on mobile, 20px from md; the first cell drops its left padding on desktop so it aligns with the header.

### Energia badge
- Inline chip with a 1px filete border and 2px radius, 12px text in faded ink, led by a 16px slate dash (stroke 2, dasharray 4 3). Always followed by the plain sentence that energia is a regulated tariff.

### Tables
- Sans 0.875rem, numbers right aligned and tabular. Header row and total row ruled in ink; body rows ruled in filete. Header cells are regular weight in faded ink. The better value in a comparison row is 600 in ink, the other faded.

### Map (signature)
- Conic conformal projection (parallels -28 and -48) drawn at build time; the browser only receives paths.
- Region fills at fill-opacity 0.42 when not selected, 0.72 on hover, 1 when selected with a 1.2px ink outline. Opacity transition 150ms ease-out. Focus adds a 2.5px ink stroke.
- Region labels 15px ink with a 3px paper halo, 400 at rest and 700 when selected.
- GBA inset: paper rectangle with 1px ink border, joined to a 0.8px ink marker over the main map by a 0.8px ink leader line. Inset title "GBA" bold 15px plus a 12px faded note.
- Every region is a keyboard button (Enter or Space); the region list below the map is the non-map alternative.

### Charts (signature)
Observable Plot with one shared style: transparent background, 12px faded-ink text, gridlines in filete at 1px, zero rule in faded ink (ink on bar charts), and a 3px paper halo behind every value label. Tooltips sit on a paper fill with a 1px filete stroke and no drop shadow.
- **Dash vocabulary:** 2 2 for reference rules (general level, "llega todo" at 100%); 3 3 in ink for the forecast; 4 3 in slate for energia.
- **Forecast fan:** last 13 months as a 1.75px ink line with 2.5px dots; fan from the last real value to the forecast month with the 80% and 90% bands from the Ink Forecast Rule; forecast point hollow (paper fill, 1.5px ink stroke, r 4) with its value in 600.
- **Backtest:** stepped bands at the same opacities, dashed forecast step line, real values filled ink when inside the 80% band and hollow when outside. Month ticks every 3 months, every 6 under 480px.
- **Pass-through rows and epochs:** dot (r 4, 4.5 for epochs) on a 1.5px range rule, sorted high to low, clipped to -60% to 180%. Ink if significant, Doubt Gray if not; energia gets a solid slate dot on a dashed slate range.
- **Wholesale vs shelf:** wholesale always a thin 1.25px ink line; shelf in the region color at 2.25px (slate dashed for energia). Direct labels at the line ends, no legend.
- **Bars:** 22px rows with 4px insets, region color, value label at the bar end, dashed ink rule for the general level. Timing bars (how much arrives each month) are ink, or Doubt Gray when not significant. Energia bars follow the Energia Flag Rule in both.
- **Supply chain:** industria as a solid 1.75px ink line, productor as a solid 1.25px faded-ink line, confidence bands in ink at 0.08. Only the forecast and energia are dashed.

### Share image
- 1200 x 630 on paper: serif masthead (700) and lede in faded ink on the left, a 2px ink rule over two serif figures (600) split by a filete rule, the region map on the right with its GBA inset titled "GBA" in serif 600. Built from the same data at every deploy.

## Do's and Don'ts

### Do:
- **Do** set every number in tabular figures and every big number in Source Serif 4.
- **Do** draw the forecast in ink with both bands (0.22 and 0.10) and print its 80% range next to the figure.
- **Do** mark energia in slate with the 4 3 dash and the badge every time it appears.
- **Do** gray out (no-significativo) any estimate whose range crosses zero, and say it in the text.
- **Do** separate content with 1px rules: ink between sections, filete inside them.
- **Do** keep transitions at 150ms ease-out on color and opacity only, and zero them under reduced motion.
- **Do** label lines directly at their ends with a paper halo instead of using legends.

### Don't:
- **Don't** draw the forecast in a region color, least of all GBA blue.
- **Don't** set text in region colors; amber and sky are fill only.
- **Don't** use shadows, cards or radius above 2px.
- **Don't** show a forecast or pass-through value without its range.
- **Don't** use uppercase labels, eyebrows or kicker text above headings.
- **Don't** draw any series that is not energia in slate; slate with the 4 3 dash means regulated tariff.
