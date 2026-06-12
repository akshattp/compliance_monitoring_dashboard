import pandas as pd
import numpy as np

# MLTF Calculations
def get_mltf_data(filtered_df) -> tuple[pd.DataFrame, float, pd.DataFrame]:
    ml_df = filtered_df[filtered_df['Risk  Category'].astype(str).str.contains('HIGH|MEDIUM', case=False, na=False)] if 'Risk  Category' in filtered_df.columns else filtered_df.iloc[0:0]
    if 'OFAC _ FATF' in filtered_df.columns:
        fatf_df = filtered_df[filtered_df['OFAC _ FATF'].astype(str).str.contains(r'FATF|OFAC|FLAG|YES', case=False, na=False)]
        ml_df = pd.concat([ml_df, fatf_df], ignore_index=True)
    ml_df = ml_df.drop_duplicates() if not ml_df.empty else ml_df

    total_amount = ml_df['Net Amt'].sum(min_count=1) if not ml_df.empty and 'Net Amt' in ml_df.columns else 0.0
    
    corporate_summary = pd.DataFrame()
    if 'Corporate' in ml_df.columns and not ml_df.empty:
        corporate_summary = ml_df.groupby('Corporate').agg(Total_Amount=('Net Amt', 'sum')).reset_index().sort_values('Total_Amount', ascending=False).head(20)
        
    return ml_df, total_amount, corporate_summary

# Dormant Account Calculations
def get_dormant_account_data(filtered_df) -> tuple[pd.DataFrame, float, pd.DataFrame]:
    if 'Balance' not in filtered_df.columns:
        return pd.DataFrame(), 0.0, pd.DataFrame()
        
    dormant = filtered_df[filtered_df['Balance'].fillna(0) == 0]
    total_amount = dormant['Net Amt'].sum(min_count=1) if not dormant.empty and 'Net Amt' in dormant.columns else 0.0
    
    branch_summary = pd.DataFrame()
    if 'Branch Name' in dormant.columns and not dormant.empty:
        branch_summary = dormant.groupby('Branch Name').agg(Total_Amount=('Net Amt', 'sum'), Count=('Net Amt', 'size')).reset_index().sort_values('Total_Amount', ascending=False)
        
    return dormant, total_amount, branch_summary

# ReKYC Calculations
def get_rekyc_summaries(filtered_df) -> tuple[pd.DataFrame, pd.DataFrame]:
    referred_summary = pd.DataFrame()
    if 'Referred By' in filtered_df.columns:
        referred_summary = filtered_df.groupby('Referred By').agg(Total_Amount=('Net Amt', 'sum'), Count=('Net Amt', 'size')).reset_index().sort_values('Total_Amount', ascending=False).head(20)

    segment_summary = pd.DataFrame()
    if 'Segments' in filtered_df.columns:
        segment_summary = filtered_df.groupby('Segments').agg(Total_Amount=('Net Amt', 'sum'), Count=('Net Amt', 'size')).reset_index().sort_values('Total_Amount', ascending=False).head(20)
        
    return referred_summary, segment_summary

# Stock Verification Calculations
def get_stock_verification_data(filtered_df) -> tuple[list, pd.DataFrame]:
    stock_columns = [col for col in filtered_df.columns if 'Stock' in col or 'Inventory' in col]
    if not stock_columns:
        return [], pd.DataFrame()
        
    stock_summary = filtered_df.groupby(stock_columns).agg(Total_Amount=('Net Amt', 'sum')).reset_index().sort_values('Total_Amount', ascending=False)
    return stock_columns, stock_summary

# VRM Calculations
def get_vrm_data(filtered_df) -> tuple[pd.DataFrame, float]:
    if 'Visiting Country' not in filtered_df.columns:
        return pd.DataFrame(), 0.0
        
    country_summary = filtered_df.groupby('Visiting Country').agg(Total_Amount=('Net Amt', 'sum'), Count=('Net Amt', 'size')).reset_index().sort_values('Total_Amount', ascending=False)
    total_amount = country_summary['Total_Amount'].sum(min_count=1) if not country_summary.empty else 0.0
    return country_summary, total_amount

# VRM Summary Calculations
def get_vrm_summary_data(filtered_df) -> tuple[pd.DataFrame, pd.DataFrame]:
    agent_summary = pd.DataFrame()
    if 'Agent Name' in filtered_df.columns:
        agent_summary = filtered_df.groupby('Agent Name').agg(Total_Amount=('Net Amt', 'sum'), Count=('Net Amt', 'size')).reset_index().sort_values('Total_Amount', ascending=False).head(20)

    country_summary = pd.DataFrame()
    if 'Visiting Country' in filtered_df.columns:
        country_summary = filtered_df.groupby('Visiting Country').agg(Total_Amount=('Net Amt', 'sum'), Count=('Net Amt', 'size')).reset_index().sort_values('Total_Amount', ascending=False).head(20)
        
    return agent_summary, country_summary

# Card Queries Calculations
def get_card_queries_data(filtered_df) -> tuple[pd.DataFrame, pd.DataFrame]:
    card_data = filtered_df[filtered_df['Product'].astype(str).str.contains('CARD|RELOAD|KIT', case=False, na=False)] if 'Product' in filtered_df.columns else filtered_df.iloc[0:0]
    if card_data.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    summary = card_data.groupby('Product').agg(Total_Amount=('Net Amt', 'sum'), Count=('Net Amt', 'size')).reset_index().sort_values('Total_Amount', ascending=False)
    return card_data, summary

# Migration Validation Calculations
def get_migration_validation_metrics(df: pd.DataFrame) -> dict:
    total_net_amount = df['Net Amt'].sum() if 'Net Amt' in df.columns else 0.0
    distinct_products = df['Product'].nunique() if 'Product' in df.columns else 0
    distinct_segments = df['Segments'].nunique() if 'Segments' in df.columns else 0
    distinct_txn_types = df['Txn Type'].nunique() if 'Txn Type' in df.columns else 0

    risk_counts = {}
    if 'Risk  Category' in df.columns:
        counts = df['Risk  Category'].value_counts()
        risk_counts = {
            'High': counts.get('High', 0),
            'Medium': counts.get('Medium', 0),
            'Low': counts.get('Low', 0),
            'Unknown': counts.get('Unknown', 0)
        }

    compliance_counts = {}
    ofac_fatf_counts = df['OFAC _ FATF'].value_counts() if 'OFAC _ FATF' in df.columns else pd.Series()
    compliance_counts = {
        'high_value': df['High Value Transaction'].sum() if 'High Value Transaction' in df.columns else 0,
        'fatf': ofac_fatf_counts.get('FATF', 0),
        'ofac': ofac_fatf_counts.get('OFAC', 0),
        'cis': ofac_fatf_counts.get('CIS COUNTRIES', 0)
    }

    distinct_values = {
        'segments': df['Segments'].dropna().unique() if 'Segments' in df.columns else np.array([]),
        'txn_types': df['Txn Type'].dropna().unique() if 'Txn Type' in df.columns else np.array([]),
        'countries': df['Visiting Country'].dropna().unique() if 'Visiting Country' in df.columns else np.array([])
    }

    return {
        'total_net_amount': total_net_amount,
        'distinct_products': distinct_products,
        'distinct_segments': distinct_segments,
        'distinct_txn_types': distinct_txn_types,
        'risk_counts': risk_counts,
        'compliance_counts': compliance_counts,
        'distinct_values': distinct_values
    }
