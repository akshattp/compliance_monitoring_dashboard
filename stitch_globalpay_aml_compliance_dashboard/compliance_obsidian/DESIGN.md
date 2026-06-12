---
name: Compliance Obsidian
colors:
  surface: '#f9f9f9'
  surface-dim: '#dadada'
  surface-bright: '#f9f9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3f3'
  surface-container: '#eeeeee'
  surface-container-high: '#e8e8e8'
  surface-container-highest: '#e2e2e2'
  on-surface: '#1a1c1c'
  on-surface-variant: '#444748'
  inverse-surface: '#2f3131'
  inverse-on-surface: '#f1f1f1'
  outline: '#747878'
  outline-variant: '#c4c7c7'
  surface-tint: '#5f5e5e'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#1c1b1b'
  on-primary-container: '#858383'
  inverse-primary: '#c8c6c5'
  secondary: '#5f5e5e'
  on-secondary: '#ffffff'
  secondary-container: '#e4e2e2'
  on-secondary-container: '#656464'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#1b1c1c'
  on-tertiary-container: '#848484'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e5e2e1'
  primary-fixed-dim: '#c8c6c5'
  on-primary-fixed: '#1c1b1b'
  on-primary-fixed-variant: '#474646'
  secondary-fixed: '#e4e2e2'
  secondary-fixed-dim: '#c8c6c6'
  on-secondary-fixed: '#1b1c1c'
  on-secondary-fixed-variant: '#474747'
  tertiary-fixed: '#e3e2e2'
  tertiary-fixed-dim: '#c7c6c6'
  on-tertiary-fixed: '#1b1c1c'
  on-tertiary-fixed-variant: '#464747'
  background: '#f9f9f9'
  on-background: '#1a1c1c'
  surface-variant: '#e2e2e2'
  muted: '#999999'
  light-ui: '#BBBBBB'
  border-base: '#E5E5E5'
  risk-high: '#EF553B'
  risk-medium: '#FFA15A'
  risk-low: '#00CC96'
  risk-unknown: '#636363'
  kpi-label: '#64748B'
  kpi-value: '#0F172A'
  grid-line: '#EEEEEE'
typography:
  page-title:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.02em
  section-heading:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  kpi-label:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  kpi-value:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  kpi-value-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  body-main:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  table-data:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  nav-pill:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 20px
  xl: 24px
  card-padding: 20px
  gutter: 16px
  sidebar-width: 280px
---

## Brand & Style

The design system is engineered for high-stakes financial surveillance and regulatory oversight. It adopts a **Corporate / Modern** aesthetic with a heavy emphasis on **Minimalism** to ensure that critical data points—such as AML (Anti-Money Laundering) risk scores and transaction anomalies—remain the absolute focus.

The visual narrative is one of precision, authority, and uncompromising clarity. By utilizing a strict monochromatic foundation, the system allows functional color (risk signaling) to communicate urgency without visual noise. The interface feels like a sophisticated instrument: calibrated, reliable, and efficient.

**Design Principles:**
- **Data over Decoration:** Every UI element must serve a functional purpose in the audit workflow.
- **Signal vs. Noise:** Use the high-contrast monochromatic palette to fade out secondary controls and amplify critical alerts.
- **Density with Dignity:** Maintain high data density required for enterprise tables while using generous white space and 12px radii to keep the experience modern and accessible.

## Colors

The palette is a "Strict Monochrome Enterprise" system. It is designed to be intentionally desaturated to provide a neutral stage for data visualization and status indicators.

