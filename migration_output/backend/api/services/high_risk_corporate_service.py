import pandas as pd
import numpy as np

def clean_for_json(df: pd.DataFrame):
    return df.replace([np.inf, -np.inf, np.nan], None).to_dict(orient='records')

def enrich_corporate_data(df: pd.DataFrame, pm_df: pd.DataFrame) -> pd.DataFrame:
    if 'CUSTOMERCODE' not in pm_df.columns or 'RISKCATEGORY' not in pm_df.columns:
        raise ValueError("Uploaded file must contain 'CUSTOMERCODE' and 'RISKCATEGORY' columns.")
        
    if 'CUSTOMERCODE' not in df.columns:
        raise ValueError("Raw transaction dataset must contain a 'CUSTOMERCODE' column to perform the match.")

    # Prepare Mapping Dictionary
    pm_mapping = pm_df[['CUSTOMERCODE', 'RISKCATEGORY']].copy()
    pm_mapping['CUSTOMERCODE'] = pm_mapping['CUSTOMERCODE'].astype(str).str.strip().str.upper()
    pm_mapping = pm_mapping.drop_duplicates(subset=['CUSTOMERCODE'])
    pm_mapping.rename(columns={'CUSTOMERCODE': 'CUSTOMERCODE_PM'}, inplace=True)

    # Prepare Base Transaction Data
    work_df = df.copy()
    work_df['Corporate_Code'] = work_df['CUSTOMERCODE'].astype(str).str.strip().str.upper()
    work_df['Corporate_Code'] = work_df['Corporate_Code'].replace(['NAN', 'NONE', 'NULL', ''], 'UNKNOWN_CODE')

    # Merge (VLOOKUP Style)
    enriched_df = pd.merge(work_df, pm_mapping, left_on='Corporate_Code', right_on='CUSTOMERCODE_PM', how='left')
    if 'CUSTOMERCODE_PM' in enriched_df.columns:
        enriched_df.drop(columns=['CUSTOMERCODE_PM'], inplace=True)

    def clean_risk_category(val):
        if pd.isna(val) or str(val).strip() == '':
            return 'Unknown Risk'
        val_str = str(val).strip().upper()
        if 'HIGH' in val_str: return 'High Risk'
        if 'MEDIUM' in val_str: return 'Medium Risk'
        if 'LOW' in val_str: return 'Low Risk'
        return 'Unknown Risk'

    def clean_risk_category_short(val):
        if pd.isna(val) or str(val).strip() == '':
            return 'Unknown'
        val_str = str(val).strip().upper()
        if 'HIGH' in val_str: return 'High'
        if 'MEDIUM' in val_str: return 'Medium'
        if 'LOW' in val_str: return 'Low'
        return 'Unknown'

    enriched_df['Risk Classification'] = enriched_df['RISKCATEGORY'].apply(clean_risk_category)
    enriched_df['Risk Category'] = enriched_df['RISKCATEGORY'].apply(clean_risk_category_short)
    return enriched_df

def get_corporate_risk_kpis(enriched_df: pd.DataFrame) -> dict:
    base_total_corps = enriched_df['Corporate_Code'].nunique() if 'Corporate_Code' in enriched_df.columns else 0

    hr_df = enriched_df[enriched_df['Risk Classification'] == 'High Risk'] if 'Risk Classification' in enriched_df.columns else pd.DataFrame()
    h_cnt = hr_df['Corporate_Code'].nunique() if not hr_df.empty else 0
    h_amt = hr_df['INRAMOUNT'].sum(min_count=1) if not hr_df.empty and 'INRAMOUNT' in hr_df.columns else 0
    h_pct = (h_cnt / base_total_corps * 100) if base_total_corps > 0 else 0

    def get_top_risk_entity(col):
        if hr_df.empty or col not in hr_df.columns:
            return 'N/A', 0, 0.0, 0.0
        agg = hr_df.groupby(col).agg(Count=('INRAMOUNT', 'size'), Exp=('INRAMOUNT', 'sum')).reset_index()
        if agg.empty:
            return 'N/A', 0, 0.0, 0.0
        agg = agg.sort_values('Exp', ascending=False)
        top = agg.iloc[0]
        pct = (top['Exp'] / h_amt * 100) if h_amt > 0 else 0
        return str(top[col]), int(top['Count']), float(top['Exp']), float(pct)

    branch_col = 'LOCATION' if 'LOCATION' in enriched_df.columns else ('Branch' if 'Branch' in enriched_df.columns else None)

    corp_n, corp_c, corp_e, corp_p = get_top_risk_entity('Corporate_Code')
    prod_n, prod_c, prod_e, prod_p = get_top_risk_entity('PRODUCT')
    seg_n, seg_c, seg_e, seg_p = get_top_risk_entity('Segment')
    br_n, br_c, br_e, br_p = get_top_risk_entity(branch_col)

    return {
        'base_total_corps': int(base_total_corps),
        'high_risk_count': int(h_cnt),
        'high_risk_amount': float(h_amt) if not pd.isna(h_amt) else 0.0,
        'high_risk_pct': float(h_pct) if not pd.isna(h_pct) else 0.0,
        'top_corp': {'name': corp_n, 'count': corp_c, 'exposure': corp_e, 'pct': corp_p},
        'top_product': {'name': prod_n, 'count': prod_c, 'exposure': prod_e, 'pct': prod_p},
        'top_segment': {'name': seg_n, 'count': seg_c, 'exposure': seg_e, 'pct': seg_p},
        'top_branch': {'name': br_n, 'count': br_c, 'exposure': br_e, 'pct': br_p},
    }

