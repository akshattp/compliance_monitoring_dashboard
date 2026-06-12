# GlobalPay AML & Compliance Dashboard
### Operations & User Manual

Welcome to the **GlobalPay AML & Compliance Monitoring Portal**. This system has been developed to automate the monthly transaction review process for the compliance team. 

Earlier, manually cleaning, cross-referencing, and analyzing transactions for AML (Anti-Money Laundering) checks took **4 to 5 days**. With this automated portal, the compliance team just has to upload the transaction ledger, and the entire audit, risk profiling, and trend analysis are completed **in minutes**.

---

## 1. How the Dashboard Works (For Non-Technical Users)

You do **not** need any coding knowledge to use this portal. Follow these simple steps to perform your monthly review:

### Step 1: Open the Portal
*   **On Windows**: Simply search for PowerShell, open it, navigate to the folder, and run:
    ```powershell
    ./run_windows.ps1
    ```
    This script will automatically install any missing dependencies and start the portal in your web browser.
*   **Direct URL**: Once running, the portal will open in your browser at `http://localhost:8501`.

### Step 2: Put Reference Files in Place
The dashboard relies on reference master lists to identify high-risk accounts and countries. Before uploading your transaction file, make sure these two files are placed in the `data/` folder:
1.  **`Party Master New Report.csv`**: Contains corporate risk categorizations (High, Medium, Low).
2.  **`OFAC_FATF COUNTRY UPDATED.xlsx`**: Contains flagged high-risk and sanctioned countries.

### Step 3: Upload the Transaction Ledger
1.  Locate the left sidebar.
2.  Drag and drop your monthly transaction workbook into the **"Upload TXN LINE MIS workbook"** box (accepts `.xlsx` or `.xls` files).
3.  The portal will show a progress bar while it processes, standardizes, and cross-references the data.

### Step 4: Verify the Row Counts
1.  Select the **Migration Validation** tab from the top navigation bar.
2.  Verify the green checkmark: `✅ Row count is consistent throughout the pipeline.`
3.  This ensures that 100% of the transactions in your raw file were successfully loaded without any loss of data.

### Step 5: Filter, Analyze, and Download
*   **Group Filters**: Each tab has a **"Filters"** expander in the sidebar or at the top. Use them to narrow down data by Branch, Product, Purpose, Date Range, or FATF Status.
*   **Search**: In any transaction table, you can type in the search box to find specific customer names, passport numbers, or transactions.
*   **Download Report**: Click the **📥 Download** or **Download filtered transactions** button to save the filtered data as a CSV spreadsheet.

---

## 2. Project Folder Structure (For Admins)

The application follows a clean modular structure. Here is where everything resides:

