import pandas as pd
import numpy as np

def get_home_kpis(df: pd.DataFrame) -> dict:
    total_transactions = len(df)
    total_net_amt = df['Net Amt'].sum() if 'Net Amt' in df.columns and not df.empty else 0
    
    ps_amount = df.loc[df['Txn Type'] == 'PS', 'Net Amt'].sum() if 'Txn Type' in df.columns else 0
    pb_amount = df.loc[df['Txn Type'] == 'PB', 'Net Amt'].sum() if 'Txn Type' in df.columns else 0
    ps_count = len(df.loc[df['Txn Type'] == 'PS']) if 'Txn Type' in df.columns else 0
    pb_count = len(df.loc[df['Txn Type'] == 'PB']) if 'Txn Type' in df.columns else 0

    ps_count_pct = (ps_count / total_transactions * 100) if total_transactions > 0 else 0
    ps_amt_pct = (ps_amount / total_net_amt * 100) if total_net_amt > 0 else 0
    pb_count_pct = (pb_count / total_transactions * 100) if total_transactions > 0 else 0
    pb_amt_pct = (pb_amount / total_net_amt * 100) if total_net_amt > 0 else 0

    average_transaction = df['Net Amt'].mean() if 'Net Amt' in df.columns and not df.empty else 0
    highest_transaction = df['Net Amt'].max() if 'Net Amt' in df.columns and not df.empty else 0
    lowest_transaction = df['Net Amt'].min() if 'Net Amt' in df.columns and not df.empty else 0
    
    highest_pct = (highest_transaction / total_net_amt * 100) if total_net_amt > 0 else 0
    lowest_pct = (lowest_transaction / total_net_amt * 100) if total_net_amt > 0 else 0

    if 'Date' in df.columns and not df['Date'].isna().all():
        date_range = f"{df['Date'].min().date()} → {df['Date'].max().date()}"
    else:
        date_range = 'N/A'

    best_segment_name, best_segment_amt, best_segment_pct = 'N/A', 0, 0
    if 'Segments' in df.columns and not df.empty:
        segment_summary = df.groupby('Segments')['Net Amt'].sum().reset_index()
        if not segment_summary.empty:
            best_s = segment_summary.sort_values('Net Amt', ascending=False).iloc[0]
            best_segment_name = best_s['Segments']
            best_segment_amt = best_s['Net Amt']
            best_segment_pct = (best_segment_amt / total_net_amt * 100) if total_net_amt > 0 else 0

    best_branch_name, best_branch_amt, best_branch_pct = 'N/A', 0, 0
    if 'Branch Name' in df.columns and not df.empty:
        branch_summary = df.groupby('Branch Name')['Net Amt'].sum().reset_index()
        if not branch_summary.empty:
            best_b = branch_summary.sort_values('Net Amt', ascending=False).iloc[0]
            best_branch_name = best_b['Branch Name']
            best_branch_amt = best_b['Net Amt']
            best_branch_pct = (best_branch_amt / total_net_amt * 100) if total_net_amt > 0 else 0

    # Clean floats for JSON serialization
    return {
        'total_transactions': int(total_transactions),
        'total_net_amt': float(total_net_amt),
        'ps_amount': float(ps_amount),
        'pb_amount': float(pb_amount),
        'ps_count': int(ps_count),
        'pb_count': int(pb_count),
        'ps_count_pct': float(ps_count_pct),
        'ps_amt_pct': float(ps_amt_pct),
        'pb_count_pct': float(pb_count_pct),
        'pb_amt_pct': float(pb_amt_pct),
        'average_transaction': float(average_transaction),
        'highest_transaction': float(highest_transaction),
        'lowest_transaction': float(lowest_transaction),
        'highest_pct': float(highest_pct),
        'lowest_pct': float(lowest_pct),
        'date_range': date_range,
        'best_segment_name': best_segment_name,
        'best_segment_amt': float(best_segment_amt),
        'best_segment_pct': float(best_segment_pct),
        'best_branch_name': best_branch_name,
        'best_branch_amt': float(best_branch_amt),
        'best_branch_pct': float(best_branch_pct),
    }

