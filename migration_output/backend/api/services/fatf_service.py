import pandas as pd
import numpy as np
from api.services.transaction_monitoring_service import detect_fatf_ofac

def get_fatf_flagged_transactions(df: pd.DataFrame, ofac_df: pd.DataFrame = None) -> pd.DataFrame:
    if ofac_df is not None:
        if 'COUNTRY' not in ofac_df.columns or 'Segment' not in ofac_df.columns:
            raise ValueError("OFAC file must contain 'COUNTRY' and 'Segment' columns.")
        
        ofac_mapping = ofac_df[['COUNTRY', 'Segment']].copy()
        ofac_mapping.rename(columns={'Segment': 'OFAC_FATF_Segment'}, inplace=True)
        ofac_mapping['COUNTRY'] = ofac_mapping['COUNTRY'].astype(str).str.strip().str.upper()
        ofac_mapping.drop_duplicates(subset=['COUNTRY'], inplace=True)

        work_df = df.copy()
        if 'CountryToTravel' in work_df.columns:
            work_df['Visiting Country_upper'] = work_df['CountryToTravel'].astype(str).str.strip().str.upper()
            enriched = pd.merge(work_df, ofac_mapping, left_on='Visiting Country_upper', right_on='COUNTRY', how='left')
            enriched['FATF / OFAC Flag'] = enriched['OFAC_FATF_Segment'].notna() & (enriched['OFAC_FATF_Segment'] != 'NOT FLAGGED')
            # For compatibility with filters, also add 'OFAC_FATF'
            enriched['OFAC_FATF'] = enriched['OFAC_FATF_Segment'].fillna('NOT FLAGGED')
            return enriched[enriched['FATF / OFAC Flag']].copy()
            
    fatf_df, fatf_sum = detect_fatf_ofac(df)
    if isinstance(fatf_df, list):
        return pd.DataFrame(fatf_df)
    return fatf_df

def get_fatf_kpis(flagged: pd.DataFrame, filtered_df: pd.DataFrame) -> dict:
    total_count = len(filtered_df)
    total_amount = filtered_df['INRAMOUNT'].sum(min_count=1) if (not filtered_df.empty and 'INRAMOUNT' in filtered_df.columns) else 0
    contrib_pct = (len(flagged) / total_count * 100) if total_count > 0 else 0
    flagged_amt = flagged['INRAMOUNT'].sum(min_count=1) if (not flagged.empty and 'INRAMOUNT' in flagged.columns) else 0
    contrib_amt_pct = (flagged_amt / total_amount * 100) if total_amount > 0 else 0
    
    return {
        'flagged_count': len(flagged),
        'flagged_amount': flagged_amt,
        'contrib_pct': contrib_pct,
        'contrib_amt_pct': contrib_amt_pct,
        'affected_branches': flagged['LOCATION'].nunique() if (not flagged.empty and 'LOCATION' in flagged.columns) else 0,
        'affected_countries': flagged['CountryToTravel'].nunique() if (not flagged.empty and 'CountryToTravel' in flagged.columns) else 0
    }

def get_fatf_branch_seg_summary(flagged: pd.DataFrame) -> pd.DataFrame:
    if flagged.empty or 'LOCATION' not in flagged.columns or 'Segment' not in flagged.columns:
        return pd.DataFrame()
    branch_seg = flagged.groupby(['LOCATION', 'Segment']).agg(Count=('INRAMOUNT', 'size'), Net_Amount=('INRAMOUNT', 'sum')).reset_index()
    return branch_seg.sort_values('Count', ascending=False)

def get_fatf_country_seg_summary(flagged: pd.DataFrame) -> pd.DataFrame:
    if flagged.empty or 'CountryToTravel' not in flagged.columns or 'Segment' not in flagged.columns:
        return pd.DataFrame()
    country_seg = flagged.groupby(['CountryToTravel', 'Segment']).agg(Count=('INRAMOUNT', 'size'), Net_Amount=('INRAMOUNT', 'sum')).reset_index()
    return country_seg.sort_values('Count', ascending=False)

def get_fatf_purpose_counts(flagged: pd.DataFrame) -> pd.DataFrame:
    if flagged.empty or 'TxnPurpose' not in flagged.columns:
        return pd.DataFrame()
    purpose_data = flagged[flagged['TxnPurpose'].notna() & (flagged['TxnPurpose'] != '')]
    res = purpose_data.groupby('TxnPurpose').agg(Count=('INRAMOUNT', 'size'), Net_Amount=('INRAMOUNT', 'sum')).reset_index()
    
    total_count = res['Count'].sum()
    total_amount = res['Net_Amount'].sum()
    
    res['Count %'] = (res['Count'] / total_count * 100) if total_count > 0 else 0
    res['Net Amount %'] = (res['Net_Amount'] / total_amount * 100) if total_amount > 0 else 0
    
    res = res.sort_values('Net_Amount', ascending=False)
    return res

def get_fatf_trend(flagged: pd.DataFrame, trend_agg: str = 'DAILY') -> pd.DataFrame:
    if flagged.empty or 'TXNDATE' not in flagged.columns:
        return pd.DataFrame()
    
    df = flagged.copy()
    df['TXNDATE'] = pd.to_datetime(df['TXNDATE'])
    # Exclude Sundays
    df = df[df['TXNDATE'].dt.dayofweek != 6]
    
    if trend_agg == 'DAILY':
        trend_df = df.groupby(df['TXNDATE'].dt.date).agg(Count=('INRAMOUNT', 'size'), Net_Amount=('INRAMOUNT', 'sum')).reset_index()
        trend_df.rename(columns={'TXNDATE': 'Time'}, inplace=True)
    else:
        if 'Week' in df.columns:
            trend_df = df.groupby('Week').agg(Count=('INRAMOUNT', 'size'), Net_Amount=('INRAMOUNT', 'sum')).reset_index()
            trend_df.rename(columns={'Week': 'Time'}, inplace=True)
        else:
            trend_df = df.groupby(pd.Grouper(key='TXNDATE', freq='W-MON')).agg(Count=('INRAMOUNT', 'size'), Net_Amount=('INRAMOUNT', 'sum')).reset_index()
            trend_df['TXNDATE'] = trend_df['TXNDATE'].dt.date
            trend_df.rename(columns={'TXNDATE': 'Time'}, inplace=True)
            
    if 'Time' in trend_df.columns:
        trend_df['Time'] = trend_df['Time'].astype(str)
        
    return trend_df
