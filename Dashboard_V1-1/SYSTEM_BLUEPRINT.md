# GlobalPay AML & Compliance Dashboard - System Blueprint

## 1. Executive Overview

### What the Application Does
The GlobalPay AML & Compliance Dashboard is an automated compliance monitoring and risk intelligence portal. It ingests raw monthly transaction ledgers, cleans and standardizes the data, cross-references it against master risk lists (Party Master, OFAC/FATF), and runs a comprehensive suite of Anti-Money Laundering (AML) and Know Your Customer (KYC) rules.

### Business Purpose & AML Use Cases
*   **Automated Surveillance:** Detects structuring, high-velocity transactions, circular fund movements (load-to-refund), and multi-entity linked anomalies.
*   **Geographical & Entity Risk:** Flags transactions to FATF/OFAC jurisdictions and interactions with high-risk corporates (Trusts, NGOs, Societies).
*   **KYC Data Quality:** Evaluates the integrity of passenger identity documents (PAN, Passports) and flags identity sharing/duplication.

### Target Users
*   Compliance Officers & Analysts
*   Internal Audit Teams
*   Risk Management Executives

### Monthly Workflow (Current Manual vs. New Automated)
**Previous Process:** Manual cleaning, VLOOKUPs against master lists, and pivot-table-based anomaly detection taking **4 to 5 days**.
**New Process (via this system):**
```text
Input File (TXN LINE MIS)
→ Canonical Processing (Standardization & Cleaning)
→ Risk Enrichment (Party Master & OFAC lookup)
→ Monitoring Engine (AML Rules Scoring)
→ Dashboard Analytics (Visualizations & KPIs)
→ Exception Investigation (Interactive Tables)
→ Export (Filtered CSVs for reporting)
```
*Total time: Minutes.*

---

## 2. Application Architecture

### Entry Points
*   **Main Application:** `app.py` (Bootstraps the UI, handles state routing, caching, and layout).

### Data Flow
```text
Upload Raw Excel Workbook
↓
Canonical Dataset Creation (canonical_dataset.py)
  ├─ Column Mapping
  ├─ Data Cleaning (clean_identifier, clean_mobile_number)
  └─ Derived Variables (Dates, USD Equivalents)
↓
Master Data Enrichment
  ├─ Party Master Lookup (Corporate Risk categorization)
  └─ OFAC / FATF Lookup (Country Risk categorization)
↓
Risk Categorization & Engine (monitoring_engine.py)
  ├─ Execute 8 Core AML Rules
  └─ Generate Risk_Rule_Count & Any_Risk_Flag
↓
Dashboard Pages (pages/ module)
  ├─ Apply Global UI Filters
  └─ Render localized KPIs, Charts, and Investigation Tables
↓
Exports
  └─ Filter-aware CSV Generation
```

---

## 3. Folder Structure

*   **`/` (Root):** Contains entry scripts (`app.py`, `run_windows.ps1`) and dependencies.
*   **`pages/`**: 
    *   **Purpose:** Contains individual modular screen definitions (React/Angular routes).
    *   **Inputs:** Filtered Canonical Dataset, Risk Dataframe, active flags.
    *   **Outputs:** Rendered UI components (KPIs, Charts, Tables).
*   **`rules/`**: 
    *   **Purpose:** The mathematical and logical core of the compliance engine.
    *   **Inputs:** Canonical Dataset.
    *   **Outputs:** Boolean arrays marking anomalous transactions and risk matrices.
*   **`charts/`**: 
    *   **Purpose:** Reusable visualization components and enterprise theme definitions.
*   **`data/`**: 
    *   **Purpose:** Directory for local persistent master lists (`Party Master New Report.csv`, `OFAC_FATF COUNTRY UPDATED.xlsx`).
*   **`utils/`**: 
    *   **Purpose:** Shared helpers (currency formatters, dynamic filter generators, UI component wrappers).

---

## 4. Canonical Dataset Documentation

### Raw Source Columns (Mapped)
`BRANCHCODE`, `LOCATION`, `TXNTYPE`, `DOCNO`, `TXNDATE`, `CUSTOMERCODE`, `CUSTOMERNAME`, `PAXNAME`, `PAXIDNO`, `AGENTCODE`, `AGENTNAME`, `TxnPurpose`, `CURRENCY`, `PRODUCT`, `ISSUER`, `SELLRATE`, `CountryToTravel`, `INSTRUMENTNO`, `LoadReload`, `Segment`, `BENEFICIARY`, `INRAMOUNT`, `EMAILID`, `MOBILENO`.