def get_home_trends(df: pd.DataFrame, trend_agg: str) -> dict:
    if 'Date' not in df.columns or df['Date'].isna().all():
        return {
            'agg_df': [],
            'highest_amount_time': None,
            'lowest_amount_time': None,
            'highest_count_time': None,
            'lowest_count_time': None,
        }

    df['Date'] = pd.to_datetime(df['Date'])

    if trend_agg == 'DAILY':
        agg_df = (
            df.groupby(df['Date'].dt.date)
            .agg(Transaction_Count=('Net Amt', 'size'), Transaction_Amount=('Net Amt', 'sum'))
            .reset_index()
        )
        agg_df.rename(columns={'Date': 'Time'}, inplace=True)
        agg_df['Time'] = agg_df['Time'].astype(str)
    else:
        if 'Week' in df.columns:
            agg_df = (
                df.groupby('Week')
                .agg(Transaction_Count=('Net Amt', 'size'), Transaction_Amount=('Net Amt', 'sum'))
                .reset_index()
            )
            agg_df.rename(columns={'Week': 'Time'}, inplace=True)
            agg_df['Time'] = agg_df['Time'].astype(str)
        else:
            agg_df = (
                df.groupby(pd.Grouper(key='Date', freq='W-MON'))
                .agg(Transaction_Count=('Net Amt', 'size'), Transaction_Amount=('Net Amt', 'sum'))
                .reset_index()
            )
            agg_df['Date'] = agg_df['Date'].dt.date.astype(str)
            agg_df.rename(columns={'Date': 'Time'}, inplace=True)

    time_amount = agg_df.sort_values('Transaction_Amount', ascending=False)
    time_count = agg_df.sort_values('Transaction_Count', ascending=False)

    highest_amount_time = time_amount.iloc[0].to_dict() if not time_amount.empty else None
    lowest_amount_time = time_amount.iloc[-1].to_dict() if not time_amount.empty else None
    highest_count_time = time_count.iloc[0].to_dict() if not time_count.empty else None
    lowest_count_time = time_count.iloc[-1].to_dict() if not time_count.empty else None

    # Cast types for JSON compatibility
    records = agg_df.to_dict(orient='records')
    return {
        'agg_df': records,
        'highest_amount_time': highest_amount_time,
        'lowest_amount_time': lowest_amount_time,
        'highest_count_time': highest_count_time,
        'lowest_count_time': lowest_count_time,
    }

