# Level-2 Technical Migration Blueprint: GlobalPay AML & Compliance Platform

This document contains the implementation-level specifications required to rewrite the Streamlit-based Python application into a modern Single Page Application (React.js / Angular) supported by a robust backend (Node.js / Python FastAPI) and a relational database (PostgreSQL / Snowflake).

---

## Table of Contents
1. Complete Page Execution Flow
2. Exact KPI Calculation Formulas
3. Exact Chart Generation Logic
4. Complete AML Rule Implementation Logic
5. Group-by and Aggregation Pseudocode
6. Filter Engine Architecture & Execution Order
7. Session State Architecture & Lifecycle
8. Complete Canonical Dataset Pipeline
9. Full Data Dictionary
10. Monitoring Rule Dependency Matrix
11. React Component Inventory & Hierarchy
12. Angular Module & Component Hierarchy
13. API Contracts (Request/Response Schemas)
14. Database Schema Recommendations
15. Export Engine Architecture
16. Caching Strategy
17. Performance Optimization Strategy
18. Error Handling Flows
19. User Interaction Flows
20. State Management Architecture
21. Route Mapping Architecture
22. Security Model & Access Control
23. Pseudocode for Critical Business Logic
24. Detailed Transaction Monitoring Execution Flow
25. Data Lineage Diagrams

---

## 25. Data Lineage Diagrams

### Raw File to Final Dashboard
```text
[Raw Excel TXN MIS] 
       │
       ▼ (Parse & Extract)
[Raw Dataframe / Staging Table]
       │
       ▼ (Column Mapping & Data Cleaning Regex)
[Standardized Dataframe] ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
       │                                           │
       ▼ (Left Join ON Party Code)                 ▼
[Party Master Enrichment]                 [Daily USD Rate Aggregation]
       │                                           │
       ▼ (Left Join ON Country)                    ▼
[OFAC / FATF Enrichment]                  [EQV USD Calculation]
       │                                           │
       ▼                                           ▼
[Merged Canonical Dataset] ◄ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
       │
       ▼ (Monitoring Engine Execution)
[Enriched Risk Profile] (Appends Rule Flags: Rule1_Flag, Rule2_Flag... Risk_Score)
       │
       ▼ (Global UI Filters Applied)
[Filtered Presentation Dataset]
       │
       ├─► [KPI Aggregation Engine] ────► [UI KPI Cards]
       ├─► [Chart Aggregation Engine] ──► [UI Visualizations]
       └─► [Table Pagination Engine] ───► [UI Data Grids] & [CSV Export]
```

---

## 8. Complete Canonical Dataset Pipeline

### Transformation Steps (Backend ETL Pipeline)
1. **Ingestion:** Read `.xlsx` buffer. Drop rows where all mapped columns are completely null.
2. **Column Projection:** Rename columns strictly to standard names (e.g., `TXNTYPE` -> `Txn Type`).
3. **Identifier Cleaning (Regex & String Manipulation):**
   * Applies to: `INSTRUMENTNO`, `Party Code`, `Agent`, `Passport`.
   * Logic: 
     * Convert to string, strip whitespace.
     * Remove exact bounding special characters: `'`, `` ` ``, `~`, `#`, `*`, `"`.
     * Regex `s.replace(/\.0$/, '')` to remove accidental float cast suffixes.
     * Regex `s.replace(/[^\x20-\x7E]/g, '')` to strip invisible/non-printable unicode.
4. **Mobile Number Cleaning:**
   * Applies to: `MOBILENO`.
   * Logic: String cast, remove `.0` suffix, `s.replace(/\s+/g, '')` (remove all spaces). Map `'NAN', 'NONE', 'NULL', ''` to `NULL`.
