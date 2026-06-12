import time
import pandas as pd
from datetime import datetime

def safe_sorted_unique(series):
    """
    Safely sort unique values from a Series, handling mixed types and NaN.
    Filters out NaN/None, converts to string, and sorts.
    """
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
    """
    Detect high-value transactions (EQV USD > 25000).
    Also detect potential structuring (20000-24999).
    Returns: (high_value_df, structuring_df, summary_dict)
    """
    start = time.perf_counter()

    empty_summary = {
        'high_value_count': 0,
        'high_value_amount': 0,
        'structuring_count': 0,
        'structuring_amount': 0,
        'highest_transaction': 0,
        'high_value_exposure': 0,
    }

    if 'EQV USD' not in df.columns:
        return (pd.DataFrame(), pd.DataFrame(), empty_summary)

    df = df.copy()
    high_value = df[df['EQV USD'] > 25000]
    structuring = df[(df['EQV USD'] >= 20000) & (df['EQV USD'] <= 25000)]

    summary = {
        'high_value_count': len(high_value),
        'high_value_amount': high_value['EQV USD'].sum() if not high_value.empty else 0,
        'high_value_exposure': high_value['Net Amt'].sum() if not high_value.empty else 0,
        'structuring_count': len(structuring),
        'structuring_amount': structuring['EQV USD'].sum() if not structuring.empty else 0,
        'highest_transaction': high_value['EQV USD'].max() if not high_value.empty else 0,
    }
    
    print(f"Rule 1 Time: {round(time.perf_counter() - start, 2)}s")
    return (high_value, structuring, summary)

def detect_fatf_ofac(df: pd.DataFrame, ofac_file=None):
    """Detect FATF/OFAC flagged transactions."""
    empty_summary = {
        'flagged_count': 0,
        'flagged_amount': 0,
        'affected_branches': 0,
        'affected_countries': 0,
    }

    if not ofac_file:
        return (pd.DataFrame(), empty_summary)

    try:
        # ofac_file can be file path or bytes/file-like object
        if isinstance(ofac_file, bytes):
            import io
            ofac_df = pd.read_excel(io.BytesIO(ofac_file), sheet_name='UPDATED FILE')
        else:
            ofac_df = pd.read_excel(ofac_file, sheet_name='UPDATED FILE')
            
        ofac_mapping = ofac_df[['COUNTRY', 'Segment']].copy()
        ofac_mapping.rename(columns={'Segment': 'OFAC_FATF_Segment'}, inplace=True)
        ofac_mapping['COUNTRY'] = ofac_mapping['COUNTRY'].astype(str).str.strip().str.upper()
        ofac_mapping.drop_duplicates(subset=['COUNTRY'], inplace=True)

        work_df = df.copy()
        if 'Visiting Country' in work_df.columns:
            work_df['Visiting Country_upper'] = work_df['Visiting Country'].astype(str).str.strip().str.upper()
            enriched = pd.merge(work_df, ofac_mapping, left_on='Visiting Country_upper', right_on='COUNTRY', how='left')
            enriched['FATF / OFAC Flag'] = enriched['OFAC_FATF_Segment'].notna() & (enriched['OFAC_FATF_Segment'] != 'NOT FLAGGED')
            # For compatibility with filters, also add 'OFAC _ FATF'
            enriched['OFAC _ FATF'] = enriched['OFAC_FATF_Segment'].fillna('NOT FLAGGED')
            flagged = enriched[enriched['FATF / OFAC Flag']]
        else:
            flagged = pd.DataFrame()
    except Exception as e:
        return (pd.DataFrame(), {**empty_summary, 'error': str(e)})
    
    summary = {
        'flagged_count': len(flagged),
        'flagged_amount': flagged['Net Amt'].sum() if not flagged.empty else 0,
        'affected_branches': flagged['Branch Name'].nunique() if 'Branch Name' in flagged.columns else 0,
        'affected_countries': flagged['Visiting Country'].nunique() if 'Visiting Country' in flagged.columns else 0,
    }
    return (flagged, summary)

