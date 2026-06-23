---
name: Thailand EV Registration
description: Monthly DLT new-car registration analysis — powertrain, brand, and model trends.
colors:
  bg:          "#020617"
  surface:     "#0f172a"
  border:      "#1e293b"
  ink:         "#f1f5f9"
  ink-muted:   "#94a3b8"
  ink-subtle:  "#64748b"
  accent-bev:  "#2dd4bf"
  accent-hev:  "#fbbf24"
  accent-phev: "#fb923c"
typography:
  headline:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.02em"
  body:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 500
    lineHeight: 1.4
  mono:
    fontFamily: "Geist Mono, ui-monospace, monospace"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.01em"
rounded:
  md: "6px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  chart-panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "24px"
  stat-strip:
    backgroundColor: "{colors.bg}"
    textColor: "{colors.ink}"
    padding: "16px 24px"
---

# Design System: Thailand EV Registration

## 1. Overview

**Creative North Star: "The DLT Terminal"**

This system reads and behaves like a terminal-native data display. Chrome disappears. Every pixel earns its place by serving the data. Hierarchy does not come from the visual weight of containers — it comes from the numbers themselves, and from the semantic colors assigned to the powertrain categories they represent.

The palette is deep-dark with near-invisible surfaces. Electric Teal signals the most important trend (BEV growth). Hybrid Amber and Plugin Orange tag the supporting categories. ICE — the established majority — is rendered in the same muted slate as secondary text: neutral, present, not highlighted. The system directs the eye toward what is changing, not toward what has always been there.

This system explicitly rejects the aesthetic it replaced: glassmorphism-as-default, gradient text on headings, hero-metric KPI cards with colored icon badges, and the generic SaaS dark-mode palette of blue/purple/emerald that signals AI-generated dashboard from across a room. Decorative background blobs, pulsing "live" indicators, gradient chart fills, and any motion that does not convey state are prohibited.

**Key Characteristics:**
- Near-invisible surfaces — panels defined by 1px borders, not shadows or blur
- Monospaced numeric values (Geist Mono, `tabular-nums`) for scannable columns
- Minimal type scale — 14px/12px/11px; no display or hero sizes
- Chart colors carry semantic weight: teal = BEV, amber = HEV, orange = PHEV, slate = ICE
- Key metrics live in the sticky header stat strip, not in a grid of KPI cards

## 2. Colors: The Terminal Palette

Near-monochrome dark with three semantic chart accents and no general-purpose decorative color. The five neutral steps carry all structural work; the three accent colors carry all data meaning.

### Primary
- **Electric Teal** (`#2dd4bf`): The BEV signal. Used exclusively to represent Battery Electric Vehicle data across all charts, and as the primary bar fill color in the brand ranking chart. Never used for UI decoration or to draw attention to non-BEV elements.

### Secondary
- **Hybrid Amber** (`#fbbf24`): HEV powertrain in all charts. Warm, transitional — appropriate for a category that is neither fully electric nor purely combustion.
- **Plugin Orange** (`#fb923c`): PHEV powertrain in all charts. Energetically between BEV teal and neutral ICE slate.

### Neutral
- **Depth Black** (`#020617`): Page background. The bedrock of the system.
- **Surface Charcoal** (`#0f172a`): Chart panels and sticky header background. One luminosity step above the bedrock.
- **Grid Line** (`#1e293b`): All borders and chart grid lines. Structural, never decorative.
- **Ink** (`#f1f5f9`): Primary text — stat strip values, headings.
- **Ink Muted** (`#94a3b8`): Secondary text — figcaptions, chart axis labels, legend text.
- **Ink Subtle** (`#64748b`): Tertiary text — stat descriptor labels. Also the ICE powertrain chart color; the semantic overlap is intentional (ICE is both neutral text and the neutral baseline powertrain).

### Named Rules

**The One Signal Rule.** Electric Teal (`#2dd4bf`) represents BEV data, and nothing else. It is not a general-purpose accent. Any new feature that needs a highlight color should use weight, position, or a border — not teal.

**The ICE-as-Neutral Rule.** ICE vehicles are the established baseline; they are visually subordinate. The eye lands on teal first, then amber, then orange. ICE arrives last because it requires no signal. This color assignment is non-negotiable — reversing it would invert the dashboard's communicative intent.

**The No-General-Accent Rule.** This system has no general-purpose UI accent color (no blue for links, no purple for focus rings). State indicators use increased weight or a border treatment. The three chart colors are data colors, not UI colors.

## 3. Typography

**Body/Headline Font:** Geist (`var(--font-geist-sans)`), with `system-ui, sans-serif` fallback. Single family throughout — weight and size carry all hierarchy.
**Mono Font:** Geist Mono (`var(--font-geist-mono)`) for all numeric values requiring column alignment.

**Character:** Geist is a contemporary geometric sans with excellent legibility at the small sizes this system requires. The mono variant ensures numeric columns in the stat strip align precisely even when values differ in digit count — critical for a financial-style data display.

### Hierarchy

- **Headline** (600, 14px, 1.3 line-height, +0.02em letter-spacing): Page title in the sticky header. The largest text in the system. Deliberately compact — this is not a marketing surface.
- **Body** (400–500, 12px, 1.5 line-height): Figcaptions, stat descriptor labels, chart legend text.
- **Label** (500, 11px, 1.4 line-height): Chart axis ticks. Smallest legible text in the system.
- **Mono** (Geist Mono, 600, 12px, 1.0 line-height, `-0.01em`, `tabular-nums`): All numeric metric values in the stat strip and any future data columns.

### Named Rules

**The No-Display Rule.** There are no display or hero heading sizes in this system. The largest text is the page title at 14px. This is a data terminal, not a landing page. Adding a clamp-scaled h1 or a 3rem hero is prohibited.