### Standardized Columns
`Branch`, `Branch Name`, `Txn Type`, `Doc Number`, `Date`, `Party Code`, `Corporate`, `Passenger Name`, `Passport`, `Agent`, `Agent Name`, `Purpose`, `Currency`, `Product`, `Issuer`, `Rate`, `Visiting Country`, `Instrument Number`, `Load Reload Type`, `Segments`, `Beneficiary Type Load or Reload`, `Net Amt`, `EMAILID`, `MOBILENO`.

### Derived Columns
*   `Day`, `Week`, `Month`, `Year`, `Weekday` (Extracted from `Date`).
*   `Daily_USD_Avg_Rate`: Mean exchange rate of USD on that specific `Date`.
*   `EQV USD` (Equivalent USD Amount): `Net Amt` / `Daily_USD_Avg_Rate`.

### Data Cleaning Rules
*   **Mobile Cleaning (`clean_mobile_number`)**: Converts to string, removes `.0` suffix (pandas float artifact), removes all spaces, maps `['', 'NAN', 'NONE', 'NULL']` to `np.nan`.
*   **Identifier Standardization (`clean_identifier`)**: Applies to Cards, Passports, Party Codes. Removes specific compliance special characters (`' \` ~ # * "`), cleans `.0` suffixes, removes non-printable/invisible characters (regex `[^\x20-\x7E]`), strips whitespace.
*   **Numeric Parsing**: Coerces `Net Amt` and `Rate` to numeric, filling NaNs with `0`.

### Risk Enrichment
*   **Party Master Integration:** Matches `Party Code` to `CUSTOMERCODE` in `Party Master New Report.csv`. Appends `Risk Category` mapped to `High`, `Medium`, `Low`, or `Unknown`.
*   **OFAC/FATF Mapping:** Matches `Visiting Country` to `COUNTRY` in `OFAC_FATF COUNTRY UPDATED.xlsx`. Appends `OFAC _ FATF` segment name, defaulting to `NOT FLAGGED`.
*   **Segment Standardization:** Normalizes legacy segments (e.g., 'Students Credila' -> 'EDUCATION', 'Tour Remittance' -> 'TOUR OPERATOR') via `SEGMENT_STANDARDIZATION_MAP`.

---

## 5. Global Filters

Applied universally via the sidebar before a page renders.

| Filter Name | Source Column | Default Behaviour |
| :--- | :--- | :--- |
| Branch | `Branch Name` | Select All |
| Product | `Product` | Select All |
| Purpose | `Purpose` | Select All (Except specific defaults like 'Tour Operator' page) |
| Txn Type | `Txn Type` | Select All |
| Corporate | `Corporate` | Select All |
| Country | `Visiting Country` | Select All |
| Risk Category | `Risk Category` | Select All (Except High Risk Corp page -> 'HIGH') |
| Currency | `Currency` | Select All |
| Agent Name | `Agent Name` | Select All |
| Segment | `Segments` | Select All |
| Date Range | `Date` | Min Date to Max Date of dataset |
| FATF Status | `FATF / OFAC Flag` | 'All' (Toggle: All / Flagged / Not Flagged) |

---

## 6. Dashboard Pages

### 6.1 Home Page
*   **Purpose:** Executive overview of monthly transactions.
*   **KPIs:** Total Txns, Total Net Amt, Avg Txn, Highest Txn, Lowest Txn, PS Count/Amt, PB Count/Amt, Date Range, Best Segment, Best Branch.
*   **Charts:** Transaction Trend (Line - Daily/Weekly), Breakdown by Purpose (Donut), Breakdown by Product (Donut), Branch-wise Activity (Bar), Country-wise Activity (Bar).
*   **Tables:** Top Transactions by Net Amt.

### 6.2 Transaction Summary
*   **Purpose:** Mix analysis (PS, PB, CB, FB) and composition.
*   **KPIs:** Count and Amount per Txn Type (PS, PB, CB, FB, FS, BB, BS, BT).
*   **Charts:** Txn Type Amount (Donut), Composition Analysis by Branch/Product/Segment (Stacked Horizontal Bar).
*   **Tables:** Purpose Summary Table.

