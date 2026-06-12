import pandas as pd

from backend.rules.monitoring_engine import get_risk_summary


def _choose_amount_column(df: pd.DataFrame):
    for col in ('Net Amt', 'EQV USD', 'Eq. Amt'):
        if col in df.columns:
            return col
    return None


def build_all_summaries(df: pd.DataFrame, risk_flags=None):
    """Build and return a dict of precomputed summary tables for the dashboard.

    This is intentionally conservative: it only computes common aggregations used
    across pages and relies on available columns. It doesn't change business logic.
    """
    summaries = {}
    amount_col = _choose_amount_column(df)

    # Branch summary
    if 'Branch Name' in df.columns:
        if amount_col:
            branch = df.groupby('Branch Name').agg(Transactions=('Branch Name', 'count'), Amount=(amount_col, 'sum')).reset_index()
        else:
            branch = df.groupby('Branch Name').size().reset_index(name='Transactions')
        summaries['branch_summary'] = branch

    # Corporate summary
    if 'Corporate' in df.columns:
        if amount_col:
            corp = df.groupby('Corporate').agg(Transactions=('Corporate', 'count'), Amount=(amount_col, 'sum')).reset_index()
        else:
            corp = df.groupby('Corporate').size().reset_index(name='Transactions')
        summaries['corporate_summary'] = corp

    # Daily summary
    if 'Date' in df.columns:
        daily = df.dropna(subset=['Date']).groupby(df['Date'].dt.date).agg(Transactions=('Date', 'count'))
        if amount_col:
            daily['Amount'] = df.dropna(subset=['Date']).groupby(df['Date'].dt.date)[amount_col].sum()
        summaries['daily_summary'] = daily.reset_index().rename(columns={'Date': 'Day'})

    # Weekly summary
    if 'Year' in df.columns and 'Week' in df.columns:
        weekly = df.groupby(['Year', 'Week']).agg(Transactions=('Date', 'count'))
        if amount_col:
            weekly['Amount'] = df.groupby(['Year', 'Week'])[amount_col].sum()
        summaries['weekly_summary'] = weekly.reset_index()

    # Transaction counts / concentration by Party Code or Agent
    if 'Party Code' in df.columns:
        top_ben = df.groupby('Party Code').agg(Transactions=('Party Code', 'count'))
        summaries['party_counts'] = top_ben.reset_index().sort_values('Transactions', ascending=False)

    if 'Agent Name' in df.columns:
        top_agents = df.groupby('Agent Name').agg(Transactions=('Agent Name', 'count'))
        summaries['agent_counts'] = top_agents.reset_index().sort_values('Transactions', ascending=False)

    # AML risk summary using the monitoring engine helper (preserves existing logic)
    try:
        if risk_flags is None:
            risk_flags = []
        aml_summary = get_risk_summary(df, risk_flags)
        summaries['aml_risk_summary'] = aml_summary
    except Exception:
        summaries['aml_risk_summary'] = pd.DataFrame()

    return summaries


def get_precomputed(summaries: dict, key: str):
    return summaries.get(key) if summaries else None
