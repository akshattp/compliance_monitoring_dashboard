import pandas as pd


def normalize_column_names(columns):
    normalized = []
    for column in columns:
        text = str(column or '').strip()
        text = text.replace('\xa0', ' ')
        text = text.replace('\u200b', '')
        text = ' '.join(text.split())
        normalized.append(text)
    return normalized


def format_indian_currency(value):
    if pd.isna(value):
        return '0'

    try:
        num = float(value)
    except (TypeError, ValueError):
        return '0'

    if num >= 10000000:
        return f'{num / 10000000:.2f} Cr'
    if num >= 100000:
        return f'{num / 100000:.2f} L'
    if num >= 1000:
        return f'{num / 1000:.2f} K'
    return f'{num:.2f}'


def human_readable_amount(value):
    return format_indian_currency(value)


def safe_string(series):
    return series.fillna('').astype(str).str.strip()


def safe_flag(value):
    return str(value).strip().upper() in ['YES', 'TRUE', 'Y', 'FLAGGED', 'FATF', 'OFAC']
