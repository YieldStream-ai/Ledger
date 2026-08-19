# YieldStream Design System

A data-dense underwriting environment for credit and lending professionals. Synthesized from three references: **Linear** (information architecture, density, dark-surface discipline), **Attio** (record-as-object hierarchy, restrained pill system, progressive disclosure), and **Mercury** (financial tone, warmth without softness, calm under density).

The point of YieldStream is judgment, not lookup. Every design decision is evaluated against one question: *does this help an underwriter form an opinion on a deal faster and with more confidence?*

---

## 1. Theme & Atmosphere

YieldStream is **light-mode-primary with a first-class dark mode** — this is the most important departure from Linear. Linear's near-black canvas reads as engineering tooling; an underwriter at a credit desk reading a memo at 9am needs the calm authority of paper, not the focus-mode aesthetic of an IDE. Mercury proves a financial tool can be light, dense, and trustworthy at the same time. Dark mode exists for late-night review sessions and is a peer, not an afterthought.

The atmosphere is **paper-precise**: a near-white canvas (`lch(98.94% 0.5 282)` — cool-tinted off-white), generous internal whitespace inside record panels, and almost no chrome. Borders are hairline and nearly absent. Shadows are forbidden except on true overlays (popovers, modals). Elevation is communicated through background tone, not depth.