**The Mono-for-Numbers Rule.** Every numeric metric — stat strip values, table cells, any future numeric column — uses Geist Mono with `tabular-nums`. Proportional figures are never used for data.

## 4. Elevation

This system uses tonal layering, not shadows. Depth is communicated entirely through background luminosity: `#020617` (base) → `#0f172a` (surface) → `#1e293b` (border/grid). There is no `box-shadow` anywhere in the production system.

The sticky header uses `bg-slate-950/95` (95% opacity background) to allow content to visually slide beneath it on scroll. This is the only translucency effect in the system, and it is structural — the header's anchor to the viewport justifies it — not decorative.

### Named Rules

**The Flat-by-Default Rule.** If you are about to add `box-shadow`, stop. Use `border: 1px solid {colors.border}` instead. Elevation in this system is tonal: a lighter background surface within a darker container. No exceptions in the data display layer.

## 5. Components

### Chart Panel

Panels are containers, not objects. The border functions as a grid line, not a frame. Internal visual noise is zero — the chart data should read without competition from its container.

- **Shape:** 6px border-radius (`rounded-md`). Consistent across all panels.
- **Background:** Surface Charcoal (`#0f172a`, `bg-slate-900`)
- **Border:** 1px solid Grid Line (`#1e293b`, `border-slate-800`)
- **Internal padding:** 24px all sides (`p-6`)
- **Caption:** `<figcaption>` — Body weight (12px/500), Ink Muted (`#94a3b8`), no uppercase, no letter-spacing, 16px bottom gap before the chart area
- **Height:** Responsive — `h-64` (256px) on mobile, `h-80` (320px) at `md` and above. Fixed per breakpoint (not fluid) to maintain predictable chart proportions
- **ARIA:** Every panel must carry `<figure aria-label="[description of chart]">` plus a `<figcaption>`. Recharts SVGs are not screen-reader accessible without this.
- **State:** Static — no hover, no focus, no interactive state on the panel itself

### Stat Strip

The primary summary surface. Replaces the hero-metric card grid. Lives in the sticky header, providing instant access to three key numbers without navigating away from the charts.

- **Layout:** Horizontal `<dl>` with `<dt>/<dd>` pairs separated by 1px vertical dividers (28px tall, Grid Line color)
- **Label (`<dt>`):** Label size (12px/400), Ink Subtle (`#64748b`)
- **Value (`<dd>`):** Geist Mono, 12px/600, `tabular-nums`. Ink (`#f1f5f9`) for neutral metrics; Electric Teal (`#2dd4bf`) for BEV Share specifically — the one metric that signals the EV story
- **State:** Static — not interactive

### Chart Colors (data vocabulary)

| Powertrain | Color | Hex | Usage |
|---|---|---|---|
| BEV | Electric Teal | `#2dd4bf` | Pie slice, area stroke/fill, brand bar fill |
| HEV | Hybrid Amber | `#fbbf24` | Pie slice, area stroke/fill |
| PHEV | Plugin Orange | `#fb923c` | Pie slice, area stroke/fill |
| ICE | Ink Subtle | `#64748b` | Pie slice, area stroke/fill — muted, not highlighted |

Area chart fill opacity: `0.06` — just enough to close the area visually, not enough to read as a filled region.
Stroke width: `1.5px` — precise, not bold.

## 6. Do's and Don'ts

### Do:
- **Do** use `<figure aria-label="[description]">` + `<figcaption>` on every chart panel. Recharts SVGs are opaque to screen readers; the accessible label is not optional.
- **Do** use Geist Mono with `tabular-nums` and `font-weight: 600` for every numeric metric value — in the stat strip, in any future table, in any future tooltip value.
- **Do** keep chart color assignments semantically constant: Electric Teal = BEV only, Hybrid Amber = HEV only, Plugin Orange = PHEV only, Ink Subtle = ICE only. The colors are data vocabulary, not decoration. Inconsistency destroys the system's communicative intent.
- **Do** use `border: 1px solid #1e293b` as the only surface separator. No shadows; tonal elevation only.
- **Do** derive all displayed metric values from actual data. When data is missing, show `—` (em dash). Hardcoded fallback numbers are data integrity bugs.
- **Do** scope transitions to the exact properties that change: `transition-colors duration-200`, not `transition-all`.
- **Do** respect `prefers-reduced-motion` — the rule is in `globals.css`. Any new animation needs a reduced-motion alternative.

### Don't:
- **Don't** use `backdrop-filter: blur(...)` or `backdrop-blur` on data surfaces. Glassmorphism is prohibited — it was the central anti-pattern this system replaced.
- **Don't** use gradient text (`background-clip: text` with a gradient background). Banned unconditionally.
- **Don't** add a hero-metric KPI card grid. Summary metrics live in the stat strip in the header, not in a three-column grid of identical cards with colored icon badges.
- **Don't** use the generic SaaS dark-mode palette: `#3b82f6` (blue), `#8b5cf6` (purple), or `#10b981` (emerald) as general UI accents. The system's three accent colors are chart-specific and carry data meaning.
- **Don't** add decorative background blobs, radial gradients behind page content, or animated glow effects. The background is solid Depth Black (`#020617`), full stop.
- **Don't** hardcode metric values. Any static number in the UI that is not a design constant is a data integrity bug.
- **Don't** use `transition-all`. It triggers layout recalculation on every animatable property. Scope to `transition-colors`.
- **Don't** build loading states as a centered spinner. Use a skeleton layout or an inline text placeholder.
- **Don't** add pulsing "Live Data Sync" badges unless the data stream is genuinely real-time. A single fetch on mount is not a live connection.
- **Don't** use display fonts, hero sizing, or clamp-scaled headings anywhere in this system.
