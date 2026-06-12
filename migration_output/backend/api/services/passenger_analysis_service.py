import pandas as pd
import numpy as np
import re

def classify_doc_type(pax_id_clean):
    """Classifies a cleaned PAX ID into PAN, PASSPORT, BLANK, or INVALID."""
    if pd.isna(pax_id_clean) or pax_id_clean == '':
        return 'BLANK'
    
    # Regex for PAN
    if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', str(pax_id_clean)):
        return 'PAN'
        
    # Regex for Passport (New and Old formats)
    if re.match(r'^[A-Z][0-9]{7}$', str(pax_id_clean)) or re.match(r'^[A-Z]{1,2}[0-9]{6,8}$', str(pax_id_clean)):
        return 'PASSPORT'
        
    return 'INVALID'

def prepare_passenger_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepares the dataframe with standardized and validated passenger columns."""
    work_df = df.copy()

    # Standardize and Validate PAXIDNO (Passport)
    if 'Passport' in work_df.columns:
        work_df['PAXIDNO_CLEAN'] = work_df['Passport'].astype(str).str.strip().str.upper().replace('NAN', np.nan).replace('', np.nan)
    else:
        work_df['Passport'] = np.nan
        work_df['PAXIDNO_CLEAN'] = np.nan

    # Create DOC_TYPE
    work_df['DOC_TYPE'] = work_df['PAXIDNO_CLEAN'].apply(classify_doc_type)
    
    # For compatibility with existing anomaly rules, PAX_VALID is considered a valid PAN
    work_df['PAX_VALID'] = work_df['DOC_TYPE'].isin(['PAN', 'PASSPORT'])

    # Standardize and Validate MOBILENO
    if 'MOBILENO' in work_df.columns:
        work_df['MOBILE_CLEAN'] = work_df['MOBILENO'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True).replace('NAN', np.nan)
        work_df['MOBILE_VALID'] = work_df['MOBILE_CLEAN'].str.match(r'^[6-9][0-9]{9}$', na=False)
    else:
        work_df['MOBILENO'] = np.nan
        work_df['MOBILE_CLEAN'] = np.nan
        work_df['MOBILE_VALID'] = False

    # Standardize and Validate EMAILID
    if 'EMAILID' in work_df.columns:
        work_df['EMAIL_CLEAN'] = work_df['EMAILID'].astype(str).str.strip().str.lower().replace('nan', np.nan)
        work_df['EMAIL_VALID'] = work_df['EMAIL_CLEAN'].str.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', na=False)
    else:
        work_df['EMAILID'] = np.nan
        work_df['EMAIL_CLEAN'] = np.nan
        work_df['EMAIL_VALID'] = False
        
    # Missing KYC Flag
    work_df['MISSING_KYC'] = work_df['PAXIDNO_CLEAN'].isna() | work_df['EMAIL_CLEAN'].isna() | work_df['MOBILE_CLEAN'].isna()

    return work_df

def get_passenger_kpis(df: pd.DataFrame) -> dict:
    total_records = len(df)
    doc_type_counts = df['DOC_TYPE'].value_counts()
    pan_count = doc_type_counts.get('PAN', 0)
    passport_count = doc_type_counts.get('PASSPORT', 0)
    invalid_count = doc_type_counts.get('INVALID', 0)
    blank_count = doc_type_counts.get('BLANK', 0)

    pan_pct = (pan_count / total_records * 100) if total_records > 0 else 0
    passport_pct = (passport_count / total_records * 100) if total_records > 0 else 0
    invalid_pct = (invalid_count / total_records * 100) if total_records > 0 else 0
    blank_pct = (blank_count / total_records * 100) if total_records > 0 else 0

    most_freq_pax_id = 'N/A'
    most_freq_pax_name = 'N/A'
    most_freq_doc_type = 'N/A'
    most_freq_count = 0
    most_freq_pct = 0
    
    non_blank_df = df[df['DOC_TYPE'] != 'BLANK']
    if not non_blank_df.empty:
        freq_series = non_blank_df['PAXIDNO_CLEAN'].value_counts()
        if not freq_series.empty:
            most_freq_pax_id = freq_series.index[0]
            most_freq_count = freq_series.iloc[0]
            most_freq_pct = (most_freq_count / total_records * 100) if total_records > 0 else 0
            
            record = df[df['PAXIDNO_CLEAN'] == most_freq_pax_id].iloc[0]
            most_freq_pax_name = record['Passenger Name'] if 'Passenger Name' in record else 'N/A'
            most_freq_doc_type = record['DOC_TYPE']

    return {
        'total_records': total_records,
        'pan_count': pan_count,
        'pan_pct': pan_pct,
        'passport_count': passport_count,
        'passport_pct': passport_pct,
        'invalid_count': invalid_count,
        'invalid_pct': invalid_pct,
        'blank_count': blank_count,
        'blank_pct': blank_pct,
        'most_freq_pax_id': most_freq_pax_id,
        'most_freq_pax_name': most_freq_pax_name,
        'most_freq_doc_type': most_freq_doc_type,
        'most_freq_count': most_freq_count,
        'most_freq_pct': most_freq_pct,
    }

def get_passenger_anomalies(df: pd.DataFrame, rule_i_threshold: int = 10) -> dict:
    anomalies = {}

    # Rule A: Same PAXIDNO, Different EMAILID
    pax_grouped_email = df.dropna(subset=['PAXIDNO_CLEAN', 'EMAIL_CLEAN']).groupby('PAXIDNO_CLEAN')['EMAIL_CLEAN'].nunique()
    suspicious_pax_email = pax_grouped_email[pax_grouped_email > 1].index
    anomalies['rule_a'] = df[df['PAXIDNO_CLEAN'].isin(suspicious_pax_email)].sort_values(['PAXIDNO_CLEAN', 'EMAIL_CLEAN'])

    # Rule B: Same PAXIDNO, Different PAXNAME
    pax_grouped_name = df.dropna(subset=['PAXIDNO_CLEAN', 'Passenger Name']).groupby('PAXIDNO_CLEAN')['Passenger Name'].nunique()
    suspicious_pax_name = pax_grouped_name[pax_grouped_name > 1].index
    anomalies['rule_b'] = df[df['PAXIDNO_CLEAN'].isin(suspicious_pax_name)].sort_values(['PAXIDNO_CLEAN', 'Passenger Name'])

    # Rule C: Same PAXIDNO, Different MOBILENO
    pax_grouped_mobile = df.dropna(subset=['PAXIDNO_CLEAN', 'MOBILE_CLEAN']).groupby('PAXIDNO_CLEAN')['MOBILE_CLEAN'].nunique()
    suspicious_pax_mobile = pax_grouped_mobile[pax_grouped_mobile > 1].index
    anomalies['rule_c'] = df[df['PAXIDNO_CLEAN'].isin(suspicious_pax_mobile)].sort_values(['PAXIDNO_CLEAN', 'MOBILE_CLEAN'])

    # Rule D: Has EMAILID/PAXNAME, Missing PAXIDNO
    anomalies['rule_d'] = df[df['EMAIL_CLEAN'].notna() & df['Passenger Name'].notna() & df['PAXIDNO_CLEAN'].isna()]

    # Rule E: Same EMAILID, Different PAXIDNO
    email_grouped_pax = df.dropna(subset=['EMAIL_CLEAN', 'PAXIDNO_CLEAN']).groupby('EMAIL_CLEAN')['PAXIDNO_CLEAN'].nunique()
    suspicious_email_pax = email_grouped_pax[email_grouped_pax > 1].index
    anomalies['rule_e'] = df[df['EMAIL_CLEAN'].isin(suspicious_email_pax)].sort_values(['EMAIL_CLEAN', 'PAXIDNO_CLEAN'])

    # Rule F: Same MOBILENO, Different PAXIDNO
    mobile_grouped_pax = df.dropna(subset=['MOBILE_CLEAN', 'PAXIDNO_CLEAN']).groupby('MOBILE_CLEAN')['PAXIDNO_CLEAN'].nunique()
    suspicious_mobile_pax = mobile_grouped_pax[mobile_grouped_pax > 1].index
    anomalies['rule_f'] = df[df['MOBILE_CLEAN'].isin(suspicious_mobile_pax)].sort_values(['MOBILE_CLEAN', 'PAXIDNO_CLEAN'])

    # Rule G: Same EMAILID, Different PAXNAME
    email_grouped_name = df.dropna(subset=['EMAIL_CLEAN', 'Passenger Name']).groupby('EMAIL_CLEAN')['Passenger Name'].nunique()
    suspicious_email_name = email_grouped_name[email_grouped_name > 1].index
    anomalies['rule_g'] = df[df['EMAIL_CLEAN'].isin(suspicious_email_name)].sort_values(['EMAIL_CLEAN', 'Passenger Name'])

    # Rule H: Same MOBILENO, Different PAXNAME
    mobile_grouped_name = df.dropna(subset=['MOBILE_CLEAN', 'Passenger Name']).groupby('MOBILE_CLEAN')['Passenger Name'].nunique()
    suspicious_mobile_name = mobile_grouped_name[mobile_grouped_name > 1].index
    anomalies['rule_h'] = df[df['MOBILE_CLEAN'].isin(suspicious_mobile_name)].sort_values(['MOBILE_CLEAN', 'Passenger Name'])

    # Rule I: Frequent Passenger Activity
    pax_counts = df['PAXIDNO_CLEAN'].value_counts()
    frequent_pax = pax_counts[pax_counts > rule_i_threshold].index
    anomalies['rule_i'] = df[df['PAXIDNO_CLEAN'].isin(frequent_pax)]

    # Rule J: Missing KYC
    anomalies['rule_j'] = df[df['MISSING_KYC']]

    return anomalies

def get_branch_quality_summary(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if 'Branch Name' not in df.columns:
        return pd.DataFrame(), {}

    branch_summary = df.groupby('Branch Name').agg(
        Total_Records=('Date', 'size'),
        Invalid_ID=('PAX_VALID', lambda x: (~x).sum()),
        Invalid_Mobile=('MOBILE_VALID', lambda x: (~x).sum()),
        Invalid_Email=('EMAIL_VALID', lambda x: (~x).sum()),
        Missing_KYC=('MISSING_KYC', 'sum')
    ).reset_index()

    branch_summary['Total_Issues'] = (
        branch_summary['Invalid_ID'] +
        branch_summary['Invalid_Mobile'] +
        branch_summary['Invalid_Email'] +
        branch_summary['Missing_KYC']
    )
    
    branch_summary = branch_summary.sort_values('Total_Issues', ascending=False)

    worst_kpis = {}
    if not branch_summary.empty:
        worst_id = branch_summary.sort_values('Invalid_ID', ascending=False).iloc[0]
        worst_kpis['worst_id'] = {'Branch': worst_id['Branch Name'], 'Count': worst_id['Invalid_ID']}

        worst_mobile = branch_summary.sort_values('Invalid_Mobile', ascending=False).iloc[0]
        worst_kpis['worst_mobile'] = {'Branch': worst_mobile['Branch Name'], 'Count': worst_mobile['Invalid_Mobile']}

        worst_email = branch_summary.sort_values('Invalid_Email', ascending=False).iloc[0]
        worst_kpis['worst_email'] = {'Branch': worst_email['Branch Name'], 'Count': worst_email['Invalid_Email']}

        worst_kyc = branch_summary.sort_values('Missing_KYC', ascending=False).iloc[0]
        worst_kpis['worst_kyc'] = {'Branch': worst_kyc['Branch Name'], 'Count': worst_kyc['Missing_KYC']}

    return branch_summary, worst_kpis
