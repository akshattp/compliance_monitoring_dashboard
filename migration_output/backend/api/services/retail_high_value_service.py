import pandas as pd
import numpy as np

def clean_for_json(df: pd.DataFrame):
    return df.replace([np.inf, -np.inf, np.nan], None).to_dict(orient='records')

def classify_retail_risk_level(eqv_usd):
    if pd.isna(eqv_usd):
        return 'UNKNOWN'
    if eqv_usd < 10000:
        return 'LOW'
    elif eqv_usd < 25000:
        return 'MEDIUM'
    else:
        return 'HIGH'

def add_retail_risk_classification(df: pd.DataFrame) -> pd.DataFrame:
    work_df = df.copy()
    if 'Equivalent USD Amount' not in work_df.columns:
        work_df['Retail_Risk_Level'] = 'UNKNOWN'
        return work_df
    
    work_df['Retail_Risk_Level'] = work_df['Equivalent USD Amount'].apply(classify_retail_risk_level)
    return work_df

def identify_high_value_transactions(df: pd.DataFrame) -> pd.DataFrame:
    if 'Equivalent USD Amount' not in df.columns:
        return df[df['INRAMOUNT'] > 10000] if 'INRAMOUNT' in df.columns else df.iloc[0:0]
    return df[df['Equivalent USD Amount'] >= 10000]

def calculate_kpis(high_value_df: pd.DataFrame) -> dict:
    kpis = {}
    if high_value_df.empty:
        kpis['total_high_value_txn'] = 0
        kpis['total_high_value_amount'] = 0.0
        kpis['highest_usd_txn'] = 0.0
        kpis['avg_usd_txn'] = 0.0
        kpis['high_risk_count'] = 0
        kpis['medium_risk_count'] = 0
        kpis['high_exposure_branch'] = 'N/A'
        kpis['high_exposure_corporate'] = 'N/A'
        return kpis
    
    kpis['total_high_value_txn'] = len(high_value_df)
    kpis['total_high_value_amount'] = float(high_value_df['Equivalent USD Amount'].fillna(0).sum())
    kpis['highest_usd_txn'] = float(high_value_df['Equivalent USD Amount'].fillna(0).max())
    kpis['avg_usd_txn'] = float(high_value_df['Equivalent USD Amount'].fillna(0).mean())
    
    kpis['high_risk_count'] = int(len(high_value_df[high_value_df['Retail_Risk_Level'] == 'HIGH']))
    kpis['medium_risk_count'] = int(len(high_value_df[high_value_df['Retail_Risk_Level'] == 'MEDIUM']))
    
    if 'LOCATION' in high_value_df.columns:
        top_branch = high_value_df.groupby('LOCATION')['Equivalent USD Amount'].sum().idxmax()
        kpis['high_exposure_branch'] = str(top_branch)
    else:
        kpis['high_exposure_branch'] = 'N/A'
    
    if 'CUSTOMERNAME' in high_value_df.columns:
        top_corp = high_value_df.groupby('CUSTOMERNAME')['Equivalent USD Amount'].sum().idxmax()
        kpis['high_exposure_corporate'] = str(top_corp)
    else:
        kpis['high_exposure_corporate'] = 'N/A'
    
    return kpis

def branch_wise_analysis(high_value_df: pd.DataFrame) -> list:
    if 'LOCATION' not in high_value_df.columns or high_value_df.empty:
        return []
    
    res = high_value_df.groupby('LOCATION').agg(
        Transaction_Count=('Equivalent USD Amount', 'size'),
        Total_USD=('Equivalent USD Amount', 'sum'),
        Avg_USD=('Equivalent USD Amount', 'mean'),
        Max_USD=('Equivalent USD Amount', 'max'),
        High_Risk_Count=('Retail_Risk_Level', lambda x: (x == 'HIGH').sum()),
        Medium_Risk_Count=('Retail_Risk_Level', lambda x: (x == 'MEDIUM').sum()),
    ).reset_index().sort_values('Total_USD', ascending=False)

    total_count = res['Transaction_Count'].sum()
    total_usd = res['Total_USD'].sum()
    res['Count'] = res['Transaction_Count']
    res['Count %'] = (res['Transaction_Count'] / total_count * 100).fillna(0) if total_count > 0 else 0
    res['Net Amount %'] = (res['Total_USD'] / total_usd * 100).fillna(0) if total_usd > 0 else 0
    return clean_for_json(res)

def corporate_wise_analysis(high_value_df: pd.DataFrame) -> list:
    if 'CUSTOMERNAME' not in high_value_df.columns or high_value_df.empty:
        return []
    
    res = high_value_df.groupby('CUSTOMERNAME').agg(
        Transaction_Count=('Equivalent USD Amount', 'size'),
        Total_USD=('Equivalent USD Amount', 'sum'),
        Avg_USD=('Equivalent USD Amount', 'mean'),
        Max_USD=('Equivalent USD Amount', 'max'),
        Customer_Count=('PAXNAME', 'nunique') if 'PAXNAME' in high_value_df.columns else (lambda x: 0),
        Branch_Count=('LOCATION', 'nunique') if 'LOCATION' in high_value_df.columns else (lambda x: 0),
    ).reset_index().sort_values('Total_USD', ascending=False)

    total_count = res['Transaction_Count'].sum()
    total_usd = res['Total_USD'].sum()
    res['Count'] = res['Transaction_Count']
    res['Count %'] = (res['Transaction_Count'] / total_count * 100).fillna(0) if total_count > 0 else 0
    res['Net Amount %'] = (res['Total_USD'] / total_usd * 100).fillna(0) if total_usd > 0 else 0
    return clean_for_json(res)

