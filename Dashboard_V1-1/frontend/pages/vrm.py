import streamlit as st
from frontend.charts import plot_bar
from frontend.ui_helpers.ui import human_readable_amount, render_page_header, render_kpi_grid, render_table_with_options
from backend.services.simple_pages_service import get_vrm_data

def render_vrm_page(filtered_df, risk_df=None, risk_flags=None):
    render_page_header('VRM', 'Visa Risk Management review of visiting country and traveller exposures.', df=filtered_df, download_key='download_button_vrm')

    if 'Visiting Country' not in filtered_df.columns:
        st.warning('Visiting Country field is required for VRM analysis.')
        return

    country_summary, total_amount = get_vrm_data(filtered_df)

    render_kpi_grid([
        ('Countries', len(country_summary)),
        ('Total VRM Amount', human_readable_amount(total_amount)),
    ])

    if not country_summary.empty:
        st.plotly_chart(plot_bar(country_summary.head(20), 'Visiting Country', 'Total_Amount', 'Visiting Country Exposure', orientation='h'), use_container_width=True)
        render_table_with_options(country_summary, key_prefix='vrm_country_summary')
