import pandas as pd
import numpy as np
import time
import re

class RowCountMismatchError(Exception):
    pass

def _validate_row_count(df, initial_count, step_name):
    if len(df) != initial_count:
        raise RowCountMismatchError(f"Row count changed after {step_name}. Initial: {initial_count}, After: {len(df)}")

def clean_mobile_number(val):
    """
    Standardize mobile numbers: remove .0 suffix, spaces, and null-like values.
    """
    if pd.isna(val) or str(val).strip().upper() in ['', 'NAN', 'NONE', 'NULL']:
        return np.nan
    s = str(val).strip()
    # Remove .0 suffix created by pandas numeric conversion
    s = re.sub(r'\.0$', '', s)
    # Remove all spaces
    s = s.replace(' ', '')
    return s

def clean_identifier(val):
    """
    Standardize identifiers (codes, cards, passports): remove leading/trailing 
    special characters, whitespace and invisible characters.
    """
    if pd.isna(val) or str(val).strip().upper() in ['', 'NAN', 'NONE', 'NULL']:
        return np.nan
    s = str(val).strip()
    # Remove leading/trailing special characters defined in compliance requirements
    chars_to_remove = "'`~#*\""
    s = s.strip(chars_to_remove).strip()
    # Clean suffix .0 which is common in numeric identifiers from Excel
    s = re.sub(r'\.0$', '', s)
    # Remove non-printable/invisible characters
    s = re.sub(r'[^\x20-\x7E]', '', s)
    return s