def customer_concentration(high_value_df: pd.DataFrame) -> list:
    if 'PAXNAME' not in high_value_df.columns or high_value_df.empty:
        return []
    
    res = high_value_df.groupby('PAXNAME').agg(
        Transaction_Count=('Equivalent USD Amount', 'size'),
        Total_USD=('Equivalent USD Amount', 'sum'),
        Avg_USD=('Equivalent USD Amount', 'mean'),
        Max_USD=('Equivalent USD Amount', 'max'),
        Corporate_Count=('CUSTOMERNAME', 'nunique') if 'CUSTOMERNAME' in high_value_df.columns else (lambda x: 0),
        Branch_Count=('LOCATION', 'nunique') if 'LOCATION' in high_value_df.columns else (lambda x: 0),
    ).reset_index().sort_values('Total_USD', ascending=False).head(20)
    return clean_for_json(res)

def product_wise_analysis(high_value_df: pd.DataFrame) -> list:
    if 'PRODUCT' not in high_value_df.columns or high_value_df.empty:
        return []
    
    res = high_value_df.groupby('PRODUCT').agg(
        Transaction_Count=('Equivalent USD Amount', 'size'),
        Total_USD=('Equivalent USD Amount', 'sum'),
        Avg_USD=('Equivalent USD Amount', 'mean'),
    ).reset_index().sort_values('Total_USD', ascending=False)
    return clean_for_json(res)

def currency_wise_analysis(high_value_df: pd.DataFrame) -> list:
    if 'CURRENCY' not in high_value_df.columns or high_value_df.empty:
        return []
    
    res = high_value_df.groupby('CURRENCY').agg(
        Transaction_Count=('Equivalent USD Amount', 'size'),
        Total_USD=('Equivalent USD Amount', 'sum'),
        Avg_USD=('Equivalent USD Amount', 'mean'),
    ).reset_index().sort_values('Total_USD', ascending=False)
    return clean_for_json(res)

def country_wise_analysis(high_value_df: pd.DataFrame) -> list:
    if 'CountryToTravel' not in high_value_df.columns or high_value_df.empty:
        return []
    
    res = high_value_df.groupby('CountryToTravel').agg(
        Count=('Equivalent USD Amount', 'size'),
        Total_USD=('Equivalent USD Amount', 'sum'),
    ).reset_index().sort_values('Total_USD', ascending=False)
    return clean_for_json(res)



def generate_observations(high_value_df: pd.DataFrame, kpis: dict) -> str:
    observations = []
    
    if high_value_df.empty:
        return "No high-value transactions detected in current filters."
    
    # Branch concentration
    if 'LOCATION' in high_value_df.columns:
        branch_summary = high_value_df['LOCATION'].value_counts()
        if len(branch_summary) > 0:
            top_branch_pct = (branch_summary.iloc[0] / len(high_value_df)) * 100
            if top_branch_pct > 30:
                observations.append(
                    f"⚠️ **Branch Concentration Risk**: {branch_summary.index[0]} accounts for {top_branch_pct:.1f}% of high-value transactions."
                )
    
    # High-risk exposure
    if kpis.get('high_risk_count', 0) > 0 and kpis.get('total_high_value_txn', 0) > 0:
        high_risk_pct = (kpis['high_risk_count'] / kpis['total_high_value_txn']) * 100
        observations.append(
            f"🔴 **High-Risk Transactions**: {kpis['high_risk_count']} transactions ({high_risk_pct:.1f}%) exceed $25K USD threshold."
        )
    
    # Repeated high-value customers
    if 'PAXNAME' in high_value_df.columns:
        repeat_customers = high_value_df['PAXNAME'].value_counts()
        multi_transaction_customers = len(repeat_customers[repeat_customers > 1])
        if multi_transaction_customers > 0:
            observations.append(
                f"👥 **Repeat Customer Activity**: {multi_transaction_customers} customers have multiple high-value transactions."
            )
    
    # Country concentration
    if 'CountryToTravel' in high_value_df.columns:
        country_summary = high_value_df['CountryToTravel'].value_counts()
        if len(country_summary) > 0:
            top_country_pct = (country_summary.iloc[0] / len(high_value_df)) * 100
            if top_country_pct > 20:
                observations.append(
                    f"🌍 **Country Concentration**: {country_summary.index[0]} represents {top_country_pct:.1f}% of high-value activity."
                )
    
    # Average transaction spike
    avg_usd = high_value_df['Equivalent USD Amount'].mean() if 'Equivalent USD Amount' in high_value_df.columns else 0
    if avg_usd > 50000:
        observations.append(
            f"📈 **High Average Transaction**: Average USD value of ${avg_usd:,.0f} indicates significant exposure."
        )
    
    return "\n\n".join(observations) if observations else "No significant patterns detected."

def format_transaction_table(high_value_df: pd.DataFrame) -> list:
    if high_value_df.empty:
        return []
    
    display_cols = [
        'TXNDATE', 'PAXNAME', 'PAXIDNO', 'CUSTOMERNAME', 'LOCATION',
        'CURRENCY', 'INRAMOUNT', 'Equivalent USD Amount', 'Retail_Risk_Level', 'PRODUCT',
        'CountryToTravel', 'TxnPurpose'
    ]
    
    available_cols = [col for col in display_cols if col in high_value_df.columns]
    
    result = high_value_df[available_cols].sort_values('Equivalent USD Amount', ascending=False).copy()
    if 'TXNDATE' in result.columns:
        result['TXNDATE'] = result['TXNDATE'].astype(str)
    
    return clean_for_json(result)

