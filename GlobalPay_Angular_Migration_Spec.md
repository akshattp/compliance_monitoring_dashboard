# GlobalPay AML Compliance Dashboard — Angular Migration Specification

**Source:** `Dashboard_V1` (Streamlit + Python)  
**Target:** Angular 17+ (Standalone Components) + FastAPI backend  
**Audience:** New frontend engineering team  

---

## 1. Project Overview

The GlobalPay AML Compliance Dashboard processes monthly foreign exchange transaction workbooks (`TXN LINE MIS`) and runs automated Anti-Money Laundering surveillance rules against them. The Streamlit prototype has been approved and is working in production. This document specifies exactly how to replicate every page, data flow, filter, KPI, and chart in Angular.

### What the app does (end-to-end)

```
User uploads .xlsx workbook (TXN LINE MIS)
        ↓
Backend: Canonical Dataset Creation
  - Column remapping (24 raw cols → standardised names)
  - Data cleaning (identifiers, mobiles, nulls)
  - Derived columns (Day/Week/Month, Daily USD avg, EQV USD)
        ↓
Backend: Risk Enrichment
  - Party Master CSV → Risk Category per corporate
  - OFAC/FATF XLSX   → OFAC _ FATF flag per visiting country
  - Segment standardisation map
        ↓
Backend: Monitoring Engine (8 AML rules)
  - Produces risk_df with boolean flag columns + Risk_Rule_Count
        ↓
Angular: Page routing via top nav bar
  - Each page receives: filteredDf, riskDf, riskFlags
  - Sidebar renders per-page multiselect + date range + FATF toggle
        ↓
Angular: KPI cards + Plotly/Chart.js charts + AG-Grid tables + CSV export
```

---

## 2. Codebase Structure (Streamlit → Angular Mapping)

### Streamlit source tree
```
Dashboard_V1/
├── frontend/
│   ├── app.py                          → app.component.ts (root shell)
│   ├── pages/
│   │   ├── home_page.py                → pages/home/
│   │   ├── transaction_summary.py      → pages/transaction-summary/
│   │   ├── tour_operator.py            → pages/tour-operator/
│   │   ├── retail_high_value_txn.py    → pages/retail-high-value/
│   │   ├── high_risk_corporate.py      → pages/high-risk-corporate/
│   │   ├── fatf.py                     → pages/fatf/
│   │   ├── transaction_monitoring.py   → pages/transaction-monitoring/
│   │   ├── agent_analysis.py           → pages/agent-analysis/
│   │   └── passenger_analysis.py       → pages/passenger-analysis/
│   ├── charts/
│   │   └── theme.py                    → shared/chart-theme.service.ts
│   └── ui_helpers/ui.py               → shared/ui-helpers.pipe.ts + shared/kpi-card.component.ts
├── backend/
│   ├── data_access/canonical_dataset.py → api/routes/upload.py (FastAPI)
│   ├── rules/aml_rules.py              → api/services/aml_rules.py
│   ├── rules/monitoring_engine.py      → api/services/monitoring_engine.py
│   ├── services/*_service.py           → api/services/*.py (one per page)
│   └── utils/filters.py               → api/utils/filters.py
```

### Recommended Angular project structure
```
src/
├── app/
│   ├── core/
│   │   ├── services/
│   │   │   ├── data.service.ts         ← file upload + state management
│   │   │   ├── filter.service.ts       ← global filter state (BehaviorSubject)
│   │   │   └── api.service.ts          ← HTTP calls to FastAPI
│   │   └── models/
│   │       ├── transaction.model.ts
│   │       └── risk-flags.model.ts
│   ├── shared/
│   │   ├── components/
│   │   │   ├── kpi-card/
│   │   │   ├── data-table/             ← AG-Grid wrapper
│   │   │   ├── sidebar-filters/
│   │   │   └── page-header/
│   │   └── pipes/
│   │       └── human-readable-amount.pipe.ts
│   ├── pages/
│   │   ├── home/
│   │   ├── transaction-summary/
│   │   ├── tour-operator/
│   │   ├── retail-high-value/
│   │   ├── high-risk-corporate/
│   │   ├── fatf/
│   │   ├── transaction-monitoring/
│   │   ├── agent-analysis/
│   │   └── passenger-analysis/
│   ├── layout/
│   │   ├── top-nav/
│   │   └── sidebar/
│   └── app.routes.ts
```

---

## 3. Design System & Theme

The approved Streamlit app uses a strict monochrome enterprise palette. Replicate exactly:

