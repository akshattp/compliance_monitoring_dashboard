import pandas as pd
import numpy as np
from backend.utils import detect_fatf_records

def get_fatf_flagged_transactions(df: pd.DataFrame, ofac_df: pd.DataFrame = None) -> pd.DataFrame:
    if ofac_df is not None:
        if 'COUNTRY' not in ofac_df.columns or 'Segment' not in ofac_df.columns:
            raise ValueError("OFAC file must contain 'COUNTRY' and 'Segment' columns.")
        
        ofac_mapping = ofac_df[['COUNTRY', 'Segment']].copy()
        ofac_mapping.rename(columns={'Segment': 'OFAC_FATF_Segment'}, inplace=True)
        ofac_mapping['COUNTRY'] = ofac_mapping['COUNTRY'].astype(str).str.strip().str.upper()
        ofac_mapping.drop_duplicates(subset=['COUNTRY'], inplace=True)

        work_df = df.copy()
        if 'Visiting Country' in work_df.columns:
            work_df['Visiting Country_upper'] = work_df['Visiting Country'].astype(str).str.strip().str.upper()
            enriched = pd.merge(work_df, ofac_mapping, left_on='Visiting Country_upper', right_on='COUNTRY', how='left')
            enriched['FATF / OFAC Flag'] = enriched['OFAC_FATF_Segment'].notna() & (enriched['OFAC_FATF_Segment'] != 'NOT FLAGGED')
            # For compatibility with filters, also add 'OFAC _ FATF'
            enriched['OFAC _ FATF'] = enriched['OFAC_FATF_Segment'].fillna('NOT FLAGGED')
            return enriched[enriched['FATF / OFAC Flag']].copy()
            
    return detect_fatf_records(df)

def get_fatf_kpis(flagged: pd.DataFrame, filtered_df: pd.DataFrame) -> dict:
    total_count = len(filtered_df)
    total_amount = filtered_df['Net Amt'].sum(min_count=1) if not filtered_df.empty else 0
    contrib_pct = (len(flagged) / total_count * 100) if total_count > 0 else 0
    contrib_amt_pct = (flagged['Net Amt'].sum(min_count=1) / total_amount * 100) if total_amount > 0 else 0
    
    return {
        'flagged_count': len(flagged),
        'flagged_amount': flagged['Net Amt'].sum(min_count=1) if not flagged.empty else 0,
        'contrib_pct': contrib_pct,
        'contrib_amt_pct': contrib_amt_pct,
    }

def get_fatf_branch_seg_summary(flagged: pd.DataFrame) -> pd.DataFrame:
    if flagged.empty or 'Branch Name' not in flagged.columns or 'Segments' not in flagged.columns:
        return pd.DataFrame()
    branch_seg = flagged.groupby(['Branch Name', 'Segments']).agg(Count=('Net Amt', 'size')).reset_index()
    return branch_seg.sort_values('Count', ascending=False)

def get_fatf_country_seg_summary(flagged: pd.DataFrame) -> pd.DataFrame:
    if flagged.empty or 'Visiting Country' not in flagged.columns or 'Segments' not in flagged.columns:
        return pd.DataFrame()
    country_seg = flagged.groupby(['Visiting Country', 'Segments']).agg(Count=('Net Amt', 'size')).reset_index()
    return country_seg.sort_values('Count', ascending=False)

def get_fatf_purpose_counts(flagged: pd.DataFrame) -> pd.DataFrame:
    if flagged.empty or 'Purpose' not in flagged.columns:
        return pd.DataFrame()
    purpose_data = flagged[flagged['Purpose'].notna() & (flagged['Purpose'] != '')]
    return purpose_data.groupby('Purpose').agg(Total_Amount=('Net Amt', 'sum')).reset_index()

def get_fatf_trend(flagged: pd.DataFrame) -> pd.DataFrame:
    if flagged.empty or 'Date' not in flagged.columns:
        return pd.DataFrame()
    return flagged.groupby('Date').agg(Total_Amount=('Net Amt', 'sum')).reset_index()