```text
Dashboard Automation/
├── app.py                      # Main entrypoint (starts the Streamlit app)
├── canonical_dataset.py        # Core processing engine (cleans data & merges master sheets)
├── requirements.txt            # Package dependencies (pandas, streamlit, plotly, openpyxl)
├── run_windows.ps1             # PowerShell script to launch the app on Windows
├── favicon-black.png           # Browser tab icon
├── global-pay-logo1.jpg         # Left sidebar brand logo
├── UIUX.jpg                    # Dashboard background banner asset
├── data/                       # Storage for reference lists
│   ├── Party Master New Report.csv
│   └── OFAC_FATF COUNTRY UPDATED.xlsx
├── charts/                     # Visualization module
│   ├── __init__.py             # Exports standard charts
│   ├── comparisons.py          # Branch comparison charts
│   ├── distributions.py        # Bar and donut charts
│   ├── heatmap.py              # Risk heatmaps
│   ├── trend.py                # Line charts (daily/weekly trends)
│   └── theme.py                # Enterprise light theme configuration
├── rules/                      # Risk Profiling module
│   ├── __init__.py             # Exports transaction rules
│   ├── aml_rules.py            # Logical checks for risk categories
│   └── monitoring_engine.py    # Master risk profiling builder & risk scoring
├── pages/                      # Individual Dashboard Tabs
│   ├── __init__.py             # Declares tabs and active layouts
│   ├── migration_validation.py # Data load check page
│   ├── home_page.py            # Overview dashboard
│   ├── transaction_summary.py  # Segment & Transaction Composition
│   ├── tour_operator.py        # Tour Operator Remittances
│   ├── retail_high_value_txn.py# Transactions over $10K USD
│   ├── high_risk_corporate.py  # Trusts, Societies & High Risk Entities
│   ├── fatf.py                 # Geographical Risk Monitoring
│   ├── bank_book.py            # Bank Book and product balances
│   ├── cash_analysis.py        # Cash flow threshold flags
│   ├── transaction_monitoring.py# Isolated AML Surveillance Console
│   ├── currency_ratio.py       # Currency composition ratios
│   ├── agent_analysis.py       # Multi-entity agent velocity audit
│   ├── mltf.py                 # Money Laundering & Terrorist Financing risks
│   └── passenger_analysis.py   # Passenger KYC quality & anomaly validation
├── utils/                      # Helper utilities
│   ├── __init__.py             # Common imports
│   ├── data_loader.py          # Legacy data load helper (for scripts)
│   ├── filters.py              # User filter query builders
│   ├── formatters.py           # Indian currency formatting (Cr / L / K)
│   └── ui.py                   # UI styles and headers
└── scripts/                    # Offline tools
    └── preview_pages.py        # Command-line preview report generator
```

---

## 3. Detailed Tab-by-Tab and Compliance Rule Guide

Each tab in the navigation bar represents a specific module. Here is a guide on what they do, the rules they apply, and what to look out for:

### 1. Migration Validation
*   **Purpose**: Quality control check to confirm that no records were deleted or altered during the import.
*   **Rules / Metrics**:
    *   Compares raw row count vs canonical row count.
    *   Displays totals for distinct Products, Segments, and Transaction Types.
    *   Shows overall breakdown of risk categories and OFAC/FATF flag counts.

### 2. Home Page
*   **Purpose**: The central landing page providing an executive overview of the month's metrics.
*   **Rules / Metrics**:
    *   **KPIs**: Overall Purchase (PB) / Sale (PS) volumes, transaction counts, averages, and date ranges.
    *   **Trends**: Daily or weekly line charts for transaction counts and volumes.
    *   **Concentrations**: Breakdowns of your top products, purposes, branches, and countries.

### 3. Transaction Summary
*   **Purpose**: Analyzes transaction type mix (e.g., PS, PB, CB, FB) and branch composition.
*   **Rules / Metrics**:
    *   Summarizes transaction types with a stack bar.
    *   Provides drilldowns into branch, product, and segment composition.
    *   Allows legend filtering to examine specific transaction categories (like cash vs bank transfers).

### 4. Tour Operator
*   **Purpose**: Specialized review of tour operator remittances.
*   **Rules / Metrics**:
    *   Filters transactions categorized under Tour operator purposes (e.g., `REMITTANCE BY TOUR OPERATORS` and `MICE -REMITANCE BY TOUR OPERATORS`).
    *   Flags concentrations to identify if a few operators represent the majority of transactions.
    *   Displays branch and corporate exposure tables.

### 5. Retail High Value TXN
*   **Purpose**: Monitors high-value individual remittances exceeding standard thresholds.
*   **Rules / Metrics**:
    *   Isolates transactions where the equivalent USD amount is **$10,000 USD or more**.
    *   **High Risk Flag**: Applied to transactions of **$25,000 USD or more**.
    *   Plots customer concentration to find repeat high-value senders.

### 6. High Risk Corporate
*   **Purpose**: Highlights corporate activity flagged in your master records.
*   **Rules / Metrics**:
    *   Isolates transactions involving entities flagged as **"HIGH"** risk in the `Party Master`.
    *   Also flags structures likely to require enhanced due diligence, such as **Trusts, NGOs, and Societies**.

