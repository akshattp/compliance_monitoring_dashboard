import streamlit as st
from frontend.ui_helpers.ui import human_readable_amount, render_page_header, render_kpi_grid, render_table_with_options
from backend.services.simple_pages_service import get_dormant_account_data

def render_dormant_account_page(filtered_df, risk_df=None, risk_flags=None):
    render_page_header('Dormant Account', 'Detect potential dormant account transactions and zero-balance activity.', df=filtered_df, download_key='download_button_dormant_account')

    if 'Balance' not in filtered_df.columns:
        st.warning('Balance field is required for dormant account analysis.')
        return

    dormant, total_amount, branch_summary = get_dormant_account_data(filtered_df)

    render_kpi_grid([
        ('Dormant Records', len(dormant)),
        ('Dormant Amount', human_readable_amount(total_amount)),
    ])

    if dormant.empty:
        st.info('No dormant-account transactions were detected.')
        return

    render_table_with_options(dormant.sort_values('Date', ascending=False), key_prefix='dormant_transactions')
    
    if not branch_summary.empty:
        st.subheader('Branch Dormant Exposure')
        render_table_with_options(branch_summary, key_prefix='dormant_branch_summary')
