import pandas as pd
import numpy as np

def clean_for_json(df: pd.DataFrame):
    return df.replace([np.inf, -np.inf, np.nan], None).to_dict(orient='records')

def get_tour_operator_observation(filtered_df: pd.DataFrame) -> str:
    total = len(filtered_df)
    if total == 0:
        return 'No tour operator transactions found for the current selection.'
    
    top_branch = filtered_df.groupby('Branch Name')['Net Amt'].sum(min_count=1).idxmax() if 'Branch Name' in filtered_df.columns and not filtered_df.empty else None
    top_corporate = filtered_df.groupby('Corporate')['Net Amt'].sum(min_count=1).idxmax() if 'Corporate' in filtered_df.columns and not filtered_df.empty else None
    
    total_amt = filtered_df['Net Amt'].sum()
    percentage = 100.0 # Contextually, if they are already filtered, it is 100%. If we had total, we could divide.
    
    return (
        f"Tour operator transactions account for 100% of filtered volume. "
        f"Top branch: {top_branch or 'N/A'}. Top corporate exposure: {top_corporate or 'N/A'}."
    )

def get_purpose_mix_data(filtered_df: pd.DataFrame) -> list:
    if filtered_df.empty or 'Purpose' not in filtered_df.columns:
        return []
    res = filtered_df.groupby('Purpose').agg(
        Total_Amount=('Net Amt', 'sum'),
        Count=('Net Amt', 'size')
    ).reset_index().sort_values('Total_Amount', ascending=False).head(10)
    return clean_for_json(res)

def get_branch_composition_data(filtered_df: pd.DataFrame) -> dict:
    if filtered_df.empty or 'Branch Name' not in filtered_df.columns:
        return {'branch_data': [], 'display_table': []}
    
    df_chart = filtered_df.copy()
    df_chart['Purpose Type'] = df_chart['Purpose'].apply(
        lambda p: 'MICE - REMITTANCE BY TOUR OPERATORS' if 'MICE' in str(p).upper() else 'REMITTANCE BY TOUR OPERATORS'
    )
    
    branch_totals = df_chart.groupby('Branch Name')['Net Amt'].size().nlargest(15).index
    chart_data = df_chart[df_chart['Branch Name'].isin(branch_totals)]
    
    branch_data = chart_data.groupby(['Branch Name', 'Purpose Type']).agg(
        Count=('Net Amt', 'size'),
        Net_Amt=('Net Amt', 'sum')
    ).reset_index()
    
    total_for_pct = branch_data.groupby('Branch Name')['Count'].transform('sum')
    branch_data['% Contribution'] = (branch_data['Count'] / total_for_pct * 100).fillna(0)
    
    branch_data['Total_Branch_Count'] = branch_data.groupby('Branch Name')['Count'].transform('sum')
    branch_data = branch_data.sort_values(['Total_Branch_Count', 'Branch Name', 'Purpose Type'], ascending=[True, True, True])

    # Table
    table_data = chart_data.groupby('Branch Name').agg(
        Count=('Net Amt', 'size'),
        Net_Amt=('Net Amt', 'sum')
    ).reset_index()
    table_data.rename(columns={'Net_Amt': 'Net Amt'}, inplace=True)
    
    total_count = table_data['Count'].sum()
    total_amt = table_data['Net Amt'].sum()
    
    table_data['Count %'] = (table_data['Count'] / total_count * 100).fillna(0)
    table_data['Net Amt %'] = (table_data['Net Amt'] / total_amt * 100).fillna(0)
    
    total_row = pd.DataFrame({
        'Branch Name': ['**TOTAL**'],
        'Count': [total_count],
        'Count %': [100.0],
        'Net Amt': [total_amt],
        'Net Amt %': [100.0]
    })
    display_table = pd.concat([table_data, total_row], ignore_index=True)

    return {
        'branch_data': clean_for_json(branch_data),
        'display_table': clean_for_json(display_table),
    }