Color is rationed. The interface is achromatic — warm grays and off-white — with **one chromatic accent** (a deep charcoal, not Linear's indigo-violet, which reads too consumer). Status colors (green, amber, red) appear *only* on data and only when they encode underwriting meaning. A green pill on a YieldStream screen means something specific about a deal; it is never decoration.

**Key characteristics:**
- Light-primary, dark-peer. Neither is "the" mode.
- Cool neutrals: `lch(98.94% 0.5 282)` canvas, `#111827` ink — clean, crisp, Bloomberg/Linear feel without warmth (LCH color space for perceptual uniformity)
- Inter Variable with `cv11, ss01, ss03` enabled globally — `cv11` gives the single-story `a` that reads as financial-document-modern
- Tabular numerals (`font-variant-numeric: tabular-nums`) on **every number, everywhere** — this is non-negotiable for an underwriting tool
- Source Serif 4 for memo prose and long-form narrative sections (the "editorial layer" Attio lacks) — used sparingly, only inside deal memos and analyst notes
- JetBrains Mono for IDs, hashes, and structured data
- One accent: `#1f2937` (slate 800). Hover `#111827` (darker). Active `#030712`. That is the entire chromatic palette outside of status.
- Status semantics: `#2F7D4F` (advance), `#B8860B` (caution), `#A8321E` (decline) — muted, never neon
- Borders use LCH: `lch(96 1 250)` hairline / `lch(92 1.5 250)` standard / `lch(85 2 250)` strong. Dark mode: `rgba(255,255,255,0.07)`. Hairline. Often absent in favor of spacing.

---

## 2. Color Palette & Roles

### Light Mode (Primary)

**Surfaces (LCH color space)**
- `--canvas`: `lch(98.94% 0.5 282)` — page background. Near-white with subtle cool tint.
- `--surface`: `lch(100% 0.5 282)` — record panels, the "card" that holds a deal
- `--surface-sunken`: `lch(95.94% 0.5 282)` — page-level left content rails, table row alternates, recessed section backgrounds
- `--surface-sunken-subtle`: `lch(90.94% 0.5 282)` — drop zone hover, input section backgrounds (more pronounced sunken effect)
- `--surface-raised`: `lch(100% 0.5 282)` + `0 1px 2px rgba(15,23,42,0.04)` — popovers, dropdowns

**Ink (Text)**
- `--ink-primary`: `#111827` — headings, key figures, deal names
- `--ink-secondary`: `#374151` — body text, table cell content
- `--ink-tertiary`: `#6B7280` — labels, metadata, column headers
- `--ink-quaternary`: `#9CA3AF` — placeholders, timestamps, disabled

**Accent (the only chromatic UI color)**
- `--accent`: `#1f2937` (slate 800) — primary CTAs, active tab underline, focused field ring, link text
- `--accent-hover`: `#111827` (slate 900, darker on hover)
- `--accent-active`: `#030712` (slate 950, pressed state)
- `--accent-wash`: `rgba(31, 41, 55, 0.04)` — selected row background, active nav item
- `--accent-wash-hover`: `rgba(31, 41, 55, 0.06)` — hover on washed elements
- `--accent-border`: `rgba(31, 41, 55, 0.12)` — active tab underlines, focus rings
- `--accent-text-on`: `#ffffff` — text on accent fills

**Status (data semantics only — never decoration)**
- `--status-advance`: `#2F7D4F` — approved, performing, in-bounds
- `--status-advance-wash`: `#2F7D4F12`
- `--status-caution`: `#B8860B` — review, watchlist, marginal
- `--status-caution-wash`: `#B8860B14`
- `--status-decline`: `#A8321E` — declined, default, out-of-bounds
- `--status-decline-wash`: `#A8321E10`
- `--status-neutral`: `#6B7280` — draft, archived, inactive

**Borders & Lines (LCH color space)**
- `--border-hairline`: `lch(96 1 250)` — softest separation, almost invisible
- `--border-standard`: `lch(92 1.5 250)` — standard surface and component border
- `--border-strong`: `lch(85 2 250)` — stronger contrast for interactive elements

### Dark Mode (Peer)

- `--canvas`: `#0E0F11` — slightly warmer than Linear's `#08090A`
- `--surface`: `#16181B`
- `--surface-sunken`: `#101113`
- `--surface-raised`: `#1C1E22`
- `--ink-primary`: `#F2F1ED` (warm white, not Linear's cool `#F7F8F8`)
- `--ink-secondary`: `#C8C7C2`
- `--ink-tertiary`: `#8A8A84`
- `--ink-quaternary`: `#5E5E58`
- `--accent`: `#6FA3D9` (lifted for contrast)
- `--accent-wash`: `#6FA3D914`
- Status colors lift ~15% in luminance; otherwise identical semantics
- `--border-hairline`: `rgba(255, 255, 255, 0.07)`

---

## 3. Typography

### Families
- **UI & Data**: `Inter Variable`, fallback `-apple-system, system-ui, Segoe UI, sans-serif`
  - `font-feature-settings: "cv11", "ss01", "ss03", "calt"`
  - `font-variant-numeric: tabular-nums` on **all numeric content** (table cells, KPIs, IDs, ratios, dates)
- **Editorial**: `Source Serif 4`, fallback `Charter, Georgia, serif` — used **only** in memo body content, analyst commentary, and the deal narrative panel. Never in chrome, never in tables. This is the single most important departure from Linear: the prose layer needs a serif because underwriting memos are documents, not UI.
- **Mono**: `JetBrains Mono`, fallback `ui-monospace, SF Mono, Menlo` — IDs, deal hashes, structured codes, raw payload viewers

### Weights
Inter at three weights only: **400** (read), **520** (UI emphasis, default for labels and table headers), **620** (announce — KPIs, deal names, section headings). Source Serif at **400** body and **600** for memo headings. No bold (700+); 620 is the ceiling.

### Hierarchy

| Role | Family | Size | Weight | Line | Tracking |
|---|---|---|---|---|---|
| KPI Display | Inter | 36px | 620 | 1.05 | -0.72px |
| Deal Name | Inter | 24px | 620 | 1.20 | -0.36px |
| Section Heading | Inter | 18px | 620 | 1.30 | -0.18px |
| Memo H1 (serif) | Source Serif | 28px | 600 | 1.25 | -0.28px |
| Memo H2 (serif) | Source Serif | 20px | 600 | 1.35 | -0.10px |
| Memo Body (serif) | Source Serif | 16px | 400 | 1.65 | 0 |
| Body | Inter | 14px | 400 | 1.55 | 0 |
| Body Emphasis | Inter | 14px | 520 | 1.55 | 0 |
| Table Cell | Inter | 13px | 400 | 1.45 | 0 |
| Table Cell Numeric | Inter (tabular) | 13px | 520 | 1.45 | 0 |
| Table Header | Inter | 11px | 520 | 1.40 | 0.4px (uppercase) |
| Label / Field | Inter | 12px | 520 | 1.40 | 0 |
| Caption / Meta | Inter | 12px | 400 | 1.45 | 0 |
| Mono ID | JetBrains Mono | 12px | 400 | 1.40 | 0 |

**Principles**
- 520 is the workhorse weight (analogous to Linear's 510)
- Numbers are *always* tabular — columns of figures must align on the decimal without effort
- The serif appears only in editorial contexts; mixing it with UI chrome is the cardinal sin
- Table headers are the only place uppercase is permitted, and only at 11px with 0.4px tracking — this is the underwriting-document convention and signals "column label" instantly

---

## 4. Components

### The Record Panel (the central object)

This is the YieldStream equivalent of Attio's company record. A deal is an object; everything you do is in service of evaluating one. The record panel is the main canvas.

- Background `--surface`, no border, sits on `--canvas`
- Top: deal name (24px/620) + status pill + ID (mono) + last-updated meta — single row, baseline-aligned
- Tab strip below: Overview · Financials · Collateral · Memo · Activity. Tab labels 13px/520, active tab underlined `2px solid --accent`, inactive `--ink-tertiary`
- Generous internal padding: 32px horizontal, 24px vertical
- Sections separated by 32px vertical space and a hairline `border-top` — never a heavy divider

### Pills — Three Semantic Types

Pills are the workhorse of state communication and must be quiet. Type does the work; background is barely there. No pill ever has a drop shadow, a gradient, or animates on hover unless interactive.

All pill types share the same physical dimensions: `2px 8px` padding, `4px` radius (not full-pill — full-pill reads consumer; 4px reads document), 12px / 520 font.

#### `<Tag>` — Non-semantic classifier

For facts about the deal that carry no judgment: industry ("Technology"), pipeline stage ("Offers Received"), lien position ("1st position"), role labels ("Primary").

- Background: `rgba(20, 20, 20, 0.05)` — flat gray wash
- Text: `--ink-secondary`
- No dot, no color encoding
- The quietest element on the page. Should be invisible in peripheral vision.

**Test:** if you can say "this is just stating what it is, not whether it's good or bad," use Tag.

#### `<Pill>` — Status judgment

For values that encode underwriting judgment: "Funded," "Low Risk," "Excellent" (FICO band), "OVERDUE," lifecycle status, submission status.

- Background: `--status-*-wash` (8–12% alpha)
- Text: `--status-*` at full saturation
- Optional 6px leading dot — use the dot when the pill appears in a scanning context (lists, grids)
- Tones: `advance` (green), `caution` (amber), `decline` (red), `neutral` (gray), `accent` (blue)

**Test:** if the color encodes a judgment the user needs to act on, use Pill.

#### `<Metric>` — Number + band

For the pattern where a raw number sits next to its qualitative band: "760 ● Excellent," "42% ● Above Average." The number is data (not state) and must not be wrapped in a pill.

- Number: `--ink-primary`, tabular-nums, `620` weight — rendered as bare text
- Band: a small `<Pill>` with the appropriate status tone and dot
- Gap: `6px` between number and pill

**Test:** if you have a number AND a qualitative label, use Metric. Don't pillify the number.

### Side Rail (Linear-derived)

There are two distinct rail elements — they use different surface tokens intentionally:

**App nav sidebar** (collapsed: 48px / expanded: 240px): `--canvas` background (`$ds-canvas`) — intentionally merges with the shell. The visual boundary comes from the page-level content shift, not a tone step. Nav items 13px/520, 8px vertical padding, 12px horizontal. Active item: `--accent-wash` background, `--accent` text, `2px` left bar in `--accent`. Hover: background lifts to `$ds-accent-wash`.

**Page-level left content rail** (`LeftRailAccordion`): `--surface-sunken` background (`$ds-surface-sunken`) — the visually distinct gray panel in merchant/submission detail views. No border-right; the tone shift from sunken to canvas is the boundary. Used for merchant profile, lender buy-box, deal intelligence sidebar panels.

### Tables (the heart of the product)

- Row height: 36px (dense) or 44px (comfortable) — user toggleable
- Header: `--ink-tertiary`, 11px/520/uppercase, 0.4px tracking, `border-bottom: 1px solid --border-standard`
- Row borders: `border-bottom: 1px solid --border-hairline` — barely visible, just enough to track across
- Hover: row background lifts to `--surface-sunken`
- Selected: `--accent-wash` background, `2px` left bar in `--accent`
- Numeric columns right-aligned, tabular-nums, 520 weight
- Sort indicator: 10px chevron in `--ink-tertiary`, only on the active sort column
- Sticky header on scroll, with a `1px` shadow `0 1px 0 var(--border-standard)` only when scrolled

### Buttons

**Primary**: `--accent` background, white text, `6px` radius, `8px 14px` padding, 13px/520. Hover: `--accent-hover`. No shadow.

**Secondary**: transparent background, `1px solid --border-standard`, `--ink-primary` text, same dimensions. Hover: background `rgba(20,20,20,0.04)`.

**Ghost**: transparent, no border, `--ink-secondary` text. Hover: background `rgba(20,20,20,0.04)`. For toolbar and contextual actions.

**Destructive**: only used in confirmation dialogs. `--status-decline` background, white text. Never used inline.

### Inputs

- Background `--surface`, `1px solid --border-standard`, `5px` radius, `8px 12px` padding, 13px/400
- Focus: `border-color --accent`, `box-shadow: 0 0 0 3px --accent-wash`. No glow, no animation longer than 120ms.
- Label above, 12px/520/`--ink-tertiary`, 6px gap

### Drop Zone

- Empty: `2px dashed --border-standard`, `--surface` background, centered icon + label. Hover: `--border-strong`, `--surface-sunken-subtle` background.
- Extracting: `1px solid --border-standard`, `--accent-wash` background, spinner in `--accent`.
- Complete: `1px solid --border-standard`, `--surface-sunken-subtle` background, checkmark in `--status-advance`. No colored borders.
- Error: `1px solid` status-decline at 30% alpha, `--status-decline-wash` background.
- **Never use colored borders on drop zones** — borders are always neutral gray (`--border-*`). Status feedback is conveyed through background wash and icon color, not border color.

### KPI Card

- `--surface` background, no border (sits on `--surface-sunken` section bg), 16px padding
- Label 11px/520/uppercase/`--ink-tertiary`
- Value 36px/620/tabular-nums/`--ink-primary`
- Delta below: 12px/520, status color + small arrow glyph
- 8px radius

### Memo Block (the editorial layer)

This is the component Attio doesn't have and Linear doesn't need. The memo block is where underwriters write narrative.

- Max-width: 680px (reading measure)
- Source Serif 4 throughout
- 16px / 1.65 line-height body
- H2s are 20px/600 with 32px top margin
- Pull quotes and risk callouts: 4px left border in `--accent` or `--status-caution`, 16px left padding, italic
- Inline numbers inside memo prose still use Inter tabular-nums (the one place we mix families inline) — keeps figures legible inside serif text

### Risk Flag

A specialized component YieldStream needs that none of the references have. Inline annotation on a row or field that surfaces an underwriting concern.

- Small triangle glyph in `--status-caution` or `--status-decline`, 12px
- On hover/click: popover with the rule that triggered it, the threshold, and a "dismiss with reason" action
- Never blocks interaction; underwriters override flags with a logged reason

---

## 5. Layout

- Base unit: **4px**. Common scale: 4, 8, 12, 16, 20, 24, 32, 48, 64
- Max content width inside record panel: 1080px
- Side rail: 240px fixed
- Detail rail (right side, contextual): 360px, collapsible
- Main canvas: fluid between rails
- Section vertical rhythm: 32px between sections, 16px between subsections, 8px between related fields
- Tables can break out of the 1080px constraint to full panel width

---

## 6. Elevation

Five levels, mostly tone-based. Shadows only on true overlays.

| Level | Treatment | Use |
|---|---|---|
| 0 Canvas | `--canvas`, no border | Page background |
| 1 Sunken | `--surface-sunken` | Side rail, table row alternate, section bg |
| 2 Surface | `--surface` | Record panel, KPI card |
| 3 Raised | `--surface` + `0 1px 2px rgba(15,23,42,0.04), 0 0 0 1px var(--border-hairline)` | Popovers, dropdowns |
| 4 Overlay | `--surface` + `0 12px 32px rgba(15,23,42,0.12), 0 0 0 1px var(--border-standard)` | Modals, command palette |

Linear uses background-luminance stepping on dark; YieldStream uses **tone stepping with warmth** on light. Shadows in light mode are warm-gray (`rgba(20,20,20,...)`), never pure black.

---

## 7. Do's and Don'ts

**Do**
- Use tabular-nums on every number, including dates, IDs, percentages, and ratios
- Reserve color for data semantics. If a color isn't carrying underwriting meaning, remove it.
- Use Source Serif only inside memos. Mixing it into UI chrome breaks the system.
- Lead with the warm off-white canvas — it's what makes YieldStream feel like a financial document, not a developer tool
- Use 4px-radius pills with washes, not full-pills with solid fills
- Right-align all numeric table columns
- Keep borders hairline; prefer spacing and tone shifts over visible lines

**Don't**
- Don't use Linear's indigo-violet — `#1f2937` slate 800 is the YieldStream accent
- Don't use full-pill (9999px) badges for status — too consumer
- Don't use shadows for elevation outside of true overlays
- Don't use bold (700+); 620 is the ceiling
- Don't use serif in tables, labels, buttons, or any chrome
- Don't decorate with status colors. A green pill must mean "advance."
- Don't use pure white `#FFFFFF` as the page canvas — use `$ds-canvas` (`lch(98.94% 0.5 282)`). The near-white LCH tone is intentional; hardcoding hex bypasses the token.
- Don't use icons larger than 16px in tables; underwriters scan, they don't browse

---

## 8. Responsive

YieldStream is desktop-first; underwriters work on 1440px+ screens. Mobile is review-only.

| Breakpoint | Width | Behavior |
|---|---|---|
| Desktop XL | 1440+ | Full three-column: rail / canvas / detail rail |
| Desktop | 1200–1440 | Detail rail collapses to icon strip, expands on hover |
| Laptop | 1024–1200 | Detail rail hidden, accessible via toolbar button |
| Tablet | 768–1024 | Side rail collapses to icon-only |
| Mobile | <768 | Read-only deal view, no editing, no tables wider than viewport (cards instead) |

---

## 9. Build Notes for Claude Code

### Stack & Styling Architecture

YieldStream uses **BEM + SCSS as the primary styling approach**, not Tailwind. Tailwind is installed only for `shadcn/ui` primitives inside `src/components/ui/`. Feature components never use Tailwind utility classes.

**Source of truth for tokens:**
- `src/styles/_variables.scss` — SCSS variables (consumed by all feature SCSS files)
- `src/styles/_mixins.scss` — Reusable SCSS mixins
- `src/styles/design-system.scss` — Exports SCSS variables as CSS custom properties at `:root`, plus base styles and utility classes
- `src/app/globals.css` — Tailwind directives + CSS custom properties for `shadcn/ui` components + global overrides

**How feature components consume tokens:**
```scss
// Every feature SCSS file imports from the shared system
@use '../../../../../styles/variables' as *;
@use '../../../../../styles/mixins' as *;

.my-component {
  background: $canvas;              // SCSS variable
  color: $ink-primary;              // SCSS variable
  border: 1px solid $border-hairline; // SCSS variable
  @include text-body(base, read);   // Mixin
}
```

**How `shadcn/ui` components consume tokens (Tailwind OK here only):**
```tsx
// src/components/ui/ — Tailwind classes reference CSS custom properties
<div className="bg-canvas text-ink-1 border-border-hairline" />
```

### Font Loading

Fonts are loaded via `next/font/google` in `src/app/layout.tsx` and exposed as CSS variables:

| Font | CSS Variable | Purpose |
|------|-------------|---------|
| Inter | `--font-inter` | UI & data (primary sans) |
| Source Serif 4 | `--font-source-serif` | Editorial / memo prose only |
| JetBrains Mono | `--font-jetbrains-mono` | IDs, hashes, structured data |

### SCSS Token Naming Convention

New design system tokens follow this naming pattern in `_variables.scss`:

```scss
// Surfaces (DS2 — use $ds- prefix, LCH color space)
$ds-canvas: lch(98.94% 0.5 282);           // Near-white with subtle cool tint
$ds-surface: lch(100% 0.5 282);            // Record panels, cards
$ds-surface-sunken: lch(95.94% 0.5 282);   // Page-level left rails, table row alternates
$ds-surface-sunken-subtle: lch(90.94% 0.5 282); // Drop zone hover, input section backgrounds
$ds-surface-raised: lch(100% 0.5 282);     // Popovers, dropdowns (+ shadow)

// Ink (text hierarchy)
$ds-ink-primary: #111827;
$ds-ink-secondary: #374151;
$ds-ink-tertiary: lch(38.376% 1.25 282 / 1);
$ds-ink-quaternary: #9ca3af;

// Accent (single chromatic color — slate ramp)
$ds-accent: #1f2937;                        // Slate 800 — primary
$ds-accent-hover: #111827;                  // Slate 900 — darker on hover
$ds-accent-active: #030712;                 // Slate 950 — pressed
$ds-accent-wash: rgba(31, 41, 55, 0.04);   // Same hue, 4% tint
$ds-accent-wash-hover: rgba(31, 41, 55, 0.06);
$ds-accent-border: rgba(31, 41, 55, 0.12); // Active tab underlines, focus rings
$ds-accent-text-on: #ffffff;               // Text on accent fills

// Status (data semantics only)
$ds-status-advance: #2f7d4f;
$ds-status-advance-wash: rgba(47, 125, 79, 0.07);
$ds-status-caution: #b8860b;
$ds-status-caution-wash: rgba(184, 134, 11, 0.08);
$ds-status-decline: #a8321e;
$ds-status-decline-wash: rgba(168, 50, 30, 0.06);
$ds-status-neutral: #6b7280;

// Borders (LCH color space)
$ds-border-hairline: lch(96 1 250);   // Softest separation, almost invisible
$ds-border-standard: lch(92 1.5 250); // Standard surface and component border
$ds-border-strong: lch(85 2 250);     // Stronger contrast for interactive elements

// Focus
$ds-focus-border: $ds-accent;
$ds-focus-ring: rgba(27, 58, 95, 0.12); // Stronger than accent-wash for focus visibility

// Typography
$ds-font-sans: var(--font-inter), 'Inter Variable', system-ui, sans-serif;
$ds-font-editorial: var(--font-source-serif), 'Source Serif 4', Charter, Georgia, serif;
$ds-font-mono: var(--font-jetbrains-mono), 'JetBrains Mono', ui-monospace, monospace;

// Weight ceiling: 620 (never bold/700+)
$ds-font-weight-read: 400;
$ds-font-weight-ui: 520;     // Workhorse — labels, table headers, emphasis
$ds-font-weight-announce: 620; // KPIs, deal names, section headings
```

### CSS Custom Properties (exported in `design-system.scss`)

```scss
:root {
  // Surfaces (LCH)
  --canvas: #{$ds-canvas};
  --surface: #{$ds-surface};
  --surface-sunken: #{$ds-surface-sunken};
  --surface-sunken-subtle: #{$ds-surface-sunken-subtle};
  --surface-raised: #{$ds-surface-raised};

  // Ink
  --ink-primary: #{$ds-ink-primary};
  --ink-secondary: #{$ds-ink-secondary};
  --ink-tertiary: #{$ds-ink-tertiary};
  --ink-quaternary: #{$ds-ink-quaternary};

  // Accent
  --accent: #{$ds-accent};
  --accent-hover: #{$ds-accent-hover};
  --accent-active: #{$ds-accent-active};
  --accent-wash: #{$ds-accent-wash};
  --accent-wash-hover: #{$ds-accent-wash-hover};
  --accent-border: #{$ds-accent-border};
  --accent-text-on: #{$ds-accent-text-on};

  // Status
  --status-advance: #{$ds-status-advance};
  --status-advance-wash: #{$ds-status-advance-wash};
  --status-caution: #{$ds-status-caution};
  --status-caution-wash: #{$ds-status-caution-wash};
  --status-decline: #{$ds-status-decline};
  --status-decline-wash: #{$ds-status-decline-wash};

  // Borders (LCH)
  --border-hairline: #{$ds-border-hairline};
  --border-standard: #{$ds-border-standard};
  --border-strong: #{$ds-border-strong};

  // Focus
  --focus-border: #{$ds-focus-border};
  --focus-ring: #{$ds-focus-ring};
}
```

### Key Mixins to Add (in `_mixins.scss`)

```scss
// Typography — coordinated font stack + size + weight + line-height
@mixin text-kpi-display {
  font-family: $font-sans;
  font-size: 36px;
  font-weight: 620;
  line-height: 1.05;
  letter-spacing: -0.72px;
  font-variant-numeric: tabular-nums;
}

@mixin text-deal-name {
  font-family: $font-sans;
  font-size: 24px;
  font-weight: 620;
  line-height: 1.20;
  letter-spacing: -0.36px;
}

@mixin text-section-heading {
  font-family: $font-sans;
  font-size: 18px;
  font-weight: 620;
  line-height: 1.30;
  letter-spacing: -0.18px;
}

@mixin text-table-header {
  font-family: $font-sans;
  font-size: 11px;
  font-weight: 520;
  line-height: 1.40;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: $ink-tertiary;
}

@mixin text-table-cell-numeric {
  font-family: $font-sans;
  font-size: 13px;
  font-weight: 520;
  line-height: 1.45;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

@mixin text-label {
  font-family: $font-sans;
  font-size: 12px;
  font-weight: 520;
  line-height: 1.40;
  color: $ink-tertiary;
}

// Editorial — scoped to memo/narrative contexts
@mixin text-memo-body {
  font-family: $font-editorial;
  font-size: 16px;
  font-weight: 400;
  line-height: 1.65;
}

@mixin text-memo-heading {
  font-family: $font-editorial;
  font-size: 20px;
  font-weight: 600;
  line-height: 1.35;
  letter-spacing: -0.10px;
}

// Elevation — tone-based, shadows only for overlays
@mixin elevation-sunken {
  background: $surface-sunken;
}

@mixin elevation-surface {
  background: $surface;
}

@mixin elevation-raised {
  background: $surface;
  box-shadow: 0 1px 2px rgba(20, 20, 20, 0.04), 0 0 0 1px $border-hairline;
}

@mixin elevation-overlay {
  background: $surface;
  box-shadow: 0 12px 32px rgba(20, 20, 20, 0.12), 0 0 0 1px $border-standard;
}

// Pill — 4px radius, wash background, status-colored text
@mixin pill($tone: neutral) {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: $font-sans;
  font-size: 12px;
  font-weight: 520;
  border: none;
  // Tone colors applied via BEM modifier or argument
}

// Button variants
@mixin btn-primary {
  @include btn-base;
  background: $accent;
  color: #ffffff;
  border-radius: 6px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 520;

  &:hover:not(:disabled) {
    background: $accent-hover;
  }
}

@mixin btn-secondary {
  @include btn-base;
  background: transparent;
  border: 1px solid $border-standard;
  color: $ink-primary;
  border-radius: 6px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 520;

  &:hover:not(:disabled) {
    background: rgba(20, 20, 20, 0.04);
  }
}

@mixin btn-ghost {
  @include btn-base;
  background: transparent;
  border: none;
  color: $ink-secondary;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 520;

  &:hover:not(:disabled) {
    background: rgba(20, 20, 20, 0.04);
  }
}
```

### Component Build Order

Build in this sequence — each unlocks the next:

1. **Tokens** — Add new SCSS variables to `_variables.scss`, export as CSS custom properties in `design-system.scss`. Keep old tokens alive (dual-token period).
2. **Fonts** — Load Inter, Source Serif 4, JetBrains Mono in `layout.tsx`. Update `$font-sans`, `$font-editorial`, `$font-mono`.
3. **Mixins** — Add typography, elevation, pill, and button mixins to `_mixins.scss`.
4. **`<Pill>`** — BEM component with SCSS, 4px radius, wash backgrounds. The smallest brick — get this right and everything downstream is easier.
5. **`<DataCell>`** — BEM component with built-in tabular-nums and right-align for numerics.
6. **`<Table>`** — BEM component using `<DataCell>`, following the table spec (36px/44px rows). No sticky headers — scroll is always bounded within a flex container, so headers remain in view naturally.
7. **`<KpiCard>`** — BEM component, 36px/620 value, 11px uppercase label.
8. **`<RecordPanel>`** — BEM component with tab strip (13px/520 labels, 2px accent underline).
9. **`<Memo>`** — BEM component that scopes Source Serif 4. Never let serif leak outside this component.
10. **`<RiskFlag>`** — Inline annotation with popover (triangle glyph, dismiss-with-reason).

### Critical Guardrails

- **Serif isolation**: Source Serif 4 is only used inside a `.memo` BEM block. The `@mixin text-memo-body` and `@mixin text-memo-heading` mixins enforce this. Never apply `$font-editorial` in a non-memo context.
- **Numeric formatting**: The `@mixin text-table-cell-numeric` bakes in `tabular-nums`. Every number in a table or KPI must go through a numeric-aware mixin or the `<DataCell numeric>` component.
- **Status color enforcement**: Status colors (`$status-advance`, `$status-caution`, `$status-decline`) are consumed through pill/badge mixins or the `<Pill>` component — never as raw color values in feature SCSS.
- **Weight ceiling**: No SCSS variable or mixin may set `font-weight` above 620. The old `$font-weight-bold: 700` is deprecated.
- **Feature components use BEM + SCSS only**: Tailwind classes are forbidden in feature component SCSS/TSX. Tailwind is permitted only inside `src/components/ui/` for shadcn primitives.
- **Dark mode is a peer**: Every new component must define dark-mode token overrides. Use a `[data-theme="dark"]` or `.dark` selector scope in `design-system.scss`.
