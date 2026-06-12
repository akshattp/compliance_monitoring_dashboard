import time
import pandas as pd
import numpy as np
from datetime import datetime

def clean_for_json(obj):
    if isinstance(obj, pd.DataFrame):
        # Convert date to string before dropping to dict
        for col in obj.columns:
            if pd.api.types.is_datetime64_any_dtype(obj[col]):
                obj[col] = obj[col].astype(str)
        return obj.replace([np.inf, -np.inf, np.nan], None).to_dict(orient='records')
    elif isinstance(obj, dict):
        return {k: (float(v) if isinstance(v, (np.float32, np.float64)) else (int(v) if isinstance(v, (np.int32, np.int64)) else v)) for k, v in obj.items()}
    return obj

def safe_sorted_unique(series):
    try:
        unique_vals = series.dropna().astype(str).unique()
        return sorted(list(unique_vals))
    except Exception:
        return []

def risk_category_label(values):
    cleaned = [str(value) for value in values.dropna().unique() if str(value).strip()]
    return ', '.join(cleaned[:3]) if cleaned else 'N/A'

def summarize_cases(df: pd.DataFrame, group_col: str, amount_col: str = None):
    work = df.copy()
    work['_group_value'] = work[group_col].astype('object').where(work[group_col].notna(), 'Unknown').astype(str)
    work['_case_count'] = 1

    aggregations = {'Count': ('_case_count', 'sum')}
    if amount_col and amount_col in work.columns:
        aggregations.update({
            'Total Amount': (amount_col, 'sum'),
            'Average Amount': (amount_col, 'mean'),
            'Max Amount': (amount_col, 'max'),
        })

    summary = work.groupby('_group_value').agg(**aggregations).reset_index()
    summary = summary.rename(columns={'_group_value': group_col})

    if 'Risk  Category' in work.columns:
        risk_summary = work.groupby('_group_value')['Risk  Category'].apply(risk_category_label).reset_index()
        risk_summary = risk_summary.rename(columns={'_group_value': group_col, 'Risk  Category': 'Risk Category'})
        summary = summary.merge(risk_summary, on=group_col, how='left')
    else:
        summary['Risk Category'] = 'N/A'

    for column in ['Total Amount', 'Average Amount', 'Max Amount']:
        if column not in summary.columns:
            summary[column] = 0

    return summary.sort_values('Count', ascending=False)

def detect_high_value_transactions(df: pd.DataFrame):
    start = time.perf_counter()

    empty_summary = {
        'high_value_count': 0,
        'high_value_amount': 0.0,
        'structuring_count': 0,
        'structuring_amount': 0.0,
        'highest_transaction': 0.0,
        'high_value_exposure': 0.0,
    }

    if 'EQV USD' not in df.columns:
        return ([], [], empty_summary)

    df = df.copy()
    high_value = df[df['EQV USD'] > 25000]
    structuring = df[(df['EQV USD'] >= 20000) & (df['EQV USD'] <= 25000)]

    summary = {
        'high_value_count': int(len(high_value)),
        'high_value_amount': float(high_value['EQV USD'].sum()) if not high_value.empty else 0.0,
        'high_value_exposure': float(high_value['Net Amt'].sum()) if not high_value.empty and 'Net Amt' in high_value.columns else 0.0,
        'structuring_count': int(len(structuring)),
        'structuring_amount': float(structuring['EQV USD'].sum()) if not structuring.empty else 0.0,
        'highest_transaction': float(high_value['EQV USD'].max()) if not high_value.empty else 0.0,
    }
    
    return (clean_for_json(high_value), clean_for_json(structuring), clean_for_json(summary))

def detect_fatf_ofac(df: pd.DataFrame):
    """Detect FATF/OFAC flagged transactions."""
    empty_summary = {
        'flagged_count': 0,
        'flagged_amount': 0.0,
        'affected_branches': 0,
        'affected_countries': 0,
    }
    
    if 'OFAC _ FATF' not in df.columns:
        return ([], empty_summary)
        
    try:
        work_df = df.copy()
        flagged = work_df[work_df['OFAC _ FATF'] != 'NOT FLAGGED']
    except Exception as e:
        return ([], {**empty_summary, 'error': str(e)})
    
    summary = {
        'flagged_count': int(len(flagged)),
        'flagged_amount': float(flagged['Net Amt'].sum()) if not flagged.empty and 'Net Amt' in flagged.columns else 0.0,
        'affected_branches': int(flagged['Branch Name'].nunique()) if 'Branch Name' in flagged.columns else 0,
        'affected_countries': int(flagged['Visiting Country'].nunique()) if 'Visiting Country' in flagged.columns else 0,
    }
    return (clean_for_json(flagged), clean_for_json(summary))