### Color palette
| Token | Hex | Usage |
|---|---|---|
| `--color-primary` | `#111111` | Active nav pill, primary buttons, chart series 1 |
| `--color-secondary` | `#444444` | Chart series 2 |
| `--color-tertiary` | `#777777` | Chart series 3, secondary labels |
| `--color-muted` | `#999999` | Chart series 4, muted text |
| `--color-light` | `#bbbbbb` | Chart series 5, borders |
| `--color-bg` | `#ffffff` | Page background |
| `--color-sidebar-bg` | `#f8f8f8` | Sidebar background |
| `--color-card-bg` | `#ffffff` | KPI card background |
| `--color-border` | `#e5e5e5` | Card/divider borders |
| `--color-grid` | `#eeeeee` | Chart grid lines |
| `--color-risk-high` | `#ef553b` | Risk HIGH badge |
| `--color-risk-medium` | `#ffa15a` | Risk MEDIUM badge |
| `--color-risk-low` | `#00cc96` | Risk LOW badge |

### Typography
- **Font family:** `Inter, Segoe UI, sans-serif` (matches Streamlit theme)
- **Page title:** 24px, weight 700, color `#111111`
- **KPI label:** 13px, weight 600, uppercase, letter-spacing 0.5px, color `#64748b`
- **KPI value:** 28–32px, weight 700, color `#0f172a`
- **KPI sub-value:** 16px, weight 500, color `#666666`
- **Section heading:** 18px, weight 600, color `#111111`

### KPI Card CSS (replicate from source)
```scss
.kpi-card {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.04);
  height: 100%;
  position: relative;
}
.kpi-badge {   /* top-right chip */
  position: absolute; top: 16px; right: 16px;
  background: #f8fafc; color: #0f172a;
  font-size: 12px; font-weight: 700;
  padding: 4px 8px; border-radius: 6px;
  border: 1px solid #e2e8f0;
}
```

### Top navigation
The nav is a horizontal pill-style radio-group fixed to the viewport top. Angular equivalent: `RouterLinkActive` + pill-button component.

```scss
.nav-bar {
  position: fixed; top: 0.55rem;
  left: 50%; transform: translateX(-50%);
  z-index: 9999;
  display: flex; gap: 4px;
  overflow-x: auto; scrollbar-width: none;
}
.nav-pill {
  border-radius: 9999px;
  padding: 8px 16px;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  background: transparent; border: none;
  &.active {
    background: #111111;
    color: #ffffff;
    font-weight: 600;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    transform: translateY(-1px);
  }
  &:hover:not(.active) {
    background: rgba(0,0,0,0.05);
    transform: translateY(-1px);
  }
}
```

---

## 4. Angular Routes & Navigation

```typescript
// app.routes.ts
export const routes: Routes = [
  { path: '', redirectTo: 'home', pathMatch: 'full' },
  { path: 'home',                  loadComponent: () => import('./pages/home/home.component') },
  { path: 'transaction-summary',   loadComponent: () => import('./pages/transaction-summary/...') },
  { path: 'tour-operator',         loadComponent: () => import('./pages/tour-operator/...') },
  { path: 'retail-high-value',     loadComponent: () => import('./pages/retail-high-value/...') },
  { path: 'high-risk-corporate',   loadComponent: () => import('./pages/high-risk-corporate/...') },
  { path: 'fatf',                  loadComponent: () => import('./pages/fatf/...') },
  { path: 'transaction-monitoring',loadComponent: () => import('./pages/transaction-monitoring/...') },
  { path: 'agent-analysis',        loadComponent: () => import('./pages/agent-analysis/...') },
  { path: 'passenger-analysis',    loadComponent: () => import('./pages/passenger-analysis/...') },
];
```

Navigation labels (match exactly — these are shown in nav pills):
- `HOME PAGE` → `/home`
- `TRANSACTION SUMMARY` → `/transaction-summary`
- `TOUR OPERATOR` → `/tour-operator`
- `RETAIL HIGH VALUE TXN` → `/retail-high-value`
- `HIGH RISK CORPORATE` → `/high-risk-corporate`
- `FATF` → `/fatf`
- `TRANSACTION MONITORING` → `/transaction-monitoring`
- `AGENT ANALYSIS` → `/agent-analysis`
- `PASSENGER ANALYSIS` → `/passenger-analysis`

---

## 5. Global State & Data Flow

### Upload → State → Pages flow

```typescript
// data.service.ts
@Injectable({ providedIn: 'root' })
export class DataService {
  private riskDf$ = new BehaviorSubject<Transaction[] | null>(null);
  private riskFlags$ = new BehaviorSubject<string[]>([]);
  private sourceRowCount$ = new BehaviorSubject<number>(0);

  uploadFile(file: File): Observable<UploadResponse> {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<UploadResponse>('/api/upload', form).pipe(
      tap(res => {
        this.riskDf$.next(res.risk_df);
        this.riskFlags$.next(res.risk_flags);
        this.sourceRowCount$.next(res.source_row_count);
      })
    );
  }
}
```