### 6.3 Tour Operator
*   **Purpose:** Review tour operator remittances and concentrations.
*   **Filters:** Defaults to `Purpose` IN `['REMITTANCE BY TOUR OPERATORS', 'MICE -REMITANCE BY TOUR OPERATORS']`.
*   **KPIs:** Txn Count, Amount, Contribution to overall PS %. Intelligence Cards (Best Operator, Beneficiary, Branch, Country).
*   **Charts:** Purpose Split (Pie), Top Branches (Stacked Bar), Top Operators (Stacked Bar), Country Combo (Line for count, Bar for Amount).

### 6.4 Retail High Value TXN
*   **Purpose:** Monitor individual high-value remittances.
*   **Logic:** Isolates transactions with `EQV USD >= 10,000`. Classifies into LOW (<10k), MEDIUM (10k-25k), HIGH (>=25k).
*   **KPIs:** High Risk Count, High Risk Exposure, Highest Exposure, Avg Exposure, Highest Risk Segment/Product/Branch/Corporate.
*   **Charts:** Risk Level Dist (Donut), Branch Exposure (Bar), Corp Exposure (Bar), Customer Concentration (Scatter), Product (Bar), Currency (Donut), Trend (Line).
*   **Observations:** Auto-generated text flagging >30% branch concentration, repeat customers, >20% country concentration.

### 6.5 High Risk Corporate
*   **Purpose:** Highlights activity involving High Risk entities.
*   **Filters:** Requires Party Master file. Defaults to `Risk Category == 'HIGH'`.
*   **Charts:** Risk Category Dist (Bar), Corporate Concentration (Bar), Branch/Country/Product Exposure (Grouped Bars).

### 6.6 FATF
*   **Purpose:** Track transactions to sanctioned/high-risk geographies.
*   **Filters:** Requires OFAC_FATF master file.
*   **Charts:** Flagged Branch by Segments (Grouped Bar), Flagged Country by Segments (Grouped Bar), Purpose Mix (Pie), Trend (Line).

### 6.7 Bank Book
*   **Purpose:** Balance and type summaries across bank channels.
*   **KPIs:** Cheque vs Transfer counts, CMS/NON CMS/HDFC totals.
*   **Charts:** Cheque vs Transfer (Donut), Segment Split (Stacked Bar), CMS Comparison (Bar).
*   **Exceptions Engine:** Auto-flags Rule 1 (>10% Party concentration), Rule 3 (>25% Account Dependency), Rule 5 (Cheque Conc.), Rule 6 (CMS Imbalance).

### 6.8 Cash Analysis
*   **Purpose:** Flag structural cash reporting bypasses.
*   **Filters:** Strictly filters for `Txn Type` IN `['PB', 'PS']`.
*   **Rules:** High Value Cash Alerts -> `Rec/Pay Amt > 49,000`.
*   **Charts:** Top Branches by PB/PS Count and Amount (Bars). Alert Trend (Line).

### 6.9 Agent Analysis
*   **Purpose:** Audit agent transaction velocity and entity linking.
*   **KPIs:** Total Agents, Agent Contribution, Seg/Prod/Purp/Branch with most Agents.
*   **Rules:** Rule 1 (1 Agent -> Many Beneficiaries), Rule 1A (1 Agent -> 1 Beneficiary High Frequency), Rule 2 (Many Corporates), Rule 3 (Many Branches), Rule 4 (Many Countries).

### 6.10 Passenger Analysis
*   **Purpose:** KYC Quality and Identity Anomaly validation.
*   **Data Prep:** Classifies `PAXIDNO` into `PAN`, `PASSPORT`, `INVALID`, `BLANK`. Validates email/mobile regex.
*   **Anomalies:** Rules A-J (See Transaction Monitoring section below).
*   **KPIs:** Worst Branch by Invalid ID/Mobile/Email/Missing KYC.

### 6.11 Currency Ratio
*   **Purpose:** Replenishment ratios (Retail Sales vs Bulk Purchase).
*   **Logic:** Ratio = (Retail Sales / Bulk Purchase) * 100.
*   **Flags:** Ratio > 100% or Ratio < 25%.

### 6.12 MLTF
*   **Purpose:** Aggregates High/Medium risk corporates + FATF flagged transactions.

---

## 7. KPI Catalogue

