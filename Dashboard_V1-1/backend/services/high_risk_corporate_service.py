import pandas as pd
import numpy as np

def enrich_corporate_data(df: pd.DataFrame, pm_df: pd.DataFrame) -> pd.DataFrame:
    if 'CUSTOMERCODE' not in pm_df.columns or 'RISKCATEGORY' not in pm_df.columns:
        raise ValueError("Uploaded file must contain 'CUSTOMERCODE' and 'RISKCATEGORY' columns.")
        
    if 'Party Code' not in df.columns:
        raise ValueError("Raw transaction dataset must contain a 'Party Code' column to perform the match.")

    # Prepare Mapping Dictionary
    pm_mapping = pm_df[['CUSTOMERCODE', 'RISKCATEGORY']].copy()
    pm_mapping['CUSTOMERCODE'] = pm_mapping['CUSTOMERCODE'].astype(str).str.strip().str.upper()
    pm_mapping = pm_mapping.drop_duplicates(subset=['CUSTOMERCODE'])

    # Prepare Base Transaction Data
    work_df = df.copy()
    work_df['Corporate_Code'] = work_df['Party Code'].astype(str).str.strip().str.upper()
    work_df['Corporate_Code'] = work_df['Corporate_Code'].replace(['NAN', 'NONE', 'NULL', ''], 'UNKNOWN_CODE')

    # Merge (VLOOKUP Style)
    enriched_df = pd.merge(work_df, pm_mapping, left_on='Corporate_Code', right_on='CUSTOMERCODE', how='left')

    def clean_risk_category(val):
        if pd.isna(val) or str(val).strip() == '':
            return 'Unknown Risk'
        val_str = str(val).strip().upper()
        if 'HIGH' in val_str: return 'High Risk'
        if 'MEDIUM' in val_str: return 'Medium Risk'
        if 'LOW' in val_str: return 'Low Risk'
        return 'Unknown Risk'

    enriched_df['Risk Classification'] = enriched_df['RISKCATEGORY'].apply(clean_risk_category)
    return enriched_df

def get_corporate_risk_kpis(enriched_df: pd.DataFrame) -> dict:
    base_total_corps = enriched_df['Corporate_Code'].nunique() if 'Corporate_Code' in enriched_df.columns else 0

    hr_df = enriched_df[enriched_df['Risk Classification'] == 'High Risk'] if 'Risk Classification' in enriched_df.columns else pd.DataFrame()
    h_cnt = hr_df['Corporate_Code'].nunique() if not hr_df.empty else 0
    h_amt = hr_df['Net Amt'].sum(min_count=1) if not hr_df.empty and 'Net Amt' in hr_df.columns else 0
    h_pct = (h_cnt / base_total_corps * 100) if base_total_corps > 0 else 0

    def get_top_risk_entity(col):
        if hr_df.empty or col not in hr_df.columns:
            return 'N/A', 0, 0, 0
        agg = hr_df.groupby(col).agg(Count=('Net Amt', 'size'), Exp=('Net Amt', 'sum')).reset_index()
        if agg.empty:
            return 'N/A', 0, 0, 0
        agg = agg.sort_values('Exp', ascending=False)
        top = agg.iloc[0]
        pct = (top['Exp'] / h_amt * 100) if h_amt > 0 else 0
        return top[col], top['Count'], top['Exp'], pct

    branch_col = 'Branch Name' if 'Branch Name' in enriched_df.columns else ('Branch' if 'Branch' in enriched_df.columns else None)

    corp_n, corp_c, corp_e, corp_p = get_top_risk_entity('Corporate_Code')
    prod_n, prod_c, prod_e, prod_p = get_top_risk_entity('Product')
    seg_n, seg_c, seg_e, seg_p = get_top_risk_entity('Segments')
    br_n, br_c, br_e, br_p = get_top_risk_entity(branch_col)

    return {
        'base_total_corps': base_total_corps,
        'high_risk_count': h_cnt,
        'high_risk_amount': h_amt,
        'high_risk_pct': h_pct,
        'top_corp': {'name': corp_n, 'count': corp_c, 'exposure': corp_e, 'pct': corp_p},
        'top_product': {'name': prod_n, 'count': prod_c, 'exposure': prod_e, 'pct': prod_p},
        'top_segment': {'name': seg_n, 'count': seg_c, 'exposure': seg_e, 'pct': seg_p},
        'top_branch': {'name': br_n, 'count': br_c, 'exposure': br_e, 'pct': br_p},
    }