def get_corporate_composition_data(filtered_df: pd.DataFrame) -> dict:
    if filtered_df.empty or 'Corporate' not in filtered_df.columns:
        return {'corp_data': [], 'display_table': [], 'total_count': 0, 'total_amt': 0}
    
    df_chart = filtered_df.copy()
    df_chart['Purpose Type'] = df_chart['Purpose'].apply(
        lambda p: 'MICE - REMITTANCE BY TOUR OPERATORS' if 'MICE' in str(p).upper() else 'REMITTANCE BY TOUR OPERATORS'
    )
    
    corp_totals = df_chart.groupby('Corporate')['Net Amt'].size().nlargest(15).index
    chart_data = df_chart[df_chart['Corporate'].isin(corp_totals)]
    
    corp_data = chart_data.groupby(['Corporate', 'Purpose Type']).agg(
        Count=('Net Amt', 'size'),
        Net_Amt=('Net Amt', 'sum')
    ).reset_index()
    
    total_for_pct = corp_data.groupby('Corporate')['Count'].transform('sum')
    corp_data['% Contribution'] = (corp_data['Count'] / total_for_pct * 100).fillna(0)
    
    corp_data['Total_Corp_Count'] = corp_data.groupby('Corporate')['Count'].transform('sum')
    corp_data = corp_data.sort_values(['Total_Corp_Count', 'Corporate', 'Purpose Type'], ascending=[True, True, True])

    # Table
    table_data = chart_data.groupby('Corporate').agg(
        Count=('Net Amt', 'size'),
        Net_Amount=('Net Amt', 'sum')
    ).reset_index()
    
    total_count = float(table_data['Count'].sum())
    total_amt = float(table_data['Net_Amount'].sum())
    
    table_data['Count %'] = (table_data['Count'] / total_count * 100).fillna(0)
    table_data['Net Amount %'] = (table_data['Net_Amount'] / total_amt * 100).fillna(0)
    
    table_data = table_data.sort_values('Count', ascending=False)
    display_table = table_data.rename(columns={'Net_Amount': 'Net Amount', 'Corporate': 'Operator'})

    return {
        'corp_data': clean_for_json(corp_data),
        'display_table': clean_for_json(display_table),
        'total_count': total_count,
        'total_amt': total_amt,
    }

def get_country_combo_data(filtered_df: pd.DataFrame) -> list:
    if filtered_df.empty or 'Visiting Country' not in filtered_df.columns or 'Purpose' not in filtered_df.columns:
        return []
    
    mice_df = filtered_df[filtered_df['Purpose'].str.contains('MICE', case=False, na=False)].copy()
    remit_df = filtered_df[filtered_df['Purpose'].str.contains('REMITTANCE', case=False, na=False) & ~filtered_df['Purpose'].str.contains('MICE', case=False, na=False)].copy()
    
    mice_country = mice_df.groupby('Visiting Country').agg(
        MICE_Count=('Net Amt', 'size'),
        MICE_Amount=('Net Amt', 'sum')
    ).reset_index()
    
    remit_country = remit_df.groupby('Visiting Country').agg(
        Remit_Count=('Net Amt', 'size'),
        Remit_Amount=('Net Amt', 'sum')
    ).reset_index()
    
    country_data = mice_country.merge(remit_country, on='Visiting Country', how='outer').fillna(0)
    country_data['Total_Amount'] = country_data['MICE_Amount'] + country_data['Remit_Amount']
    res = country_data.sort_values('Total_Amount', ascending=False).head(15)
    return clean_for_json(res)

