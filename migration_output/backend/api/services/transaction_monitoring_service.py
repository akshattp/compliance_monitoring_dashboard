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

    if 'Risk Category' in work.columns:
        risk_summary = work.groupby('_group_value')['Risk Category'].apply(risk_category_label).reset_index()
        risk_summary = risk_summary.rename(columns={'_group_value': group_col, 'Risk Category': 'Risk Category'})
        summary = summary.merge(risk_summary, on=group_col, how='left')
    else:
        summary['Risk Category'] = 'N/A'

    for column in ['Total Amount', 'Average Amount', 'Max Amount']:
        if column not in summary.columns:
            summary[column] = 0

    return summary.sort_values('Count', ascending=False)

def detect_high_value_transactions(df: pd.DataFrame, threshold: float = 25000):
    start = time.perf_counter()

    empty_summary = {
        'high_value_count': 0,
        'high_value_amount': 0.0,
        'structuring_count': 0,
        'structuring_amount': 0.0,
        'highest_transaction': 0.0,
        'high_value_exposure': 0.0,
    }

    if 'Equivalent USD Amount' not in df.columns:
        return ([], [], empty_summary)

    df = df.copy()
    high_value = df[df['Equivalent USD Amount'] > threshold]
    structuring = df[(df['Equivalent USD Amount'] >= (threshold * 0.8)) & (df['Equivalent USD Amount'] <= threshold)]

    summary = {
        'high_value_count': int(len(high_value)),
        'high_value_amount': float(high_value['Equivalent USD Amount'].sum()) if not high_value.empty else 0.0,
        'high_value_exposure': float(high_value['INRAMOUNT'].sum()) if not high_value.empty and 'INRAMOUNT' in high_value.columns else 0.0,
        'structuring_count': int(len(structuring)),
        'structuring_amount': float(structuring['Equivalent USD Amount'].sum()) if not structuring.empty else 0.0,
        'highest_transaction': float(high_value['Equivalent USD Amount'].max()) if not high_value.empty else 0.0,
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
    
    if 'OFAC_FATF' not in df.columns:
        return ([], empty_summary)
        
    try:
        work_df = df.copy()
        flagged = work_df[work_df['OFAC_FATF'] != 'NOT FLAGGED']
    except Exception as e:
        return ([], {**empty_summary, 'error': str(e)})
    
    summary = {
        'flagged_count': int(len(flagged)),
        'flagged_amount': float(flagged['INRAMOUNT'].sum()) if not flagged.empty and 'INRAMOUNT' in flagged.columns else 0.0,
        'affected_branches': int(flagged['LOCATION'].nunique()) if 'LOCATION' in flagged.columns else 0,
        'affected_countries': int(flagged['CountryToTravel'].nunique()) if 'CountryToTravel' in flagged.columns else 0,
    }
    return (clean_for_json(flagged), clean_for_json(summary))

def detect_multiple_operators_same_beneficiary(df: pd.DataFrame):
    empty_summary = {
        'suspicious_beneficiary_count': 0,
        'flagged_txn_count': 0,
        'flagged_amount': 0.0,
    }

    benef_col = 'BENEFICIARY'
    if 'Segment' not in df.columns or benef_col not in df.columns or 'CUSTOMERCODE' not in df.columns or 'CUSTOMERNAME' not in df.columns:
        return ([], empty_summary)

    df = df.copy()
    tour_op = df[df['Segment'] == 'TOUR OPERATOR'].copy()

    if tour_op.empty:
        return ([], empty_summary)

    grp = tour_op.groupby(benef_col).agg(
        unique_operators=('CUSTOMERNAME', 'nunique'),
        txn_count=('CUSTOMERNAME', 'size'),
        total_amount=('INRAMOUNT', 'sum'),
    ).reset_index()

    suspicious_beneficiaries = grp[(grp['unique_operators'] >= 2) & (grp['txn_count'] >= 5)][benef_col].tolist()
    flagged = tour_op[tour_op[benef_col].isin(suspicious_beneficiaries)]

    summary = {
        'suspicious_beneficiary_count': int(len(suspicious_beneficiaries)),
        'flagged_txn_count': int(len(flagged)),
        'flagged_amount': float(flagged['INRAMOUNT'].sum()) if not flagged.empty and 'INRAMOUNT' in flagged.columns else 0.0,
    }
    
    return (clean_for_json(flagged), clean_for_json(summary))

def detect_high_frequency_remittances(df: pd.DataFrame, threshold: int = 5):
    empty_summary = {
        'repeat_pair_count': 0,
        'flagged_txn_count': 0,
        'flagged_amount': 0.0,
    }

    benef_col = 'BENEFICIARY'
    if 'Segment' not in df.columns or benef_col not in df.columns or 'CUSTOMERCODE' not in df.columns or 'CUSTOMERNAME' not in df.columns:
        return ([], empty_summary)

    df = df.copy()
    tour_op = df[df['Segment'] == 'TOUR OPERATOR'].copy()

    if tour_op.empty:
        return ([], empty_summary)

    grp = tour_op.groupby(['CUSTOMERCODE', benef_col]).agg(
        txn_count=('CUSTOMERCODE', 'size'),
        total_amount=('INRAMOUNT', 'sum'),
    ).reset_index()

    suspicious_pairs = grp[grp['txn_count'] > threshold][['CUSTOMERCODE', benef_col]]
    if suspicious_pairs.empty:
        return ([], empty_summary)

    flagged = tour_op.merge(
        suspicious_pairs,
        on=['CUSTOMERCODE', benef_col],
        how='inner'
    )

    summary = {
        'repeat_pair_count': int(len(suspicious_pairs)),
        'flagged_txn_count': int(len(flagged)),
        'flagged_amount': float(flagged['INRAMOUNT'].sum()) if not flagged.empty and 'INRAMOUNT' in flagged.columns else 0.0,
    }
    
    return (clean_for_json(flagged), clean_for_json(summary))

def detect_configurable_load_refund_window(df: pd.DataFrame, threshold_days: int):
    instr_col, type_col = 'INSTRUMENTNO', 'LoadReload'
    prod_col = 'PRODUCT'
    txn_col = 'TXNTYPE'
    amt_col = 'INRAMOUNT'
    date_col = 'TXNDATE'

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
        'LOCATION', 'CUSTOMERNAME', 'PAXNAME', 'MOBILENO', 'EMAILID',
        'PRODUCT', 'CURRENCY', 'TxnPurpose', 'CountryToTravel', 'Risk Category',
        'AGENTNAME', 'Segment', 'CUSTOMERCODE', 'DOCNO', 'ISSUER'
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
    prod_col, txn_col = 'PRODUCT', 'TXNTYPE'
    if any(c not in df.columns for c in [instr_col, mob_col, prod_col, txn_col]):
        return ([], {"count": 0, "total_cards": 0, "max_cards": 0, "txn_count": 0, "exposure": 0.0})

    d = df[(df[prod_col].isin(['EC', 'FC'])) & (df[txn_col] == 'PS')].copy()
    d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
    d[mob_col] = d[mob_col].astype(str).str.strip().str.upper()
    
    sub = d[(d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[mob_col] != '') & (d[mob_col] != 'NAN')]
    grouped = sub.groupby(mob_col).agg(
        Distinct_Cards=(instr_col, 'nunique'),
        Transactions=('INRAMOUNT', 'size'),
        Exposure=('INRAMOUNT', 'sum'),
        List_of_Cards=(instr_col, lambda x: ', '.join(sorted(map(str, x.unique()))))
    ).reset_index()
    
    flagged = grouped[grouped['Distinct_Cards'] >= 3]
    flagged_mobs = set(flagged[mob_col])
    flagged_data = sub[sub[mob_col].isin(flagged_mobs)]
    
    return (clean_for_json(flagged), {
        "count": int(len(flagged)), 
        "total_cards": int(flagged_data[instr_col].nunique()) if not flagged.empty else 0, 
        "max_cards": int(flagged['Distinct_Cards'].max()) if not flagged.empty else 0, 
        "txn_count": int(len(flagged_data)),
        "exposure": float(flagged_data['INRAMOUNT'].sum()) if not flagged_data.empty and 'INRAMOUNT' in flagged_data.columns else 0.0
    })

def detect_multiple_cards_traveller(df: pd.DataFrame):
    instr_col, pax_col = 'INSTRUMENTNO', 'PAXNAME'
    prod_col, txn_col = 'PRODUCT', 'TXNTYPE'
    if any(c not in df.columns for c in [instr_col, pax_col, prod_col, txn_col]):
        return ([], {"count": 0, "total_cards": 0, "max_cards": 0, "txn_count": 0, "exposure": 0.0})

    d = df[(df[prod_col].isin(['EC', 'FC'])) & (df[txn_col] == 'PS')].copy()
    d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
    d[pax_col] = d[pax_col].astype(str).str.strip().str.upper()
    
    # Ensure PAXIDNO is present
    if 'PAXIDNO' in d.columns:
        d['PAXIDNO'] = d['PAXIDNO'].astype(str).str.strip().str.upper().fillna('N/A')
    else:
        d['PAXIDNO'] = 'N/A'
        
    sub = d[(d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[pax_col] != '') & (d[pax_col] != 'NAN')]
    
    grouped = sub.groupby(['PAXIDNO', pax_col]).agg(
        Distinct_Cards=(instr_col, 'nunique'),
        Transactions=('INRAMOUNT', 'size'),
        Exposure=('INRAMOUNT', 'sum'),
        List_of_Cards=(instr_col, lambda x: ', '.join(sorted(map(str, x.unique()))))
    ).reset_index()
    
    flagged = grouped[grouped['Distinct_Cards'] >= 2]
    flagged.rename(columns={pax_col: 'PAXNAME'}, inplace=True)
    
    flagged_paxs = set(flagged['PAXNAME'])
    flagged_data = sub[sub[pax_col].isin(flagged_paxs)]
    
    return (clean_for_json(flagged), {
        "count": int(len(flagged)), 
        "total_cards": int(flagged_data[instr_col].nunique()) if not flagged.empty else 0, 
        "max_cards": int(flagged['Distinct_Cards'].max()) if not flagged.empty else 0,
        "txn_count": int(len(flagged_data)),
        "exposure": float(flagged_data['INRAMOUNT'].sum()) if not flagged_data.empty and 'INRAMOUNT' in flagged_data.columns else 0.0
    })

def detect_multiple_cards_multi_operator(df: pd.DataFrame):
    instr_col, pax_col, corp_col = 'INSTRUMENTNO', 'PAXNAME', 'CUSTOMERNAME'
    prod_col, txn_col = 'PRODUCT', 'TXNTYPE'
    if any(c not in df.columns for c in [instr_col, pax_col, corp_col, prod_col, txn_col]):
        return ([], {"count": 0, "total_operators": 0, "total_cards": 0, "max_operators": 0, "txn_count": 0, "exposure": 0.0})

    d = df[(df[prod_col].isin(['EC', 'FC'])) & (df[txn_col] == 'PS')].copy()
    d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
    d[pax_col] = d[pax_col].astype(str).str.strip().str.upper()
    d[corp_col] = d[corp_col].astype(str).str.strip().str.upper()
    
    if 'PAXIDNO' in d.columns:
        d['PAXIDNO'] = d['PAXIDNO'].astype(str).str.strip().str.upper().fillna('N/A')
    else:
        d['PAXIDNO'] = 'N/A'
        
    sub = d[(d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[pax_col] != '') & (d[pax_col] != 'NAN')]
    grouped = sub.groupby(['PAXIDNO', pax_col]).agg(
        Distinct_Operators=(corp_col, 'nunique'),
        Distinct_Cards=(instr_col, 'nunique'),
        Transactions=('INRAMOUNT', 'size'),
        Exposure=('INRAMOUNT', 'sum'),
        Operator_List=(corp_col, lambda x: ', '.join(sorted(map(str, x.unique())))),
        Card_List=(instr_col, lambda x: ', '.join(sorted(map(str, x.unique()))))
    ).reset_index()
    
    flagged = grouped[(grouped['Distinct_Operators'] >= 2) & (grouped['Distinct_Cards'] >= 2)]
    flagged.rename(columns={pax_col: 'PAXNAME'}, inplace=True)
    
    flagged_paxs = set(flagged['PAXNAME'])
    flagged_data = sub[sub[pax_col].isin(flagged_paxs)]
    
    return (clean_for_json(flagged), {
        "count": int(len(flagged)), 
        "total_operators": int(flagged_data[corp_col].nunique()) if not flagged.empty else 0, 
        "total_cards": int(flagged_data[instr_col].nunique()) if not flagged.empty else 0, 
        "max_operators": int(flagged['Distinct_Operators'].max()) if not flagged.empty else 0, 
        "txn_count": int(len(flagged_data)),
        "exposure": float(flagged_data['INRAMOUNT'].sum()) if not flagged_data.empty and 'INRAMOUNT' in flagged_data.columns else 0.0
    })

def build_consolidated_risk_table(df: pd.DataFrame, threshold_days: int, high_value_threshold: float, freq_threshold: int) -> list:
    if df.empty:
        return []
        
    df = df.copy()
    
    # Pre-clean dates & types
    if 'TXNDATE' in df.columns:
        df['TXNDATE'] = pd.to_datetime(df['TXNDATE'], errors='coerce')
        
    # Initialize flags
    f_hv = pd.Series(False, index=df.index)
    f_fatf = pd.Series(False, index=df.index)
    f_mult_op = pd.Series(False, index=df.index)
    f_high_freq = pd.Series(False, index=df.index)
    f_lrw = pd.Series(False, index=df.index)
    f_mc_contact = pd.Series(False, index=df.index)
    f_mc_trav = pd.Series(False, index=df.index)
    f_mc_mo = pd.Series(False, index=df.index)
    
    # 1. High Value
    if 'Equivalent USD Amount' in df.columns:
        f_hv = df['Equivalent USD Amount'] > high_value_threshold
        
    # 2. FATF OFAC
    if 'OFAC_FATF' in df.columns:
        f_fatf = df['OFAC_FATF'] != 'NOT FLAGGED'
        
    # 3. Multiple Operators same Beneficiary
    benef_col = 'BENEFICIARY'
    if 'Segment' in df.columns and benef_col in df.columns and 'CUSTOMERNAME' in df.columns:
        tour_op = df[df['Segment'] == 'TOUR OPERATOR']
        if not tour_op.empty:
            grp = tour_op.groupby(benef_col).agg(
                unique_ops=('CUSTOMERNAME', 'nunique'),
                txn_count=('CUSTOMERNAME', 'size')
            )
            suspicious_beneficiaries = grp[(grp['unique_ops'] >= 2) & (grp['txn_count'] >= 5)].index.tolist()
            f_mult_op = df[benef_col].isin(suspicious_beneficiaries) & (df['Segment'] == 'TOUR OPERATOR')
            
    # 4. High Frequency Remittances
    if 'Segment' in df.columns and benef_col in df.columns and 'CUSTOMERCODE' in df.columns:
        tour_op = df[df['Segment'] == 'TOUR OPERATOR']
        if not tour_op.empty:
            grp = tour_op.groupby(['CUSTOMERCODE', benef_col]).size().reset_index(name='txn_count')
            suspicious_pairs = grp[grp['txn_count'] > freq_threshold]
            if not suspicious_pairs.empty:
                keys = df[['CUSTOMERCODE', benef_col]].astype(str).agg(lambda x: '_'.join(x), axis=1)
                susp_keys = suspicious_pairs[['CUSTOMERCODE', benef_col]].astype(str).agg(lambda x: '_'.join(x), axis=1).tolist()
                f_high_freq = keys.isin(susp_keys) & (df['Segment'] == 'TOUR OPERATOR')
                
    # 5. Load-to-Refund Window
    instr_col = 'INSTRUMENTNO'
    type_col = 'LoadReload'
    prod_col = 'PRODUCT'
    txn_col = 'TXNTYPE'
    amt_col = 'INRAMOUNT'
    date_col = 'TXNDATE'
    if all(col in df.columns for col in [instr_col, type_col, prod_col, txn_col, amt_col, date_col]):
        d = df[df[prod_col].isin(['EC', 'FC'])].copy()
        if not d.empty:
            d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
            d[type_col] = d[type_col].astype(str).str.strip().str.upper()
            sub = d[(d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[date_col].notnull())].copy()
            sub['orig_idx'] = sub.index
            loads_df = sub[(sub[type_col].isin(['LOAD', 'RELOAD'])) & (sub[txn_col] == 'PS')]
            refunds_df = sub[sub[type_col] == 'REFUND']
            if not loads_df.empty and not refunds_df.empty:
                pairs = loads_df.merge(refunds_df[[instr_col, date_col, 'orig_idx']], on=instr_col, how='inner', suffixes=('_LOAD', '_REFUND'))
                pairs['WITHIN_DAYS'] = (pairs[f'{date_col}_REFUND'] - pairs[f'{date_col}_LOAD']).dt.days
                flagged_pairs = pairs[(pairs['WITHIN_DAYS'] >= 0) & (pairs['WITHIN_DAYS'] <= threshold_days)]
                flagged_indices = pd.concat([flagged_pairs['orig_idx_LOAD'], flagged_pairs['orig_idx_REFUND']]).unique()
                f_lrw.loc[flagged_indices] = True
                
    # 6. Multiple Cards Contact
    mob_col = 'MOBILENO'
    if all(col in df.columns for col in [instr_col, mob_col, prod_col, txn_col]):
        d = df[(df[prod_col].isin(['EC', 'FC'])) & (df[txn_col] == 'PS')].copy()
        d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
        d[mob_col] = d[mob_col].astype(str).str.strip().str.upper()
        sub = d[(d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[mob_col] != '') & (d[mob_col] != 'NAN')]
        if not sub.empty:
            grouped = sub.groupby(mob_col).agg(Distinct_Cards=(instr_col, 'nunique'))
            flagged_mobs = grouped[grouped['Distinct_Cards'] >= 3].index.tolist()
            f_mc_contact = df[mob_col].astype(str).str.strip().str.upper().isin(flagged_mobs) & (df[prod_col].isin(['EC', 'FC'])) & (df[txn_col] == 'PS')
            
    # 7. Multiple Cards Traveller
    pax_col = 'PAXNAME'
    if all(col in df.columns for col in [instr_col, pax_col, prod_col, txn_col]):
        d = df[(df[prod_col].isin(['EC', 'FC'])) & (df[txn_col] == 'PS')].copy()
        d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
        d[pax_col] = d[pax_col].astype(str).str.strip().str.upper()
        sub = d[(d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[pax_col] != '') & (d[pax_col] != 'NAN')]
        if not sub.empty:
            grouped = sub.groupby(pax_col).agg(Distinct_Cards=(instr_col, 'nunique'))
            flagged_paxs = grouped[grouped['Distinct_Cards'] >= 2].index.tolist()
            f_mc_trav = df[pax_col].astype(str).str.strip().str.upper().isin(flagged_paxs) & (df[prod_col].isin(['EC', 'FC'])) & (df[txn_col] == 'PS')
            
    # 8. Multi-Card Multi-Operator Use
    corp_col = 'CUSTOMERNAME'
    if all(col in df.columns for col in [instr_col, pax_col, corp_col, prod_col, txn_col]):
        d = df[(df[prod_col].isin(['EC', 'FC'])) & (df[txn_col] == 'PS')].copy()
        d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
        d[pax_col] = d[pax_col].astype(str).str.strip().str.upper()
        d[corp_col] = d[corp_col].astype(str).str.strip().str.upper()
        sub = d[(d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[pax_col] != '') & (d[pax_col] != 'NAN')]
        if not sub.empty:
            grouped = sub.groupby(pax_col).agg(
                Distinct_Operators=(corp_col, 'nunique'),
                Distinct_Cards=(instr_col, 'nunique')
            )
            flagged_paxs = grouped[(grouped['Distinct_Operators'] >= 2) & (grouped['Distinct_Cards'] >= 2)].index.tolist()
            f_mc_mo = df[pax_col].astype(str).str.strip().str.upper().isin(flagged_paxs) & (df[prod_col].isin(['EC', 'FC'])) & (df[txn_col] == 'PS')
            
    # Add rules count
    df['R1_HV'] = f_hv
    df['R2_FATF'] = f_fatf
    df['R3_MultOp'] = f_mult_op
    df['R4_HighFreq'] = f_high_freq
    df['R5_Lrw'] = f_lrw
    df['R6_McContact'] = f_mc_contact
    df['R7_McTrav'] = f_mc_trav
    df['R8_McMo'] = f_mc_mo
    
    df['Risk_Rule_Count'] = (
        f_hv.astype(int) + 
        f_fatf.astype(int) + 
        f_mult_op.astype(int) + 
        f_high_freq.astype(int) + 
        f_lrw.astype(int) + 
        f_mc_contact.astype(int) + 
        f_mc_trav.astype(int) + 
        f_mc_mo.astype(int)
    )
    
    # Map booleans to ✔ / ✘
    for r in ['R1_HV', 'R2_FATF', 'R3_MultOp', 'R4_HighFreq', 'R5_Lrw', 'R6_McContact', 'R7_McTrav', 'R8_McMo']:
        df[r] = df[r].map({True: '✔', False: '✘'})
        
    keep_cols = [
        'TXNDATE', 'CUSTOMERNAME', 'PAXNAME', 'PAXIDNO', 'LOCATION', 'INRAMOUNT', 'Equivalent USD Amount',
        'Risk_Rule_Count', 'R1_HV', 'R2_FATF', 'R3_MultOp', 'R4_HighFreq', 'R5_Lrw', 'R6_McContact', 'R7_McTrav', 'R8_McMo'
    ]
    keep_cols = [c for c in keep_cols if c in df.columns]
    res_df = df[keep_cols]
    return clean_for_json(res_df)