| KPI Name | Calculation Logic / Formula | Dashboard Location | Business Meaning |
| :--- | :--- | :--- | :--- |
| **Total Net Amount** | `SUM(Net Amt)` | Global/Home | Total monetary volume processed. |
| **PS Count / Amt** | `COUNT` / `SUM(Net Amt)` WHERE `Txn Type == 'PS'` | Home Page | Volume/value of Purchase Sales. |
| **Contribution to PS %** | `(Filtered Net Amt / Total PS Net Amt) * 100` | Tour Operator | Reliance of sales on specific operator segments. |
| **High Risk Count** | `COUNT` WHERE `EQV USD >= 25,000` | Retail High Value | Transactions requiring immediate AML review. |
| **Structuring Alerts** | `COUNT` WHERE `EQV USD` between 20,000 and 25,000 | Retail High Value | Potential attempts to evade $25k reporting limits. |
| **Same-Day Refunds** | `COUNT` WHERE Load-Refund `WITHIN_DAYS == 0` | Txn Monitoring | Circular fund movements (layering indicator). |
| **Average Refund Delay** | `MEAN(REFUND_DATE - LOAD_DATE)` | Txn Monitoring | Speed at which prepaid cards are cashed out. |
| **Missing KYC** | `COUNT` WHERE ID, Email, OR Mobile is Null | Passenger Analysis | Data quality gap posing regulatory risk. |

---

## 8. Chart Catalogue

| Chart Name | Chart Type | X Axis | Y Axis | Grouping / Color | Dashboard Page | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Transaction Trend** | Line | Date (Daily/Weekly) | Count or Net Amt | None | Home Page | Velocity monitoring over time. |
| **Purpose Mix** | Donut | - | Net Amt | Purpose | Home, Tour Op | Composition of transaction reasons. |
| **Branch-wise Txn Type**| Stacked Bar (Horiz) | Net Amt / Count | Branch Name | Txn Type | Txn Summary | Channel usage by geographic location. |
| **Customer Concentration**| Scatter | Txn Count | Total USD | Size=Max_USD | Retail High Value | Identify whales and high-velocity individuals. |
| **Country Exposure** | Bar | Country | Net Amt | Risk Category | High Risk Corp | Geopolitical risk mapping. |
| **Cheque vs Transfer** | Donut | - | Count / Amt | Cheque/Transfer | Bank Book | Payment method splits. |
| **Alert Branch Dist** | Bar | Branch | Alert Count | None | Cash Analysis | Identifies branches violating 49k cash rules. |
| **Agent Frequency** | Bar | Agent Name | Count / Amt | None | Agent Analysis | Find outlier agents handling massive volumes. |
| **Distribution of Refund Delays** | Histogram | Days (Delay) | Event Count | None | Txn Monitoring | Shows clustering of rapid refund behavior. |

---

## 9. Transaction Monitoring Engine

### Core AML Rules

#### 1. High Value Transactions
*   **Objective:** Flag massive individual exposures and structuring.
*   **Detection Logic:** `EQV USD > 25,000`. Structuring alert: `20,000 <= EQV USD <= 25,000`.
*   **Outputs:** Count, Exposure amount, highest transaction.

#### 2. FATF / OFAC Match
*   **Objective:** Sanctions screening.
*   **Detection Logic:** `Visiting Country` joined against OFAC lists. Flags if segment is NOT 'NOT FLAGGED'.

#### 3. Multiple Operators to Same Beneficiary
*   **Objective:** Detect Hawala/Shell Operator networks.
*   **Filters:** `Segments == 'TOUR OPERATOR'`.
*   **Detection Logic:** Group by `Beneficiary`. Flag if `COUNT(DISTINCT Corporate) >= 2` AND `COUNT(Txns) >= 5`.

#### 4. High Frequency Remittances (Velocity)
*   **Objective:** Detect structured remittances to a single entity.
*   **Filters:** `Segments == 'TOUR OPERATOR'`.
*   **Detection Logic:** Group by `[Party Code, Beneficiary]`. Flag if `COUNT(Txns) > 5`.

#### 5. Configurable Load-to-Refund Window
*   **Objective:** Detect card misuse, immediate cancellation, or layering.
*   **Filters:** `Product IN ['EC', 'FC']`.
*   **Detection Logic:** 
    1. Split dataset into `Loads` (`Type IN ['LOAD', 'RELOAD']` AND `Txn Type == 'PS'`).
    2. Split dataset into `Refunds` (`Type == 'REFUND'`).
    3. INNER JOIN on `INSTRUMENTNO`.
    4. Calculate `WITHIN_DAYS = REFUND_DATE - LOAD_DATE`.
    5. Flag if `0 <= WITHIN_DAYS <= threshold_days` (UI configurable, engine default 30).