### 7. FATF
*   **Purpose**: Monitors transactions to high-risk geographical zones.
*   **Rules / Metrics**:
    *   Cross-references country names with the `OFAC/FATF Country` sheet.
    *   Isolates countries marked as FATF grey-list/black-list, OFAC sanctioned, or CIS Countries.

### 8. Bank Book
*   **Purpose**: Balances and type summaries across your banking channels.
*   **Rules / Metrics**:
    *   Groups and compares transaction counts and totals across the bank book's payment categories.

### 9. Cash Analysis
*   **Purpose**: Flags structural transactions designed to bypass regulatory cash reporting.
*   **Rules / Metrics**:
    *   Isolates cash-like transaction types (`PS` - Cash Sale, `PB` - Cash Purchase).
    *   **Structuring Rule**: Identifies transactions between **45,000 and 50,000 INR** (designed to catch splits just under the 50,000 INR pan-card declaration limit).

### 10. Transaction Monitoring (AML Surveillance Console)
*   **Purpose**: This is your main investigation console. It applies **4 isolated AML rules** that run independently.
*   **The 4 Rules Applied**:
    1.  **High Value Transaction**: Flagged if a transaction's equivalent USD amount exceeds **$25,000 USD**. It also checks for structuring alerts (transactions between $20,000 and $25,000 USD).
    2.  **FATF / OFAC Match**: Flagged if a transaction's visiting country is matches a flagged region on the OFAC/FATF master lists.
    3.  **Multiple Tour Operators to Same Beneficiary**: Flagged if **2 or more distinct operators** send **5 or more total transactions** to the exact same beneficiary name within the month. (Checks for shell operators/hawala routing).
    4.  **High Frequency Remittances**: Flagged if **a single operator** sends **more than 5 remittances** to the exact same beneficiary in the month. (Checks for structured velocity).

### 11. Currency Ratio
*   **Purpose**: Tracks utilization and reserve mix across major world currencies (USD, EUR, GBP, etc.).

### 12. Agent Analysis
*   **Purpose**: Audits transaction agents for compliance issues.
*   **Suspicious Agent Rules Applied**:
    *   **Rule 1 (Different Beneficiaries)**: Flags agents routing transactions to different beneficiaries above a configurable threshold.
    *   **Rule 2 (Different Corporates)**: Flags agents operating under multiple distinct corporate accounts.
    *   **Rule 3 (Different Branches)**: Flags agents executing transactions across multiple distinct branches.
    *   **Rule 4 (Different Countries)**: Flags agents routing bookings to multiple visiting countries.

### 13. MLTF
*   **Purpose**: Money Laundering & Terrorist Financing risk flags.
*   **Rules / Metrics**:
    *   Isolates and aggregates transactions flagged as High or Medium risk for audit reports.

### 14. Passenger Analysis
*   **Purpose**: Essential page to inspect customer documentation quality (KYC).
*   **KYC Rules & Anomaly Checks**:
    *   **PAX ID Classifier**: Categorizes passenger documentation IDs into **PAN** (format: 5 letters, 4 digits, 1 letter), **Passport** (format: 1 letter, 7 digits), **Blank**, or **Invalid** formats.
    *   **Anomaly Rule A**: Flags passengers sharing the same ID number but using different email addresses.
    *   **Anomaly Rule B**: Flags passengers sharing the same ID number but using different names.
    *   **Anomaly Rule C**: Flags passengers sharing the same ID number but using different mobile numbers.
    *   **Anomaly Rule D**: Flags records where name and contact info are present but the ID is missing.
    *   **Anomaly Rule E**: Flags single emails linked to multiple PAX IDs.
    *   **Anomaly Rule F**: Flags single mobile numbers linked to multiple PAX IDs.
    *   **Anomaly Rule G/H**: Flags single contact info associated with multiple names.
    *   **Anomaly Rule J (Missing KYC)**: Flags any record missing a valid ID, email, or phone.
    *   **Branch Quality Ranking**: Ranks branches from best to worst based on their total data issue counts, giving each branch a percentage data quality score.