5. **Date Parsing:** Cast `Date` to Standard ISO-8601 DateTime. Generate `Day`, `Week`, `Month`, `Year`, `Weekday`.
6. **Numeric Coercion:** Cast `Net Amt` and `Rate` to float. Fill `NULL` with `0.00`.
7. **Party Master Join:**
   * Apply identifier cleaning to `CUSTOMERCODE` in Party Master.
   * `LEFT JOIN` on `Party Code = CUSTOMERCODE`. Map `RISKCATEGORY_PM` to `Risk Category` (High, Medium, Low, Unknown).
8. **OFAC / FATF Join:**
   * Trim and UPPERCASE both `Visiting Country` and Master `COUNTRY`.
   * `LEFT JOIN`. Coalesce mapped segment to `'NOT FLAGGED'`.
9. **Daily USD Rate Calculation:**
   * Subquery: `SELECT Date, AVG(Rate) as Daily_USD_Avg_Rate FROM staging WHERE Currency = 'USD' GROUP BY Date`.
   * Broadcast/Join back to main dataset. Backfill/Forward-fill missing dates if necessary.
   * Calculate `EQV USD` = `Net Amt` / `Daily_USD_Avg_Rate`.
10. **Segment Standardization:**
    * Switch `Segment` mapping: `'Students Credila' -> 'EDUCATION'`, `'Tour Remittance' -> 'TOUR OPERATOR'`, etc. Default unmatched to `'OTHER'`.

---

## 9. Full Data Dictionary

| Column Name | Data Type | Source Mapping | Nullable | Description / Validation |
| :--- | :--- | :--- | :--- | :--- |
| `Branch` | VARCHAR | `BRANCHCODE` | Yes | Branch ID. |
| `Branch Name` | VARCHAR | `LOCATION` | No | Full name of the branch. |
| `Txn Type` | VARCHAR(2) | `TXNTYPE` | No | Enumerated: `PS`, `PB`, `CB`, `FB`, etc. |
| `Doc Number` | VARCHAR | `DOCNO` | Yes | System generated transaction receipt ID. |
| `Date` | DATE | `TXNDATE` | No | Execution date of the transaction. |
| `Party Code` | VARCHAR | `CUSTOMERCODE` | No | Cleaned corporate entity ID. |
| `Corporate` | VARCHAR | `CUSTOMERNAME` | Yes | Name of the corporate entity/remitter. |
| `Passenger Name` | VARCHAR | `PAXNAME` | Yes | Name of the ultimate traveller/beneficiary. |
| `Passport` | VARCHAR | `PAXIDNO` | Yes | Cleaned passenger ID (PAN/Passport). |
| `Agent Name` | VARCHAR | `AGENTNAME` | Yes | Third-party booking agent name. |
| `Purpose` | VARCHAR | `TxnPurpose` | Yes | Regulatory reason code (e.g., Leisure, Education). |
| `Currency` | VARCHAR(3) | `CURRENCY` | No | ISO 4217 Currency Code. |
| `Product` | VARCHAR(2) | `PRODUCT` | No | Enumerated: `EC`, `FC`, `TT`, `DD`. |
| `Rate` | DECIMAL(10,4)| `SELLRATE` | No | Exchange rate applied. Defaults to 0. |
| `Visiting Country` | VARCHAR | `CountryToTravel`| Yes | Destination country. |
| `Instrument Number` | VARCHAR | `INSTRUMENTNO` | Yes | Cleaned Prepaid Card Number. |
| `Load Reload Type` | VARCHAR | `LoadReload` | Yes | Enumerated: `LOAD`, `RELOAD`, `REFUND`. |
| `Segments` | VARCHAR | `Segment` | Yes | Standardized business unit segment. |
| `Beneficiary Type...`| VARCHAR | `BENEFICIARY` | Yes | Name of the receiving party/institution. |
| `Net Amt` | DECIMAL(18,2)| `INRAMOUNT` | No | Base currency volume. |
| `EMAILID` | VARCHAR | `EMAILID` | Yes | Customer email address. |
| `MOBILENO` | VARCHAR | `MOBILENO` | Yes | Cleaned mobile number (no spaces/decimals). |
| `EQV USD` | DECIMAL(18,2)| *Derived* | No | Calculated USD exposure for thresholding. |
| `Risk Category` | VARCHAR | *Derived* | No | `High`, `Medium`, `Low`, `Unknown`. |
| `OFAC _ FATF` | VARCHAR | *Derived* | No | Target list segment name or `NOT FLAGGED`. |
| `Risk_Rule_Count` | INTEGER | *Derived* | No | Sum of triggered AML rules (0-8). |

