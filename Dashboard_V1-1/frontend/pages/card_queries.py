import streamlit as st
from frontend.ui_helpers.ui import render_page_header, render_table_with_options
from frontend.charts import plot_bar
from backend.services.simple_pages_service import get_card_queries_data

def render_card_queries_page(filtered_df, risk_df=None, risk_flags=None):
    render_page_header('Card Queries', 'Card and reload product review for suspicious or high-value activity.', df=filtered_df, download_key='download_button_card_queries')

    card_data, summary = get_card_queries_data(filtered_df)

    if card_data.empty:
        st.info('No card or reload product transactions found in the current selection.')
        return

    if not summary.empty:
        st.plotly_chart(plot_bar(summary.head(20), 'Product', 'Total_Amount', 'Card/Reload Product Exposure', orientation='h'), use_container_width=True)
        
    render_table_with_options(card_data.sort_values('Net Amt', ascending=False), key_prefix='card_queries')