def detect_multiple_operators_same_beneficiary(df: pd.DataFrame):
    """
    Detect multiple tour operators sending to the same beneficiary.
    Filters for Segments == 'TOUR OPERATOR'.
    """
    start = time.perf_counter()

    empty_summary = {
        'suspicious_beneficiary_count': 0,
        'flagged_txn_count': 0,
        'flagged_amount': 0,
    }

    benef_col = 'Beneficiary Type Load or Reload'
    if 'Segments' not in df.columns or benef_col not in df.columns or 'Party Code' not in df.columns or 'Corporate' not in df.columns:
        return (pd.DataFrame(), empty_summary)

    df = df.copy()
    tour_op = df[df['Segments'] == 'TOUR OPERATOR'].copy()

    if tour_op.empty:
        return (pd.DataFrame(), empty_summary)

    # Group by beneficiary and count unique operators + transaction count
    grp = tour_op.groupby(benef_col).agg(
        unique_operators=('Corporate', 'nunique'),
        txn_count=('Corporate', 'size'),
        total_amount=('Net Amt', 'sum'),
    ).reset_index()

    # Flag where multiple operators and >=5 transactions
    suspicious_beneficiaries = grp[(grp['unique_operators'] >= 2) & (grp['txn_count'] >= 5)][benef_col].tolist()
    flagged = tour_op[tour_op[benef_col].isin(suspicious_beneficiaries)]

    summary = {
        'suspicious_beneficiary_count': len(suspicious_beneficiaries),
        'flagged_txn_count': len(flagged),
        'flagged_amount': flagged['Net Amt'].sum() if not flagged.empty else 0,
    }
    
    result = (flagged, summary)
    print(f"Rule 3 Time: {round(time.perf_counter() - start, 2)}s")
    return result

def detect_high_frequency_remittances(df: pd.DataFrame):
    """
    Detect same operator sending >=5 remittances to same beneficiary.
    Filters for Segments == 'TOUR OPERATOR'.
    """
    start = time.perf_counter()

    empty_summary = {
        'repeat_pair_count': 0,
        'flagged_txn_count': 0,
        'flagged_amount': 0,
    }

    benef_col = 'Beneficiary Type Load or Reload'
    if 'Segments' not in df.columns or benef_col not in df.columns or 'Party Code' not in df.columns or 'Corporate' not in df.columns:
        return (pd.DataFrame(), empty_summary)

    df = df.copy()
    tour_op = df[df['Segments'] == 'TOUR OPERATOR'].copy()

    if tour_op.empty:
        return (pd.DataFrame(), empty_summary)

    # Group by operator + beneficiary
    grp = tour_op.groupby(['Party Code', benef_col]).agg(
        txn_count=('Party Code', 'size'),
        total_amount=('Net Amt', 'sum'),
    ).reset_index()

    # Flag where transaction count >= 5
    # Note: original code checks `grp['txn_count'] > 5` inside condition, but task summary mentions >=5. We stick strictly to original `grp['txn_count'] > 5`.
    # Wait, let's look at original code: `grp[grp['txn_count'] > 5]` (line 553). We will maintain the exact logic.
    suspicious_pairs = grp[grp['txn_count'] > 5][['Party Code', benef_col]]
    if suspicious_pairs.empty:
        return (pd.DataFrame(), empty_summary)

    # Filter flagged transactions
    flagged = tour_op.merge(
        suspicious_pairs,
        on=['Party Code', benef_col],
        how='inner'
    )

    summary = {
        'repeat_pair_count': len(suspicious_pairs),
        'flagged_txn_count': len(flagged),
        'flagged_amount': flagged['Net Amt'].sum() if not flagged.empty else 0,
    }
    
    result = (flagged, summary)
    print(f"Rule 4 Time: {round(time.perf_counter() - start, 2)}s")
    return result