def get_home_breakdowns(df: pd.DataFrame, is_count: bool, purpose_threshold: float) -> dict:
    agg_col = 'Count' if is_count else 'Net Amt'
    
    # 1. Purpose Breakdown
    purpose_df = pd.DataFrame()
    purpose_summary_table = pd.DataFrame()
    if 'Purpose' in df.columns:
        purp_agg = df.groupby('Purpose').agg(
            Count=('Net Amt', 'size'),
            Net_Amt=('Net Amt', 'sum')
        ).reset_index()
        purp_agg.rename(columns={'Net_Amt': 'Net Amt'}, inplace=True)
        purp_agg = purp_agg.sort_values(agg_col, ascending=False)
        
        total_val = purp_agg[agg_col].sum()
        purp_agg['Percentage'] = (purp_agg[agg_col] / total_val * 100) if total_val > 0 else 0
        
        below_thresh = purp_agg['Percentage'] < purpose_threshold
        others_df = purp_agg[below_thresh].copy()
        main_df = purp_agg[~below_thresh].copy()
        
        if not others_df.empty:
            others_row = pd.DataFrame([{
                'Purpose': 'Others',
                'Count': others_df['Count'].sum(),
                'Net Amt': others_df['Net Amt'].sum(),
                'Percentage': others_df['Percentage'].sum()
            }])
            purpose_df = pd.concat([main_df, others_row], ignore_index=True)
        else:
            purpose_df = main_df.copy()
            
        purp_agg['is_other'] = purp_agg['Percentage'] < purpose_threshold
        total_count = purp_agg['Count'].sum()
        total_amount = purp_agg['Net Amt'].sum()
        purp_agg['% Count'] = (purp_agg['Count'] / total_count * 100) if total_count > 0 else 0
        purp_agg['% Net Amount'] = (purp_agg['Net Amt'] / total_amount * 100) if total_amount > 0 else 0
        
        display_df = purp_agg[['Purpose', 'Count', '% Count', 'Net Amt', '% Net Amount', 'is_other']].copy()
        total_row = pd.DataFrame({
            'Purpose': ['**TOTAL**'], 'Count': [total_count], '% Count': [100.0],
            'Net Amt': [total_amount], '% Net Amount': [100.0], 'is_other': [False]
        })
        purpose_summary_table = pd.concat([display_df, total_row], ignore_index=True)

    # 2. Product Breakdown
    product_df = pd.DataFrame()
    product_summary_table = pd.DataFrame()
    if 'Product' in df.columns:
        product_summary = df.groupby('Product').agg(
            Count=('Net Amt', 'size'),
            Net_Amt=('Net Amt', 'sum')
        ).reset_index()
        product_summary.rename(columns={'Net_Amt': 'Net Amt'}, inplace=True)
        product_summary = product_summary.sort_values(agg_col, ascending=False)
        
        total_count = product_summary['Count'].sum()
        total_amount = product_summary['Net Amt'].sum()
        prod_breakdown = product_summary.copy()
        prod_breakdown['% Count'] = (prod_breakdown['Count'] / total_count * 100) if total_count > 0 else 0
        prod_breakdown['% Net Amount'] = (prod_breakdown['Net Amt'] / total_amount * 100) if total_amount > 0 else 0
        
        total_row = pd.DataFrame({
            'Product': ['**TOTAL**'],
            'Count': [total_count],
            '% Count': [100.0],
            'Net Amt': [total_amount],
            '% Net Amount': [100.0]
        })
        product_df = prod_breakdown.copy()
        product_summary_table = pd.concat([prod_breakdown, total_row], ignore_index=True)

    # 3. Branch Breakdown
    branch_df = pd.DataFrame()
    branch_field = 'Branch Name' if 'Branch Name' in df.columns else 'Branch'
    if branch_field in df.columns:
        res = df.groupby(branch_field).agg(
            Count=('Net Amt', 'size'),
            Net_Amt=('Net Amt', 'sum')
        ).reset_index()
        res.rename(columns={'Net_Amt': 'Net Amt'}, inplace=True)
        branch_df = res.sort_values(agg_col, ascending=False).head(15)

    # 4. Country Breakdown
    country_df = pd.DataFrame()
    if 'Visiting Country' in df.columns:
        res = df.groupby('Visiting Country').agg(
            Count=('Net Amt', 'size'),
            Net_Amt=('Net Amt', 'sum')
        ).reset_index()
        res.rename(columns={'Net_Amt': 'Net Amt'}, inplace=True)
        country_df = res.sort_values(agg_col, ascending=False).head(15)

    return {
        'purpose_df': purpose_df.to_dict(orient='records') if not purpose_df.empty else [],
        'purpose_summary_table': purpose_summary_table.to_dict(orient='records') if not purpose_summary_table.empty else [],
        'product_df': product_df.to_dict(orient='records') if not product_df.empty else [],
        'product_summary_table': product_summary_table.to_dict(orient='records') if not product_summary_table.empty else [],
        'branch_df': branch_df.to_dict(orient='records') if not branch_df.empty else [],
        'country_df': country_df.to_dict(orient='records') if not country_df.empty else [],
    }