def get_risk_distribution(enriched_df: pd.DataFrame, target_y: str) -> pd.DataFrame:
    return enriched_df.groupby('Risk Classification').agg(
        Transaction_Count=('Net Amt', 'size'),
        Net_Amt=('Net Amt', 'sum')
    ).reset_index()

def get_top_corporates(enriched_df: pd.DataFrame, target_y: str) -> pd.DataFrame:
    return enriched_df.groupby('Corporate_Code').agg(
        Transaction_Count=('Net Amt', 'size'),
        Net_Amt=('Net Amt', 'sum')
    ).reset_index().sort_values(target_y, ascending=False).head(15)

def get_branch_exposure(enriched_df: pd.DataFrame, target_y: str) -> pd.DataFrame:
    branch_col = 'Branch Name' if 'Branch Name' in enriched_df.columns else ('Branch' if 'Branch' in enriched_df.columns else None)
    if not branch_col:
        return pd.DataFrame()
    return enriched_df.groupby([branch_col, 'Risk Classification']).agg(
        Transaction_Count=('Net Amt', 'size'),
        Net_Amt=('Net Amt', 'sum')
    ).reset_index().sort_values(target_y, ascending=False)

def get_country_exposure(enriched_df: pd.DataFrame, target_y: str) -> pd.DataFrame:
    if 'Visiting Country' not in enriched_df.columns:
        return pd.DataFrame()
    return enriched_df.groupby(['Visiting Country', 'Risk Classification']).agg(
        Transaction_Count=('Net Amt', 'size'),
        Net_Amt=('Net Amt', 'sum')
    ).reset_index().sort_values(target_y, ascending=False)

def get_product_exposure_details(enriched_df: pd.DataFrame, target_y: str) -> dict:
    if 'Product' not in enriched_df.columns:
        return {}
        
    product_data = enriched_df.groupby(['Product', 'Risk Classification']).agg(
        Transaction_Count=('Net Amt', 'size'),
        Net_Amt=('Net Amt', 'sum')
    ).reset_index().sort_values(target_y, ascending=False)

    prod_table_data = enriched_df.groupby('Product').agg(
        Count=('Net Amt', 'size'),
        Net_Amount=('Net Amt', 'sum')
    ).reset_index()
    
    total_count = prod_table_data['Count'].sum()
    total_amt = prod_table_data['Net_Amount'].sum()
    
    prod_table_data['Count %'] = (prod_table_data['Count'] / total_count * 100) if total_count > 0 else 0
    prod_table_data['Net Amount %'] = (prod_table_data['Net_Amount'] / total_amt * 100) if total_amt > 0 else 0
    prod_table_data = prod_table_data.sort_values('Net_Amount', ascending=False)
    
    total_row = pd.DataFrame({
        'Product': ['**TOTAL**'],
        'Count': [total_count],
        'Count %': [100.0],
        'Net_Amount': [total_amt],
        'Net Amount %': [100.0]
    })
    display_prod_table = pd.concat([prod_table_data, total_row], ignore_index=True)
    display_prod_table.rename(columns={'Net_Amount': 'Net Amount'}, inplace=True)

    return {
        'product_data': product_data,
        'display_prod_table': display_prod_table,
    }

def get_trend_exposure(enriched_df: pd.DataFrame, trend_agg: str) -> pd.DataFrame:
    if 'Date' not in enriched_df.columns:
        return pd.DataFrame()

    if trend_agg == "DAILY":
        trend_data = enriched_df.groupby([enriched_df['Date'].dt.date, 'Risk Classification']).agg(
            Transaction_Count=('Net Amt', 'size'), 
            Net_Amt=('Net Amt', 'sum')
        ).reset_index()
        trend_data.rename(columns={'Date': 'Time'}, inplace=True)
    else:
        trend_data = enriched_df.groupby([pd.Grouper(key='Date', freq='W-MON'), 'Risk Classification']).agg(
            Transaction_Count=('Net Amt', 'size'), 
            Net_Amt=('Net Amt', 'sum')
        ).reset_index()
        trend_data['Date'] = trend_data['Date'].dt.date
        trend_data.rename(columns={'Date': 'Time'}, inplace=True)

    return trend_data