def get_operator_intelligence(filtered_df: pd.DataFrame) -> dict:
    total_txn = len(filtered_df)
    total_amount = float(filtered_df['Net Amt'].fillna(0).sum()) if not filtered_df.empty else 0.0

    op_name, op_count, op_count_pct, op_amt, op_amt_pct = 'N/A', 0, 0.0, 0.0, 0.0
    if 'Corporate' in filtered_df.columns and not filtered_df.empty:
        op_agg = filtered_df.groupby('Corporate').agg(Count=('Net Amt', 'size'), Amount=('Net Amt', 'sum')).reset_index().sort_values('Count', ascending=False)
        if not op_agg.empty:
            op_name = str(op_agg.iloc[0]['Corporate'])
            op_count = int(op_agg.iloc[0]['Count'])
            op_amt = float(op_agg.iloc[0]['Amount'])
            op_count_pct = float((op_count / total_txn * 100) if total_txn > 0 else 0)
            op_amt_pct = float((op_amt / total_amount * 100) if total_amount > 0 else 0)

    benef_name, benef_count, benef_count_pct, benef_amt, benef_amt_pct = 'N/A', 0, 0.0, 0.0, 0.0
    b_col = 'Beneficiary Type Load or Reload'
    if b_col in filtered_df.columns and not filtered_df.empty:
        b_agg = filtered_df.groupby(b_col).agg(Count=('Net Amt', 'size'), Amount=('Net Amt', 'sum')).reset_index().sort_values('Count', ascending=False)
        if not b_agg.empty:
            benef_name = str(b_agg.iloc[0][b_col])
            benef_count = int(b_agg.iloc[0]['Count'])
            benef_amt = float(b_agg.iloc[0]['Amount'])
            benef_count_pct = float((benef_count / total_txn * 100) if total_txn > 0 else 0)
            benef_amt_pct = float((benef_amt / total_amount * 100) if total_amount > 0 else 0)

    branch_name, branch_count, branch_count_pct, branch_amt, branch_amt_pct = 'N/A', 0, 0.0, 0.0, 0.0
    if 'Branch Name' in filtered_df.columns and not filtered_df.empty and total_txn > 0:
        br_agg = filtered_df.groupby('Branch Name').agg(Count=('Net Amt', 'size'), Amount=('Net Amt', 'sum')).reset_index().sort_values('Count', ascending=False)
        if not br_agg.empty:
            branch_name = str(br_agg.iloc[0]['Branch Name'])
            branch_count = int(br_agg.iloc[0]['Count'])
            branch_amt = float(br_agg.iloc[0]['Amount'])
            branch_count_pct = float((branch_count / total_txn * 100) if total_txn > 0 else 0)
            branch_amt_pct = float((branch_amt / total_amount * 100) if total_amount > 0 else 0)

    country_name, country_count, country_count_pct, country_amt, country_amt_pct = 'N/A', 0, 0.0, 0.0, 0.0
    if 'Visiting Country' in filtered_df.columns and not filtered_df.empty and total_txn > 0:
        vc_agg = filtered_df.groupby('Visiting Country').agg(Count=('Net Amt', 'size'), Amount=('Net Amt', 'sum')).reset_index().sort_values('Count', ascending=False)
        if not vc_agg.empty:
            country_name = str(vc_agg.iloc[0]['Visiting Country'])
            country_count = int(vc_agg.iloc[0]['Count'])
            country_amt = float(vc_agg.iloc[0]['Amount'])
            country_count_pct = float((country_count / total_txn * 100) if total_txn > 0 else 0)
            country_amt_pct = float((country_amt / total_amount * 100) if total_amount > 0 else 0)

    return {
        'best_operator': {'name': op_name, 'count': op_count, 'count_pct': op_count_pct, 'amount': op_amt, 'amount_pct': op_amt_pct},
        'best_beneficiary': {'name': benef_name, 'count': benef_count, 'count_pct': benef_count_pct, 'amount': benef_amt, 'amount_pct': benef_amt_pct},
        'best_branch': {'name': branch_name, 'count': branch_count, 'count_pct': branch_count_pct, 'amount': branch_amt, 'amount_pct': branch_amt_pct},
        'best_country': {'name': country_name, 'count': country_count, 'count_pct': country_count_pct, 'amount': country_amt, 'amount_pct': country_amt_pct},
    }

def get_tour_operator_kpis(filtered_df: pd.DataFrame) -> dict:
    total_txn = len(filtered_df)
    total_amount = float(filtered_df['Net Amt'].fillna(0).sum()) if not filtered_df.empty else 0.0

    ps_total = float(filtered_df.loc[filtered_df['Txn Type'] == 'PS', 'Net Amt'].fillna(0).sum()) if 'Txn Type' in filtered_df.columns and not filtered_df.empty else 0.0
    contribution_to_ps = float((total_amount / ps_total * 100) if ps_total > 0 else 0)

    return {
        'total_txn': total_txn,
        'total_amount': total_amount,
        'contribution_to_ps': contribution_to_ps,
    }
