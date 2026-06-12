import os
import io
import pandas as pd
import numpy as np

def _get_col(df, possible_names, default=None):
    for name in possible_names:
        if name in df.columns:
            return name
    return default

def load_bank_book_data(file_bytes=None, default_path=None, sheet_name='Sheet1') -> dict:
    df = None
    if file_bytes is not None:
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
    elif default_path is not None and os.path.exists(default_path):
        df = pd.read_excel(default_path, sheet_name=sheet_name)
    else:
        return {}

    # Identify dynamic column names
    col_receipt = _get_col(df, ['Receipt Amount', 'Receipt Amt', 'Amount', 'Credit'], 'Receipt Amount')
    col_cheque_transfer = _get_col(df, ['Cheque/Transfer', 'Cheque / Transfer'], 'Cheque/Transfer')
    col_cms = _get_col(df, ['CMS / NON CMS / HDFC - 14', 'CMS/NON CMS/HDFC-14', 'CMS / NON CMS / HDFC-14', 'Business Classification'], 'CMS / NON CMS / HDFC - 14')
    col_segment = _get_col(df, ['Segment'], 'Segment')
    col_party = _get_col(df, ['Party Name', 'Party'], 'Party Name')
    col_account = _get_col(df, ['Account Name', 'Account'], 'Account Name')
    col_date = _get_col(df, ['Date', 'Value Date', 'Txn Date'], 'Date')
    col_cheque_no = _get_col(df, ['Cheque No', 'Cheque Number', 'Chq No'], 'Cheque No')

    # Basic data cleaning
    if col_receipt in df.columns:
        df[col_receipt] = pd.to_numeric(df[col_receipt], errors='coerce').fillna(0)
    if col_date in df.columns:
        df[col_date] = pd.to_datetime(df[col_date], errors='coerce')

    return {
        'df': df,
        'col_receipt': col_receipt,
        'col_cheque_transfer': col_cheque_transfer,
        'col_cms': col_cms,
        'col_segment': col_segment,
        'col_party': col_party,
        'col_account': col_account,
        'col_date': col_date,
        'col_cheque_no': col_cheque_no,
    }

def get_bank_book_kpis(bb_df: pd.DataFrame, cols: dict) -> dict:
    col_receipt = cols['col_receipt']
    col_cheque_transfer = cols['col_cheque_transfer']
    col_cms = cols['col_cms']
    col_segment = cols['col_segment']
    col_party = cols['col_party']

    total_receipt_amount = bb_df[col_receipt].sum() if col_receipt in bb_df.columns else 0
    total_txns = len(bb_df)

    cheque_txns = len(bb_df[bb_df[col_cheque_transfer].astype(str).str.contains('cheque', case=False, na=False)]) if col_cheque_transfer in bb_df.columns else 0
    transfer_txns = len(bb_df[bb_df[col_cheque_transfer].astype(str).str.contains('transfer', case=False, na=False)]) if col_cheque_transfer in bb_df.columns else 0
    
    cms_amt = bb_df[bb_df[col_cms].astype(str).str.contains('CMS', case=False, na=False) & ~bb_df[col_cms].astype(str).str.contains('NON', case=False, na=False)][col_receipt].sum() if col_cms in bb_df.columns else 0
    non_cms_amt = bb_df[bb_df[col_cms].astype(str).str.contains('NON CMS', case=False, na=False)][col_receipt].sum() if col_cms in bb_df.columns else 0
    hdfc_amt = bb_df[bb_df[col_cms].astype(str).str.contains('HDFC', case=False, na=False)][col_receipt].sum() if col_cms in bb_df.columns else 0
    
    top_segment = bb_df.groupby(col_segment)[col_receipt].sum().idxmax() if (col_segment in bb_df.columns and not bb_df.empty) else "N/A"
    top_party = bb_df.groupby(col_party)[col_receipt].sum().idxmax() if (col_party in bb_df.columns and not bb_df.empty) else "N/A"
    largest_receipt = bb_df[col_receipt].max() if not bb_df.empty else 0

    return {
        'total_txns': total_txns,
        'total_receipt_amount': total_receipt_amount,
        'cheque_txns': cheque_txns,
        'transfer_txns': transfer_txns,
        'cms_amt': cms_amt,
        'non_cms_amt': non_cms_amt,
        'hdfc_amt': hdfc_amt,
        'top_segment': top_segment,
        'top_party': top_party,
        'largest_receipt': largest_receipt,
    }