The FastAPI `/api/upload` endpoint should:
1. Run `create_canonical_dataset()` 
2. Run `build_transaction_risk_profile()` 
3. Return `{ risk_df: [...], risk_flags: [...], source_row_count: N }` as JSON

### Filter State

```typescript
// filter.service.ts
@Injectable({ providedIn: 'root' })
export class FilterService {
  private filters$ = new BehaviorSubject<PageFilters>({});
  private dateRange$ = new BehaviorSubject<DateRange | null>(null);
  private fatfStatus$ = new BehaviorSubject<'All' | 'Flagged' | 'Not Flagged'>('All');

  getFilteredData(pageKey: string, data: Transaction[]): Transaction[] {
    // Apply multiselect filters + date range + FATF toggle
    // Mirror logic from backend/utils/filters.py → apply_filters()
  }
}
```

### Per-page filter columns (from `PAGE_CONFIG` in `pages/__init__.py`)

| Page | Filter Columns |
|---|---|
| HOME PAGE | Branch Name, Product, Purpose, Txn Type, Corporate, Visiting Country, Risk Category, Currency, Agent Name, OFAC_FATF, Segments |
| TRANSACTION SUMMARY | Branch Name, Txn Type, Purpose, Currency, Risk Category, Segments, Product |
| TOUR OPERATOR | Branch Name, Purpose, Txn Type, Corporate, Agent Name, Visiting Country, Currency, Segments |
| RETAIL HIGH VALUE TXN | Branch Name, Purpose, Txn Type, Corporate, Currency, Agent Name, Segments |
| HIGH RISK CORPORATE | Branch Name, Corporate, Risk Category, Purpose, Agent Name, Currency, Segments, Product |
| FATF | Branch Name, Visiting Country, OFAC_FATF, Purpose, Corporate, Currency, Segments |
| TRANSACTION MONITORING | Branch Name, Corporate, Agent Name, Party Code, Passport, Purpose, Txn Type, Visiting Country, Segments |
| AGENT ANALYSIS | Agent Name, Agent, Branch Name, Branch, Txn Type, Corporate, Visiting Country, Product, Purpose |
| PASSENGER ANALYSIS | Branch Name, Segments, Txn Type |

### Per-page default filters (pre-selected on load)

| Page | Default Filter |
|---|---|
| TOUR OPERATOR | Purpose = `['REMITTANCE BY TOUR OPERATORS', 'MICE -REMITANCE BY TOUR OPERATORS']` |
| HIGH RISK CORPORATE | Risk Category = `['HIGH']` |
| FATF | OFAC_FATF = `['YES', 'OFAC', 'FATF', 'FLAG']` |
| CASH ANALYSIS | Txn Type = `['PB', 'PS']` |
| All others | Select All (no default restriction) |

### All pages also have (always in sidebar)
- **Date Range:** `Start Date` → `End Date` (min/max of dataset)
- **FATF/OFAC Status:** Radio: `All` / `Flagged` / `Not Flagged` (default: All)

---

## 6. Shared Components

### `KpiCardComponent`
Input props: `title: string`, `value: string | number`, `delta?: string`, `badge?: string`

### `PageHeaderComponent`
Renders: `<h1>`, description subtitle, CSV download button.  
Source reference: `render_page_header()` in `ui_helpers/ui.py`

### `HumanReadableAmountPipe`
Converts raw numbers to Indian-style formatted strings:
- ≥ 1 Crore → `₹X.XXCr`
- ≥ 1 Lakh → `₹X.XXL`
- Otherwise → `₹X,XXX`

Source: `backend/utils/formatters.py → human_readable_amount()`

### `DataTableComponent`
AG-Grid wrapper with:
- Column auto-sizing
- Row-level CSV export button
- Search/filter bar
- Pagination (default 50 rows)
- Red highlight for High risk rows

### `ChartThemeService`
Provides a shared Plotly/Chart.js configuration object matching `frontend/charts/theme.py`:
```typescript
export const ENTERPRISE_THEME = {
  colorway: ['#111111','#444444','#777777','#999999','#bbbbbb'],
  font: { family: 'Inter, Segoe UI, sans-serif', color: '#111111', size: 13 },
  paper_bgcolor: '#ffffff',
  plot_bgcolor: '#ffffff',
  gridcolor: '#eeeeee',
  linecolor: '#dddddd',
};
```

---

## 7. Page-by-Page Specification

---

### 7.1 HOME PAGE

**Source file:** `frontend/pages/home_page.py`  
**Backend service:** `backend/services/home_service.py`  
**API endpoint:** `POST /api/pages/home`