---

## 14. Database Schema Recommendations

For scalable backend migration, an RDBMS (PostgreSQL) is recommended.

```sql
CREATE TABLE tx_master (
    txn_id UUID PRIMARY KEY,
    batch_id UUID REFERENCES upload_batches(batch_id),
    branch_name VARCHAR(100),
    txn_type VARCHAR(5),
    txn_date DATE,
    party_code VARCHAR(50),
    corporate_name VARCHAR(255),
    passenger_name VARCHAR(255),
    passport_no VARCHAR(50),
    purpose VARCHAR(100),
    currency VARCHAR(3),
    product VARCHAR(5),
    rate DECIMAL(15, 6),
    visiting_country VARCHAR(100),
    instrument_no VARCHAR(50),
    load_reload_type VARCHAR(20),
    segments VARCHAR(50),
    beneficiary VARCHAR(255),
    net_amt DECIMAL(18, 2),
    email_id VARCHAR(255),
    mobile_no VARCHAR(20),
    eqv_usd DECIMAL(18, 2)
);

CREATE TABLE risk_profiles (
    txn_id UUID PRIMARY KEY REFERENCES tx_master(txn_id),
    party_risk_category VARCHAR(20),
    fatf_flag BOOLEAN,
    ofac_segment VARCHAR(100),
    rule1_high_value BOOLEAN,
    rule2_fatf BOOLEAN,
    rule3_multi_op BOOLEAN,
    rule4_high_freq BOOLEAN,
    rule5_load_refund BOOLEAN,
    rule6_multi_card_contact BOOLEAN,
    rule7_multi_card_traveller BOOLEAN,
    rule8_multi_card_multi_op BOOLEAN,
    risk_rule_count INTEGER,
    any_risk_flag BOOLEAN
);

CREATE INDEX idx_tx_date ON tx_master(txn_date);
CREATE INDEX idx_tx_instrument ON tx_master(instrument_no);
CREATE INDEX idx_risk_count ON risk_profiles(risk_rule_count);
```

---

## 4. Complete AML Rule Implementation Logic & 5. Pseudocode

### Rule 1: High Value Transaction
*   **Logic:** Simple thresholding on calculated USD exposure.
*   **SQL Pseudocode:**
    ```sql
    UPDATE risk_profiles SET rule1_high_value = TRUE 
    FROM tx_master t WHERE risk_profiles.txn_id = t.txn_id AND t.eqv_usd > 25000;
    ```

### Rule 2: FATF / OFAC Match
*   **Logic:** String match against pre-joined master list column.
*   **SQL Pseudocode:**
    ```sql
    UPDATE risk_profiles SET rule2_fatf = TRUE 
    WHERE ofac_segment != 'NOT FLAGGED' AND ofac_segment IS NOT NULL;
    ```

### Rule 3: Multiple Operators to Same Beneficiary
*   **Logic:** Detects Hawala routing. Segments = 'TOUR OPERATOR'. Group by Beneficiary. Count distinct operators (Party Code) > 5.
*   **SQL Pseudocode:**
    ```sql
    WITH SuspiciousBens AS (
        SELECT beneficiary, DATE_TRUNC('month', txn_date) as window
        FROM tx_master WHERE UPPER(segments) = 'TOUR OPERATOR'
        GROUP BY beneficiary, DATE_TRUNC('month', txn_date)
        HAVING COUNT(DISTINCT party_code) > 5
    )
    UPDATE risk_profiles SET rule3_multi_op = TRUE 
    FROM tx_master t JOIN SuspiciousBens sb ON t.beneficiary = sb.beneficiary 
    WHERE risk_profiles.txn_id = t.txn_id;
    ```

