import sys
from pathlib import Path

# Ensure parent directory is on sys.path so package imports resolve when running from package folder
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.data_loader import load_transaction_data
from rules import build_transaction_risk_profile, get_risk_summary
import pandas as pd

INPUT = 'APRIL TRANSACTION REJESTERED REPORT.xlsx'


def overall_summary(df: pd.DataFrame) -> str:
    total_txn = len(df)
    total_amt = float(df['EQV USD'].sum()) if 'EQV USD' in df.columns else float(df['Net Amt'].sum())
    date_min = df['Date'].min()
    date_max = df['Date'].max()
    html = f"""
    <h1>Overall Transaction Summary (Preview)</h1>
    <ul>
      <li>Total Transactions: {total_txn}</li>
      <li>Total Amount (EQV USD): {total_amt:,.2f}</li>
      <li>Date Range: {date_min.date() if pd.notna(date_min) else 'N/A'} to {date_max.date() if pd.notna(date_max) else 'N/A'}</li>
    </ul>
    """
    return html


def transaction_monitoring_preview(risk_df, risk_flags) -> str:
    summary_df = get_risk_summary(risk_df, risk_flags)
    html = '<h1>Transaction Monitoring - Risk Summary</h1>'
    html += summary_df.to_html(index=False)
    return html


if __name__ == '__main__':
    print('Loading data from', INPUT)
    df = load_transaction_data(default_path=INPUT)
    print('Building risk profile...')
    risk_df, risk_flags = build_transaction_risk_profile(df)

    print('Generating overall summary...')
    overall_html = overall_summary(df)
    with open('preview_overall_summary.html', 'w', encoding='utf-8') as f:
        f.write(overall_html)

    print('Generating transaction monitoring preview...')
    tm_html = transaction_monitoring_preview(risk_df, risk_flags)
    with open('preview_transaction_monitoring.html', 'w', encoding='utf-8') as f:
        f.write(tm_html)

    print('Preview files created: preview_overall_summary.html, preview_transaction_monitoring.html')
