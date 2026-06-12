import pandas as pd
import numpy as np

def get_transaction_type_kpis(df: pd.DataFrame) -> dict:
    txn_types_to_show = ['PS', 'PB', 'CB', 'FB', 'FS', 'BB', 'BS', 'BT']
    kpi_data = {}
    if 'Txn Type' in df.columns:
        for txn_type in txn_types_to_show:
            type_df = df[df['Txn Type'] == txn_type]
            kpi_data[txn_type] = {
                'count': len(type_df),
                'amount': type_df['Net Amt'].sum(min_count=1)
            }
    else:
        for txn_type in txn_types_to_show:
            kpi_data[txn_type] = {'count': 0, 'amount': 0}
    return kpi_data

def get_transaction_type_breakdown(df: pd.DataFrame) -> dict:
    if 'Txn Type' not in df.columns:
        return {}

    txn_by_type = df.groupby('Txn Type').agg(
        Count=('Net Amt', 'size'), 
        Amount=('Net Amt', 'sum')
    ).reset_index()

    if txn_by_type.empty:
        return {}

    total_amount_pie = txn_by_type['Amount'].sum()
    txn_by_type['% Contribution'] = (txn_by_type['Amount'] / total_amount_pie * 100) if total_amount_pie > 0 else 0

    total_count_table = txn_by_type['Count'].sum()
    total_amount_table = txn_by_type['Amount'].sum()
    table_data = txn_by_type.copy()
    table_data['Count %'] = (table_data['Count'] / total_count_table * 100) if total_count_table > 0 else 0
    table_data['Amount %'] = (table_data['Amount'] / total_amount_table * 100) if total_amount_table > 0 else 0
    
    total_row = pd.DataFrame({
        'Txn Type': ['**TOTAL**'], 
        'Count': [total_count_table], 
        'Count %': [100.0], 
        'Amount': [total_amount_table], 
        'Amount %': [100.0]
    })
    display_table = pd.concat([table_data, total_row], ignore_index=True)

    return {
        'txn_by_type': txn_by_type,
        'display_table': display_table,
    }

def get_txn_composition_data(df: pd.DataFrame, group_col: str, selected_txns: list, y_col: str) -> dict:
    if df.empty or group_col not in df.columns or 'Txn Type' not in df.columns:
        return {}

    comp_df = df.copy()
    if selected_txns:
        comp_df = comp_df[comp_df['Txn Type'].isin(selected_txns)]

    if comp_df.empty:
        return {}

    agg_df = comp_df.groupby([group_col, 'Txn Type']).agg(
        Count=('Net Amt', 'size'), 
        Total_Amount=('Net Amt', 'sum')
    ).reset_index()
    
    total_for_pct_count = agg_df.groupby(group_col)['Count'].transform('sum')
    total_for_pct_amt = agg_df.groupby(group_col)['Total_Amount'].transform('sum')
    
    agg_df['Count %'] = (agg_df['Count'] / total_for_pct_count * 100).fillna(0)
    agg_df['Net Amount %'] = (agg_df['Total_Amount'] / total_for_pct_amt * 100).fillna(0)

    agg_df['Total_Sort'] = agg_df.groupby(group_col)[y_col].transform('sum')
    chart_df = agg_df.sort_values(['Total_Sort', group_col, 'Txn Type'], ascending=[False, True, True])

    # Table breakdown
    table_data = comp_df.groupby(group_col).agg(
        Count=('Net Amt', 'size'), 
        Total_Amount=('Net Amt', 'sum')
    ).reset_index()
    
    total_count = table_data['Count'].sum()
    total_amt = table_data['Total_Amount'].sum()
    
    table_data['Count %'] = (table_data['Count'] / total_count * 100).fillna(0)
    table_data['Net Amount %'] = (table_data['Total_Amount'] / total_amt * 100).fillna(0)
    table_data = table_data.sort_values(y_col, ascending=False)
    
    display_table = table_data.rename(columns={'Total_Amount': 'Net Amount'})

    return {
        'chart_df': chart_df,
        'display_table': display_table,
        'total_count': total_count,
        'total_amount': total_amt,
        'records_count': len(comp_df),
    }

def get_purpose_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    if 'Purpose' not in df.columns:
        return pd.DataFrame()
    return df.groupby('Purpose').agg(
        Total_Amount=('Net Amt', 'sum'), 
        Count=('Net Amt', 'size')
    ).reset_index().sort_values('Total_Amount', ascending=False)
