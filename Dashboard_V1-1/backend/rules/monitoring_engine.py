import pandas as pd

# --- Custom Rule Functions ---
def rule_high_value(df: pd.DataFrame) -> pd.Series:
    # Business requirement: use 'EQV USD' column and flag EQV USD > 25000
    if 'EQV USD' not in df.columns:
        return pd.Series(False, index=df.index)
    return df['EQV USD'] > 25000

def rule_fatf_ofac(df: pd.DataFrame) -> pd.Series:
    if 'OFAC _ FATF' not in df.columns:
        return pd.Series(False, index=df.index)
    return df['OFAC _ FATF'].astype(str).str.contains(r'FATF|OFAC|FLAG|YES', case=False, na=False)

def rule_multiple_operators_same_beneficiary(df: pd.DataFrame) -> pd.Series:
    # Business requirement:
    # - consider only rows where Segments == 'TOUR OPERATOR'
    # - use 'Beneficiary Type Load or Reload' as the beneficiary identifier
    # - within the same month window, flag beneficiary+window where multiple operators > 5
    benef_col = 'Beneficiary Type Load or Reload'
    if 'Segments' not in df.columns or benef_col not in df.columns or 'Party Code' not in df.columns or 'Date' not in df.columns:
        return pd.Series(False, index=df.index)

    d = df.copy()
    d['Segments_up'] = d['Segments'].astype(str).str.upper()
    mask = d['Segments_up'] == 'TOUR OPERATOR'
    if not mask.any():
        return pd.Series(False, index=df.index)

    d.loc[:, 'Date'] = pd.to_datetime(d['Date'], errors='coerce')
    d.loc[:, 'window'] = d['Date'].dt.to_period('M')

    sub = d.loc[mask, :].copy()
    # Group by window + beneficiary
    grp = sub.groupby(['window', benef_col]).agg(unique_ops=('Party Code', 'nunique'))
    # Identify keys meeting the condition
    suspicious_keys = set(grp[grp['unique_ops'] > 5].index.tolist())

    # Map back to boolean series for original df
    keys = list(zip(d['window'], d[benef_col]))
    flags = [k in suspicious_keys for k in keys]
    return pd.Series(flags, index=df.index) & mask

def rule_high_frequency_remit_to_beneficiary(df: pd.DataFrame) -> pd.Series:
    # Business requirement:
    # - consider only rows where Segments == 'TOUR OPERATOR'
    # - use 'Beneficiary Type Load or Reload' as the beneficiary identifier
    # - within the same month window, flag rows where same operator (Party Code) -> beneficiary transaction count > 5
    benef_col = 'Beneficiary Type Load or Reload'
    if 'Segments' not in df.columns or benef_col not in df.columns or 'Party Code' not in df.columns or 'Date' not in df.columns:
        return pd.Series(False, index=df.index)

    d = df.copy()
    d['Segments_up'] = d['Segments'].astype(str).str.upper()
    mask = d['Segments_up'] == 'TOUR OPERATOR'
    if not mask.any():
        return pd.Series(False, index=df.index)

    d.loc[:, 'Date'] = pd.to_datetime(d['Date'], errors='coerce')
    d.loc[:, 'window'] = d['Date'].dt.to_period('M')

    sub = d.loc[mask, :].copy()
    counts = sub.groupby(['window', benef_col, 'Party Code']).size()
    suspicious_keys = set([k for k, v in counts.items() if v > 5])

    keys = list(zip(d['window'], d[benef_col], d['Party Code']))
    flags = [k in suspicious_keys for k in keys]
    return pd.Series(flags, index=df.index) & mask

