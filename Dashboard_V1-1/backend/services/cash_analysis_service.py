import os
import io
import pandas as pd
import numpy as np

def load_cash_analysis_data(file_bytes=None, default_path=None, sheet_name='RptTimeBasedCashAnylises') -> pd.DataFrame:
    df = None
    if file_bytes is not None:
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
    elif default_path is not None and os.path.exists(default_path):
        df = pd.read_excel(default_path, sheet_name=sheet_name)
    else:
        return pd.DataFrame()

    required_cols = ['Branch', 'Txn Type', 'Rec/Pay Amt.']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        # Return empty or partially cleaned, check caller
        return pd.DataFrame()

    # Clean Data
    df['Rec/Pay Amt.'] = pd.to_numeric(df['Rec/Pay Amt.'], errors='coerce').fillna(0)
    
    if 'Txn Date' in df.columns:
        df['Txn Date'] = pd.to_datetime(df['Txn Date'], errors='coerce')

    # Basic filtering strictly to PB and PS as requested
    df = df[df['Txn Type'].isin(['PB', 'PS'])]
    return df

def get_cash_analysis_kpis(subset_df: pd.DataFrame) -> dict:
    total_txns = len(subset_df)
    total_amount = subset_df['Rec/Pay Amt.'].sum() if 'Rec/Pay Amt.' in subset_df.columns else 0
    branch_count = subset_df['Branch'].nunique() if 'Branch' in subset_df.columns else 0
    highest_branch = subset_df.groupby('Branch')['Rec/Pay Amt.'].sum().idxmax() if ('Branch' in subset_df.columns and not subset_df.empty) else "N/A"

    return {
        'total_txns': total_txns,
        'total_amount': total_amount,
        'branch_count': branch_count,
        'highest_branch': highest_branch
    }

def build_cash_summary_table(subset_df: pd.DataFrame, total_txns: int, total_amount: float) -> pd.DataFrame:
    if subset_df.empty or 'Branch' not in subset_df.columns or 'Rec/Pay Amt.' not in subset_df.columns:
        return pd.DataFrame()

    summary = subset_df.groupby('Branch').agg(
        Count=('Rec/Pay Amt.', 'size'),
        RecPayAmt=('Rec/Pay Amt.', 'sum')
    ).reset_index()
    summary.rename(columns={'RecPayAmt': 'Rec/Pay Amt.'}, inplace=True)
    
    summary['Count %'] = (summary['Count'] / total_txns * 100).round(2) if total_txns > 0 else 0
    summary['Rec/Pay Amt. %'] = (summary['Rec/Pay Amt.'] / total_amount * 100).round(2) if total_amount > 0 else 0
    summary = summary.sort_values('Rec/Pay Amt.', ascending=False)
    
    total_row = pd.DataFrame([{
        'Branch': 'TOTAL',
        'Count': total_txns,
        'Rec/Pay Amt.': total_amount,
        'Count %': 100.0,
        'Rec/Pay Amt. %': 100.0
    }])
    
    return pd.concat([summary, total_row], ignore_index=True)

def get_ps_alerts_data(ps_df: pd.DataFrame) -> dict:
    if ps_df.empty or 'Rec/Pay Amt.' not in ps_df.columns:
        return {
            'alert_txns': 0,
            'alert_amount': 0,
            'alert_branches': 0,
            'highest_alert_desc': 'N/A',
            'alerts_df': pd.DataFrame(),
            'alert_summary': pd.DataFrame(),
            'date_trend': pd.DataFrame()
        }

    ps_alerts = ps_df[ps_df['Rec/Pay Amt.'] > 49000].copy()
    alert_txns = len(ps_alerts)
    alert_amount = ps_alerts['Rec/Pay Amt.'].sum()
    alert_branches = ps_alerts['Branch'].nunique() if 'Branch' in ps_alerts.columns else 0

    if alert_txns > 0 and 'Branch' in ps_alerts.columns:
        highest_alert_row = ps_alerts.loc[ps_alerts['Rec/Pay Amt.'].idxmax()]
        highest_alert_desc = f"{highest_alert_row['Branch']} (₹{highest_alert_row['Rec/Pay Amt.']:,.2f})"
    else:
        highest_alert_desc = "N/A"

    alert_summary = pd.DataFrame()
    if alert_txns > 0 and 'Branch' in ps_alerts.columns:
        alert_summary = ps_alerts.groupby('Branch')['Rec/Pay Amt.'].agg(['size', 'sum']).reset_index()
        alert_summary.rename(columns={'size': 'Count', 'sum': 'Alert Amount'}, inplace=True)

    date_trend = pd.DataFrame()
    if alert_txns > 0 and 'Txn Date' in ps_alerts.columns:
        date_trend = ps_alerts.groupby(ps_alerts['Txn Date'].dt.date)['Rec/Pay Amt.'].sum().reset_index()
        date_trend.rename(columns={'Txn Date': 'Date', 'Rec/Pay Amt.': 'Alert Amount'}, inplace=True)

    return {
        'alert_txns': alert_txns,
        'alert_amount': alert_amount,
        'alert_branches': alert_branches,
        'highest_alert_desc': highest_alert_desc,
        'alerts_df': ps_alerts,
        'alert_summary': alert_summary,
        'date_trend': date_trend
    }
