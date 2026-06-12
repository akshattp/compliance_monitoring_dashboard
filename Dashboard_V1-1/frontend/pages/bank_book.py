import os
import io
import pandas as pd
import streamlit as st
import plotly.express as px
from frontend.charts import plot_donut, plot_bar, apply_enterprise_chart_style
from frontend.ui_helpers.ui import human_readable_amount, render_page_header, render_kpi_grid, render_table_with_options

from backend.services.bank_book_service import (
    load_bank_book_data,
    get_bank_book_kpis,
    build_summary_table,
    get_segment_trend_data,
    get_acc_seg_matrix,
    get_exception_insights_data
)

def render_bank_book_page(filtered_df, risk_df=None, risk_flags=None):
    render_page_header('Bank Book Analysis', 'Transform the monthly Bank Book report into an interactive analysis dashboard.', download_key='download_button_bank_book')

    default_path = "/Users/akshat/Document/Coding Project/GloabalPaywsfx_Dashboard_Automation-main/CONSOLIDATE BANK BOOK.xlsx"
    sheet_name = 'Sheet1'
    
    st.markdown("### Data Source")
    st.info("Upload the CONSOLIDATE BANK BOOK workbook, or use the default provided file.")
    uploaded_file = st.file_uploader("Upload Bank Book Workbook", type=['xlsx', 'xls'], key="bank_book_uploader")

    df = None
    file_bytes = None
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        # Save file bytes in session state to share or keep state across page switches if needed
        st.session_state['bb_file_bytes'] = file_bytes
        st.session_state['bb_filename'] = uploaded_file.name
    elif 'bb_file_bytes' in st.session_state:
        file_bytes = st.session_state['bb_file_bytes']
        st.info(f"Using uploaded file: {st.session_state.get('bb_filename', 'Uploaded File')}")

    try:
        if file_bytes is not None:
            data_dict = load_bank_book_data(file_bytes=file_bytes, sheet_name=sheet_name)
        elif os.path.exists(default_path):
            data_dict = load_bank_book_data(default_path=default_path, sheet_name=sheet_name)
        else:
            st.warning(f"Default file not found at `{default_path}`. Please upload the file.")
            return

        if not data_dict:
            st.error("Error: Loaded data dictionary is empty.")
            return
            
        df = data_dict['df']
        col_receipt = data_dict['col_receipt']
        col_cheque_transfer = data_dict['col_cheque_transfer']
        col_cms = data_dict['col_cms']
        col_segment = data_dict['col_segment']
        col_party = data_dict['col_party']
        col_account = data_dict['col_account']
        col_date = data_dict['col_date']
        col_cheque_no = data_dict['col_cheque_no']

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    if df is None or df.empty:
        st.warning("The loaded bank book dataframe is empty or could not be parsed.")
        return

    if col_receipt not in df.columns:
        st.error(f"Could not find receipt amount column. Looked for 'Receipt Amount'.")
        return

    # ---------------------------------------------------------
    # FILTERS
    # ---------------------------------------------------------
    st.markdown("### Global Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        account_options = ['All'] + sorted(df[col_account].dropna().astype(str).unique().tolist()) if col_account in df.columns else ['All']
        selected_account = st.selectbox("Account Name", account_options, key='bb_account_filter')
        
        party_options = ['All'] + sorted(df[col_party].dropna().astype(str).unique().tolist()) if col_party in df.columns else ['All']
        selected_party = st.selectbox("Party Name", party_options, key='bb_party_filter')
        
    with col2:
        segment_options = ['All'] + sorted(df[col_segment].dropna().astype(str).unique().tolist()) if col_segment in df.columns else ['All']
        selected_segment = st.selectbox("Segment", segment_options, key='bb_segment_filter')
        
        cms_options = ['All'] + sorted(df[col_cms].dropna().astype(str).unique().tolist()) if col_cms in df.columns else ['All']
        selected_cms = st.selectbox("CMS / NON CMS / HDFC", cms_options, key='bb_cms_filter')
        
    with col3:
        ct_options = ['All'] + sorted(df[col_cheque_transfer].dropna().astype(str).unique().tolist()) if col_cheque_transfer in df.columns else ['All']
        selected_ct = st.selectbox("Cheque/Transfer", ct_options, key='bb_ct_filter')
        
        if col_date in df.columns and not df[col_date].dropna().empty:
            min_date = df[col_date].min().date()
            max_date = df[col_date].max().date()
            date_range = st.date_input("Date Range", value=(min_date, max_date), key='bb_date_filter')
        else:
            date_range = None

    # Apply Filters
    bb_df = df.copy()
    if selected_account != 'All' and col_account in bb_df.columns:
        bb_df = bb_df[bb_df[col_account] == selected_account]
    if selected_party != 'All' and col_party in bb_df.columns:
        bb_df = bb_df[bb_df[col_party] == selected_party]
    if selected_segment != 'All' and col_segment in bb_df.columns:
        bb_df = bb_df[bb_df[col_segment] == selected_segment]
    if selected_cms != 'All' and col_cms in bb_df.columns:
        bb_df = bb_df[bb_df[col_cms] == selected_cms]
    if selected_ct != 'All' and col_cheque_transfer in bb_df.columns:
        bb_df = bb_df[bb_df[col_cheque_transfer] == selected_ct]
    if date_range is not None and len(date_range) == 2:
        bb_df = bb_df[(bb_df[col_date].dt.date >= date_range[0]) & (bb_df[col_date].dt.date <= date_range[1])]

    cols_dict = {
        'col_receipt': col_receipt,
        'col_cheque_transfer': col_cheque_transfer,
        'col_cms': col_cms,
        'col_segment': col_segment,
        'col_party': col_party,
        'col_account': col_account,
        'col_date': col_date,
        'col_cheque_no': col_cheque_no,
    }

    # Fetch KPIs
    kpis = get_bank_book_kpis(bb_df, cols_dict)
    total_receipt_amount = kpis['total_receipt_amount']
    total_txns = kpis['total_txns']

    st.markdown("---")

    # ---------------------------------------------------------
    # SECTION 1: EXECUTIVE SUMMARY KPIs
    # ---------------------------------------------------------
    st.header("1. Executive Summary")
    
    render_kpi_grid([
        ('Total Transactions', f"{total_txns:,}"),
        ('Total Receipt Amount', f"₹{total_receipt_amount:,.2f}"),
        ('Cheque Transactions', f"{kpis['cheque_txns']:,}"),
        ('Transfer Transactions', f"{kpis['transfer_txns']:,}"),
    ])
    render_kpi_grid([
        ('CMS Amount', f"₹{kpis['cms_amt']:,.2f}"),
        ('NON CMS Amount', f"₹{kpis['non_cms_amt']:,.2f}"),
        ('HDFC Amount', f"₹{kpis['hdfc_amt']:,.2f}"),
    ])
    render_kpi_grid([
        ('Top Segment', str(kpis['top_segment'])),
        ('Top Party', str(kpis['top_party'])),
        ('Largest Single Receipt', f"₹{kpis['largest_receipt']:,.2f}"),
    ])

    st.markdown("---")

    # ---------------------------------------------------------
    # SECTION 2: CHEQUE VS TRANSFER ANALYSIS
    # ---------------------------------------------------------
    st.header("2. Cheque vs Transfer Analysis")
    if col_cheque_transfer in bb_df.columns:
        ct_summary_with_total = build_summary_table(bb_df, col_receipt, col_cheque_transfer, total_txns, total_receipt_amount)
        if not ct_summary_with_total.empty:
            render_table_with_options(ct_summary_with_total, key_prefix='ct_summary')
            
            # Exclude TOTAL row for chart plotting
            ct_summary_for_charts = ct_summary_with_total[ct_summary_with_total[col_cheque_transfer] != 'TOTAL']
            
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(plot_donut(ct_summary_for_charts, col_cheque_transfer, 'Count', 'Cheque vs Transfer Count'), use_container_width=True)
            with c2:
                st.plotly_chart(plot_donut(ct_summary_for_charts, col_cheque_transfer, 'Receipt Amount', 'Cheque vs Transfer Amount'), use_container_width=True)
                
            if col_segment in bb_df.columns:
                seg_ct = bb_df.groupby([col_cheque_transfer, col_segment])[col_receipt].sum().reset_index()
                fig_ct_seg = px.bar(seg_ct, x=col_cheque_transfer, y=col_receipt, color=col_segment, title='Segment Split within Cheque/Transfer', barmode='stack')
                st.plotly_chart(apply_enterprise_chart_style(fig_ct_seg), use_container_width=True)
    else:
        st.warning("Cheque/Transfer column missing.")
        
    st.markdown("---")

    # ---------------------------------------------------------
    # SECTION 3: CMS / NON CMS / HDFC ANALYSIS
    # ---------------------------------------------------------
    st.header("3. CMS / NON CMS / HDFC Analysis")
    if col_cms in bb_df.columns:
        cms_summary_with_total = build_summary_table(bb_df, col_receipt, col_cms, total_txns, total_receipt_amount)
        if not cms_summary_with_total.empty:
            render_table_with_options(cms_summary_with_total, key_prefix='cms_summary')
            
            # Exclude TOTAL row for chart plotting
            cms_summary_for_charts = cms_summary_with_total[cms_summary_with_total[col_cms] != 'TOTAL']
            
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(plot_bar(cms_summary_for_charts, col_cms, 'Receipt Amount', 'CMS Amount Comparison'), use_container_width=True)
                st.plotly_chart(plot_donut(cms_summary_for_charts, col_cms, 'Receipt Amount', 'Contribution %'), use_container_width=True)
            with c2:
                st.plotly_chart(plot_bar(cms_summary_for_charts, col_cms, 'Count', 'CMS Count Comparison'), use_container_width=True)
    else:
        st.warning("CMS classification column missing.")

    st.markdown("---")

    # ---------------------------------------------------------
    # SECTION 4: SEGMENT ANALYSIS
    # ---------------------------------------------------------
    st.header("4. Segment Analysis")
    if col_segment in bb_df.columns:
        seg_summary_with_total = build_summary_table(bb_df, col_receipt, col_segment, total_txns, total_receipt_amount)
        if not seg_summary_with_total.empty:
            render_table_with_options(seg_summary_with_total, key_prefix='seg_summary')
            
            # Exclude TOTAL row for chart plotting
            seg_summary_for_charts = seg_summary_with_total[seg_summary_with_total[col_segment] != 'TOTAL']
            
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(plot_donut(seg_summary_for_charts, col_segment, 'Receipt Amount', 'Segment Contribution %'), use_container_width=True)
            with c2:
                st.plotly_chart(plot_bar(seg_summary_for_charts, col_segment, 'Receipt Amount', 'Segment Amount Distribution'), use_container_width=True)
                
            if col_date in bb_df.columns:
                seg_trend = get_segment_trend_data(bb_df, col_date, col_segment, col_receipt)
                if not seg_trend.empty:
                    fig_trend = px.line(seg_trend, x='Date', y=col_receipt, color=col_segment, title='Segment Trend')
                    st.plotly_chart(apply_enterprise_chart_style(fig_trend), use_container_width=True)
    else:
        st.warning("Segment column missing.")

    st.markdown("---")

    # ---------------------------------------------------------
    # SECTION 5: ACCOUNT NAME VS SEGMENT ANALYSIS
    # ---------------------------------------------------------
    st.header("5. Account Name vs Segment Analysis")
    if col_account in bb_df.columns and col_segment in bb_df.columns and col_cms in bb_df.columns:
        
        def render_acc_seg_matrix_ui(title, matrix_data, prefix):
            st.markdown(f"#### {title}")
            if not matrix_data:
                st.info("No data available.")
                return
            
            # Count Matrix
            st.markdown("**Count Matrix**")
            render_table_with_options(matrix_data['count_matrix'].reset_index(), key_prefix=f'{prefix}_count')
            
            # Amount Matrix
            st.markdown("**Receipt Amount Matrix**")
            render_table_with_options(matrix_data['amt_matrix'].reset_index(), key_prefix=f'{prefix}_amt')
            
            # Charts
            acc_summary = matrix_data['acc_summary']
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(plot_bar(acc_summary.sort_values('Amount', ascending=False).head(10), col_account, 'Amount', 'Top Account Names by Receipt Amount', orientation='h'), use_container_width=True)
            with c2:
                st.plotly_chart(plot_bar(acc_summary.sort_values('Count', ascending=False).head(10), col_account, 'Count', 'Top Account Names by Count', orientation='h'), use_container_width=True)
                
            seg_mix = matrix_data['seg_mix']
            fig_mix = px.bar(seg_mix, x=col_account, y=col_receipt, color=col_segment, title='Segment Mix by Account Name', barmode='stack')
            st.plotly_chart(apply_enterprise_chart_style(fig_mix), use_container_width=True)

        cms_matrix_data = get_acc_seg_matrix(bb_df, cols_dict, 'CMS')
        non_cms_matrix_data = get_acc_seg_matrix(bb_df, cols_dict, 'NON CMS')
        
        render_acc_seg_matrix_ui("CMS", cms_matrix_data, "cms_matrix")
        st.markdown("<br>", unsafe_allow_html=True)
        render_acc_seg_matrix_ui("NON CMS", non_cms_matrix_data, "non_cms_matrix")
    else:
        st.warning("Required columns for Account vs Segment analysis are missing.")

    st.markdown("---")

    # ---------------------------------------------------------
    # SECTION 6: PARTY CONCENTRATION ANALYSIS
    # ---------------------------------------------------------
    st.header("6. Party Concentration Analysis")
    if col_party in bb_df.columns:
        unique_parties = bb_df[col_party].nunique()
        party_summary = bb_df.groupby(col_party).agg(Amount=(col_receipt, 'sum'), Count=(col_receipt, 'size')).reset_index().sort_values('Amount', ascending=False)
        top_party_name = party_summary.iloc[0][col_party] if not party_summary.empty else "N/A"
        top_party_amt = party_summary.iloc[0]['Amount'] if not party_summary.empty else 0
        top_party_pct = (top_party_amt / total_receipt_amount * 100) if total_receipt_amount > 0 else 0
        
        render_kpi_grid([
            ('Unique Parties', f"{unique_parties:,}"),
            ('Top Party', str(top_party_name)),
            ('Top Party Amount', f"₹{top_party_amt:,.2f}"),
            ('Top Party %', f"{top_party_pct:.2f}%"),
        ])
        
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_bar(party_summary.head(20), col_party, 'Amount', 'Top 20 Parties by Amount', orientation='h'), use_container_width=True)
        with c2:
            st.plotly_chart(plot_bar(party_summary.sort_values('Count', ascending=False).head(20), col_party, 'Count', 'Top 20 Parties by Count', orientation='h'), use_container_width=True)
            
        st.plotly_chart(plot_donut(party_summary.head(10), col_party, 'Amount', 'Party Concentration % (Top 10)'), use_container_width=True)
    else:
        st.warning("Party Name column missing.")

    st.markdown("---")

    # ---------------------------------------------------------
    # SECTION 7: EXCEPTION & INSIGHT ENGINE
    # ---------------------------------------------------------
    st.header("7. Exception & Insight Engine")
    st.info("Automated rules flagging concentration risks and data quality issues.")
    
    insights = get_exception_insights_data(bb_df, cols_dict, kpis)
    
    e1, e2 = st.columns(2)
    
    with e1:
        # Rule 1: High Concentration Party (>10%)
        if col_party in bb_df.columns and total_receipt_amount > 0:
            st.markdown("##### Rule 1: High Concentration Party (>10%)")
            high_conc = insights.get('rule1_high_conc', pd.DataFrame())
            if not high_conc.empty:
                st.dataframe(high_conc, hide_index=True)
            else:
                st.success("No party exceeds 10% concentration.")
                
        # Rule 3: Account Dependency (>25%)
        if col_account in bb_df.columns and total_receipt_amount > 0:
            st.markdown("##### Rule 3: Account Dependency (>25%)")
            acc_dep = insights.get('rule3_acc_dep', pd.DataFrame())
            if not acc_dep.empty:
                st.dataframe(acc_dep, hide_index=True)
            else:
                st.success("No account exceeds 25% dependency.")
                
        # Rule 5: Cheque Concentration
        if col_party in bb_df.columns and col_cheque_transfer in bb_df.columns:
            st.markdown("##### Rule 5: Cheque Concentration")
            chq_party = insights.get('rule5_chq_conc', pd.DataFrame())
            if not chq_party.empty:
                st.markdown("Top 5 Parties by Cheque Receipt Amount:")
                st.dataframe(chq_party, hide_index=True)
            else:
                st.success("No cheque transactions found.")

        # Rule 7: Duplicate Receipt Pattern
        if col_party in bb_df.columns:
            st.markdown("##### Rule 7: Duplicate Receipt Pattern")
            dup_summary = insights.get('rule7_dup_pattern', pd.DataFrame())
            if not dup_summary.empty:
                st.dataframe(dup_summary, hide_index=True)
            else:
                st.success("No duplicate patterns found.")

    with e2:
        # Rule 2: Single Large Receipt (Top 20)
        st.markdown("##### Rule 2: Top 20 Single Largest Receipts")
        largest_receipts = insights.get('rule2_largest', pd.DataFrame())
        if not largest_receipts.empty:
            st.dataframe(largest_receipts, hide_index=True)
        else:
            st.info("No data to display.")
        
        # Rule 4: Segment Dependency (>60%)
        if col_segment in bb_df.columns and total_receipt_amount > 0:
            st.markdown("##### Rule 4: Segment Dependency (>60%)")
            seg_dep = insights.get('rule4_seg_dep', pd.DataFrame())
            if not seg_dep.empty:
                st.dataframe(seg_dep, hide_index=True)
            else:
                st.success("No segment exceeds 60% dependency.")
                
        # Rule 6: CMS vs NON CMS Imbalance
        if col_cms in bb_df.columns and total_receipt_amount > 0:
            st.markdown("##### Rule 6: CMS vs NON CMS Imbalance")
            imbalance_msg = insights.get('rule6_imbalance')
            if imbalance_msg:
                st.warning(imbalance_msg)
            else:
                st.success("CMS and NON CMS are reasonably balanced.")
                
        # Rule 8: Data Quality Checks
        st.markdown("##### Rule 8: Data Quality Checks")
        dq_issues = insights.get('rule8_dq', pd.DataFrame())
        if not dq_issues.empty:
            st.dataframe(dq_issues, hide_index=True)
        else:
            st.success("No major data quality issues found.")