def detect_multiple_operators_same_beneficiary(df: pd.DataFrame):
    empty_summary = {
        'suspicious_beneficiary_count': 0,
        'flagged_txn_count': 0,
        'flagged_amount': 0.0,
    }

    benef_col = 'Beneficiary Type Load or Reload'
    if 'Segments' not in df.columns or benef_col not in df.columns or 'Party Code' not in df.columns or 'Corporate' not in df.columns:
        return ([], empty_summary)

    df = df.copy()
    tour_op = df[df['Segments'] == 'TOUR OPERATOR'].copy()

    if tour_op.empty:
        return ([], empty_summary)

    grp = tour_op.groupby(benef_col).agg(
        unique_operators=('Corporate', 'nunique'),
        txn_count=('Corporate', 'size'),
        total_amount=('Net Amt', 'sum'),
    ).reset_index()

    suspicious_beneficiaries = grp[(grp['unique_operators'] >= 2) & (grp['txn_count'] >= 5)][benef_col].tolist()
    flagged = tour_op[tour_op[benef_col].isin(suspicious_beneficiaries)]

    summary = {
        'suspicious_beneficiary_count': int(len(suspicious_beneficiaries)),
        'flagged_txn_count': int(len(flagged)),
        'flagged_amount': float(flagged['Net Amt'].sum()) if not flagged.empty and 'Net Amt' in flagged.columns else 0.0,
    }
    
    return (clean_for_json(flagged), clean_for_json(summary))

def detect_high_frequency_remittances(df: pd.DataFrame):
    empty_summary = {
        'repeat_pair_count': 0,
        'flagged_txn_count': 0,
        'flagged_amount': 0.0,
    }

    benef_col = 'Beneficiary Type Load or Reload'
    if 'Segments' not in df.columns or benef_col not in df.columns or 'Party Code' not in df.columns or 'Corporate' not in df.columns:
        return ([], empty_summary)

    df = df.copy()
    tour_op = df[df['Segments'] == 'TOUR OPERATOR'].copy()

    if tour_op.empty:
        return ([], empty_summary)

    grp = tour_op.groupby(['Party Code', benef_col]).agg(
        txn_count=('Party Code', 'size'),
        total_amount=('Net Amt', 'sum'),
    ).reset_index()

    suspicious_pairs = grp[grp['txn_count'] > 5][['Party Code', benef_col]]
    if suspicious_pairs.empty:
        return ([], empty_summary)

    flagged = tour_op.merge(
        suspicious_pairs,
        on=['Party Code', benef_col],
        how='inner'
    )

    summary = {
        'repeat_pair_count': int(len(suspicious_pairs)),
        'flagged_txn_count': int(len(flagged)),
        'flagged_amount': float(flagged['Net Amt'].sum()) if not flagged.empty and 'Net Amt' in flagged.columns else 0.0,
    }
    
    return (clean_for_json(flagged), clean_for_json(summary))