### Rule 4: High-Frequency Remittances to Single Beneficiary
*   **Logic:** Segments = 'TOUR OPERATOR'. Group by Month, Beneficiary, Party Code. Transaction Count > 5.
*   **SQL Pseudocode:**
    ```sql
    WITH SuspiciousPairs AS (
        SELECT beneficiary, party_code, DATE_TRUNC('month', txn_date) as window
        FROM tx_master WHERE UPPER(segments) = 'TOUR OPERATOR'
        GROUP BY beneficiary, party_code, DATE_TRUNC('month', txn_date)
        HAVING COUNT(*) > 5
    )
    -- Update corresponding IDs
    ```

### Rule 5: Configurable Load-to-Refund Window
*   **Logic:** Product EC/FC. Match LOAD/RELOAD (PS) with REFUND (PB or unspecified). Calculate days between.
*   **SQL Pseudocode:**
    ```sql
    WITH Loads AS (
        SELECT txn_id, instrument_no, txn_date as load_date, net_amt as load_amt 
        FROM tx_master 
        WHERE product IN ('EC', 'FC') AND txn_type = 'PS' AND UPPER(load_reload_type) IN ('LOAD', 'RELOAD')
    ),
    Refunds AS (
        SELECT txn_id, instrument_no, txn_date as refund_date, net_amt as refund_amt 
        FROM tx_master 
        WHERE product IN ('EC', 'FC') AND UPPER(load_reload_type) = 'REFUND'
    ),
    MatchedPairs AS (
        SELECT l.txn_id as load_txn_id, r.txn_id as refund_txn_id, 
               (r.refund_date - l.load_date) as within_days
        FROM Loads l JOIN Refunds r ON l.instrument_no = r.instrument_no
        WHERE (r.refund_date - l.load_date) >= 0 AND (r.refund_date - l.load_date) <= :threshold_days
    )
    -- Flag both load_txn_id and refund_txn_id in risk_profiles.
    ```

### Rule 6: Multiple Cards Linked to Same Contact Information
*   **Logic:** Smurfing detection. Group by Mobile, distinct Instrument count >= 3.
*   **SQL Pseudocode:**
    ```sql
    WITH SuspiciousMobiles AS (
        SELECT mobile_no FROM tx_master 
        WHERE product IN ('EC', 'FC') AND txn_type = 'PS' AND mobile_no IS NOT NULL
        GROUP BY mobile_no HAVING COUNT(DISTINCT instrument_no) >= 3
    )
    -- Update flags for matching mobiles.
    ```

### Rule 7 & 8: Multi-Card Traveller & Multi-Operator
*   **Logic:** Group by Passenger Name.
    *   Rule 7: `HAVING COUNT(DISTINCT instrument_no) >= 2`
    *   Rule 8: `HAVING COUNT(DISTINCT instrument_no) >= 2 AND COUNT(DISTINCT corporate_name) >= 2`

---

## 10. Monitoring Rule Dependency Matrix

| Rule | Required Columns | Pre-requisite Filter | Threshold Configurable? |
| :--- | :--- | :--- | :--- |
| **Rule 1 (High Value)** | `EQV USD` | None | Yes ($25,000 global, $20,000 alert) |
| **Rule 2 (FATF/OFAC)** | `Visiting Country` | Requires `OFAC_master` Table | No |
| **Rule 3 & 4 (Tour Op)** | `Segments`, `Beneficiary`, `Party Code` | `Segments = 'TOUR OPERATOR'` | Yes (Freq > 5) |
| **Rule 5 (Load/Refund)** | `Product`, `Txn Type`, `Load Reload Type`, `Instrument No`, `Date` | `Product IN ('EC', 'FC')` | Yes (0 to N days) |
| **Rule 6 (Contact Link)** | `Product`, `Txn Type`, `Mobile No`, `Instrument No` | `Product IN ('EC', 'FC')` & `PS`| No (Fixed >= 3) |
| **Rule 7 & 8 (Pax Link)** | `Product`, `Txn Type`, `Passenger Name`, `Instrument No`, `Corporate` | `Product IN ('EC', 'FC')` & `PS`| No (Fixed >= 2) |