def rule_same_traveller_multiple_operators(df: pd.DataFrame) -> pd.Series:
    # Vectorized: Same traveller details used by multiple operators within the same month
    key_column = 'Passenger Name' if 'Passenger Name' in df.columns else None
    if key_column is None or 'Agent Name' not in df.columns or 'Date' not in df.columns:
        return pd.Series(False, index=df.index)
    d = df.copy()
    d['Date'] = pd.to_datetime(d['Date'], errors='coerce')
    d['window'] = d['Date'].dt.to_period('M')
    ops_per_trav = d.groupby(['window', key_column])['Agent Name'].nunique()
    key = list(zip(d['window'], d[key_column]))
    ops_counts = [ops_per_trav.get(k, 0) for k in key]
    return pd.Series([c > 1 for c in ops_counts], index=df.index)

def rule_same_traveller_multiple_beneficiaries(df: pd.DataFrame) -> pd.Series:
    # Vectorized: More than three unique beneficiaries linked to the same traveller within the same month for the same operator (Segments)
    key_column = 'Passenger Name' if 'Passenger Name' in df.columns else None
    if key_column is None or 'Party Code' not in df.columns or 'Segments' not in df.columns or 'Date' not in df.columns:
        return pd.Series(False, index=df.index)
    d = df.copy()
    d['Date'] = pd.to_datetime(d['Date'], errors='coerce')
    d['window'] = d['Date'].dt.to_period('M')
    ben_counts = d.groupby(['window', key_column, 'Segments'])['Party Code'].nunique()
    key = list(zip(d['window'], d[key_column], d['Segments']))
    cnts = [ben_counts.get(k, 0) for k in key]
    return pd.Series([c > 3 for c in cnts], index=df.index)

# Default window for engine-level flagging for configurable load-to-refund rule
ENGINE_DEFAULT_WINDOW_DAYS = 30

def rule_configurable_load_refund_window(df: pd.DataFrame) -> pd.Series:
    instr_col = 'INSTRUMENTNO'
    type_col = 'LoadReload'
    prod_col = 'Product'
    txn_col = 'Txn Type'
    date_col = 'Date'
    if any(c not in df.columns for c in [instr_col, type_col, prod_col, date_col]):
        return pd.Series(False, index=df.index)
    
    d = df.copy()
    d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
    d[type_col] = d[type_col].astype(str).str.strip().str.upper()
    d[date_col] = pd.to_datetime(d[date_col], errors='coerce')
    
    # Mandatory Card Monitoring Pre-filters
    filter_mask = (d[prod_col].isin(['EC', 'FC']))
    mask_data = (d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[date_col].notnull())
    mask_valid = filter_mask & mask_data
    
    if not mask_valid.any():
        return pd.Series(False, index=df.index)
    
    sub = d[mask_valid].copy()
    sub['orig_idx'] = sub.index

    # Step 1 & 2: Create Load (PS) and Refund datasets
    loads_df = sub[(sub[type_col].isin(['LOAD', 'RELOAD'])) & (sub[txn_col] == 'PS')]
    refunds_df = sub[sub[type_col] == 'REFUND']
    
    if loads_df.empty or refunds_df.empty:
        return pd.Series(False, index=df.index)

    # Step 3: Match using standard merge (Inner Join on INSTRUMENTNO)
    pairs = loads_df.merge(
        refunds_df[[instr_col, date_col, 'orig_idx']], 
        on=instr_col, 
        how='inner', 
        suffixes=('_LOAD', '_REFUND')
    )

    # Step 4 & 5: Calculate interval and filter out refunds before loads
    pairs['WITHIN_DAYS'] = (pairs[f'{date_col}_REFUND'] - pairs[f'{date_col}_LOAD']).dt.days
    
    # Step 6: Apply AML Threshold (Cumulative 0 to 30 days for engine default)
    flagged_pairs = pairs[(pairs['WITHIN_DAYS'] >= 0) & (pairs['WITHIN_DAYS'] <= ENGINE_DEFAULT_WINDOW_DAYS)]

    # Map flagged pairs back to original transaction indices
    flagged_indices = pd.concat([flagged_pairs['orig_idx_LOAD'], flagged_pairs['orig_idx_REFUND']]).unique()
    
    final_flags = pd.Series(False, index=df.index)
    final_flags.loc[flagged_indices] = True

    return final_flags & mask_data

