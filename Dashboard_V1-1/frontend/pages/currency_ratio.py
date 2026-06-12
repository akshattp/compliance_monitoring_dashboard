import os
import io
import pandas as pd
import streamlit as st
import plotly.express as px
from frontend.charts import plot_donut, plot_bar, apply_enterprise_chart_style
from frontend.ui_helpers.ui import human_readable_amount, render_page_header, render_kpi_grid, render_table_with_options

from backend.services.currency_ratio_service import (
    load_currency_ratio_data,
    get_currency_ratio_kpis,
    build_currency_ratio_table
)

def render_currency_ratio_page(filtered_df, risk_df=None, risk_flags=None):
    render_page_header('Currency Ratio Analysis', 'Currency mix and replenishment ratio analysis for the month.', download_key='download_button_currency_ratio')

    default_path = "/Users/akshat/Document/Coding Project/GloabalPaywsfx_Dashboard_Automation-main/CURRENCY RATIO APRIL 2026.xlsx"
    sheet_name = 'ImportFromExcel(164)'
    
    st.markdown("### Data Source")
    st.info("Upload the Currency Ratio workbook, or use the default provided file.")
    uploaded_file = st.file_uploader("Upload Currency Ratio Workbook", type=['xlsx', 'xls'], key="currency_ratio_uploader")

    df = None
    file_bytes = None
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        st.session_state['ratio_file_bytes'] = file_bytes
        st.session_state['ratio_filename'] = uploaded_file.name
    elif 'ratio_file_bytes' in st.session_state:
        file_bytes = st.session_state['ratio_file_bytes']
        st.info(f"Using uploaded file: {st.session_state.get('ratio_filename', 'Uploaded File')}")

    try:
        if file_bytes is not None:
            df = load_currency_ratio_data(file_bytes=file_bytes, sheet_name=sheet_name)
        elif os.path.exists(default_path):
            df = load_currency_ratio_data(default_path=default_path, sheet_name=sheet_name)
        else:
            st.warning(f"Default file not found at `{default_path}`. Please upload the file.")
            return
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    if df is None or df.empty:
        st.warning("The currency ratio dataframe is empty or could not be loaded correctly.")
        return

    # Fetch calculations
    kpis = get_currency_ratio_kpis(df)
    total_retail = kpis['total_retail']
    total_bulk = kpis['total_bulk']
    overall_ratio = kpis['overall_ratio']

    render_kpi_grid([
        ('Total Retail Sales', f"₹{total_retail:,.2f}"),
        ('Total Bulk Purchase', f"₹{total_bulk:,.2f}"),
        ('Overall Retail Sales Ratio', f"{overall_ratio:.2f}%"),
        ('Exception Branches', f"{kpis['exception_count']}"),
    ])

    highest_row = kpis['highest_row']
    lowest_row = kpis['lowest_row']
    if highest_row is not None and lowest_row is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Highest Ratio Branch", highest_row['LOCATION'], f"{highest_row['Retail Sales %']:.2f}%")
        with col2:
            st.metric("Lowest Ratio Branch", lowest_row['LOCATION'], f"{lowest_row['Retail Sales %']:.2f}%")

    st.markdown("---")

    # Exception Flags
    exception_high = kpis['exception_high']
    exception_low = kpis['exception_low']
    if not exception_high.empty or not exception_low.empty:
        st.markdown("### Exception Flags")
        c1, c2 = st.columns(2)
        with c1:
            if not exception_high.empty:
                st.warning(f"**{len(exception_high)} Branches with Ratio > 100%**")
                st.dataframe(exception_high[['LOCATION', 'Retail Sales %']].sort_values('Retail Sales %', ascending=False), hide_index=True)
        with c2:
            if not exception_low.empty:
                st.info(f"**{len(exception_low)} Branches with Ratio < 25%**")
                st.dataframe(exception_low[['LOCATION', 'Retail Sales %']].sort_values('Retail Sales %', ascending=True), hide_index=True)
        st.markdown("---")

    # Table Generation
    table_df = build_currency_ratio_table(df, total_retail, total_bulk, overall_ratio)
    if table_df.empty:
        st.warning("No tabular data to display.")
        return

    st.markdown("### Analytics Visuals")
    
    # Chart 1: Top 10 Branches by Retail Sales %
    top_10 = table_df.sort_values('Retail Sales %', ascending=False).head(10)
    fig_top10 = plot_bar(top_10, 'LOCATION', 'Retail Sales %', 'Top 10 Branches by Retail Sales %')
    st.plotly_chart(fig_top10, use_container_width=True)

    # Chart 2: Branch-wise Retail Sales %
    fig_branch = plot_bar(table_df.sort_values('Retail Sales %', ascending=True), 'LOCATION', 'Retail Sales %', 'Branch-wise Retail Sales %', orientation='h')
    st.plotly_chart(fig_branch, use_container_width=True)

    # Chart 3: Retail Sales vs Bulk Purchase
    melted = table_df.melt(id_vars=['LOCATION'], value_vars=['Retail Sales', 'Bulk Purchase'], var_name='Type', value_name='Amount')
    fig_grouped = px.bar(melted, x='LOCATION', y='Amount', color='Type', barmode='group', title='Retail Sales vs Bulk Purchase')
    fig_grouped = apply_enterprise_chart_style(fig_grouped)
    st.plotly_chart(fig_grouped, use_container_width=True)

    # Chart 4: Branch Contribution to Retail Sales (remove TOTAL row if present)
    fig_donut = plot_donut(table_df, 'LOCATION', 'Retail Sales', 'Branch Contribution to Retail Sales')
    st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("---")
    st.markdown("### Branch Currency Ratio Table")
    
    total_row = pd.DataFrame([{
        'LOCATION': 'TOTAL',
        'Retail Sales': total_retail,
        'Bulk Purchase': total_bulk,
        'Retail Sales %': round(overall_ratio, 2),
        'Retail Contribution %': 100.0,
        'Bulk Contribution %': 100.0
    }])
    table_df_with_total = pd.concat([table_df, total_row], ignore_index=True)

    render_table_with_options(table_df_with_total, key_prefix='currency_ratio_table')
