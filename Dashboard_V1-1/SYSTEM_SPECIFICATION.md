# Enterprise System Specification & Migration Architecture
**Project:** GlobalPay AML & Compliance Platform  
**Target Stack:** React.js / Angular, FastAPI / Node.js, PostgreSQL / Snowflake  
**Document Status:** Production-Grade Freeze Specification

---

## Table of Contents
1. Complete Data Lineage
2. Complete Data Dictionary
3. Page Execution Flow
4. KPI Registry
5. Chart Registry
6. AML Rule Engine Registry
7. KYC Rule Engine Registry
8. Rule Dependency Matrix
9. Global Filter Engine
10. Session State Architecture
11. React Component Architecture
12. Angular Module Architecture
13. API Contracts
14. Database Design
15. Risk Scoring Engine
16. Export Engine
17. Audit Logging
18. Error Handling Catalog
19. Performance Specification
20. Testing Framework
21. Deployment Architecture
22. Migration Freeze Specification

---

## SECTION 1: COMPLETE DATA LINEAGE

Mapping the journey of critical fields from raw ingestion to final UI render.

### 1.1 INSTRUMENTNO (Prepaid Cards)
```text
Raw Column: INSTRUMENTNO
↓
Canonical Column: Instrument Number
↓
Cleaning Logic: clean_identifier() -> Remove ` ' ~ # * ", strip whitespace, remove .0 suffix.
↓
Transformation Logic: Uppercase, null check.
↓
Derived Fields: None directly.
↓
Pages Using It: Transaction Monitoring, Passenger Analysis.
↓
Rules Using It: Load-to-Refund, Multi-Card Contact, Multi-Card Pax, Multi-Card Operator.
↓
Charts Using It: Top 15 Cards by Same-Day Reload/Refund Events.
↓
Exports Using It: Load/Refund CSV, Multi-Card CSVs.
```

### 1.2 MOBILENO
```text
Raw Column: MOBILENO
↓
Canonical Column: MOBILENO
↓
Cleaning Logic: clean_mobile_number() -> String cast, strip spaces, remove .0 suffix, map 'NAN' to NULL.
↓
Transformation Logic: None.
↓
Derived Fields: None.
↓
Pages Using It: Passenger Analysis, Transaction Monitoring.
↓
Rules Using It: KYC Rule C, KYC Rule F, KYC Rule H, Rule 6 (Multi-Card Same Contact).
↓
Charts Using It: Top Mobile Numbers by Linked Card Count.
↓
Exports Using It: Passenger Analysis CSV, Rule 6 CSV.
```

### 1.3 INRAMOUNT
```text
Raw Column: INRAMOUNT
↓
Canonical Column: Net Amt
↓
Cleaning Logic: pd.to_numeric(errors='coerce').fillna(0)
↓
Transformation Logic: Cast to Decimal/Float.
↓
Derived Fields: EQV USD (Net Amt / Daily_USD_Avg_Rate).
↓
Pages Using It: All Pages.
↓
Rules Using It: Rule 1 (High Value), Rule 5 (Load-Refund Exposure).
↓
Charts Using It: Transaction Trend, Purpose Mix, Branch-wise Activity.
↓
Exports Using It: All CSV Exports.
```

### 1.4 TXNDATE
```text
Raw Column: TXNDATE
↓
Canonical Column: Date
↓
Cleaning Logic: pd.to_datetime(errors='coerce')
↓
Transformation Logic: ISO-8601 parsing.
↓
Derived Fields: Day, Week, Month, Year, Weekday, Date_Day (Date-only part).
↓
Pages Using It: All Pages (Global Date Filter).
↓
Rules Using It: Rule 5 (Load-Refund Window `dt.days` delta).
↓
Charts Using It: Time Series Trend lines.
↓
Exports Using It: All CSVs.
```

---

## SECTION 2: COMPLETE DATA DICTIONARY

| Column | Data Type | Source | Nullable | Default | Transformation | Used By | Business Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `Branch` | VARCHAR | `BRANCHCODE` | Yes | `NULL` | Trim | Home | Identifier for physical branch |
| `Branch Name` | VARCHAR | `LOCATION` | No | `UNKNOWN` | Trim | Global Filter | Physical branch name |
| `Txn Type` | VARCHAR(2) | `TXNTYPE` | No | `UNKNOWN` | UPPER | Rule 5, Filters | Indicator of Purchase (PS) vs Bank (PB) |
| `Doc Number` | VARCHAR | `DOCNO` | No | `NULL` | `clean_identifier` | DB PK | Core transaction receipt ID |
| `Date` | DATE/TIME | `TXNDATE` | No | `1970-01-01` | `to_datetime` | All | Execution timestamp |
| `Party Code` | VARCHAR | `CUSTOMERCODE` | No | `UNKNOWN` | `clean_identifier` | Rule 3, 4 | Corporate Entity ID |
| `Corporate` | VARCHAR | `CUSTOMERNAME` | Yes | `NULL` | Trim | Rule 8 | Corporate Entity Name |
| `Passenger Name` | VARCHAR | `PAXNAME` | Yes | `NULL` | Trim | Rule 7, 8 | Ultimate beneficiary/traveller |
| `Passport` | VARCHAR | `PAXIDNO` | Yes | `NULL` | `clean_identifier` | KYC Rules | Passport / PAN number |
| `Purpose` | VARCHAR | `TxnPurpose` | Yes | `NULL` | Trim | Filter | Regulatory reason code |
| `Currency` | VARCHAR(3) | `CURRENCY` | No | `INR` | UPPER | DB Calc | Transacted currency |
| `Product` | VARCHAR(2) | `PRODUCT` | No | `NULL` | UPPER | Rule 5, 6, 7, 8 | Financial instrument (EC/FC) |
| `Rate` | DECIMAL | `SELLRATE` | No | `0.0` | `to_numeric` | EQV USD Calc | Exchange rate |
| `Visiting Country` | VARCHAR | `CountryToTravel` | Yes | `NULL` | UPPER | Rule 2 (FATF) | Geopolitical risk map |
| `Instrument Number`| VARCHAR | `INSTRUMENTNO` | Yes | `NULL` | `clean_identifier` | Rule 5, 6, 7, 8 | Prepaid card serial |
| `Load Reload Type` | VARCHAR | `LoadReload` | Yes | `NULL` | UPPER | Rule 5 | Transaction action |
| `Segments` | VARCHAR | `Segment` | No | `OTHER` | Standardization Map | Rule 3, 4 | Internal business unit |
| `Beneficiary` | VARCHAR | `BENEFICIARY` | Yes | `NULL` | Trim | Rule 3, 4 | Remittance receiver |
| `Net Amt` | DECIMAL | `INRAMOUNT` | No | `0.0` | `to_numeric` | All | Base currency volume |
| `EMAILID` | VARCHAR | `EMAILID` | Yes | `NULL` | Lowercase | KYC Rules | Passenger email |
| `MOBILENO` | VARCHAR | `MOBILENO` | Yes | `NULL` | `clean_mobile_number` | Rule 6, KYC | Passenger phone |
| `EQV USD` | DECIMAL | *Derived* | No | `0.0` | NetAmt / Rate | Rule 1 | Risk threshold mapping |
| `Risk Category` | VARCHAR | *Derived* | No | `Unknown`| Join Party Master | Filters | High/Med/Low corporate risk |
| `OFAC _ FATF` | VARCHAR | *Derived* | No | `NOT FLAGGED`| Join OFAC Master | Rule 2 | Sanctions hit |

---

## SECTION 3: PAGE EXECUTION FLOW

### 3.1 Typical Page Lifecycle (e.g., Transaction Monitoring)

```text
1. User Routes to /dashboard/monitoring
↓
2. App reads Redux/NgRx Global State (activeBatchId, currentFilters)
↓
3. GET /api/v1/monitoring/execute triggered.
   Payload: { filters: { branch: 'All', dates: [...] } }
