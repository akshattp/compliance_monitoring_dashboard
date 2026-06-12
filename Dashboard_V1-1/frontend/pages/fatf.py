import streamlit as st
import pandas as pd
import plotly.express as px
from frontend.charts import plot_trend
from frontend.ui_helpers.ui import human_readable_amount, render_page_header, render_kpi_grid, render_table_with_options

from backend.services.fatf_service import (
    get_fatf_flagged_transactions,
    get_fatf_kpis,
    get_fatf_branch_seg_summary,
    get_fatf_country_seg_summary,
    get_fatf_purpose_counts,
    get_fatf_trend,
)

def render_fatf_page(filtered_df: pd.DataFrame, risk_df=None, risk_flags=None):
    render_page_header('FATF', 'Analyze FATF / OFAC exposures, high-risk geographies and flagged transactions.', df=filtered_df, download_key='download_button_fatf')

    st.markdown('### FATF/OFAC List Integration')
    col_ofac, _ = st.columns([1, 1])
    with col_ofac:
        ofac_file = st.file_uploader("Upload OFAC_FATF COUNTRY UPDATED.xlsx", type=['xlsx', 'xls'], key='ofac_uploader_widget_fatf')
        if ofac_file is not None:
            st.session_state['shared_ofac_file'] = ofac_file.getvalue()
            st.session_state['shared_ofac_filename'] = ofac_file.name
        
        if ofac_file is None and 'shared_ofac_file' in st.session_state:
            import io
            ofac_file = io.BytesIO(st.session_state['shared_ofac_file'])
            ofac_file.name = st.session_state['shared_ofac_filename']
            st.success(f"Using shared file: {ofac_file.name}")
        
    if not ofac_file:
        st.info("Please upload the **OFAC_FATF COUNTRY UPDATED.xlsx** file to enrich and view flagged transactions.")
        return

    try:
        # Load ofac file bytes into dataframe
        import io
        ofac_df = pd.read_excel(io.BytesIO(st.session_state['shared_ofac_file']), sheet_name='UPDATED FILE')
        flagged = get_fatf_flagged_transactions(filtered_df, ofac_df)
    except Exception as e:
        st.error(f"Error evaluating OFAC file: {e}")
        return

    # Calculate KPIs in backend
    kpis = get_fatf_kpis(flagged, filtered_df)
    render_kpi_grid([
        ('Flagged Transactions', kpis['flagged_count']),
        ('Flagged Amount', human_readable_amount(kpis['flagged_amount'])),
        ('Contribution %', f"{kpis['contrib_pct']:.1f}%"),
        ('Contribution Amount %', f"{kpis['contrib_amt_pct']:.1f}%"),
    ])

    if flagged.empty:
        st.info('No FATF/OFAC flagged transactions were detected under current filters.')
        return

    # Grouped bar: Branch vs Segments
    if 'Branch Name' in flagged.columns and 'Segments' in flagged.columns:
        branch_seg = get_fatf_branch_seg_summary(flagged)
        if not branch_seg.empty:
            fig_branch_seg = px.bar(
                branch_seg,
                x='Branch Name',
                y='Count',
                color='Segments',
                title='Flagged Branch Level by Segments',
                barmode='group',
                category_orders={'Branch Name': branch_seg['Branch Name'].unique()[::-1]}
            )
            fig_branch_seg.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_branch_seg, use_container_width=True)

    # Grouped bar: Visiting Country vs Segments
    if 'Visiting Country' in flagged.columns and 'Segments' in flagged.columns:
        country_seg = get_fatf_country_seg_summary(flagged)
        if not country_seg.empty:
            fig_country_seg = px.bar(
                country_seg,
                x='Visiting Country',
                y='Count',
                color='Segments',
                title='Flagged Visiting Country by Segments',
                barmode='group',
                category_orders={'Visiting Country': country_seg['Visiting Country'].unique()[::-1]}
            )
            fig_country_seg.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_country_seg, use_container_width=True)

    # Pie chart: all valid purposes (no grouping)
    if 'Purpose' in flagged.columns:
        purpose_counts = get_fatf_purpose_counts(flagged)
        if not purpose_counts.empty:
            fig_purpose = px.pie(
                purpose_counts,
                names='Purpose',
                values='Total_Amount',
                title='Flagged Purpose Mix'
            )
            fig_purpose.update_traces(textinfo='percent+label', pull=[0.05]*len(purpose_counts))
            st.plotly_chart(fig_purpose, use_container_width=True)

    # Trend chart
    if 'Date' in flagged.columns and not flagged['Date'].isna().all():
        trend_df = get_fatf_trend(flagged)
        if not trend_df.empty:
            st.plotly_chart(plot_trend(trend_df, 'Date', 'Total_Amount', 'Flagged Transaction Trend'), use_container_width=True)

    st.markdown('### Flagged Transactions')
    render_table_with_options(flagged.sort_values('Net Amt', ascending=False), key_prefix='fatf_flagged')