def build_summary_table(bb_df: pd.DataFrame, col_receipt: str, group_col: str, total_txns: int, total_receipt_amount: float) -> pd.DataFrame:
    if group_col not in bb_df.columns:
        return pd.DataFrame()
        
    summary = bb_df.groupby(group_col).agg(
        Count=(col_receipt, 'size'),
        ReceiptAmount=(col_receipt, 'sum')
    ).reset_index()
    summary.rename(columns={'ReceiptAmount': 'Receipt Amount'}, inplace=True)
    summary['Count %'] = (summary['Count'] / total_txns * 100).round(2) if total_txns > 0 else 0
    summary['Receipt Amount %'] = (summary['Receipt Amount'] / total_receipt_amount * 100).round(2) if total_receipt_amount > 0 else 0
    summary['Average Receipt'] = (summary['Receipt Amount'] / summary['Count']).round(2)
    summary = summary.sort_values('Receipt Amount', ascending=False)
    
    total_row = pd.DataFrame([{
        group_col: 'TOTAL',
        'Count': summary['Count'].sum(),
        'Receipt Amount': summary['Receipt Amount'].sum(),
        'Count %': 100.0,
        'Receipt Amount %': 100.0,
        'Average Receipt': round(summary['Receipt Amount'].sum() / summary['Count'].sum(), 2) if summary['Count'].sum() > 0 else 0
    }])
    return pd.concat([summary, total_row], ignore_index=True)

def get_segment_trend_data(bb_df: pd.DataFrame, col_date: str, col_segment: str, col_receipt: str) -> pd.DataFrame:
    if col_date not in bb_df.columns or col_segment not in bb_df.columns or col_receipt not in bb_df.columns:
        return pd.DataFrame()
    seg_trend = bb_df.groupby([bb_df[col_date].dt.date, col_segment])[col_receipt].sum().reset_index()
    seg_trend.rename(columns={col_date: 'Date'}, inplace=True)
    return seg_trend

def get_acc_seg_matrix(bb_df: pd.DataFrame, cols: dict, cms_type: str) -> dict:
    col_account = cols['col_account']
    col_segment = cols['col_segment']
    col_cms = cols['col_cms']
    col_receipt = cols['col_receipt']

    if col_account not in bb_df.columns or col_segment not in bb_df.columns or col_cms not in bb_df.columns:
        return {}

    if cms_type == 'CMS':
        df_subset = bb_df[bb_df[col_cms].astype(str).str.contains('CMS', case=False, na=False) & ~bb_df[col_cms].astype(str).str.contains('NON', case=False, na=False)]
    else:
        df_subset = bb_df[bb_df[col_cms].astype(str).str.contains('NON CMS', case=False, na=False)]

    if df_subset.empty:
        return {}

    count_matrix = pd.crosstab(df_subset[col_account], df_subset[col_segment], margins=True, margins_name='TOTAL')
    amt_matrix = pd.crosstab(df_subset[col_account], df_subset[col_segment], values=df_subset[col_receipt], aggfunc='sum', margins=True, margins_name='TOTAL').fillna(0)
    
    acc_summary = df_subset.groupby(col_account).agg(Amount=(col_receipt, 'sum'), Count=(col_receipt, 'size')).reset_index()
    seg_mix = df_subset.groupby([col_account, col_segment])[col_receipt].sum().reset_index()

    return {
        'count_matrix': count_matrix,
        'amt_matrix': amt_matrix,
        'acc_summary': acc_summary,
        'seg_mix': seg_mix,
    }

