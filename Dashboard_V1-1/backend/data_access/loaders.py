import pandas as pd
from backend.utils.formatters import normalize_column_names, safe_string

NUMERIC_COLUMNS = [
    'Net Amt',
    'Eq. Amt',
    'EQV USD',
    'Fe Amt.',
    'Rate',
    'Cost Rate',
    'Profit',
    'Tax',
    'Charges',
    'Recd Amt',
    'Balance',
    'Comm Value',
    'Agt Comm.',
    'TCS',
]


def _harmonize_columns(columns):
    normalized = []
    for column in columns:
        text = str(column or '').strip()
        text = text.replace('\xa0', ' ')
        text = text.replace('\u200b', '')
        text = ' '.join(text.split())
        normalized.append(text)
    return normalized


def _expand_columns(df: pd.DataFrame) -> pd.DataFrame:
    if 'Branch Name' not in df.columns and 'Branch' in df.columns:
        df['Branch Name'] = df['Branch']
    if 'EQV USD' not in df.columns and 'Eq. Amt' in df.columns:
        df['EQV USD'] = df['Eq. Amt']
    if 'Purpose' not in df.columns and 'Txn Type' in df.columns:
        df['Purpose'] = pd.NA
    if 'Risk  Category' not in df.columns:
        df['Risk  Category'] = pd.NA
    if 'Currency' not in df.columns:
        df['Currency'] = pd.NA
    if 'OFAC _ FATF' not in df.columns:
        df['OFAC _ FATF'] = pd.NA
    return df


def load_transaction_data(uploaded_file=None, default_path=None):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
    elif default_path is not None:
        df = pd.read_excel(default_path, engine='openpyxl')
    else:
        raise FileNotFoundError('No transaction file provided.')

    df.columns = _harmonize_columns(df.columns)
    df = _expand_columns(df)

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    else:
        df['Date'] = pd.NaT

    df['Day'] = df['Date'].dt.day.fillna(0).astype(int)
    df['Week'] = df['Date'].dt.isocalendar().week.fillna(0).astype(int)
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    df['Year'] = df['Date'].dt.year.fillna(0).astype(int)
    df['Weekday'] = df['Date'].dt.day_name().fillna('Unknown')
    df['Corporate'] = safe_string(df['Corporate']) if 'Corporate' in df.columns else ''
    df['Purpose'] = safe_string(df['Purpose']) if 'Purpose' in df.columns else ''
    df['Txn Type'] = safe_string(df['Txn Type']).str.upper() if 'Txn Type' in df.columns else ''
    df['OFAC _ FATF'] = safe_string(df['OFAC _ FATF'])
    df['Branch Name'] = safe_string(df['Branch Name'])
    df['Agent Name'] = safe_string(df['Agent Name']) if 'Agent Name' in df.columns else ''

    return df