---

## 24. Detailed Transaction Monitoring Execution Flow

1. **Engine Invocation**: Called via API `/api/v1/monitoring/execute`.
2. **Context Resolution**: Backend pulls the `active_batch_id` and globally filtered subset based on UI sidebar state.
3. **Parallel Rule Execution**: Rules 1-8 execute concurrently against the filtered subset in DB/Memory.
4. **Metric Generation**: For each rule, aggregate KPIs (Count, Exposure Sum, Max Amount) are calculated *only for the flagged subset*.
5. **Result Merging**: The backend constructs a unified JSON response containing summary metrics and paginated tables for each rule expander.

---

## 6. Filter Engine Architecture & Execution Order

1. **Global Store Initialization:** User selects values in the Sidebar. State is updated in Redux/NgRx.
2. **Query Builder:** Frontend constructs a standardized JSON filter payload.
3. **Backend `WHERE` Clause Construction (Execution Order):**
   *   `AND branch_name IN (...)`
   *   `AND txn_type IN (...)`
   *   `AND txn_date BETWEEN start_date AND end_date`
   *   `AND (fatf_flag = TRUE)` *(if FATF toggle applied)*
4. **Local Overrides:** Individual charts/tables (e.g., "High Value Transactions") apply their own local overrides (e.g., `AND eqv_usd > 25000`) on top of the base `WHERE` clause.

---

## 7. Session State Architecture & Lifecycle & 20. State Management

**Recommended Library:** Redux Toolkit (React) or NgRx (Angular).

**State Tree:**
```json
{
  "auth": { "user": "jwt_token", "role": "compliance_analyst" },
  "dataset": { "activeBatchId": "uuid-1234", "totalRows": 150000, "isProcessing": false },
  "filters": {
    "global": { "dateRange": ["2026-06-01", "2026-06-30"], "branches": ["ALL"], "fatfStatus": "ALL" },
    "local": { "monitoringRule5Threshold": 1, "investigationSearchQuery": "" }
  },
  "referenceData": { "partyMasterVersion": "v1.2", "ofacVersion": "v2.0" }
}
```
**Lifecycle:**
*   `UPLOAD_INIT` -> Clears `dataset` state.
*   `UPLOAD_SUCCESS` -> Sets `activeBatchId`. Triggers `FETCH_DASHBOARD_DATA`.
*   `UPDATE_FILTER` -> Modifies `filters.global`. Triggers debounce -> `FETCH_DASHBOARD_DATA`.

---

## 1. Complete Page Execution Flow & 19. User Interaction & 21. Route Mapping

**Route:** `/dashboard/monitoring`
**Execution Flow:**
1. **Mount:** `TransactionMonitoring` container component mounts.
2. **Dispatch:** Fires `FetchMonitoringData` action with current global filters.
3. **Loading State:** Skeleton loaders render for 8 rule expanders.
4. **API Response:** Backend returns `{ ruleSummaries: [], highValueData: [], ... }`.
5. **Render:** 
   * `<SummaryTable>` renders overall exposures.
   * `<RuleAccordion>` components map over data. Each renders a `<KpiGrid>`, a `<PlotlyChart>`, and an `<AgGridTable>`.
6. **Interaction (Change Threshold):** User moves "Load-to-Refund" slider to `7`. 
   * Dispatches `UPDATE_LOCAL_FILTER({ rule: 'loadRefund', threshold: 7 })`.
   * Dedicated API call fired for just Rule 5. 
   * Target accordion re-renders with updated KPIs and histogram.