*   **Consolidation Logic:** Merges duplicate context columns (e.g., `Branch_LOAD`, `Branch_REFUND`). If identical, keeps one. If different, concatenates with ` / `.

#### 6. Multiple Cards to Same Contact Information
*   **Objective:** Smurfing/Mule account detection.
*   **Filters:** `Product IN ['EC', 'FC']`, `Txn Type == 'PS'`.
*   **Detection Logic:** Group by `MOBILENO`. Flag if `COUNT(DISTINCT INSTRUMENTNO) >= 3`.

#### 7. Multiple Cards to Same Traveller
*   **Objective:** Capital flight/Structuring.
*   **Filters:** `Product IN ['EC', 'FC']`, `Txn Type == 'PS'`.
*   **Detection Logic:** Group by `Passenger Name`. Flag if `COUNT(DISTINCT INSTRUMENTNO) >= 2`.

#### 8. Multi-Card Multi-Operator Use
*   **Objective:** Sophisticated layering utilizing multiple financial institutions.
*   **Filters:** `Product IN ['EC', 'FC']`, `Txn Type == 'PS'`.
*   **Detection Logic:** Group by `Passenger Name`. Flag if `COUNT(DISTINCT INSTRUMENTNO) >= 2` AND `COUNT(DISTINCT Corporate) >= 2`.

### KYC Anomaly Rules (Passenger Analysis)
*   **Rule A:** Same PAX ID, Different Emails.
*   **Rule B:** Same PAX ID, Different Names.
*   **Rule C:** Same PAX ID, Different Mobiles.
*   **Rule D:** Missing PAX ID with valid Contact Info.
*   **Rule E:** Same Email, Different PAX IDs.
*   **Rule F:** Same Mobile, Different PAX IDs.
*   **Rule G:** Same Email, Different Names.
*   **Rule H:** Same Mobile, Different Names.
*   **Rule I:** Frequent Passenger Activity (Configurable threshold, default >10).
*   **Rule J:** Missing KYC (ID, Email, or Mobile is empty).

---

## 10. Risk Flag Engine

Executed in `build_transaction_risk_profile()`.

*   **Individual Rule Flags:** Boolean columns appended to dataset (e.g., `df['High Value Transaction'] = True/False`).
*   **Risk_Rule_Count:** `SUM(Rule_1_Flag, Rule_2_Flag, ..., Rule_8_Flag)` per transaction row.
*   **Any_Risk_Flag:** `Risk_Rule_Count > 0`.
*   **Risk Score:** Weighted sum based on severity. (e.g., High Value = 2, FATF = 3).

---

## 11. Transaction Risk Review Table

A consolidated view located at the bottom of the Transaction Monitoring page.

*   **Search Logic:** Case-insensitive, partial-match text search across `['Passenger Name', 'INSTRUMENTNO', 'MOBILENO', 'Corporate', 'Party Code', 'Beneficiary Type Load or Reload']`.
*   **Risk Count Filter:** Numeric input (0 to Total Active Rules). Filters dataframe: `Risk_Rule_Count >= threshold`.
*   **Reset Logic:** Clears search text and sets threshold to 0.
*   **Flag Columns:** Rule booleans are converted to UI indicators (`✔` / `✘`).

---

## 12. Export Framework

*   **Format:** Standard CSV (`text/csv`). UTF-8 encoded.
*   **Implementation:** Utilizes Streamlit's `st.download_button`. 
*   **Locations:** Every module has a top-right global export. Investigation tables have localized exports.
*   **Logic:** Exports respect *all* currently active UI filters and specific rule contexts.

---

## 13. Configuration Registry

| Configuration Setting | Usage | Default Value | Min/Max Range |
| :--- | :--- | :--- | :--- |
| **High Value Threshold** | Retail High Value Page / Rule 1 | $25,000 | - |
| **Structuring Minimum** | Retail High Value Page / Cash | $20,000 (Retail) / ₹49,000 (Cash) | - |
| **Beneficiary Freq Threshold**| Txn Monitoring Rule 4 | 5 Transactions | - |
| **Load-to-Refund Window** | Txn Monitoring Rule 5 | 1 Day (UI) / 30 Days (Engine) | 0 to Max Date Range |
| **Max Cards per Mobile** | Txn Monitoring Rule 6 | 3 Cards | - |
| **Agent Link Threshold** | Agent Analysis Rules 1-4 | 10 Linked Entities | 1 to infinity |