↓
4. Backend retrieves cached canonical dataset for batchId.
↓
5. Backend applies Global Filters (WHERE branch_name IN (...))
↓
6. Backend executes Rules 1 through 8 in parallel (via SQL CTEs or Pandas).
↓
7. Backend calculates KPIs per rule (e.g., COUNT(DISTINCT instrument_no)).
↓
8. Backend formats Payload (Summary Matrix + Paginated Table Data + Chart Series).
↓
9. Frontend receives JSON Response.
↓
10. <SummaryTable> mounts and maps Summary Matrix.
↓
11. <RuleAccordion> mounts. Contains <KpiGrid>, <PlotlyChart>, <AgGrid>.
↓
12. User clicks "Download". POST /api/v1/export with active table state -> Blob Stream.
```

---

## SECTION 4: KPI REGISTRY

### 4.1 High Value Transaction Count
*   **Formula:** `COUNT(txn_id) WHERE eqv_usd > 25000`
*   **Input Columns:** `eqv_usd`
*   **Filters Applied:** Global Filters.
*   **Formatting:** Integer, Thousand Separator.
*   **React Component:** `<MetricCard title="High Value Count" value={val} />`
*   **Business Meaning:** Absolute count of transactions requiring mandatory AML reporting.

### 4.2 Configurable Load-to-Refund Events
*   **Formula:** `COUNT(load_txn_id) WHERE (refund_date - load_date) <= threshold`
*   **Input Columns:** `load_date`, `refund_date`, `instrument_no`
*   **Filters Applied:** Global Filters + Local Slider (Threshold).
*   **Business Meaning:** Number of times cards were loaded and refunded rapidly, indicating layering.

### 4.3 Missing KYC Count
*   **Formula:** `COUNT(txn_id) WHERE passport IS NULL OR emailid IS NULL OR mobileno IS NULL`
*   **Input Columns:** `Passport`, `EMAILID`, `MOBILENO`
*   **Business Meaning:** Transactions bypassing primary identification.

### 4.4 Suspicious Beneficiary Count (Tour Op)
*   **Formula:** `COUNT(DISTINCT beneficiary) WHERE operator_count >= 2 AND txn_count >= 5`
*   **Input Columns:** `Beneficiary`, `Corporate`
*   **Business Meaning:** Distinct receiver names being utilized by multiple shell/tour operators.

---

## SECTION 5: CHART REGISTRY

### 5.1 Distribution of Refund Delays
*   **Chart Name:** Distribution of Refund Delays
*   **Chart Type:** Histogram (Plotly `histogram` or Recharts `BarChart`)
*   **Input DataFrame:** `rule5_dataset` (Load-to-Refund valid pairs)
*   **GroupBy Logic:** Bins of `within_days` (0, 1, 2, 3...)
*   **Aggregation Logic:** `COUNT(instrument_no)` per bin.
*   **Sorting Logic:** Ascending by `within_days`.
*   **Business Purpose:** Visualizing if bad actors are cashing out instantly (0 days) or holding funds.
*   **Pseudocode:**
    ```sql
    SELECT within_days, COUNT(*) as event_count 
    FROM load_refund_pairs 
    WHERE within_days <= :threshold 
    GROUP BY within_days ORDER BY within_days ASC;
    ```

### 5.2 Branch Exposure
*   **Chart Name:** Top 10 Branches by Suspicious Case Count
*   **Chart Type:** Horizontal Bar Chart
*   **Input DataFrame:** Rule-specific output sets (e.g., `high_value_df`).
*   **Aggregation Logic:** `COUNT(txn_id)` and `SUM(net_amt)`.
*   **Sorting Logic:** Descending by `COUNT`. Limit 10.
*   **Hover Behavior:** Show Total Amount, Average Amount, Max Amount.

### 5.3 Customer Concentration
*   **Chart Name:** Customer Concentration
*   **Chart Type:** Scatter Plot / Bubble Chart
*   **X Axis:** `Transaction Count`
*   **Y Axis:** `Total USD`
*   **Bubble Size:** `Max_USD`
*   **Business Purpose:** Identifying whales (high count + high amount).

---

## SECTION 6: AML RULE ENGINE REGISTRY

### 6.1 Rule 1: High Value Transaction
*   **Rule ID:** `AML_001`
*   **Objective:** Identify individual transactions over $25,000 USD.
*   **Severity:** 2 (Medium)
*   **Thresholds:** High = 25,000. Structuring = 20,000 to 24,999.
*   **Input Columns:** `EQV USD`, `Net Amt`.
*   **Matching Logic:** `WHERE eqv_usd > 25000`.
*   **Pseudocode:**
    ```javascript
    const flagged = dataset.filter(row => row.eqv_usd > 25000);
    const structuring = dataset.filter(row => row.eqv_usd >= 20000 && row.eqv_usd <= 25000);
    return { flagged, structuring };
    ```

### 6.2 Rule 3: Multiple Operators to Same Beneficiary
*   **Rule ID:** `AML_003`
*   **Objective:** Detect Hawala networks.
*   **Filters:** `Segments == 'TOUR OPERATOR'`
*   **Thresholds:** `>= 2 Operators`, `>= 5 Transactions` per month.
*   **Pseudocode:**
    ```sql
    SELECT Beneficiary
    FROM transactions
    WHERE Segment = 'TOUR OPERATOR'
    GROUP BY Beneficiary, DATE_TRUNC('month', Date)
    HAVING COUNT(DISTINCT Corporate) >= 2 AND COUNT(txn_id) >= 5;
    ```

### 6.3 Rule 5: Configurable Load-to-Refund Window
*   **Rule ID:** `AML_005`
*   **Objective:** Identify prepaid cards loaded and refunded rapidly.
*   **Filters:** `Product IN ('EC', 'FC')`
*   **Configurable Parameters:** `threshold_days` (default 1, max 30).
*   **Matching Logic (NO `merge_asof`):**
    ```python
    # Create separate Load and Refund sets
    loads = df[(df['LoadReload'].isin(['LOAD','RELOAD'])) & (df['Txn Type'] == 'PS')]
    refunds = df[df['LoadReload'] == 'REFUND']
    
    # Inner Join on Instrument Number
    pairs = loads.merge(refunds, on='INSTRUMENTNO', suffixes=('_LOAD', '_REFUND'))
    
    # Calculate Days
    pairs['WITHIN_DAYS'] = (pairs['Date_REFUND'] - pairs['Date_LOAD']).dt.days
    
    # Apply thresholds (prevent negative days - refund before load)
    flagged = pairs[(pairs['WITHIN_DAYS'] >= 0) & (pairs['WITHIN_DAYS'] <= threshold_days)]
    ```
*   **Consolidation Edge Case:** Duplicate fields like `Branch_LOAD` and `Branch_REFUND` must be evaluated. If identical, keep `Branch`. If different, concatenate `Branch_LOAD / Branch_REFUND`.

### 6.4 Rule 8: Multi-Card Multi-Operator Use
*   **Rule ID:** `AML_008`
*   **Objective:** Sophisticated capital flight using different tour operators.
*   **Filters:** `Product IN ('EC', 'FC')`, `Txn Type == 'PS'`.
*   **Aggregation:** 
    ```sql
    SELECT Passenger_Name 
    FROM transactions 
    GROUP BY Passenger_Name 
    HAVING COUNT(DISTINCT INSTRUMENTNO) >= 2 AND COUNT(DISTINCT Corporate) >= 2;
    ```

---

## SECTION 7: KYC RULE ENGINE REGISTRY

### Passenger Analysis Rules
*   **Rule A: Same PAX ID, Different Emails**
    *   **Logic:** `GROUP BY Passport HAVING COUNT(DISTINCT EMAILID) > 1`
    *   **Example:** Passport A123 used with `john@a.com` and `john@b.com`.
*   **Rule B: Same PAX ID, Different Names**
    *   **Logic:** `GROUP BY Passport HAVING COUNT(DISTINCT Passenger_Name) > 1`
*   **Rule E: Same Email, Different PAX IDs**
    *   **Logic:** `GROUP BY EMAILID HAVING COUNT(DISTINCT Passport) > 1`
    *   **Failure Case:** Travel agent uses their own email for 50 different customers. Flags all 50.

---

## SECTION 8: RULE DEPENDENCY MATRIX

| Rule ID | Required Columns | Derived Columns | Config Parameter | Default Page |
| :--- | :--- | :--- | :--- | :--- |
| AML_001 | Net Amt, Rate | EQV USD | None | Txn Monitoring |
| AML_002 | Visiting Country | OFAC_FATF Flag | None | Txn Monitoring |
| AML_003 | Segment, Beneficiary, Corporate | Month_Window | None | Txn Monitoring |
| AML_004 | Segment, Beneficiary, Corporate | Month_Window | None | Txn Monitoring |
| AML_005 | Product, Txn Type, LoadReload, InstrumentNo, Date | WITHIN_DAYS | `threshold_days` | Txn Monitoring |
| AML_006 | Product, Txn Type, MobileNo, InstrumentNo | Card_Count | None | Txn Monitoring |
| KYC_A | Passport, Email | None | None | Passenger Analysis|
| KYC_E | Email, Passport | None | None | Passenger Analysis|

---

## SECTION 9: GLOBAL FILTER ENGINE

### Filter Order & Execution Pipeline
Filters MUST be applied in the backend database engine to prevent shipping massive JSON payloads to the frontend.

**Execution Order (WHERE Clause Builder):**
1.  **Date Range:** Indexed execution (`WHERE txn_date BETWEEN x AND y`).
2.  **Product / Txn Type / Branch:** Standard string IN clauses.
3.  **Risk Category / FATF:** Calculated properties.

**State Persistence (Redux):**
```typescript
interface GlobalFilterState {
  dateRange: [string, string];
  branches: string[];
  products: string[];
  fatfStatus: 'All' | 'Flagged' | 'Not Flagged';
}
// Action
dispatch(updateFilter({ field: 'branches', value: ['Mumbai', 'Delhi'] }));
// Side Effect
// Cancels in-flight API requests, debounces 300ms, triggers new API fetch.
```

---

## SECTION 10: SESSION STATE ARCHITECTURE

| Variable Name | Purpose | Created In | Used In | Default | Lifetime |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `activeBatchId` | Ties user to DB dataset | Upload Module | All Pages | `null` | Session/JWT expiry |
| `loadRefundThreshold` | Rule 5 parameter | Monitoring UI | Rule 5 SQL | `1` | Session |
| `ofacMasterVersion` | Tracks active OFAC list | Upload Module | FATF Rule | `null` | Persistent |
| `investigationSearch` | Global review table text | Review UI | Grid Filter | `""` | Page Unmount |

**Lifecycle Diagram:**
```text
[Login] -> [Upload / Select Batch] -> set(activeBatchId)
  -> [Navigate to Monitoring] 
  -> [Change Slider] -> set(loadRefundThreshold) -> Trigger Rule 5 API Fetch
  -> [Navigate Away] -> clear(investigationSearch)
