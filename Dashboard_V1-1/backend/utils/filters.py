import pandas as pd


def get_filter_options(df: pd.DataFrame, columns):
    options = {}
    for column in columns:
        if column in df.columns:
            values = df[column].dropna().unique()
            options[column] = sorted(values, key=lambda x: str(x))
    return options


def normalize_default_filters(defaults, options):
    normalized = {}
    for column, value in defaults.items():
        if column not in options:
            continue
        if isinstance(value, (list, tuple, set)):
            matched = [item for item in value if item in options[column]]
            normalized[column] = matched or options[column]
        else:
            normalized[column] = value if value in options[column] else options[column]
    return normalized


def apply_filters(df: pd.DataFrame, filters, date_range=None):
    mask = pd.Series(True, index=df.index)

    for column, values in filters.items():
        if column in df.columns and values:
            mask &= df[column].isin(values)

    if date_range is not None and 'Date' in df.columns:
        start_date, end_date = date_range
        if start_date is not None and end_date is not None:
            mask &= (df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))

    return df[mask].copy()