def get_exception_insights_data(bb_df: pd.DataFrame, cols: dict, kpis: dict) -> dict:
    col_party = cols['col_party']
    col_receipt = cols['col_receipt']
    col_account = cols['col_account']
    col_cheque_transfer = cols['col_cheque_transfer']
    col_segment = cols['col_segment']
    col_cms = cols['col_cms']
    col_cheque_no = cols['col_cheque_no']

    total_receipt_amount = kpis['total_receipt_amount']
    cms_amt = kpis['cms_amt']
    non_cms_amt = kpis['non_cms_amt']

    insights = {}

    # Rule 1: High Concentration Party (>10%)
    if col_party in bb_df.columns and total_receipt_amount > 0:
        party_pct = (bb_df.groupby(col_party)[col_receipt].sum() / total_receipt_amount * 100).reset_index()
        party_pct.rename(columns={col_receipt: 'Receipt Amount %'}, inplace=True)
        high_conc = party_pct[party_pct['Receipt Amount %'] > 10].sort_values('Receipt Amount %', ascending=False)
        insights['rule1_high_conc'] = high_conc
    else:
        insights['rule1_high_conc'] = pd.DataFrame()

    # Rule 3: Account Dependency (>25%)
    if col_account in bb_df.columns and total_receipt_amount > 0:
        acc_pct = (bb_df.groupby(col_account)[col_receipt].sum() / total_receipt_amount * 100).reset_index()
        acc_pct.rename(columns={col_receipt: 'Receipt Amount %'}, inplace=True)
        acc_dep = acc_pct[acc_pct['Receipt Amount %'] > 25].sort_values('Receipt Amount %', ascending=False)
        insights['rule3_acc_dep'] = acc_dep
    else:
        insights['rule3_acc_dep'] = pd.DataFrame()

    # Rule 5: Cheque Concentration
    if col_party in bb_df.columns and col_cheque_transfer in bb_df.columns:
        cheque_df = bb_df[bb_df[col_cheque_transfer].astype(str).str.contains('cheque', case=False, na=False)]
        chq_party = cheque_df.groupby(col_party)[col_receipt].sum().reset_index().sort_values(col_receipt, ascending=False).head(5)
        insights['rule5_chq_conc'] = chq_party
    else:
        insights['rule5_chq_conc'] = pd.DataFrame()

    # Rule 7: Duplicate Receipt Pattern
    if col_party in bb_df.columns:
        dups = bb_df[bb_df.duplicated([col_party, col_receipt], keep=False)]
        if not dups.empty:
            dup_summary = dups.groupby([col_party, col_receipt]).size().reset_index(name='Occurrences').sort_values('Occurrences', ascending=False).head(10)
            insights['rule7_dup_pattern'] = dup_summary
        else:
            insights['rule7_dup_pattern'] = pd.DataFrame()
    else:
        insights['rule7_dup_pattern'] = pd.DataFrame()

    # Rule 2: Top 20 Single Largest Receipts
    display_cols = [c for c in [col_party, col_receipt, col_segment, col_cheque_transfer] if c in bb_df.columns]
    insights['rule2_largest'] = bb_df.nlargest(20, col_receipt)[display_cols] if not bb_df.empty else pd.DataFrame()

    # Rule 4: Segment Dependency (>60%)
    if col_segment in bb_df.columns and total_receipt_amount > 0:
        seg_pct = (bb_df.groupby(col_segment)[col_receipt].sum() / total_receipt_amount * 100).reset_index()
        seg_pct.rename(columns={col_receipt: 'Receipt Amount %'}, inplace=True)
        seg_dep = seg_pct[seg_pct['Receipt Amount %'] > 60].sort_values('Receipt Amount %', ascending=False)
        insights['rule4_seg_dep'] = seg_dep
    else:
        insights['rule4_seg_dep'] = pd.DataFrame()

    # Rule 6: CMS vs NON CMS Imbalance
    imbalance = None
    if total_receipt_amount > 0:
        if (cms_amt / total_receipt_amount) > 0.8:
            imbalance = f"Heavy CMS Imbalance: CMS contributes {cms_amt/total_receipt_amount*100:.1f}%"
        elif (non_cms_amt / total_receipt_amount) > 0.8:
            imbalance = f"Heavy NON CMS Imbalance: NON CMS contributes {non_cms_amt/total_receipt_amount*100:.1f}%"
    insights['rule6_imbalance'] = imbalance

    # Rule 8: Data Quality Checks
    quality_issues = []
    if col_party in bb_df.columns:
        missing_party = bb_df[bb_df[col_party].isna() | (bb_df[col_party] == '')]
        if not missing_party.empty: quality_issues.append({"Issue": "Blank Party Name", "Count": len(missing_party)})
    if col_segment in bb_df.columns:
        missing_seg = bb_df[bb_df[col_segment].isna() | (bb_df[col_segment] == '')]
        if not missing_seg.empty: quality_issues.append({"Issue": "Blank Segment", "Count": len(missing_seg)})
    if col_account in bb_df.columns:
        missing_acc = bb_df[bb_df[col_account].isna() | (bb_df[col_account] == '')]
        if not missing_acc.empty: quality_issues.append({"Issue": "Blank Account Name", "Count": len(missing_acc)})
    if col_cheque_no in bb_df.columns:
        missing_chq = bb_df[(bb_df[col_cheque_transfer].astype(str).str.contains('cheque', case=False, na=False)) & (bb_df[col_cheque_no].isna() | (bb_df[col_cheque_no] == ''))]
        if not missing_chq.empty: quality_issues.append({"Issue": "Blank Cheque No (for Cheques)", "Count": len(missing_chq)})
        
    insights['rule8_dq'] = pd.DataFrame(quality_issues) if quality_issues else pd.DataFrame()

    return insights
