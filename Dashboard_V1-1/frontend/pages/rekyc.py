import streamlit as st
from frontend.ui_helpers.ui import render_page_header, render_table_with_options
from frontend.charts import plot_bar
from backend.services.simple_pages_service import get_rekyc_summaries

def render_rekyc_page(filtered_df, risk_df=None, risk_flags=None):
    render_page_header('ReKYC', 'Re-KYC review of referrals, segments and customer remediation activity.', df=filtered_df, download_key='download_button_rekyc')

    if 'Referred By' not in filtered_df.columns and 'Segments' not in filtered_df.columns:
        st.warning('Referred By or Segments are required for ReKYC analysis.')
        return

    referred_summary, segment_summary = get_rekyc_summaries(filtered_df)

    if 'Referred By' in filtered_df.columns and not referred_summary.empty:
        st.subheader('Referred By Summary')
        st.plotly_chart(plot_bar(referred_summary, 'Referred By', 'Total_Amount', 'Referral Exposure', orientation='h'), use_container_width=True)
        render_table_with_options(referred_summary, key_prefix='rekyc_referred')

    if 'Segments' in filtered_df.columns and not segment_summary.empty:
        st.subheader('Segments Summary')
        st.plotly_chart(plot_bar(segment_summary, 'Segments', 'Total_Amount', 'Segment Exposure', orientation='h'), use_container_width=True)
        render_table_with_options(segment_summary, key_prefix='rekyc_segments')