#### KPI Cards — Row 1 (5 columns)
| KPI | Field | Format |
|---|---|---|
| Total Transactions Recorded | `total_transactions` | `{:,}` |
| Total Transaction Amount | `total_net_amt` | HumanReadableAmount |
| Average Transaction Value | `average_transaction` | HumanReadableAmount |
| Highest Single Transaction Value | `highest_transaction` | HumanReadableAmount + delta `{highest_pct:.2f}% of Total Amount` |
| Lowest Single Transaction Value | `lowest_transaction` | HumanReadableAmount + delta `-{lowest_pct:.2f}% of Total Amount` |

#### KPI Cards — Row 2 (4 columns)
| KPI | Field | Delta |
|---|---|---|
| PS Count | `ps_count` | `{ps_count_pct:.1f}%` |
| Total PS Amount | `ps_amount` | `{ps_amt_pct:.1f}%` |
| PB Count | `pb_count` | `-{pb_count_pct:.1f}%` |
| Total PB Amount | `pb_amount` | `-{pb_amt_pct:.1f}%` |

#### KPI Cards — Row 3 (3 columns)
| KPI | Field |
|---|---|
| Date Range | `date_range` (formatted as `YYYY-MM-DD → YYYY-MM-DD`) |
| Best Segment | `{best_segment_name} \| {best_segment_amt}` + delta `{best_segment_pct:.1f}%` |
| Best Branch | `{best_branch_name} \| {best_branch_amt}` + delta `{best_branch_pct:.1f}%` |

#### Trend Highlights section
- Toggle: **DAILY** / **WEEKLY** (controls aggregation)
- 4 summary KPIs: Highest Amount Day, Lowest Amount Day, Highest Count Day, Lowest Count Day
- Chart 1: Line chart — Time vs Transaction_Amount
- Chart 2: Line chart — Time vs Transaction_Count

#### Breakdowns section
- Toggle: **NET AMOUNT** / **COUNT** (controls chart metric)
- Number input: "Enter Threshold %" for Purpose grouping (default 1.0)
- Chart 1 (col1): Donut — Purpose-wise share. Hover: Count + Net Amt + %
- Table 1 (col1): Purpose Wise Breakdown table (gray highlight for 'Others' rows)
- Chart 2 (col2): Donut — Product-wise share
- Table 2 (col2): Product Wise Breakdown table
- Chart 3 (col1, row2): Horizontal bar — Branch-wise (sorted ascending by value)
- Chart 4 (col2, row2): Horizontal bar — Country-wise (sorted ascending)

#### Bottom table
- Title: "Top Transactions"
- Data: filtered_df sorted by Net Amt descending
- DataTableComponent with CSV export

---

### 7.2 TRANSACTION SUMMARY

**Source file:** `frontend/pages/transaction_summary.py`  
**Backend service:** `backend/services/transaction_summary_service.py`  
**API endpoint:** `POST /api/pages/transaction-summary`

#### KPI Grid — Transaction types
Display 8 KPI cards in 2 rows of 4:  
Types: `PS`, `PB`, `CB`, `FB`, `FS`, `BB`, `BS`, `BT`

Each card shows:
- Title: `{TYPE} Transactions`
- Big number: `count` (formatted with commas)
- Subtitle: `Amount: {HumanReadableAmount(amount)}`

#### Transaction Analysis by Type
- Donut chart: Txn Type share by Amount (or Count via toggle)
- Horizontal stacked bar: Breakdown by Branch / Product / Segment — toggled via radio

#### Purpose Summary Table
- DataTableComponent showing Purpose-level aggregation
- Columns: Purpose, Count, % Count, Net Amt, % Net Amount

---

### 7.3 TOUR OPERATOR

**Source file:** `frontend/pages/tour_operator.py`  
**Backend service:** `backend/services/tour_operator_service.py`  
**API endpoint:** `POST /api/pages/tour-operator`  
**Default filter:** Purpose IN `['REMITTANCE BY TOUR OPERATORS', 'MICE -REMITANCE BY TOUR OPERATORS']`

#### KPI Cards (2 rows)
Row 1: Txn Count, Total Amount, Contribution to PS %  
Row 2 (Intelligence Cards): Best Operator, Best Beneficiary (Party Code), Best Branch, Best Country  
Each Intelligence Card shows: name (large), amount/count (medium), % share (badge)

#### Charts
1. **Pie — Purpose Mix:** `REMITTANCE BY TOUR OPERATORS` vs `MICE`. Colors: `#111111` / `#888888`
2. **Stacked Horizontal Bar — Top Branches:** by Transaction Count, stacked by Purpose Type. Sorted by total descending.
3. **Stacked Horizontal Bar — Top Operators (Corporate):** by Transaction Count, stacked by Purpose Type.
4. **Combo chart — Country:** Line for count, Bar for Amount. X-axis = Visiting Country.

#### Observations section
Display bullet-point observations generated by `get_tour_operator_observation()` service function. These are textual compliance flags (e.g. "Top operator X represents Y% of tour remittances").

#### Table
DataTableComponent: filtered tour operator transactions

