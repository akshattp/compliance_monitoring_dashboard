import streamlit as st
from frontend.ui_helpers.ui import render_page_header, render_table_with_options
from backend.services.simple_pages_service import get_vrm_summary_data

def render_vrm_summary_page(filtered_df, risk_df=None, risk_flags=None):
    render_page_header('VRM Summary', 'VRM executive summary of flagged country and agent activity.', df=filtered_df, download_key='download_button_vrm_summary')

    if filtered_df.empty:
        st.info('No transactions available for VRM summary.')
        return

    agent_summary, country_summary = get_vrm_summary_data(filtered_df)

    if 'Agent Name' in filtered_df.columns and not agent_summary.empty:
        st.subheader('Agent Contribution Summary')
        render_table_with_options(agent_summary, key_prefix='vrm_summary_agent')

    if 'Visiting Country' in filtered_df.columns and not country_summary.empty:
        st.subheader('Country Exposure Summary')
        render_table_with_options(country_summary, key_prefix='vrm_summary_country')