---

## 2. Exact KPI Calculation Formulas & 3. Exact Chart Generation Logic

### Example: Load-to-Refund Rule
**KPIs:**
*   `Total Flagged Cards`: `SELECT COUNT(DISTINCT instrument_no) FROM rule5_dataset`
*   `Same-Day Refunds`: `SELECT COUNT(*) FROM rule5_dataset WHERE within_days = 0`
*   `Average Refund Delay`: `SELECT AVG(within_days) FROM rule5_dataset`
*   `Exposure Amount`: `SELECT SUM(load_amt) + SUM(refund_amt) FROM rule5_dataset`

**Chart: Distribution of Refund Delays (Histogram)**
*   **Data Prep:** Backend returns array of `within_days` integers.
*   **Plotly Logic:** 
    ```javascript
    <Plot
      data={[{ x: ruleData.map(d => d.within_days), type: 'histogram', xbins: { size: 1 } }]}
      layout={{ title: 'Distribution of Refund Delays', xaxis: { title: 'Days' }, yaxis: { title: 'Event Count' } }}
    />
    ```

---

## 13. API Contracts (Request/Response Schemas)

### `POST /api/v1/monitoring/load-refund`
**Request Schema:**
```json
{
  "batchId": "uuid",
  "thresholdDays": 7,
  "globalFilters": { "branch": ["ALL"], "startDate": "2026-06-01", "endDate": "2026-06-30" }
}
```
**Response Schema:**
```json
{
  "summary": { "flaggedCards": 45, "events": 62, "sameDayRefunds": 12, "exposureUsd": 150000.00 },
  "chartData": [ {"days": 0, "count": 12}, {"days": 1, "count": 25} ],
  "tableData": [
    { "instrumentNo": "40013642", "loadDate": "2026-06-20", "refundDate": "2026-06-27", "withinDays": 7, "loadAmt": 5000, "refundAmt": 5000 }
  ],
  "pagination": { "total": 62, "page": 1, "limit": 100 }
}
```

---

## 11. React Component Inventory & Hierarchy

```text
<AppRoot>
 ├─ <AuthGuard>
 │   └─ <DashboardLayout>
 │       ├─ <SidebarNavigation> (Material Drawer)
 │       │   └─ <GlobalFilterPanel> (Context-aware selects)
 │       └─ <PageContainer>
 │           ├─ <TransactionSummaryPage>
 │           ├─ <RetailHighValuePage>
 │           └─ <TransactionMonitoringPage>
 │               ├─ <OverallSummaryTable> (Ag-Grid)
 │               ├─ <RuleAccordion id="high-value">
 │               │   ├─ <KpiGrid metrics={data.kpis} />
 │               │   ├─ <ChartContainer type="bar" data={data.chart} />
 │               │   └─ <InvestigationDataTable data={data.table} />
 │               ├─ <RuleAccordion id="load-refund">
 │               │   ├─ <SliderControl label="Threshold" />
 │               │   └─ ...
 │               └─ <ConsolidatedReviewTable> (Ag-Grid with boolean flags)
```

---

## 12. Angular Module & Component Hierarchy

```text
AppModule
 ├─ CoreModule (AuthService, ApiService, ErrorInterceptor)
 ├─ SharedModule
 │   ├─ KpiCardComponent
 │   ├─ PlotlyChartComponent
 │   └─ AgGridWrapperComponent
 └─ FeaturesModule
     ├─ LayoutComponent (Sidebar + RouterOutlet)
     ├─ MonitoringModule
     │   ├─ MonitoringPageComponent
     │   ├─ RuleExpanderComponent
     │   └─ RiskReviewTableComponent
     └─ UploadModule (File dropzone & Validation)
```

---

## 15. Export Engine Architecture

