import pandas as pd

from .filters import (
    get_filter_options,
    normalize_default_filters,
    apply_filters
)
from .formatters import (
    normalize_column_names,
    format_indian_currency,
    human_readable_amount,
    safe_string,
    safe_flag
)

def detect_fatf_records(df: pd.DataFrame) -> pd.DataFrame:
    if 'FATF / OFAC Flag' in df.columns:
        return df[df['FATF / OFAC Flag']].copy()
    return df.iloc[0:0].copy()