def detect_configurable_load_refund_window(df: pd.DataFrame, threshold_days: int):
    start = time.perf_counter()
    instr_col, type_col = 'INSTRUMENTNO', 'LoadReload'
    prod_col = 'Product'
    txn_col = 'Txn Type'
    amt_col = 'Net Amt'
    date_col = 'Date'

    empty_summary = {"count": 0, "events": 0, "same_day_refunds": 0, "avg_delay": 0, "min_delay": 0, "max_delay": 0, "exposure": 0}

    core_cols = [instr_col, type_col, prod_col, date_col, amt_col, txn_col]
    if not all(col in df.columns for col in core_cols):
        return (pd.DataFrame(), empty_summary)

    d = df[df[prod_col].isin(['EC', 'FC'])].copy()
    if d.empty:
        return (pd.DataFrame(), empty_summary)

    d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
    d[type_col] = d[type_col].astype(str).str.strip().str.upper()
    d[date_col] = pd.to_datetime(d[date_col], errors='coerce')

    sub = d[(d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[date_col].notnull())].copy()
    if sub.empty:
        return (pd.DataFrame(), empty_summary)

    # Define common contextual columns to carry through
    all_context_cols = [
        'Branch Name', 'Corporate', 'Passenger Name', 'MOBILENO', 'EMAILID',
        'Product', 'Currency', 'Purpose', 'Visiting Country', 'Risk  Category',
        'Agent Name', 'Segments', 'Party Code', 'Doc Number', 'Issuer'
    ]
    context_cols_present = [col for col in all_context_cols if col in sub.columns]

    # Split Load (PS) and Refund datasets
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
        return (pd.DataFrame(), empty_summary)

    # Merge loads and refunds
    pairs = loads_df.merge(refunds_df, on=instr_col, how='inner')

    # Calculate delay and filter out retroactive matches
    pairs['WITHIN_DAYS'] = (pairs['REFUND_DATE'] - pairs['LOAD_DATE']).dt.days
    valid_pairs = pairs[pairs['WITHIN_DAYS'] >= 0].copy()

    # Apply dynamic threshold
    flagged_output = valid_pairs[valid_pairs['WITHIN_DAYS'] <= threshold_days].copy()

    if flagged_output.empty:
        return (pd.DataFrame(), empty_summary)

    # Column Consolidation
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

    # KPI Calculations
    total_flagged_cards = flagged_output['INSTRUMENTNO'].nunique()
    total_flagged_events = len(flagged_output)
    same_day_refunds = len(flagged_output[flagged_output['WITHIN_DAYS'] == 0])
    avg_delay = flagged_output['WITHIN_DAYS'].mean() if total_flagged_events > 0 else 0
    min_delay = flagged_output['WITHIN_DAYS'].min() if total_flagged_events > 0 else 0
    max_delay = flagged_output['WITHIN_DAYS'].max() if total_flagged_events > 0 else 0
    exposure_amount = flagged_output['LOAD_AMOUNT'].sum() + flagged_output['REFUND_AMOUNT'].sum()

    summary = {
        "count": total_flagged_cards,
        "events": total_flagged_events,
        "same_day_refunds": same_day_refunds,
        "avg_delay": avg_delay,
        "min_delay": min_delay,
        "max_delay": max_delay,
        "exposure": exposure_amount
    }
    
    print(f"Rule: Configurable Load/Refund Window Monitoring Time: {round(time.perf_counter() - start, 2)}s")
    return (flagged_output, summary)

def detect_multiple_cards_contact(df: pd.DataFrame):
    start = time.perf_counter()
    instr_col, mob_col = 'INSTRUMENTNO', 'MOBILENO'
    prod_col, txn_col = 'Product', 'Txn Type'
    if any(c not in df.columns for c in [instr_col, mob_col, prod_col, txn_col]):
        return (pd.DataFrame(), {"count": 0, "total_cards": 0, "max_cards": 0, "exposure": 0})

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
    
    print(f"Rule: Multiple Cards Contact Time: {round(time.perf_counter() - start, 2)}s")
    return (flagged, {
        "count": len(flagged), 
        "total_cards": flagged_data[instr_col].nunique() if not flagged.empty else 0, 
        "max_cards": flagged['Card_Count'].max() if not flagged.empty else 0, 
        "exposure": flagged_data['Net Amt'].sum() if not flagged_data.empty else 0
    })

def detect_multiple_cards_traveller(df: pd.DataFrame):
    start = time.perf_counter()
    instr_col, pax_col = 'INSTRUMENTNO', 'Passenger Name'
    prod_col, txn_col = 'Product', 'Txn Type'
    if any(c not in df.columns for c in [instr_col, pax_col, prod_col, txn_col]):
        return (pd.DataFrame(), {"count": 0, "total_cards": 0, "max_cards": 0, "exposure": 0})

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
    
    print(f"Rule: Multiple Cards Traveller Time: {round(time.perf_counter() - start, 2)}s")
    return (flagged, {
        "count": len(flagged), 
        "total_cards": flagged_data[instr_col].nunique() if not flagged.empty else 0, 
        "max_cards": flagged['Card_Count'].max() if not flagged.empty else 0,
        "exposure": flagged_data['Net Amt'].sum() if not flagged_data.empty else 0
    })

def detect_multiple_cards_multi_operator(df: pd.DataFrame):
    start = time.perf_counter()
    instr_col, pax_col, corp_col = 'INSTRUMENTNO', 'Passenger Name', 'Corporate'
    prod_col, txn_col = 'Product', 'Txn Type'
    if any(c not in df.columns for c in [instr_col, pax_col, corp_col, prod_col, txn_col]):
        return (pd.DataFrame(), {"count": 0, "total_operators": 0, "total_cards": 0, "max_operators": 0, "exposure": 0})

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
    
    print(f"Rule: Multi-Card Multi-Operator Time: {round(time.perf_counter() - start, 2)}s")
    return (flagged, {
        "count": len(flagged), 
        "total_operators": flagged_data[corp_col].nunique() if not flagged.empty else 0, 
        "total_cards": flagged_data[instr_col].nunique() if not flagged.empty else 0, 
        "max_operators": flagged['Operator_Count'].max() if not flagged.empty else 0, 
        "exposure": flagged_data['Net Amt'].sum() if not flagged_data.empty else 0
    })