def rule_multiple_cards_contact(df: pd.DataFrame) -> pd.Series:
    instr_col = 'INSTRUMENTNO'
    mob_col = 'MOBILENO'
    prod_col, txn_col = 'Product', 'Txn Type'
    if any(c not in df.columns for c in [instr_col, mob_col, prod_col, txn_col]):
        return pd.Series(False, index=df.index)
        
    d = df.copy()
    d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
    d[mob_col] = d[mob_col].astype(str).str.strip().str.upper()
    
    # Mandatory Card Monitoring Pre-filters
    filter_mask = (d[prod_col].isin(['EC', 'FC'])) & (d[txn_col] == 'PS')
    mask_data = (d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[mob_col] != '') & (d[mob_col] != 'NAN')
    mask_valid = filter_mask & mask_data
    
    if not mask_valid.any():
        return pd.Series(False, index=df.index)
        
    card_counts = d[mask_valid].groupby(mob_col)[instr_col].nunique()
    suspicious_mobs = set(card_counts[card_counts >= 3].index)
    return d[mob_col].isin(suspicious_mobs) & mask_valid

def rule_multiple_cards_traveller(df: pd.DataFrame) -> pd.Series:
    instr_col = 'INSTRUMENTNO'
    pax_col = 'Passenger Name'
    prod_col, txn_col = 'Product', 'Txn Type'
    if any(c not in df.columns for c in [instr_col, pax_col, prod_col, txn_col]):
        return pd.Series(False, index=df.index)
        
    d = df.copy()
    d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
    d[pax_col] = d[pax_col].astype(str).str.strip().str.upper()
    
    # Mandatory Card Monitoring Pre-filters
    filter_mask = (d[prod_col].isin(['EC', 'FC'])) & (d[txn_col] == 'PS')
    mask_data = (d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[pax_col] != '') & (d[pax_col] != 'NAN')
    mask_valid = filter_mask & mask_data
    
    if not mask_valid.any():
        return pd.Series(False, index=df.index)
        
    card_counts = d[mask_valid].groupby(pax_col)[instr_col].nunique()
    suspicious_paxs = set(card_counts[card_counts >= 2].index)
    return d[pax_col].isin(suspicious_paxs) & mask_valid

def rule_multiple_cards_multi_operator(df: pd.DataFrame) -> pd.Series:
    instr_col = 'INSTRUMENTNO'
    pax_col = 'Passenger Name'
    corp_col = 'Corporate'
    prod_col, txn_col = 'Product', 'Txn Type'
    if any(c not in df.columns for c in [instr_col, pax_col, corp_col, prod_col, txn_col]):
        return pd.Series(False, index=df.index)
        
    d = df.copy()
    d[instr_col] = d[instr_col].astype(str).str.strip().str.upper()
    d[pax_col] = d[pax_col].astype(str).str.strip().str.upper()
    d[corp_col] = d[corp_col].astype(str).str.strip().str.upper()
    
    # Mandatory Card Monitoring Pre-filters
    filter_mask = (d[prod_col].isin(['EC', 'FC'])) & (d[txn_col] == 'PS')
    mask_data = (d[instr_col] != '') & (d[instr_col] != 'NAN') & (d[pax_col] != '') & (d[pax_col] != 'NAN')
    mask_valid = filter_mask & mask_data
    
    if not mask_valid.any():
        return pd.Series(False, index=df.index)
        
    counts = d[mask_valid].groupby(pax_col).agg(card_count=(instr_col, 'nunique'), operator_count=(corp_col, 'nunique'))
    suspicious_paxs = set(counts[(counts['card_count'] >= 2) & (counts['operator_count'] >= 2)].index)
    return d[pax_col].isin(suspicious_paxs) & mask_valid