*   **Problem:** Frontend downloading of massive DataFrames crashes the browser tab.
*   **Solution:** Backend streaming.
*   **Architecture:**
    1. User clicks "Download Filtered Data".
    2. Frontend POSTs current filter state and table ID to `/api/v1/export/csv`.
    3. Backend executes SQL query.
    4. Backend pipes DB cursor to `csv-stringify` stream.
    5. Node.js pipes stream directly to HTTP Response object (`Content-Type: text/csv`, `Content-Disposition: attachment`).
    6. Browser downloads file dynamically without holding the full payload in memory.

---

## 16. Caching Strategy & 17. Performance Optimization Strategy

### Backend (Redis / In-Memory DB)
*   **Parsed Datasets:** Cache the output of the canonical pipeline in a columnar format (like Parquet or ClickHouse/Snowflake micro-partitions) or heavily indexed PostgreSQL temp tables.
*   **Master Lists:** Cache Party Master and OFAC lookups in Redis. Do not execute string-matching logic per request; execute it *once* upon file upload.

### Frontend
*   **API Caching:** Use `React Query` or `RTK Query` with a stale-time of `Infinity` for the active batch. If global filters change, invalidate the query cache.
*   **Virtualization:** Use `Ag-Grid` or `react-window` for all `<InvestigationDataTable>` components to render only visible DOM nodes, allowing 100k+ rows to be scrolled smoothly.
*   **Web Workers:** If any light aggregation must remain on the frontend, move it to a Web Worker to prevent UI thread blocking.

---

## 18. Error Handling Flows

1. **File Upload Errors (e.g., Missing Columns):**
   * Backend validates headers -> Throws `400 Bad Request` with `{ missingColumns: ['TXNDATE'] }`.
   * Frontend catches -> Renders localized `<Alert severity="error">` inside the Upload dropzone.
2. **Data Type / Parsing Errors (`NaN` or Float Casts):**
   * Handled gracefully in canonicalization via `try/catch` and fallback to defaults (`0` or `'Unknown'`). Logged in backend `audit_logs` table for admin review.
3. **API Timeouts (Complex Queries):**
   * Standard API timeout set to 30s. If exceeded, return `504 Gateway Timeout`.
   * Frontend shows `<TimeoutFallback>` component with a "Retry Query" button.

---

## 22. Security Model & Access Control Recommendations

*   **Authentication:** JWT (JSON Web Tokens) issued via Azure AD or internal SSO.
*   **RBAC (Role-Based Access Control):**
    *   `Compliance_Viewer`: Can view dashboards and export anonymized reports.
    *   `Compliance_Analyst`: Can upload new monthly MIS files, update threshold variables, and view PII.
    *   `System_Admin`: Can upload master reference lists (OFAC / Party Master).
*   **Data Masking:** Based on JWT role, backend API masks columns like `Passport` or `Mobile_No` (e.g., `XXXXX1234`) before transmitting JSON to the browser for lower-tier roles.

---

## 23. Detailed Pseudocode for Critical Business Logic

### Consolidating Context Columns (Load/Refund Rule UI Logic)
To reproduce the intelligent investigation table that merges fields like `Corporate_LOAD` and `Corporate_REFUND`.

```javascript
// JavaScript / React pseudocode for column consolidation mapping
function consolidateRowData(row) {
    const consolidated = { ...row };
    const contextFields = ['Corporate', 'Branch Name', 'Passenger Name', 'MOBILENO'];
    
    contextFields.forEach(field => {
        const loadVal = row[`${field}_LOAD`] || '';
        const refundVal = row[`${field}_REFUND`] || '';
        
        if (loadVal === refundVal) {
            consolidated[field] = loadVal;
        } else {
            consolidated[field] = `${loadVal} / ${refundVal}`;
        }
        
        delete consolidated[`${field}_LOAD`];
        delete consolidated[`${field}_REFUND`];
    });
    
    return consolidated;
}
```
*This logic should ideally be executed in the backend SQL query via a `CASE WHEN` statement to reduce JSON payload size.*