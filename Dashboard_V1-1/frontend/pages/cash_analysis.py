import os
import io
import pandas as pd
import streamlit as st
import plotly.express as px
from frontend.charts import plot_donut, plot_bar, apply_enterprise_chart_style
from frontend.ui_helpers.ui import human_readable_amount, render_page_header, render_kpi_grid, render_table_with_options

from backend.services.cash_analysis_service import (
    load_cash_analysis_data,
    get_cash_analysis_kpis,
    build_cash_summary_table,
    get_ps_alerts_data
)

def render_cash_analysis_page(filtered_df, risk_df=None, risk_flags=None):
    render_page_header('Cash Analysis', 'Identify cash-like flows, threshold structuring and branch cash concentration.', download_key='download_button_cash_analysis')

    default_path = "/Users/akshat/Document/Coding Project/GloabalPaywsfx_Dashboard_Automation-main/CASH ANALYSIS APRIL 2026.xlsx"
    sheet_name = 'RptTimeBasedCashAnylises'
    
    st.markdown("### Data Source")
    st.info("Upload the Cash Analysis workbook, or use the default provided file.")
    uploaded_file = st.file_uploader("Upload Cash Analysis Workbook", type=['xlsx', 'xls'], key="cash_analysis_uploader")

    df = None
    file_bytes = None
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        st.session_state['cash_file_bytes'] = file_bytes
        st.session_state['cash_filename'] = uploaded_file.name
    elif 'cash_file_bytes' in st.session_state:
        file_bytes = st.session_state['cash_file_bytes']
        st.info(f"Using uploaded file: {st.session_state.get('cash_filename', 'Uploaded File')}")

    try:
        if file_bytes is not None:
            df = load_cash_analysis_data(file_bytes=file_bytes, sheet_name=sheet_name)
        elif os.path.exists(default_path):
            df = load_cash_analysis_data(default_path=default_path, sheet_name=sheet_name)
        else:
            st.warning(f"Default file not found at `{default_path}`. Please upload the file.")
            return
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    if df is None or df.empty:
        st.warning("The cash analysis dataframe is empty or could not be loaded correctly.")
        return

    # UI Filters
    st.markdown("### Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        branch_options = ['All'] + sorted(df['Branch'].dropna().unique().tolist())
        selected_branch = st.selectbox("Branch", branch_options, key='cash_branch_filter')
    
    with col2:
        txn_options = ['All'] + sorted(df['Txn Type'].dropna().unique().tolist())
        selected_txn = st.selectbox("Txn Type", txn_options, key='cash_txn_filter')
        
    with col3:
        if 'Txn Date' in df.columns and not df['Txn Date'].dropna().empty:
            min_date = df['Txn Date'].min().date()
            max_date = df['Txn Date'].max().date()
            date_range = st.date_input("Date Range", value=(min_date, max_date), key='cash_date_filter')
        else:
            date_range = None

    # Apply Filters
    filtered_df_cash = df.copy()
    if selected_branch != 'All':
        filtered_df_cash = filtered_df_cash[filtered_df_cash['Branch'] == selected_branch]
    if selected_txn != 'All':
        filtered_df_cash = filtered_df_cash[filtered_df_cash['Txn Type'] == selected_txn]
    if date_range is not None and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df_cash = filtered_df_cash[(filtered_df_cash['Txn Date'].dt.date >= start_date) & (filtered_df_cash['Txn Date'].dt.date <= end_date)]

    pb_df = filtered_df_cash[filtered_df_cash['Txn Type'] == 'PB']
    ps_df = filtered_df_cash[filtered_df_cash['Txn Type'] == 'PS']

    st.markdown("---")
    
    # ---------------------------------------------------------
    # PB ANALYSIS
    # ---------------------------------------------------------
    st.header("PB ANALYSIS")
    
    pb_kpis = get_cash_analysis_kpis(pb_df)
    total_pb_txns = pb_kpis['total_txns']
    total_pb_amount = pb_kpis['total_amount']

    render_kpi_grid([
        ('Total PB Transactions', f"{total_pb_txns:,}"),
        ('Total PB Amount', f"₹{total_pb_amount:,.2f}"),
        ('Branch Count', f"{pb_kpis['branch_count']}"),
        ('Highest PB Branch', str(pb_kpis['highest_branch'])),
    ])

    if not pb_df.empty:
        pb_summary_total = build_cash_summary_table(pb_df, total_pb_txns, total_pb_amount)
        if not pb_summary_total.empty:
            st.markdown("#### PB Summary Table")
            render_table_with_options(pb_summary_total, key_prefix='pb_summary_table')
            
            # Remove TOTAL row for charts
            pb_summary_for_charts = pb_summary_total[pb_summary_total['Branch'] != 'TOTAL']
            
            st.markdown("#### PB Visuals")
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(plot_bar(pb_summary_for_charts.sort_values('Count', ascending=False).head(10), 'Branch', 'Count', 'Top Branches by PB Count'), use_container_width=True)
            with col2:
                st.plotly_chart(plot_bar(pb_summary_for_charts.head(10), 'Branch', 'Rec/Pay Amt.', 'Top Branches by PB Amount'), use_container_width=True)
                
            st.plotly_chart(plot_donut(pb_summary_for_charts, 'Branch', 'Rec/Pay Amt.', 'PB Branch Contribution %'), use_container_width=True)
        
    st.markdown("---")

    # ---------------------------------------------------------
    # PS ANALYSIS
    # ---------------------------------------------------------
    st.header("PS ANALYSIS")
    
    ps_kpis = get_cash_analysis_kpis(ps_df)
    total_ps_txns = ps_kpis['total_txns']
    total_ps_amount = ps_kpis['total_amount']

    render_kpi_grid([
        ('Total PS Transactions', f"{total_ps_txns:,}"),
        ('Total PS Amount', f"₹{total_ps_amount:,.2f}"),
        ('Branch Count', f"{ps_kpis['branch_count']}"),
        ('Highest PS Branch', str(ps_kpis['highest_branch'])),
    ])

    if not ps_df.empty:
        ps_summary_total = build_cash_summary_table(ps_df, total_ps_txns, total_ps_amount)
        if not ps_summary_total.empty:
            st.markdown("#### PS Summary Table")
            render_table_with_options(ps_summary_total, key_prefix='ps_summary_table')
            
            # Remove TOTAL row for charts
            ps_summary_for_charts = ps_summary_total[ps_summary_total['Branch'] != 'TOTAL']
            
            st.markdown("#### PS Visuals")
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(plot_bar(ps_summary_for_charts.sort_values('Count', ascending=False).head(10), 'Branch', 'Count', 'Top Branches by PS Count'), use_container_width=True)
            with col2:
                st.plotly_chart(plot_bar(ps_summary_for_charts.head(10), 'Branch', 'Rec/Pay Amt.', 'Top Branches by PS Amount'), use_container_width=True)
                
            st.plotly_chart(plot_donut(ps_summary_for_charts, 'Branch', 'Rec/Pay Amt.', 'PS Branch Contribution %'), use_container_width=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # PS HIGH VALUE CASH ALERTS
    # ---------------------------------------------------------
    st.header("PS HIGH VALUE CASH ALERTS")
    st.info("Flagged all PS transactions where Rec/Pay Amt. > 49,000")
    
    alerts_data = get_ps_alerts_data(ps_df)
    alert_txns = alerts_data['alert_txns']
    
    render_kpi_grid([
        ('Alert Transaction Count', f"{alert_txns:,}"),
        ('Alert Amount', f"₹{alerts_data['alert_amount']:,.2f}"),
        ('Branches Involved', f"{alerts_data['alert_branches']}"),
        ('Highest Alert Transaction', alerts_data['highest_alert_desc']),
    ])

    if alert_txns > 0:
        st.markdown("#### Alert Table")
        
        alerts_df = alerts_data['alerts_df']
        alert_cols = ['Branch', 'Party', 'Txn Date', 'Doc.No.', 'Net Amt.', 'Rec/Pay Amt.', 'User Name']
        display_alert_cols = [c for c in alert_cols if c in alerts_df.columns]
        
        alert_table_df = alerts_df[display_alert_cols].sort_values('Rec/Pay Amt.', ascending=False)
        render_table_with_options(alert_table_df, key_prefix='ps_alerts_table')
        
        st.markdown("#### Alert Charts")
        alert_summary = alerts_data['alert_summary']
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_bar(alert_summary.sort_values('Count', ascending=False), 'Branch', 'Count', 'Alert Branch Distribution (Count)'), use_container_width=True)
        with col2:
            st.plotly_chart(plot_bar(alert_summary.sort_values('Alert Amount', ascending=False), 'Branch', 'Alert Amount', 'Alert Amount by Branch'), use_container_width=True)
            
        date_trend = alerts_data['date_trend']
        if not date_trend.empty:
            fig_trend = px.line(date_trend, x='Date', y='Alert Amount', title='Alert Trend by Date')
            fig_trend = apply_enterprise_chart_style(fig_trend)
            st.plotly_chart(fig_trend, use_container_width=True)
