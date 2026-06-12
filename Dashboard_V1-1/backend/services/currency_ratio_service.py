import os
import io
import pandas as pd
import numpy as np

def load_currency_ratio_data(file_bytes=None, default_path=None, sheet_name='ImportFromExcel(164)') -> pd.DataFrame:
    df = None
    if file_bytes is not None:
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
    elif default_path is not None and os.path.exists(default_path):
        df = pd.read_excel(default_path, sheet_name=sheet_name)
    else:
        return pd.DataFrame()

    required_cols = ['LOCATION', 'RETAIL SALES', 'TOTAL BULK PURCHASE EXCLUDING FRANCHISEE PURCHASE']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        return pd.DataFrame()

    df['RETAIL SALES'] = pd.to_numeric(df['RETAIL SALES'], errors='coerce').fillna(0)
    df['TOTAL BULK PURCHASE EXCLUDING FRANCHISEE PURCHASE'] = pd.to_numeric(df['TOTAL BULK PURCHASE EXCLUDING FRANCHISEE PURCHASE'], errors='coerce').fillna(0)
    
    df['Retail Sales %'] = (df['RETAIL SALES'] / df['TOTAL BULK PURCHASE EXCLUDING FRANCHISEE PURCHASE']) * 100
    df['Retail Sales %'] = df['Retail Sales %'].fillna(0)
    df.loc[df['Retail Sales %'] == float('inf'), 'Retail Sales %'] = 100.0
    return df

def get_currency_ratio_kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            'total_retail': 0.0,
            'total_bulk': 0.0,
            'overall_ratio': 0.0,
            'exception_count': 0,
            'highest_row': None,
            'lowest_row': None,
            'exception_high': pd.DataFrame(),
            'exception_low': pd.DataFrame()
        }

    total_retail = df['RETAIL SALES'].sum()
    total_bulk = df['TOTAL BULK PURCHASE EXCLUDING FRANCHISEE PURCHASE'].sum()
    overall_ratio = (total_retail / total_bulk * 100) if total_bulk > 0 else 0

    valid_ratio_df = df[df['TOTAL BULK PURCHASE EXCLUDING FRANCHISEE PURCHASE'] > 0]
    
    # Store indices or row values as dicts/df
    highest_row = None
    if not valid_ratio_df.empty:
        h_idx = valid_ratio_df['Retail Sales %'].idxmax()
        highest_row = valid_ratio_df.loc[h_idx].to_dict()

    lowest_row = None
    if not valid_ratio_df.empty:
        l_idx = valid_ratio_df['Retail Sales %'].idxmin()
        lowest_row = valid_ratio_df.loc[l_idx].to_dict()

    exception_high = df[df['Retail Sales %'] > 100].copy()
    exception_low = df[(df['Retail Sales %'] < 25) & (df['TOTAL BULK PURCHASE EXCLUDING FRANCHISEE PURCHASE'] > 0)].copy()

    return {
        'total_retail': total_retail,
        'total_bulk': total_bulk,
        'overall_ratio': overall_ratio,
        'exception_count': len(exception_high) + len(exception_low),
        'highest_row': highest_row,
        'lowest_row': lowest_row,
        'exception_high': exception_high,
        'exception_low': exception_low
    }

def build_currency_ratio_table(df: pd.DataFrame, total_retail: float, total_bulk: float, overall_ratio: float) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    table_df = df[['LOCATION', 'RETAIL SALES', 'TOTAL BULK PURCHASE EXCLUDING FRANCHISEE PURCHASE', 'Retail Sales %']].copy()
    table_df.rename(columns={
        'RETAIL SALES': 'Retail Sales',
        'TOTAL BULK PURCHASE EXCLUDING FRANCHISEE PURCHASE': 'Bulk Purchase'
    }, inplace=True)
    
    table_df['Retail Contribution %'] = (table_df['Retail Sales'] / total_retail * 100).fillna(0) if total_retail > 0 else 0
    table_df['Bulk Contribution %'] = (table_df['Bulk Purchase'] / total_bulk * 100).fillna(0) if total_bulk > 0 else 0

    table_df['Retail Sales %'] = table_df['Retail Sales %'].round(2)
    table_df['Retail Contribution %'] = table_df['Retail Contribution %'].round(2)
    table_df['Bulk Contribution %'] = table_df['Bulk Contribution %'].round(2)
    table_df = table_df.sort_values('Retail Sales', ascending=False)
    
    return table_df
