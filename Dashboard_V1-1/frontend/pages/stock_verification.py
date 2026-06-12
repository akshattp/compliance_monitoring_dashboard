import streamlit as st
from frontend.ui_helpers.ui import render_page_header, render_table_with_options
from backend.services.simple_pages_service import get_stock_verification_data

def render_stock_verification_page(filtered_df, risk_df=None, risk_flags=None):
    render_page_header('Stock Verification', 'Stock verification page for inventory-related transactions and exposure.', df=filtered_df, download_key='download_button_stock_verification')

    stock_columns, stock_summary = get_stock_verification_data(filtered_df)
    if not stock_columns:
        st.info('No stock or inventory fields were present in the loaded dataset.')
        return

    st.subheader('Stock / Inventory Fields Detected')
    st.write(stock_columns)

    if not stock_summary.empty:
        render_table_with_options(stock_summary, key_prefix='stock_summary')