**Key Usage Guidelines:**
- **Primary (#111111):** Reserved for primary actions, active navigation states, and high-level typography.
- **Risk Spectrum:** These are the only vibrant colors permitted. `risk-high` must be used sparingly for immediate attention. `risk-low` indicates a "cleared" or "safe" status.
- **Surface Strategy:** Use `neutral` (#F8F8F8) for the sidebar and page backgrounds to create a subtle contrast with the white (#FFFFFF) KPI and data cards.
- **Secondary/Tertiary/Muted:** These are strictly for chart series and varying levels of text hierarchy to ensure a logical information architecture.

## Typography

This design system utilizes **Inter** for its exceptional legibility in data-heavy environments. The typographic scale is optimized for high-density dashboards where multiple information types (labels, values, metadata) coexist.

**Standardization Notes:**
- **KPI Labels:** Always uppercase with increased letter spacing to distinguish them from interactive data or body text.
- **KPI Values:** These are the largest elements on the page, designed for immediate "at-a-glance" status checks.
- **Tables:** Use the `table-data` style (13px) for AG-Grid rows to maximize the amount of information visible without scrolling.
- **Risk Text:** When text indicates a risk level, use `body-main` weight 600 in the corresponding risk color.

## Layout & Spacing

The layout uses a **Fixed Grid** approach for internal dashboard content to maintain the structural integrity of complex chart arrangements, while utilizing fluid widths for the AG-Grid data tables.

**Layout Model:**
- **Main Shell:** A fixed-width or max-width container (typically 1440px) centered on the screen.
- **Sidebar:** A collapsible left sidebar (280px) houses global filters. It pushes content rather than overlaying it.
- **Grid:** A 12-column system for dashboard layouts. KPI cards typically span 3 columns (4 per row), while primary charts span 6 or 8 columns.
- **Rhythm:** An 8px base unit drives all spacing. KPI cards specifically use a 20px (`lg`) internal padding to provide "breathing room" for large financial values.

**Breakpoints:**
- **Desktop (1200px+):** Full sidebar and 12-column grid.
- **Tablet (768px - 1199px):** Sidebar collapses to icons only. KPI cards reflow to a 2x2 grid.
- **Mobile (<767px):** Single column layout. Top nav pills transform into a scrollable horizontal list.

## Elevation & Depth

Visual hierarchy is achieved through **Tonal Layers** and extremely **Subtle Shadows**. The system avoids aggressive depth to maintain a "flat" enterprise professional feel.

**Elevation Levels:**
- **Surface (Level 0):** Background (#F8F8F8). No shadow.
- **Content Cards (Level 1):** White background with a 1px border (#E5E5E5) and a very soft shadow: `0 4px 6px rgba(0,0,0,0.04)`.
- **Navigation (Level 2):** Active navigation pills use a more pronounced shadow `0 4px 10px rgba(0,0,0,0.2)` to indicate their floating, global nature.
- **Modals/Overlays (Level 3):** Used for drill-down views, utilizing a 15% black backdrop blur and a deeper `0 12px 24px rgba(0,0,0,0.1)` shadow.

## Shapes

The shape language utilizes varied corner radii to distinguish between different types of interface elements.

- **Primary Containers (Cards):** Use a `12px` (Standard Rounded) radius. This softens the high-density data and gives the dashboard a modern, premium feel.
- **Navigation Elements:** Global navigation pills use a **Pill-shape (9999px)** radius, signifying their interactive and global status.
- **Badges:** Risk badges and KPI indicators use a `6px` radius for a sharper, more precise look.
- **Inputs:** Form fields and sidebar filters match the `8px` or `12px` card rounding to maintain consistency across the surface.

## Components

### Navigation
- **Floating Pill Bar:** A centered, fixed-top horizontal container. 
- **Inactive Pills:** Transparent background, primary text.
- **Active Pill:** Primary (#111111) background, white text, subtle shadow.
- **Hover State:** `rgba(0,0,0,0.05)` background with a smooth 0.3s transition.

### KPI Cards
- **Structure:** 20px padding. Label (top-left), Value (center), Sub-value/Trend (below value).
- **Badges:** Small chips in the top-right corner using `#f8fafc` background and a 1px border. They display secondary metrics (e.g., "% of Total").

### AG-Grid Tables
- **Header:** Light gray background (#F8F8F8) with bold 13px text.
- **Rows:** 1px border-bottom (#EEEEEE). High-risk rows must feature a subtle `#EF553B` left-edge border (4px width).
- **Zebra Striping:** Not used; rely on clean border lines for readability.

### Input Fields & Filters
- **Sidebar Filters:** Collapsible sections with "Select All" functionality at the top.
- **Search Bars:** 12px border radius, 1px border (#E5E5E5), with a search icon prefix.

### Charts (Plotly-style)
- **Grid Lines:** Always `#EEEEEE`.
- **Primary Series:** Primary (#111111).
- **Secondary Series:** Secondary (#444444).
- **Muted/Others:** Muted (#999999).