RISK_RULES = [
    ('High Value Transaction', rule_high_value, 2),
    ('FATF / OFAC', rule_fatf_ofac, 3),
    ('Multiple Tour Operators/Remitters to Same Beneficiary', rule_multiple_operators_same_beneficiary, 2),
    ('High-Frequency Remittances to a Single Beneficiary by One Tour Operator/Remmiter', rule_high_frequency_remit_to_beneficiary, 2),
    ('Configurable Load-to-Refund Window', rule_configurable_load_refund_window, 2),
    ('Multiple Cards Linked to Same Contact Information', rule_multiple_cards_contact, 2),
    ('Multiple Cards Linked to Same Traveller Name', rule_multiple_cards_traveller, 2),
    ('Multiple Cards Used by Same Traveller Across Different Operators', rule_multiple_cards_multi_operator, 2),
]


def build_transaction_risk_profile(df: pd.DataFrame):
    result = df.copy()
    for rule_name, rule_fn, _ in RISK_RULES:
        result[rule_name] = rule_fn(result)

    result['Risk_Rule_Count'] = result[[rule_name for rule_name, _, _ in RISK_RULES]].sum(axis=1)
    result['Any_Risk_Flag'] = result['Risk_Rule_Count'] > 0
    result['Risk Score'] = sum(weight * result[rule_name].astype(int) for rule_name, _, weight in RISK_RULES)
    return result, [rule_name for rule_name, _, _ in RISK_RULES]


def get_risk_summary(df: pd.DataFrame, risk_flags):
    summary_rows = []
    total_cases = len(df)
    total_amount = df['Net Amt'].sum(min_count=1) if 'Net Amt' in df.columns else 0
    for flag in risk_flags:
        if flag not in df.columns:
            continue
        flagged = df[df[flag]]
        triggered_cases = len(flagged)
        triggered_amount = float(flagged['Net Amt'].sum()) if 'Net Amt' in flagged else 0
        triggered_cases_pct = (triggered_cases / total_cases * 100) if total_cases > 0 else 0
        triggered_amount_pct = (triggered_amount / total_amount * 100) if total_amount > 0 else 0
        summary_rows.append({
            'Rule': flag,
            'Triggered Cases': triggered_cases,
            'Triggered Amount': triggered_amount,
            'Triggered Cases%': triggered_cases_pct,
            'Triggered Amount %': triggered_amount_pct,
        })
    return pd.DataFrame(summary_rows)


def get_rule_details():
    # Return concise metadata for the active rule set. Keep descriptions aligned with compliance definitions.
    return [
        {'rule': 'High Value Transaction', 'description': 'Transaction EQV USD exceeds 25,000 USD.', 'severity': 2},
        {'rule': 'FATF / OFAC', 'description': 'Transaction flagged for FATF/OFAC exposure.', 'severity': 3},
        {'rule': 'Multiple Tour Operators/Remitters to Same Beneficiary', 'description': 'Multiple operators remit to the same beneficiary within the month (>=5 txns).', 'severity': 2},
        {'rule': 'High-Frequency Remittances to a Single Beneficiary by One Tour Operator/Remmiter', 'description': 'Single operator sends >5 remittances to the same beneficiary within the month.', 'severity': 2},
        {'rule': 'Configurable Load-to-Refund Window', 'description': f'Identify cards with load/reload and refund within {ENGINE_DEFAULT_WINDOW_DAYS} days (configurable in UI).', 'severity': 2},
        {'rule': 'Multiple Cards Linked to Same Contact Information', 'description': 'Mobile numbers associated with >=3 distinct card instruments.', 'severity': 2},
        {'rule': 'Multiple Cards Linked to Same Traveller Name', 'description': 'Travellers holding >=2 distinct card instruments.', 'severity': 2},
        {'rule': 'Multiple Cards Used by Same Traveller Across Different Operators', 'description': 'Travellers using >=2 cards across >=2 different operators.', 'severity': 2},
    ]