def get_risk_distribution(enriched_df: pd.DataFrame) -> list:
    if 'Risk Classification' not in enriched_df.columns:
        return []
    res = enriched_df.groupby('Risk Classification').agg(
        Transaction_Count=('INRAMOUNT', 'size'),
        Net_Amt=('INRAMOUNT', 'sum')
    ).reset_index()
    return clean_for_json(res)

def get_top_corporates(enriched_df: pd.DataFrame) -> list:
    if 'Corporate_Code' not in enriched_df.columns:
        return []
    res = enriched_df.groupby('Corporate_Code').agg(
        Transaction_Count=('INRAMOUNT', 'size'),
        Net_Amt=('INRAMOUNT', 'sum')
    ).reset_index().sort_values('Net_Amt', ascending=False).head(15)
    return clean_for_json(res)

def get_branch_exposure(enriched_df: pd.DataFrame) -> list:
    branch_col = 'LOCATION' if 'LOCATION' in enriched_df.columns else ('Branch' if 'Branch' in enriched_df.columns else None)
    if not branch_col or 'Risk Classification' not in enriched_df.columns:
        return []
    res = enriched_df.groupby([branch_col, 'Risk Classification']).agg(
        Transaction_Count=('INRAMOUNT', 'size'),
        Net_Amt=('INRAMOUNT', 'sum')
    ).reset_index().sort_values('Net_Amt', ascending=False)
    res.rename(columns={branch_col: 'LOCATION'}, inplace=True)
    return clean_for_json(res)

def get_country_exposure(enriched_df: pd.DataFrame) -> list:
    if 'CountryToTravel' not in enriched_df.columns or 'Risk Classification' not in enriched_df.columns:
        return []
    res = enriched_df.groupby(['CountryToTravel', 'Risk Classification']).agg(
        Transaction_Count=('INRAMOUNT', 'size'),
        Net_Amt=('INRAMOUNT', 'sum')
    ).reset_index().sort_values('Net_Amt', ascending=False)
    return clean_for_json(res)

def get_product_exposure_details(enriched_df: pd.DataFrame) -> dict:
    if 'PRODUCT' not in enriched_df.columns or 'Risk Classification' not in enriched_df.columns:
        return {'product_data': [], 'display_prod_table': []}
        
    product_data = enriched_df.groupby(['PRODUCT', 'Risk Classification']).agg(
        Transaction_Count=('INRAMOUNT', 'size'),
        Net_Amt=('INRAMOUNT', 'sum')
    ).reset_index().sort_values('Net_Amt', ascending=False)

    prod_table_data = enriched_df.groupby('PRODUCT').agg(
        Count=('INRAMOUNT', 'size'),
        Net_Amount=('INRAMOUNT', 'sum')
    ).reset_index()
    
    total_count = prod_table_data['Count'].sum()
    total_amt = prod_table_data['Net_Amount'].sum()
    
    prod_table_data['Count %'] = (prod_table_data['Count'] / total_count * 100) if total_count > 0 else 0
    prod_table_data['Net Amount %'] = (prod_table_data['Net_Amount'] / total_amt * 100) if total_amt > 0 else 0
    prod_table_data = prod_table_data.sort_values('Net_Amount', ascending=False)
    
    total_row = pd.DataFrame({
        'PRODUCT': ['**TOTAL**'],
        'Count': [total_count],
        'Count %': [100.0],
        'Net_Amount': [total_amt],
        'Net Amount %': [100.0]
    })
    display_prod_table = pd.concat([prod_table_data, total_row], ignore_index=True)
    display_prod_table.rename(columns={'Net_Amount': 'INRAMOUNT'}, inplace=True)

    return {
        'product_data': clean_for_json(product_data),
        'display_prod_table': clean_for_json(display_prod_table),
    }

def get_trend_exposure(enriched_df: pd.DataFrame, trend_agg: str) -> list:
    if 'TXNDATE' not in enriched_df.columns or 'Risk Classification' not in enriched_df.columns:
        return []

    df_copy = enriched_df.copy()
    if 'TXNDATE' in df_copy.columns:
        df_copy['TXNDATE'] = pd.to_datetime(df_copy['TXNDATE'], errors='coerce')
        # Exclude Sundays
        df_copy = df_copy[df_copy['TXNDATE'].dt.dayofweek != 6]

    if trend_agg == "DAILY":
        trend_data = df_copy.groupby([df_copy['TXNDATE'].dt.date, 'Risk Classification']).agg(
            Transaction_Count=('INRAMOUNT', 'size'), 
            Net_Amt=('INRAMOUNT', 'sum')
        ).reset_index()
        trend_data.rename(columns={'TXNDATE': 'Time'}, inplace=True)
    else:
        trend_data = df_copy.groupby([pd.Grouper(key='TXNDATE', freq='W-MON'), 'Risk Classification']).agg(
            Transaction_Count=('INRAMOUNT', 'size'), 
            Net_Amt=('INRAMOUNT', 'sum')
        ).reset_index()
        trend_data['TXNDATE'] = trend_data['TXNDATE'].dt.date
        trend_data.rename(columns={'TXNDATE': 'Time'}, inplace=True)

    if 'Time' in trend_data.columns:
        trend_data['Time'] = trend_data['Time'].astype(str)
        
    return clean_for_json(trend_data)

def get_transactions_table(enriched_df: pd.DataFrame) -> list:
    if enriched_df.empty:
        return []
    display_df = enriched_df.drop(columns=['Corporate_Code', 'CUSTOMERCODE', 'RISKCATEGORY'], errors='ignore')
    if 'TXNDATE' in display_df.columns:
        display_df['TXNDATE'] = display_df['TXNDATE'].astype(str)
    return clean_for_json(display_df)