---

### 7.4 RETAIL HIGH VALUE TXN

**Source file:** `frontend/pages/retail_high_value_txn.py`  
**Backend service:** `backend/services/retail_high_value_service.py`  
**API endpoint:** `POST /api/pages/retail-high-value`

#### Risk Classification Logic (replicate in Angular/API)
Threshold: transactions classified as High Value if `EQV USD > 10,000`  
Risk levels assigned by `classify_retail_risk_level()`:
- **HIGH:** FATF flagged OR Risk Category = HIGH
- **MEDIUM:** Risk Category = MEDIUM OR amount > 25,000 USD
- **LOW:** otherwise

#### KPI Cards
From `calculate_kpis()`:
- Total High-Value Txns, Total USD Exposure, Avg USD per Txn, Highest Single USD, Structuring Candidates (20,000–25,000 range)

#### Charts
1. **Donut — Risk Level Distribution:** HIGH / MEDIUM / LOW / UNKNOWN. Colors: `#ef553b` / `#ffa15a` / `#00cc96` / `#636363`
2. **Horizontal Bar — Top Branches by USD Exposure** (top 15)
3. **Vertical Bar — Top Corporates by USD Exposure** (top 15)
4. **Scatter or Bar — Customer Concentration** (top customers by transaction frequency)
5. **Donut — Product-wise Distribution**
6. **Horizontal Bar — Currency-wise Distribution**

#### Observations
Textual list from `generate_observations()` — compliance flags for reporting.

#### Table
High-value transactions with columns: Date, Branch Name, Corporate, Txn Type, Currency, Net Amt, EQV USD, Retail_Risk_Level

---

### 7.5 HIGH RISK CORPORATE

**Source file:** `frontend/pages/high_risk_corporate.py`  
**Backend service:** `backend/services/high_risk_corporate_service.py`  
**API endpoint:** `POST /api/pages/high-risk-corporate`  
**Default filter:** Risk Category = `['HIGH']`

#### Special Input
This page requires a secondary file upload for Party Master.  
In Angular: secondary drag-and-drop area or file picker for `Party Master New report.csv`.  
On upload: POST to `/api/upload/party-master` → returns enriched dataset.

#### Corporate Risk Overview KPIs
From `get_corporate_risk_kpis()`:
- Total High-Risk Corporates, Total Txns (HIGH), Total Amount (HIGH), % of Overall Transactions, % of Overall Amount, Avg Txn per Corporate

Each card uses the badge pattern (small risk-category badge in top-right corner).

#### Charts
1. **Donut — Risk Distribution** (HIGH / MEDIUM / LOW / UNKNOWN)
2. **Horizontal Bar — Top Corporates** by Txn Amount (top 10)
3. **Horizontal Bar — Branch Exposure** by total amount
4. **Horizontal Bar — Country Exposure** (Visiting Country by amount)
5. **Grouped Bar or Stacked Bar — Product Exposure** by product type

#### Trend Chart
Line chart: monthly/weekly trend of High Risk Corporate transaction amounts

#### Tables
- Corporate-level summary (Corporate, Count, Amount, % Share, Risk Category)
- Detailed transaction table with DataTableComponent

---

### 7.6 FATF

**Source file:** `frontend/pages/fatf.py`  
**Backend service:** `backend/services/fatf_service.py`  
**API endpoint:** `POST /api/pages/fatf`  
**Default filter:** OFAC_FATF IN `['YES', 'OFAC', 'FATF', 'FLAG']`

#### Special Input
Requires OFAC/FATF reference file: `OFAC_FATF COUNTRY UPDATED.xlsx` (sheet: `UPDATED FILE`).  
If already uploaded in another session, reuse from shared state (the Streamlit app shares this across tabs via session state).

#### KPI Cards (4 columns)
- Flagged Transactions (count)
- Flagged Amount (HumanReadableAmount)
- Contribution % (count-based)
- Contribution Amount %

#### Charts
1. **Grouped Bar — Branch vs Segments** (X=Branch Name, Y=Count, Color=Segments, barmode=group)
2. **Grouped Bar — Visiting Country vs Segments** (X=Visiting Country, Y=Count, Color=Segments)
3. **Bar — Purpose-wise flagged count** (X=Purpose, Y=Count)
4. **Line — Flagged Transaction Trend** over time

#### Table
DataTableComponent: all flagged transactions  
Columns: Date, Branch Name, Visiting Country, Corporate, Purpose, Currency, Net Amt, OFAC_FATF segment

---

### 7.7 TRANSACTION MONITORING

**Source file:** `frontend/pages/transaction_monitoring.py`  
**Backend service:** `backend/services/transaction_monitoring_service.py`  
**API endpoint:** `POST /api/pages/transaction-monitoring`

This is the core AML detection page. It runs 8 rule detectors and displays results for each.

