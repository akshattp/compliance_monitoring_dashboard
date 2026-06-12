import pandas as pd


def _normalize_key(series: pd.Series) -> pd.Series:
    return series.fillna('').astype(str).str.strip().str.upper()


def mark_high_value(df: pd.DataFrame, threshold=10000) -> pd.Series:
    if 'Net Amt' not in df.columns:
        return pd.Series(False, index=df.index)
    return df['Net Amt'] > threshold


def mark_fatf_ofac(df: pd.DataFrame) -> pd.Series:
    if 'OFAC _ FATF' not in df.columns:
        return pd.Series(False, index=df.index)
    return df['OFAC _ FATF'].astype(str).str.contains(r'FATF|OFAC|FLAG|YES', case=False, na=False)


def mark_multiple_operators_same_beneficiary(df: pd.DataFrame) -> pd.Series:
    if 'Party Code' not in df.columns or 'Agent Name' not in df.columns:
        return pd.Series(False, index=df.index)
    beneficiary = _normalize_key(df['Party Code'])
    operator = _normalize_key(df['Agent Name'])
    risky_beneficiaries = operator.groupby(beneficiary).nunique()
    suspicious = risky_beneficiaries[risky_beneficiaries > 1].index
    return beneficiary.isin(suspicious)


def mark_high_frequency_beneficiary(df: pd.DataFrame, minimum_transactions=5) -> pd.Series:
    if 'Party Code' not in df.columns:
        return pd.Series(False, index=df.index)
    beneficiary = _normalize_key(df['Party Code'])
    counts = beneficiary.value_counts()
    suspicious = counts[counts >= minimum_transactions].index
    return beneficiary.isin(suspicious)


def mark_same_traveller_multiple_operators(df: pd.DataFrame) -> pd.Series:
    key_column = 'Passport' if 'Passport' in df.columns else 'Passenger Name'
    if key_column not in df.columns or 'Agent Name' not in df.columns:
        return pd.Series(False, index=df.index)
    traveller = _normalize_key(df[key_column])
    operator = _normalize_key(df['Agent Name'])
    multiples = operator.groupby(traveller).nunique()
    suspicious = multiples[multiples > 1].index
    return traveller.isin(suspicious)


def mark_same_traveller_multiple_beneficiaries(df: pd.DataFrame) -> pd.Series:
    key_column = 'Passport' if 'Passport' in df.columns else 'Passenger Name'
    if key_column not in df.columns or 'Party Code' not in df.columns:
        return pd.Series(False, index=df.index)
    traveller = _normalize_key(df[key_column])
    beneficiary = _normalize_key(df['Party Code'])
    multiples = beneficiary.groupby(traveller).nunique()
    suspicious = multiples[multiples > 1].index
    return traveller.isin(suspicious)


def mark_duplicate_cards_same_traveller(df: pd.DataFrame) -> pd.Series:
    key_column = 'Passport' if 'Passport' in df.columns else 'Passenger Name'
    if key_column not in df.columns:
        return pd.Series(False, index=df.index)
    traveller = _normalize_key(df[key_column])
    card_column = next((col for col in ['Card Number', 'Kit No', 'Doc Number', 'Branch name / Doc No.', 'Txn No'] if col in df.columns), None)
    if card_column is None:
        return pd.Series(False, index=df.index)
    card_id = _normalize_key(df[card_column])
    multiplicity = card_id.groupby(traveller).nunique()
    suspicious = multiplicity[multiplicity > 1].index
    return traveller.isin(suspicious)


def mark_reload_frequency(df: pd.DataFrame, minimum_reloads=3) -> pd.Series:
    if 'Benificiary Type Load or Reload' not in df.columns:
        return pd.Series(False, index=df.index)
    reload_flag = df['Benificiary Type Load or Reload'].astype(str).str.contains('RELOAD', case=False, na=False)
    if 'Party Code' in df.columns:
        groups = df.loc[reload_flag].groupby('Party Code').size()
        suspicious = groups[groups >= minimum_reloads].index
        return df['Party Code'].isin(suspicious) & reload_flag
    key_column = 'Passport' if 'Passport' in df.columns else 'Passenger Name'
    if key_column not in df.columns:
        return pd.Series(False, index=df.index)
    traveller = _normalize_key(df[key_column])
    groups = df.loc[reload_flag].groupby(traveller).size()
    suspicious = groups[groups >= minimum_reloads].index
    return traveller.isin(suspicious) & reload_flag


def mark_velocity_same_traveller_day(df: pd.DataFrame, minimum_transactions=3) -> pd.Series:
    key_column = 'Passport' if 'Passport' in df.columns else 'Passenger Name'
    if key_column not in df.columns or 'Date' not in df.columns:
        return pd.Series(False, index=df.index)
    traveller = _normalize_key(df[key_column])
    dated = df.assign(Traveller=traveller, TxnDate=df['Date'].dt.date)
    count_by_day = dated.groupby(['Traveller', 'TxnDate']).size().reset_index(name='TxnCount')
    suspicious = count_by_day[count_by_day['TxnCount'] >= minimum_transactions]
    if suspicious.empty:
        return pd.Series(False, index=df.index)
    merged = dated.merge(suspicious[['Traveller', 'TxnDate']], on=['Traveller', 'TxnDate'], how='left', indicator=True)
    return merged['_merge'] == 'both'


def mark_high_risk_corporate(df: pd.DataFrame) -> pd.Series:
    if 'Risk  Category' not in df.columns:
        return pd.Series(False, index=df.index)
    return df['Risk  Category'].astype(str).str.contains('HIGH|TRUST|NGO|SOCIETY', case=False, na=False)