---

## 4. Frequently Asked Questions (FAQ)

#### Q: I uploaded a ledger and received a "Row Count Mismatch" error. What should I do?
*   **Reason**: The pipeline standardizes and cleans row values. If a join or lookup duplicate exists in your reference data, row counts can change.
*   **Fix**: Ensure your `Party Master New Report.csv` has unique customer code entries and no duplicate rows.

#### Q: The charts are blank or throw a "Key Error".
*   **Reason**: Your uploaded transaction spreadsheet is missing one or more required columns.
*   **Fix**: Verify your transaction sheet columns match standard bank names (e.g., `BRANCHCODE`, `LOCATION`, `TXNTYPE`, `DOCNO`, `TXNDATE`, `CUSTOMERCODE`, `CUSTOMERNAME`, `AGENTCODE`, `AGENTNAME`, `TxnPurpose`, `CURRENCY`, `PRODUCT`, `INRAMOUNT`).

#### Q: Can I run this offline?
*   **Yes**. The system operates entirely on your local machine. It does not upload any transaction data to the internet, satisfying internal corporate privacy and audit controls.

---

## 5. Detailed Troubleshooting Guide for Non-Technical Users

If you see a large red box or a UI error on the screen, don't panic! It is almost always a data format issue. Here is exactly what to check based on what you see:

### Problem: "KeyError: 'Some Column Name'"
*   **What you see:** A red error box that says `KeyError` followed by a column name like `'Net Amt'` or `'Segments'`.
*   **Why it happens:** The dashboard is looking for a specific column in your uploaded Excel file, but it cannot find it. This happens if the column was deleted, renamed (even accidentally adding a space like `"Segments "`), or misspelled in the raw file.
*   **How to fix:** Open your raw Excel file and verify that the column mentioned in the error exists exactly as expected. Correct the column header name in Excel, save the file, and re-upload it to the portal.

### Problem: "FileNotFoundError: [Errno 2] No such file or directory"
*   **What you see:** An error mentioning `FileNotFoundError` for the master reference files.
*   **Why it happens:** The system cannot find the `Party Master New Report.csv` or the `OFAC_FATF COUNTRY UPDATED.xlsx` files in the `data/` folder.
*   **How to fix:** Ensure both of those files are saved in the `data/` folder inside the `Dashboard Automation` directory. Check that their names match *exactly*.

### Problem: "ValueError: Cannot convert string to float"
*   **What you see:** A red error mentioning `ValueError` when trying to plot a chart or calculate KPIs.
*   **Why it happens:** You have text or special characters (like "N/A", "TBD", or a comma in the wrong place) inside a column that should only contain numbers (such as an amount column).
*   **How to fix:** Open the Excel file, go to the amount columns, and ensure there are no alphabetic characters or hidden spaces in the numerical data. Clear any "N/A" strings, save, and re-upload.

### Problem: Charts are completely blank or say "No data available"
*   **What you see:** A blank space where a pie chart or bar chart should be, or a message saying there's no data.
*   **Why it happens:** The filters you have applied in the sidebar or at the top of the tab are too restrictive, resulting in zero matching transactions. 
*   **How to fix:** Look at your filters. Click the "X" on some of the filter tags (like Date Range, Branch, or Product) to widen your search until data appears again.

### Problem: The Dashboard stopped responding / Spinner keeps spinning forever
*   **What you see:** The word "Running..." in the top right corner with a spinner that doesn't go away for more than 5 minutes.
*   **Why it happens:** Your uploaded file might be excessively large (e.g., hundreds of megabytes), or a background process froze.
*   **How to fix:** Refresh your web browser page (press F5 or Ctrl+R). If that doesn't work, go to the black command prompt / PowerShell window where you started the dashboard, press `Ctrl + C` to stop it, and then run `./run_windows.ps1` again.