```

---

## SECTION 11: REACT COMPONENT ARCHITECTURE

```text
<App>
 │
 ├── <AuthGuard>
 │   └── <DashboardLayout>
 │       ├── <SidebarNavigation> (MUI Drawer)
 │       │   └── <GlobalFilterPanel> (MUI Autocomplete)
 │       │
 │       └── <PageContainer>
 │           ├── <TransactionMonitoringPage>
 │           │   ├── <SummaryTable> (AgGridReact)
 │           │   │
 │           │   ├── <RuleAccordion id="load-refund">
 │           │   │   ├── <AccordionSummary> Title & Count
 │           │   │   ├── <AccordionDetails>
 │           │   │   │   ├── <SliderControl onChange={dispatch} />
 │           │   │   │   ├── <KpiGrid data={kpis} />
 │           │   │   │   ├── <PlotlyChart data={histogram} />
 │           │   │   │   └── <InvestigationTable data={table} onExport={...} />
 │           │   │
 │           │   └── <TransactionRiskReviewTable>
```

### Component: `<InvestigationTable />`
*   **Props:** `data` (Array), `columns` (Array of AgGrid ColDefs), `isLoading` (boolean), `onExport` (function).
*   **State:** Pagination config, internal column sorting.
*   **Features:** Virtualization (AgGrid handles DOM recycling), custom cell renderers for Boolean Flags (✔/✘).

---

## SECTION 12: ANGULAR MODULE ARCHITECTURE

```text
src/app/
├── core/
│   ├── auth/ (AuthService, AuthGuard)
│   ├── http/ (ApiService, TokenInterceptor, ErrorInterceptor)
│   └── store/ (NgRx Actions, Reducers, Effects)
├── shared/
│   ├── components/ (kpi-card, plotly-wrapper, ag-grid-wrapper)
│   ├── pipes/ (currency-inr.pipe.ts)
│   └── utils/ (file-downloader.ts)
├── features/
│   ├── upload/ (UploadComponent)
│   ├── monitoring/ (MonitoringPageComponent, RuleExpanderComponent)
│   ├── retail/ (HighValuePageComponent)
│   └── layout/ (SidebarComponent, HeaderComponent)
```

---

## SECTION 13: API CONTRACTS (OpenAPI Style)

### `POST /api/v1/monitoring/rule/load-refund`

**Request Schema:**
```json
{
  "batch_id": "uuid-string",
  "threshold_days": 7,
  "filters": {
    "branches": ["All"],
    "products": ["EC", "FC"],
    "date_range": ["2026-06-01", "2026-06-30"]
  },
  "pagination": {
    "page": 1,
    "limit": 500
  }
}
```

**Response Schema:**
```json
{
  "status": "success",
  "data": {
    "kpis": {
      "total_cards": 142,
      "same_day_refunds": 12,
      "exposure_usd": 450000.50
    },
    "chart": [
      { "within_days": 0, "count": 12 },
      { "within_days": 1, "count": 45 }
    ],
    "table": [
      {
        "INSTRUMENTNO": "40011111",
        "WITHIN_DAYS": 1,
        "LOAD_DATE": "2026-06-10",
        "REFUND_DATE": "2026-06-11",
        "LOAD_AMOUNT": 10000.00,
        "REFUND_AMOUNT": 10000.00,
        "Corporate": "Acme Corp / Delta Inc"
      }
    ],
    "meta": {
      "total_records": 142,
      "current_page": 1,
      "total_pages": 1
    }
  }
}
```

---

## SECTION 14: DATABASE DESIGN

### Recommended Schema (PostgreSQL)

**`upload_batches`**
*   `batch_id` (UUID, PK)
*   `uploaded_at` (TIMESTAMP)
*   `uploaded_by` (UUID)
*   `status` (VARCHAR) - Processing, Completed, Failed
*   `row_count` (INT)

**`tx_master`** (Partitioned by `batch_id`)
*   `txn_id` (UUID, PK)
*   `batch_id` (UUID, FK, Indexed)
*   `txn_date` (DATE, Indexed)
*   `instrument_no` (VARCHAR, Indexed)
*   `mobile_no` (VARCHAR, Indexed)
*   `eqv_usd` (DECIMAL)
*   *(...all other canonical columns)*

**`risk_profiles`** (1-to-1 with `tx_master`)
*   `txn_id` (UUID, PK, FK)
*   `rule_1_flag` (BOOLEAN)
*   `rule_5_flag` (BOOLEAN)
*   `risk_rule_count` (INT, Indexed)

**Partitioning Strategy:**
List partition `tx_master` and `risk_profiles` by `batch_id`. This allows instant deletion of an entire batch if a user re-uploads or deletes a dataset, eliminating `DELETE` lock contention.

---

## SECTION 15: RISK SCORING ENGINE

Calculated per transaction row.

**Rule Weights:**
*   Rule 1 (High Value): 2
*   Rule 2 (FATF/OFAC): 3
*   Rule 3 (Multi-Op to Beneficiary): 2
*   Rule 4 (High Freq Remittance): 2
*   Rule 5 (Load-to-Refund): 2
*   Rule 6 (Multi-Card Contact): 2
*   Rule 7 (Multi-Card Pax): 2
*   Rule 8 (Multi-Card Multi-Op): 2

**Formula:**
`Risk Score = SUM(Rule_i_Flag * Rule_i_Weight)`

**Alert Levels:**
*   `0`: Clear
*   `1 - 2`: Low Risk (Monitor)
*   `3 - 4`: Medium Risk (Investigate)
*   `>= 5`: High Risk (Escalate to Compliance Head)

---

## SECTION 16: EXPORT ENGINE

*   **Export Flow:**
    1. UI requests CSV export with current JSON filter state.
    2. Backend validates JWT.
    3. Backend constructs `COPY (SELECT * FROM tx_master WHERE ...) TO STDOUT WITH CSV HEADER`.
    4. Stream piped to response.
*   **File Naming:** `GlobalPay_{RuleName}_{YYYYMMDD_HHMMSS}.csv`.
*   **Performance:** Uses Node.js Streams (`pg-query-stream`) or FastAPI StreamingResponse. Memory footprint remains <50MB regardless of export size.

---

## SECTION 17: AUDIT LOGGING

**`audit_logs` table schema:**
*   `log_id` (UUID, PK)
*   `user_id` (UUID)
*   `action` (VARCHAR) - `UPLOAD`, `DOWNLOAD_EXPORT`, `CHANGE_THRESHOLD`, `LOGIN`
*   `target_module` (VARCHAR)
*   `metadata` (JSONB) - Captures the exact filters applied during a download or the before/after threshold values.
*   `timestamp` (TIMESTAMP)

---

## SECTION 18: ERROR HANDLING CATALOG

| Failure | Cause | Detection | Recovery/User Message |
| :--- | :--- | :--- | :--- |
| **Missing Master File** | `Party Master` not uploaded. | Server startup check. | Disables dependent rules. UI Warning: "Upload Party Master to enable High Risk scoring." |
| **Column Map Fail** | Excel missing `INRAMOUNT`. | File validation pre-ingest. | Reject file. UI Error: "Missing mandatory column: INRAMOUNT." |
| **Load Refund Join Fail** | Memory leak or bad index. | `try/catch` around SQL. | Log error. Return empty dataframe. UI Error: "Rule unavailable." |
| **Invalid Date** | Excel date is "TBD". | Pandas/SQL date cast error. | Cast to `NULL`. Flag in Data Quality report. |

---

## SECTION 19: PERFORMANCE SPECIFICATION

**Hardware Baseline:** 4 vCPU, 16GB RAM (Containerized). Database on SSD.

| Dataset Size | Target Upload/ETL Time | Target Filter Query Time | Target Export Time |
| :--- | :--- | :--- | :--- |
| 50,000 Rows | < 5 seconds | < 0.5 seconds | < 2 seconds |
| 100,000 Rows| < 10 seconds | < 1.0 seconds | < 3 seconds |
| 500,000 Rows| < 30 seconds | < 2.5 seconds | < 10 seconds |
| 1,000,000 Rows| < 60 seconds | < 4.0 seconds | < 20 seconds |

**Optimization Strategy:**
*   B-Tree indexes on `txn_date`, `instrument_no`, `mobile_no`.
*   Materialized views for high-level aggregations (Home Page KPIs).
*   Frontend Virtual DOM for table rendering.

---

## SECTION 20: TESTING FRAMEWORK

*   **Unit Tests (Jest/PyTest):**
    *   Assert `clean_mobile_number(" 9876543210.0 ")` returns `"9876543210"`.
    *   Assert Rule 5 logic correctly drops pairs where `within_days < 0`.
*   **Integration Tests (Postman/Supertest):**
    *   Upload sample 100-row MIS. Assert `/api/v1/monitoring/execute` returns HTTP 200 with exactly 2 flagged records for Rule 1.
*   **User Acceptance (Cypress/Playwright):**
    *   Simulate User adjusting "Load-to-Refund" slider to 7. Verify network call fires and chart DOM updates.

---

## SECTION 21: DEPLOYMENT ARCHITECTURE

**Recommended Enterprise Stack:**
*   **Frontend:** React (Next.js) or Angular, deployed on Vercel or AWS Amplify / S3 + CloudFront.
*   **Backend:** Python FastAPI (Uvicorn), deployed on AWS ECS (Fargate) or Azure Container Apps.
*   **Database:** Amazon RDS (PostgreSQL) or Azure Database for PostgreSQL.
*   **Cache:** Redis (ElastiCache) for session state and Master list lookups.
*   **Auth:** Azure Active Directory (SAML/OIDC) integration via backend middleware.

---

## SECTION 22: MIGRATION FREEZE SPECIFICATION

*This is the official functional baseline representing 100% feature parity with the legacy Streamlit application.*

*   **Current Version:** 1.0.0-freeze
*   **Total Dashboard Pages:** 14 (Migration Validation, Home, Txn Summary, Tour Op, Retail High Value, High Risk Corp, FATF, Bank Book, Cash Analysis, Txn Monitoring, Currency Ratio, Agent Analysis, Passenger Analysis, MLTF)
*   **Total KPIs Calculated:** 38 unique metric formulas.
*   **Total Charts:** 22 unique Plotly visualizations.
*   **Total AML Rules:** 8 core transaction surveillance rules.
*   **Total KYC Rules:** 10 Passenger/Identity anomaly rules.
*   **Total Exports:** 16 (1 Global per page + specific investigation tables).
*   **Total Configurations:** 6 UI-adjustable variables.

*(End of Specification)*