#### Rule Detectors — each rendered as an expandable panel

| Rule | Function | Threshold/Logic |
|---|---|---|
| **Rule 1: High Value Transactions** | `detect_high_value_transactions()` | EQV USD > 25,000. Also detects structuring (20,000–25,000). |
| **Rule 2: FATF/OFAC Flagged** | `detect_fatf_ofac()` | Requires OFAC file. Returns flagged rows. |
| **Rule 3: Multiple Operators → Same Beneficiary** | `detect_multiple_operators_same_beneficiary()` | Party Code served by >1 Agent Name |
| **Rule 4: High Frequency Remittances** | `detect_high_frequency_remittances()` | Party Code appears ≥5 times (configurable) |
| **Rule 5: Load-Refund Window** | `detect_configurable_load_refund_window()` | Card loaded then refunded within N days (configurable) |
| **Rule 6: Multiple Cards per Contact** | `detect_multiple_cards_contact()` | Same MOBILENO → multiple INSTRUMENTNO |
| **Rule 7: Multiple Cards per Traveller** | `detect_multiple_cards_traveller()` | Same Passport → multiple INSTRUMENTNO |
| **Rule 8: Multi-Operator Traveller** | `detect_multiple_cards_multi_operator` | Same Passport → multiple Agent Names |

#### Page-level KPI Summary (from `summarize_cases()`)
Top row: count of cases flagged per rule (8 metric cards)

#### For each rule section, render
- Expandable accordion panel with rule title + case count badge
- Bar chart: Count by Branch (or by Agent/Corporate depending on rule)
- Pie chart: Count distribution by Risk Category
- DataTableComponent: full flagged records with CSV download

#### Configurable inputs (shown above rule sections)
- **High Value Threshold:** number input (default 25000 USD)
- **Frequency Threshold:** number input (default 5 transactions)
- **Load-Refund Window:** number input in days (default 30)

---

### 7.8 AGENT ANALYSIS

**Source file:** `frontend/pages/agent_analysis.py`  
**Backend service:** `backend/services/agent_analysis_service.py`  
**API endpoint:** `POST /api/pages/agent-analysis`

#### KPI Cards
From `get_agent_kpis()`:
- Total Agents, Total Agent Transactions, Total Agent Amount, Contribution % to overall

Each card uses the badge pattern with agent name or % badge.

#### Charts
1. **Bar — Agent Frequency Table** (top agents by transaction count)
2. **Line or Bar — Agent Trend** over time
3. **Suspicious Agent Panels** (3 sub-sections):
   - Agents with many relationships (many-to-many)
   - Agent → Many Beneficiaries (1 agent, many Party Codes)
   - Agent → 1 Beneficiary (high frequency to same Party Code)

#### Tables
- Agent frequency table: Agent Name, Count, Net Amt, % Share
- Suspicious agents detail table with DataTableComponent

---

### 7.9 PASSENGER ANALYSIS

**Source file:** `frontend/pages/passenger_analysis.py`  
**Backend service:** `backend/services/passenger_analysis_service.py`  
**API endpoint:** `POST /api/pages/passenger-analysis`

#### KPI Cards — Row 1 (3 columns)
- Total Records
- PAN Card IDs (count + % of total)
- Passport IDs (count + % of total)

#### KPI Cards — Row 2 (3 columns)
- Invalid/Unknown IDs (count + negative delta %)
- Blank IDs (count + negative delta %)
- Most Frequent Identity (PAX ID + Doc Type, Name, Times seen + %)

#### Anomaly Detection Rules (8 expandable accordion panels)

| Rule | Logic |
|---|---|
| **Rule A: Same PAX ID, Different Emails** | Single Passport/PAN → multiple distinct EMAILID values |
| **Rule B: Same PAX ID, Different Names** | Single Passport/PAN → multiple distinct Passenger Names |
| **Rule C: Same PAX ID, Different Mobiles** | Single Passport/PAN → multiple distinct MOBILENO values |
| **Rule D: Missing PAX ID with Contact Info** | Passport is blank/null but EMAILID or MOBILENO present |
| **Rule E: Same Email, Different PAX IDs** | Single EMAILID → multiple distinct Passports/PANs |
| **Rule F: Same Mobile, Different PAX IDs** | Single MOBILENO → multiple distinct Passports/PANs |
| **Rule G: Frequent Passenger** | PAX ID appears ≥ threshold (configurable, default 10) |
| **Rule H: Duplicate/Shared Identity** | Passport appears for >1 distinct Passenger Name |

Each panel shows: description text, count of flagged records, DataTableComponent with records.

#### Threshold Input
Number input: "Transaction Count Threshold for Frequent Passenger" (default 10, min 2)

---

## 8. FastAPI Backend Endpoints

All existing Python service files can be adapted to FastAPI with minimal changes.