def detect_configurable_load_refund_window(df: pd.DataFrame, threshold_days: int):
    instr_col, type_col = 'INSTRUMENTNO', 'LoadReload'
    prod_col = 'Product'
    txn_col = 'Txn Type'
    amt_col = 'Net Amt'
    date_col = 'Date'

    empty_summary = {"count": 0, "events": 0, "same_day_refunds": 0, "avg_delay": 0.0, "min_delay": 0.0, "max_delay": 0.0, "exposure": 0.0}

    core_cols = [instr_col, type_col, prod_col, date_col, amt_col, txn_col]
    if not all(col in df.columns for col in core_cols):
        return ([], empty_summary)

    d = df[df[prod_col].isin(['EC', 'FC'])].copy()
    if d.empty:
        return ([], empty_summary)

    d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
    d[type_col] = d[type_col].astype(str).str.strip().str.upper()
    d[date_col] = pd.to_datetime(d[date_col], errors='coerce')

    sub = d[(d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[date_col].notnull())].copy()
    if sub.empty:
        return ([], empty_summary)

    all_context_cols = [
        'Branch Name', 'Corporate', 'Passenger Name', 'MOBILENO', 'EMAILID',
        'Product', 'Currency', 'Purpose', 'Visiting Country', 'Risk  Category',
        'Agent Name', 'Segments', 'Party Code', 'Doc Number', 'Issuer'
    ]
    context_cols_present = [col for col in all_context_cols if col in sub.columns]

    load_select_cols = [instr_col, date_col, amt_col, txn_col] + context_cols_present
    loads_df = sub[(sub[type_col].isin(['LOAD', 'RELOAD'])) & (sub[txn_col] == 'PS')][load_select_cols].copy()
    loads_df = loads_df.rename(columns={
        date_col: 'LOAD_DATE',
        amt_col: 'LOAD_AMOUNT',
        txn_col: 'LOAD_TXN_TYPE'
    })
    loads_df = loads_df.rename(columns={col: f'{col}_LOAD' for col in context_cols_present})

    refund_select_cols = [instr_col, date_col, amt_col, txn_col] + context_cols_present
    refunds_df = sub[sub[type_col] == 'REFUND'][refund_select_cols].copy()
    refunds_df = refunds_df.rename(columns={
        date_col: 'REFUND_DATE',
        amt_col: 'REFUND_AMOUNT',
        txn_col: 'REFUND_TXN_TYPE'
    })
    refunds_df = refunds_df.rename(columns={col: f'{col}_REFUND' for col in context_cols_present})

    if loads_df.empty or refunds_df.empty:
        return ([], empty_summary)

    pairs = loads_df.merge(refunds_df, on=instr_col, how='inner')
    pairs['WITHIN_DAYS'] = (pairs['REFUND_DATE'] - pairs['LOAD_DATE']).dt.days
    valid_pairs = pairs[pairs['WITHIN_DAYS'] >= 0].copy()

    flagged_output = valid_pairs[valid_pairs['WITHIN_DAYS'] <= threshold_days].copy()
    if flagged_output.empty:
        return ([], empty_summary)

    final_cols_order = [instr_col, 'WITHIN_DAYS', 'LOAD_DATE', 'REFUND_DATE', 'LOAD_AMOUNT', 'REFUND_AMOUNT', 'LOAD_TXN_TYPE', 'REFUND_TXN_TYPE']
    for col in context_cols_present:
        load_col_name = f'{col}_LOAD'
        refund_col_name = f'{col}_REFUND'

        if load_col_name in flagged_output.columns and refund_col_name in flagged_output.columns:
            is_identical = (flagged_output[load_col_name].fillna('') == flagged_output[refund_col_name].fillna(''))
            combined_vals = flagged_output[load_col_name].astype(str) + ' / ' + flagged_output[refund_col_name].astype(str)
            
            flagged_output[col] = [
                orig if ident else comb 
                for ident, orig, comb in zip(is_identical, flagged_output[load_col_name], combined_vals)
            ]
            
            flagged_output = flagged_output.drop(columns=[load_col_name, refund_col_name])
            final_cols_order.append(col)
        elif load_col_name in flagged_output.columns:
            flagged_output = flagged_output.rename(columns={load_col_name: col})
            final_cols_order.append(col)
        elif refund_col_name in flagged_output.columns:
            flagged_output = flagged_output.rename(columns={refund_col_name: col})
            final_cols_order.append(col)

    flagged_output = flagged_output[final_cols_order]

    summary = {
        "count": int(flagged_output['INSTRUMENTNO'].nunique()),
        "events": int(len(flagged_output)),
        "same_day_refunds": int(len(flagged_output[flagged_output['WITHIN_DAYS'] == 0])),
        "avg_delay": float(flagged_output['WITHIN_DAYS'].mean()),
        "min_delay": float(flagged_output['WITHIN_DAYS'].min()),
        "max_delay": float(flagged_output['WITHIN_DAYS'].max()),
        "exposure": float(flagged_output['LOAD_AMOUNT'].sum() + flagged_output['REFUND_AMOUNT'].sum())
    }
    return (clean_for_json(flagged_output), clean_for_json(summary))

def detect_multiple_cards_contact(df: pd.DataFrame):
    instr_col, mob_col = 'INSTRUMENTNO', 'MOBILENO'
    prod_col, txn_col = 'Product', 'Txn Type'
    if any(c not in df.columns for c in [instr_col, mob_col, prod_col, txn_col]):
        return ([], {"count": 0, "total_cards": 0, "max_cards": 0, "exposure": 0.0})

    d = df[(df[prod_col].isin(['EC', 'FC'])) & (df[txn_col] == 'PS')].copy()
    d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
    d[mob_col] = d[mob_col].astype(str).str.strip().str.upper()
    
    sub = d[(d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[mob_col] != '') & (d[mob_col] != 'NAN')]
    grouped = sub.groupby(mob_col).agg(
        Card_Count=(instr_col, 'nunique'),
        List_of_Cards=(instr_col, lambda x: ', '.join(sorted(map(str, x.unique()))))
    ).reset_index()
    
    flagged = grouped[grouped['Card_Count'] >= 3]
    flagged_mobs = set(flagged[mob_col])
    flagged_data = sub[sub[mob_col].isin(flagged_mobs)]
    
    return (clean_for_json(flagged), {
        "count": int(len(flagged)), 
        "total_cards": int(flagged_data[instr_col].nunique()) if not flagged.empty else 0, 
        "max_cards": int(flagged['Card_Count'].max()) if not flagged.empty else 0, 
        "exposure": float(flagged_data['Net Amt'].sum()) if not flagged_data.empty and 'Net Amt' in flagged_data.columns else 0.0
    })

