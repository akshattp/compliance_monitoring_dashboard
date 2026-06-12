import streamlit as st
import pandas as pd
from frontend.ui_helpers.ui import render_page_header, render_kpi_grid, render_table_with_options, human_readable_amount
from frontend.charts import plot_bar
from backend.services.simple_pages_service import get_mltf_data

def render_mltf_page(filtered_df, risk_df=None, risk_flags=None):
    render_page_header('MLTF', 'Money Laundering and Terrorist Financing risk review.', df=filtered_df, download_key='download_button_mltf')

    ml_df, total_amount, corporate_summary = get_mltf_data(filtered_df)

    render_kpi_grid([
        ('MLTF-related Records', len(ml_df)),
        ('MLTF Amount', human_readable_amount(total_amount)),
    ])

    if ml_df.empty:
        st.info('No MLTF-related records found under current filters.')
        return

    if not corporate_summary.empty:
        st.plotly_chart(plot_bar(corporate_summary, 'Corporate', 'Total_Amount', 'Top MLTF Corporates', orientation='h'), use_container_width=True)

    render_table_with_options(ml_df.sort_values('Net Amt', ascending=False), key_prefix='mltf_records')