---

## 14. Session State

| Key | Purpose | Default Value |
| :--- | :--- | :--- |
| `current_file_id` | Tracks active file to prevent unnecessary re-processing. | Uploaded File Hash |
| `risk_df` | Holds the fully enriched, memory-cached dataframe. | `None` |
| `risk_flags` | List of active rule column names. | `[]` |
| `shared_ofac_file` | Persists the uploaded OFAC file across page navigations. | `None` |
| `review_search` | State for the Transaction Review table text filter. | `""` |
| `review_threshold` | State for the Transaction Review table risk count filter. | `0` |
| `load_refund_threshold` | Configurable days for the Load-to-Refund rule. | `1` |
| `top_page_selector` | Tracks active active routing page. | `'Migration Validation'` |

---

## 15. React/Angular Migration Mapping

To rebuild the UI/UX without Streamlit, map the current components as follows:

| Streamlit Component | React Equivalent (MUI / AntD) | Angular Equivalent (Angular Material) |
| :--- | :--- | :--- |
| `st.sidebar` | Persistent Left Drawer / Sidenav | `mat-sidenav` |
| `st.multiselect` | Autocomplete with Multi-select chips | `mat-select` with `multiple` |
| `st.metric` | Custom KPI Card Component | Custom KPI Card Component |
| `st.expander` | Accordion / Expansion Panel | `mat-expansion-panel` |
| `st.dataframe` | AG Grid / DataTables / MUI DataGrid | AG Grid / `mat-table` (with pagination) |
| `st.plotly_chart` | `react-plotly.js` or Recharts | `angular-plotly.js` or Highcharts |
| `@st.cache_data` | Redux / React Query / SWR / Zustand | NgRx / RxJS BehaviorSubjects |

---

## 16. API Design Requirements

For a decoupled SPA architecture, the following backend endpoints (Node.js/Python FastAPI) must be constructed:

*   `POST /api/v1/dataset/upload`
    *   **Payload:** `multipart/form-data` (TXN MIS file, Master Files).
    *   **Response:** Job ID, Row counts, Validation status.
*   `POST /api/v1/dataset/process`
    *   **Action:** Executes Canonical Pipeline + Risk Engine.
*   `POST /api/v1/dashboard/query`
    *   **Payload:** Global Filters (Branch, Date Range, Product, etc.), Target View.
    *   **Response:** Aggregated JSON for Charts & KPIs.
*   `POST /api/v1/monitoring/execute`
    *   **Payload:** Rule Name, dynamic thresholds (e.g., `load_refund_window: 7`).
    *   **Response:** Paginated anomalous transaction records, Rule KPIs.
*   `POST /api/v1/export`
    *   **Payload:** Current Filters, Table context.
    *   **Response:** Blob / URL to download generated CSV.

---

## 17. Technical Debt & Known Issues

*   **In-Memory Processing Constraint:** The current architecture relies heavily on Pandas processing entirely in RAM. Files over 1-2 million rows may cause memory limits on standard machines. Future architecture should push aggregation to a Database (SQL/Snowflake) via the backend API.
*   **Stateless Uploads:** If the browser refreshes, the uploaded transaction file is lost. A backend migration should implement a persistent datastore with session/tenant IDs.
*   **Global Sorting in Asynchronous Merges:** Earlier versions of Rule 5 used `merge_asof`, causing strict monotonicity errors. The logic is now correctly stabilized using Inner Joins and vectorized date-math (`dt.days`), which must be strictly replicated in any SQL migration (e.g., using `DATEDIFF`).
*   **Refund Transaction Types:** Load transactions are `PS`, Refunds are `PB`. Any global application of `Txn Type == 'PS'` onto the dataset will silently destroy refund matching logic. The pipeline must filter `PS` only *after* splitting the loads and refunds.
*   **Special Character Injection:** Legacy data systems often inject characters like backticks (\`) into Card Numbers. The `clean_identifier` step in canonicalization is mandatory to prevent type-casting crashes in arrow/JSON serialization.
```