### Core endpoints

```
POST /api/upload
  Body: multipart/form-data { file: .xlsx }
  Returns: { risk_df: [...], risk_flags: [...], source_row_count: N }

POST /api/upload/party-master
  Body: multipart/form-data { file: .csv }
  Returns: { enriched_df: [...] }

POST /api/upload/ofac
  Body: multipart/form-data { file: .xlsx }
  Returns: { ofac_df: [...] }

POST /api/filter-options
  Body: { page_key: string, columns: string[] }
  Returns: { options: { [column]: string[] } }

POST /api/pages/home
  Body: { filtered_df: [...] }
  Returns: { kpis: {...}, trends: {...}, breakdowns: {...} }

POST /api/pages/transaction-summary
POST /api/pages/tour-operator
POST /api/pages/retail-high-value
POST /api/pages/high-risk-corporate
POST /api/pages/fatf
POST /api/pages/transaction-monitoring
POST /api/pages/agent-analysis
POST /api/pages/passenger-analysis
```

> **Performance note:** For large workbooks, consider storing the processed `risk_df` server-side (Redis or in-memory) keyed by a session token, and passing only the token + filter params in subsequent page requests — rather than re-posting the full dataframe on every page navigation.

---

## 9. AML Rules Logic (for Client-Side Reference)

These 8 rules are computed server-side in `aml_rules.py`. The Angular frontend only displays results — do not reimplement rule logic in TypeScript.

| Rule | Column Produced | Logic Summary |
|---|---|---|
| High Value | `High_Value_Flag` | `Net Amt > 10,000` |
| FATF/OFAC | `FATF_Flag` | `OFAC _ FATF` contains FATF/OFAC/FLAG/YES |
| Multi-Operator Beneficiary | `Multi_Operator_Beneficiary` | Party Code served by >1 Agent |
| High Frequency | `High_Freq_Beneficiary` | Party Code appears ≥5 times |
| Same Traveller Multi-Operator | `Same_Traveller_Multi_Operator` | Passport → >1 Agent Name |
| Same Traveller Multi-Beneficiary | `Same_Traveller_Multi_Beneficiary` | Passport → >1 Party Code |
| Duplicate Cards (traveller) | `Duplicate_Card_Traveller` | Passport → >1 INSTRUMENTNO |
| Reload Frequency | `Reload_Freq_Flag` | Beneficiary has ≥3 RELOAD transactions |

The `monitoring_engine.py` aggregates these into:
- `Risk_Rule_Count` — integer (0–8), how many rules a row triggered
- `Any_Risk_Flag` — boolean, `Risk_Rule_Count > 0`

---

## 10. Data Models (TypeScript interfaces)

```typescript
// transaction.model.ts
export interface Transaction {
  Branch: string;
  'Branch Name': string;
  'Txn Type': string;
  'Doc Number': string;
  Date: string;              // ISO date string
  'Party Code': string;
  Corporate: string;
  'Passenger Name': string;
  Passport: string;
  Agent: string;
  'Agent Name': string;
  Purpose: string;
  Currency: string;
  Product: string;
  Issuer: string;
  Rate: number;
  'Visiting Country': string;
  'Load Reload Type': string;
  Segments: string;
  'Beneficiary Type Load or Reload': string;
  'Net Amt': number;
  EMAILID: string;
  MOBILENO: string;
  // Derived
  Day: string;
  Week: number;
  Month: number;
  Year: number;
  'Daily_USD_Avg_Rate': number;
  'EQV USD': number;
  // Enrichment
  'Risk  Category': 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';
  'OFAC _ FATF': string;
  'FATF / OFAC Flag': boolean;
  // Risk flags
  Risk_Rule_Count: number;
  Any_Risk_Flag: boolean;
  [key: string]: any;
}

export interface PageFilters {
  [column: string]: string[];
}

export interface DateRange {
  start: Date;
  end: Date;
}

export interface RiskFlags {
  High_Value_Flag: boolean;
  FATF_Flag: boolean;
  Multi_Operator_Beneficiary: boolean;
  High_Freq_Beneficiary: boolean;
  Same_Traveller_Multi_Operator: boolean;
  Same_Traveller_Multi_Beneficiary: boolean;
  Duplicate_Card_Traveller: boolean;
  Reload_Freq_Flag: boolean;
}
```

---

## 11. Recommended Angular Libraries