def detect_multiple_cards_traveller(df: pd.DataFrame):
    instr_col, pax_col = 'INSTRUMENTNO', 'Passenger Name'
    prod_col, txn_col = 'Product', 'Txn Type'
    if any(c not in df.columns for c in [instr_col, pax_col, prod_col, txn_col]):
        return ([], {"count": 0, "total_cards": 0, "max_cards": 0, "exposure": 0.0})

    d = df[(df[prod_col].isin(['EC', 'FC'])) & (df[txn_col] == 'PS')].copy()
    d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
    d[pax_col] = d[pax_col].astype(str).str.strip().str.upper()
    
    sub = d[(d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[pax_col] != '') & (d[pax_col] != 'NAN')]
    grouped = sub.groupby(pax_col).agg(
        Card_Count=(instr_col, 'nunique'),
        List_of_Cards=(instr_col, lambda x: ', '.join(sorted(map(str, x.unique()))))
    ).reset_index()
    
    flagged = grouped[grouped['Card_Count'] >= 2]
    flagged.rename(columns={pax_col: 'PAXNAME'}, inplace=True)
    
    flagged_paxs = set(flagged['PAXNAME'])
    flagged_data = sub[sub[pax_col].isin(flagged_paxs)]
    
    return (clean_for_json(flagged), {
        "count": int(len(flagged)), 
        "total_cards": int(flagged_data[instr_col].nunique()) if not flagged.empty else 0, 
        "max_cards": int(flagged['Card_Count'].max()) if not flagged.empty else 0,
        "exposure": float(flagged_data['Net Amt'].sum()) if not flagged_data.empty and 'Net Amt' in flagged_data.columns else 0.0
    })

def detect_multiple_cards_multi_operator(df: pd.DataFrame):
    instr_col, pax_col, corp_col = 'INSTRUMENTNO', 'Passenger Name', 'Corporate'
    prod_col, txn_col = 'Product', 'Txn Type'
    if any(c not in df.columns for c in [instr_col, pax_col, corp_col, prod_col, txn_col]):
        return ([], {"count": 0, "total_operators": 0, "total_cards": 0, "max_operators": 0, "exposure": 0.0})

    d = df[(df[prod_col].isin(['EC', 'FC'])) & (df[txn_col] == 'PS')].copy()
    d[instr_col], d[pax_col], d[corp_col] = d[instr_col].astype(str).str.strip().str.upper(), d[pax_col].astype(str).str.strip().str.upper(), d[corp_col].astype(str).str.strip().str.upper()
    
    sub = d[(d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[pax_col] != '') & (d[pax_col] != 'NAN')]
    grouped = sub.groupby(pax_col).agg(
        Operator_Count=(corp_col, 'nunique'),
        Card_Count=(instr_col, 'nunique'),
        Operator_List=(corp_col, lambda x: ', '.join(sorted(map(str, x.unique())))),
        Card_List=(instr_col, lambda x: ', '.join(sorted(map(str, x.unique()))))
    ).reset_index()
    
    flagged = grouped[(grouped['Operator_Count'] >= 2) & (grouped['Card_Count'] >= 2)]
    flagged.rename(columns={pax_col: 'PAXNAME'}, inplace=True)
    
    flagged_paxs = set(flagged['PAXNAME'])
    flagged_data = sub[sub[pax_col].isin(flagged_paxs)]
    
    return (clean_for_json(flagged), {
        "count": int(len(flagged)), 
        "total_operators": int(flagged_data[corp_col].nunique()) if not flagged.empty else 0, 
        "total_cards": int(flagged_data[instr_col].nunique()) if not flagged.empty else 0, 
        "max_operators": int(flagged['Operator_Count'].max()) if not flagged.empty else 0, 
        "exposure": float(flagged_data['Net Amt'].sum()) if not flagged_data.empty and 'Net Amt' in flagged_data.columns else 0.0
    })