def standardize_identifier_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Centralized preprocessing to clean known identifier-like columns.
    """
    mobile_cols = ['MOBILENO']
    
    identifier_cols = [
        'INSTRUMENTNO', 'Instrument Number',
        'Party Code', 'CUSTOMERCODE', 'PARTYCODE', 
        'Agent', 'AGENTCODE', 
        'Passport', 'PASSPORTNO', 
        'DOCNO'
    ]

    for col in df.columns:
        if col in mobile_cols:
            df[col] = df[col].apply(clean_mobile_number)
        elif col in identifier_cols:
            df[col] = df[col].apply(clean_identifier)
            
    return df

def create_canonical_dataset(txn_df: pd.DataFrame, party_master_path: str, ofac_path: str):
    """
    Creates a canonical compliance dataset from raw transaction data and reference files.
    """
    initial_row_count = len(txn_df)
    print(f"Source Row Count: {initial_row_count}")

    # 1. Standardize columns 
    column_mapping = {
        'BRANCHCODE': 'Branch',
        'LOCATION': 'Branch Name',
        'TXNTYPE': 'Txn Type',
        'DOCNO': 'Doc Number',
        'TXNDATE': 'Date',
        'CUSTOMERCODE': 'Party Code',
        'CUSTOMERNAME': 'Corporate',
        'PAXNAME': 'Passenger Name',
        'PAXIDNO': 'Passport',
        'AGENTCODE': 'Agent',
        'AGENTNAME': 'Agent Name',
        'TxnPurpose': 'Purpose',
        'CURRENCY': 'Currency',
        'PRODUCT': 'Product',
        'ISSUER': 'Issuer',
        'SELLRATE': 'Rate',
        'CountryToTravel': 'Visiting Country',
        'INSTRUMENTNO': 'INSTRUMENTNO',
        'LoadReload': 'LoadReload',
        'Segment': 'Segment',
        'BENEFICIARY': 'Beneficiary Type Load or Reload',
        'INRAMOUNT': 'Net Amt',
        'EMAILID': 'EMAILID',
        'MOBILENO': 'MOBILENO',
    }

    # Keep only columns that exist in the source, and rename
    df = txn_df[[col for col in column_mapping.keys() if col in txn_df.columns]].copy()
    df.rename(columns=column_mapping, inplace=True)

    # Global Data Standardization: Clean identifiers and contact info
    df = standardize_identifier_columns(df)

    # Basic data cleaning
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Net Amt'] = pd.to_numeric(df['Net Amt'], errors='coerce').fillna(0)
    df['Rate'] = pd.to_numeric(df['Rate'], errors='coerce')

    # Add date components for analysis (from legacy data.py)
    df['Day'] = df['Date'].dt.day.fillna(0).astype(int)
    df['Week'] = df['Date'].dt.isocalendar().week.fillna(0).astype(int)
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    df['Year'] = df['Date'].dt.year.fillna(0).astype(int)
    df['Weekday'] = df['Date'].dt.day_name().fillna('Unknown')

    # 2. Party Master Lookup
    pm_start = time.perf_counter()
    import os
    if os.path.exists(party_master_path):
        pm_df = pd.read_csv(party_master_path)
        pm_df.rename(columns={'Customer Code': 'CUSTOMERCODE', 'RISKCATEGORY': 'RISKCATEGORY_PM'}, inplace=True)
        pm_mapping = pm_df[['CUSTOMERCODE', 'RISKCATEGORY_PM']].copy()
        pm_mapping['CUSTOMERCODE'] = pm_mapping['CUSTOMERCODE'].apply(clean_identifier)
        pm_mapping.drop_duplicates(subset=['CUSTOMERCODE'], inplace=True)

        df = pd.merge(df, pm_mapping, left_on='Party Code', right_on='CUSTOMERCODE', how='left', validate="many_to_one")
        _validate_row_count(df, initial_row_count, "Party Master Lookup")
        print("Row count validated after Party Master Lookup.")
        
        def map_risk_category(risk):
            if pd.isna(risk):
                return 'Unknown'
            risk = str(risk).upper()
            if 'HIGH' in risk:
                return 'High'
            if 'MEDIUM' in risk:
                return 'Medium'
            if 'LOW' in risk:
                return 'Low'
            return 'Unknown'

        df['Risk Category'] = df['RISKCATEGORY_PM'].apply(map_risk_category)
        df.drop(columns=['CUSTOMERCODE', 'RISKCATEGORY_PM'], inplace=True, errors='ignore')
    else:
        df['Risk Category'] = 'Unknown'
        print("Party Master file not found, skipping enrichment.")
        
    print(f"Party Master Lookup Time: {round(time.perf_counter() - pm_start, 2)}s")

    # 3. OFAC FATF Lookup
    ofac_start = time.perf_counter()
    if os.path.exists(ofac_path):
        ofac_df = pd.read_excel(ofac_path, sheet_name='UPDATED FILE')
        ofac_mapping = ofac_df[['COUNTRY', 'Segment']].copy()
        ofac_mapping.rename(columns={'Segment': 'OFAC_FATF_Segment'}, inplace=True)
        ofac_mapping['COUNTRY'] = ofac_mapping['COUNTRY'].astype(str).str.strip().str.upper()
        ofac_mapping.drop_duplicates(subset=['COUNTRY'], inplace=True)

        df['Visiting Country_upper'] = df['Visiting Country'].astype(str).str.strip().str.upper()
        df = pd.merge(df, ofac_mapping, left_on='Visiting Country_upper', right_on='COUNTRY', how='left', validate="many_to_one")
        _validate_row_count(df, initial_row_count, "OFAC FATF Lookup")
        print("Row count validated after OFAC FATF Lookup.")

        df['OFAC_FATF'] = df['OFAC_FATF_Segment'].fillna('NOT FLAGGED')
        df.drop(columns=['Visiting Country_upper', 'COUNTRY', 'OFAC_FATF_Segment'], inplace=True, errors='ignore')
    else:
        df['OFAC_FATF'] = 'NOT FLAGGED'
        print("OFAC FATF file not found, skipping enrichment.")
        
    print(f"OFAC Lookup Time: {round(time.perf_counter() - ofac_start, 2)}s")

    # 4. Calculate Equivalent USD Amount
    eqv_start = time.perf_counter()
    df['DateOnly'] = df['Date'].dt.date
    usd_rates = df[df['Currency'] == 'USD'].groupby('DateOnly')['Rate'].mean().reset_index()
    usd_rates.rename(columns={'Rate': 'Daily_USD_Avg_Rate'}, inplace=True)
    
    df = pd.merge(df, usd_rates, on='DateOnly', how='left')
    df['Daily_USD_Avg_Rate'] = df['Daily_USD_Avg_Rate'].ffill().bfill()

    df['Equivalent USD Amount'] = df['Net Amt'] / df['Daily_USD_Avg_Rate']
    df.drop(columns=['DateOnly', 'Daily_USD_Avg_Rate'], inplace=True)
    
    _validate_row_count(df, initial_row_count, "Equivalent USD Amount Calculation")
    print("Row count validated after Equivalent USD Amount Calculation.")
    print(f"EQV USD Calculation Time: {round(time.perf_counter() - eqv_start, 2)}s")

    # 5. Create compliance fields
    df['High Value Transaction'] = df['Equivalent USD Amount'] > 25000
    df['FATF / OFAC Flag'] = df['OFAC_FATF'] != 'NOT FLAGGED'
    
    # For compatibility with existing pages
    df.rename(columns={
        'Equivalent USD Amount': 'EQV USD',
        'OFAC_FATF': 'OFAC _ FATF',
        'Risk Category': 'Risk  Category' # Note the double space in original code
    }, inplace=True)

    # 6. Standardize Segments
    if 'Segment' in df.columns:
        # Validation: Print Raw Segment Distribution
        print("\nRaw Segment Distribution")
        print("=" * 50)
        print(df["Segment"].value_counts(dropna=False))
        print("=" * 50)

        SEGMENT_STANDARDIZATION_MAP = {
            'Students Credila': 'EDUCATION',
            'Students Non-Credila': 'EDUCATION',
            'Corporate': 'CORPORATE',
            'Tour Remittance': 'TOUR OPERATOR',
            'Leisure': 'OTHER',
            'Other Remittance': 'OTHER',
            'Wholesale': 'OTHER',
            'Inter-Branch': 'OTHER',
            'Referral': 'OTHER',
            'Others': 'OTHER'
        }

        # Step 1: Create a new column 'Grouped Segment'
        df['Grouped Segment'] = (
            df['Segment']
            .astype(str)
            .str.strip()
            .map(SEGMENT_STANDARDIZATION_MAP)
            .fillna('OTHER')
        )
        
        # Step 2: Map 'Grouped Segment' to 'Segments' for dashboard compatibility
        df['Segments'] = df['Grouped Segment']

        # Validation
        print("\nGrouped Segment Distribution")
        print("=" * 50)
        print(df['Grouped Segment'].value_counts(dropna=False))
        print("=" * 50)

        print("\nSegments Distribution")
        print("=" * 50)
        print(df['Segments'].value_counts(dropna=False))
        print("=" * 50)

        # Row count validation
        _validate_row_count(df, initial_row_count, "Segment Standardization")
        print("Row count validated after Segment Standardization.")

        # Drop the intermediate column as it's no longer needed
        df.drop(columns=['Grouped Segment'], inplace=True)

    TEXT_COLUMNS = [
        'Passport',
        'Issuer',
        'Party Code',
        'Corporate',
        'Passenger Name',
        'EMAILID',
        'MOBILENO',
        'Beneficiary Type Load or Reload',
        'Instrument Number'
    ]
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str)

    _validate_row_count(df, initial_row_count, "Final Derived Fields")
    print(f"Canonical dataset created successfully. Final row count: {len(df)}")

    return df