| Purpose | Library | Why |
|---|---|---|
| Charts | `plotly.js` (via `angular-plotly.js`) | Exact match to existing Streamlit charts (Plotly) — zero visual delta |
| Data tables | `ag-grid-angular` (Community) | Matches the filter/sort/export behavior of `render_table_with_options()` |
| File upload | `ngx-dropzone` or native `<input type="file">` | Two upload zones needed (main XLSX + Party Master CSV + OFAC XLSX) |
| HTTP | `HttpClient` (built-in) | Standard Angular HTTP |
| State | `@ngrx/store` or RxJS `BehaviorSubject` | For global riskDf state shared across all pages |
| Date picker | Angular Material `<mat-datepicker>` | Matches Streamlit date_input |
| Multiselect | `ng-select` | Matches Streamlit multiselect with "Select All" behaviour |
| Notifications | Angular Material `MatSnackBar` | For upload success/error toasts |

---

## 12. Sidebar Filters — Implementation Notes

The sidebar filter component must support a **"Select All" toggle** pattern:

```typescript
// sidebar-filters.component.ts
// Logic from app.py → build_page_filters()

onOptionChange(column: string, selected: string[]) {
  if (selected.includes('SELECT ALL')) {
    this.selectedFilters[column] = this.allOptions[column];
  } else {
    this.selectedFilters[column] = selected;
  }
  this.filterChange.emit(this.selectedFilters);
}
```

When all options are pre-selected (default state), show "Select All" as the visible selection in the dropdown — not every individual value. This reduces visual noise. Match exactly the behavior in `build_page_filters()` in `app.py`.

---

## 13. CSV Export

Every page has a download button for the current filtered dataset.  
Source: `build_download_button()` in `home_page.py`.

```typescript
// Angular implementation
exportToCsv(data: Transaction[], filename: string) {
  const csv = this.convertToCsv(data);
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename || 'filtered_transactions.csv';
  a.click();
}
```

---

## 14. Special Page Behaviors

### HIGH RISK CORPORATE
- This page is **non-functional without a Party Master upload.** Show a clear info banner: "Please upload the Party Master New report.csv file to enable this page."
- The Party Master file can be pre-bundled in the backend at startup (`data/Party Master New Report.csv`) — in that case expose it as a default that can be overridden.

### FATF
- Similarly requires OFAC/FATF XLSX. The backend pre-bundles `data/OFAC_FATF COUNTRY UPDATED.xlsx`.
- In Angular: if the backend already has the reference file, the page loads normally. Show an override option for when compliance officers need to use a newer list.

### TRANSACTION MONITORING
- The FATF/OFAC sub-detector (Rule 2) also requires the OFAC file.
- Share a single uploaded OFAC file across FATF page and Transaction Monitoring page — use a shared service to cache the uploaded file reference.

---

## 15. Column Mapping Reference

Raw Excel columns → Canonical dataset column names:

| Raw Column | Canonical Name |
|---|---|
| `BRANCHCODE` | `Branch` |
| `LOCATION` | `Branch Name` |
| `TXNTYPE` | `Txn Type` |
| `DOCNO` | `Doc Number` |
| `TXNDATE` | `Date` |
| `CUSTOMERCODE` | `Party Code` |
| `CUSTOMERNAME` | `Corporate` |
| `PAXNAME` | `Passenger Name` |
| `PAXIDNO` | `Passport` |
| `AGENTCODE` | `Agent` |
| `AGENTNAME` | `Agent Name` |
| `TxnPurpose` | `Purpose` |
| `CURRENCY` | `Currency` |
| `PRODUCT` | `Product` |
| `ISSUER` | `Issuer` |
| `SELLRATE` | `Rate` |
| `CountryToTravel` | `Visiting Country` |
| `INSTRUMENTNO` | `Instrument Number` |
| `LoadReload` | `Load Reload Type` |
| `Segment` | `Segments` |
| `BENEFICIARY` | `Beneficiary Type Load or Reload` |
| `INRAMOUNT` | `Net Amt` |
| `EMAILID` | `EMAILID` |
| `MOBILENO` | `MOBILENO` |

---

## 16. Segment Standardization Map

The canonical dataset standardizes legacy segment names. Reference list from `canonical_dataset.py`:

```python
SEGMENT_STANDARDIZATION_MAP = {
  'Students Credila': 'EDUCATION',
  'Tour Remittance': 'TOUR OPERATOR',
  # ... (full map in canonical_dataset.py)
}
```

This runs **server-side** only. The Angular frontend will always see standardized segment names.

---

## 17. Implementation Priority

Build in this order to ship a working MVP quickly:

1. **Upload flow + canonical dataset API** (all pages depend on this)
2. **Home Page** (validates the full data pipeline)
3. **Sidebar filter service** (unblocks all other pages)
4. **Transaction Summary** (simple, no secondary uploads)
5. **FATF** (validates the OFAC integration)
6. **Transaction Monitoring** (most complex — do last among core pages)
7. **Tour Operator, Retail High Value, High Risk Corporate, Agent Analysis, Passenger Analysis** (can be parallelised once shared components exist)

---

*Document generated from full codebase analysis of `Dashboard_V1` (Streamlit). Last updated: June 2026.*
