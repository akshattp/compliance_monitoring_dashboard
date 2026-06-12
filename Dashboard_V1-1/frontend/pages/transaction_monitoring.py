import io
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

from frontend.charts import apply_enterprise_chart_style
from frontend.ui_helpers.ui import (
    render_page_header,
    render_kpi_grid,
    render_table_with_options,
    human_readable_amount
)

from backend.services.transaction_monitoring_service import (
    safe_sorted_unique,
    summarize_cases,
    detect_high_value_transactions,
    detect_fatf_ofac,
    detect_multiple_operators_same_beneficiary,
    detect_high_frequency_remittances,
    detect_configurable_load_refund_window,
    detect_multiple_cards_contact,
    detect_multiple_cards_traveller,
    detect_multiple_cards_multi_operator
)

def _apply_count_bar_style(fig):
    fig.update_traces(textposition='outside', cliponaxis=False)
    fig.update_layout(height=300, showlegend=False, yaxis_title='Count of Cases / Transactions')
    return fig

def _render_count_bar(summary: pd.DataFrame, x_col: str, title: str):
    fig = px.bar(
        summary,
        x=x_col,
        y='Count',
        text='Count',
        title=title,
        labels={x_col: x_col, 'Count': 'Count of Cases / Transactions'},
        hover_data={
            'Count': True,
            'Total Amount': ':,.2f',
            'Average Amount': ':,.2f',
            'Max Amount': ':,.2f',
            'Risk Category': True,
        },
    )
    return apply_enterprise_chart_style(_apply_count_bar_style(fig))

def _render_count_pie(summary: pd.DataFrame, names_col: str, title: str):
    fig = px.pie(
        summary,
        values='Count',
        names=names_col,
        title=title,
        hole=0.35,
        custom_data=['Total Amount', 'Average Amount', 'Max Amount', 'Risk Category'],
    )
    fig.update_traces(
        hovertemplate=(
            f'{names_col}: %{{label}}<br>'
            'Count: %{value}<br>'
            'Percentage: %{percent}<br>'
            'Total Amount: %{customdata[0]:,.2f}<br>'
            'Average Amount: %{customdata[1]:,.2f}<br>'
            'Max Amount: %{customdata[2]:,.2f}<br>'
            'Risk Category: %{customdata[3]}<extra></extra>'
        )
    )
    fig.update_layout(height=300)
    return apply_enterprise_chart_style(fig)

def _render_investigation_table(df: pd.DataFrame, key_prefix: str):
    table_df = df.copy()

    csv = table_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label='Download investigation records',
        data=csv,
        file_name=f'{key_prefix}.csv',
        mime='text/csv',
        key=f'{key_prefix}__download',
    )
    render_table_with_options(table_df, key_prefix=key_prefix)

def _render_high_value_rule_ui(df: pd.DataFrame, high_value_df, structuring_df, summary):
    """Render the High Value Transaction rule card."""
    with st.expander('🔍 Filters', expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_branches = st.multiselect(
                'Branch',
                options=safe_sorted_unique(df['Branch Name']) if 'Branch Name' in df.columns else [],
                default=None,
                key='hv_branch_filter',
            )
        with col2:
            selected_countries = st.multiselect(
                'Visiting Country',
                options=safe_sorted_unique(df['Visiting Country']) if 'Visiting Country' in df.columns else [],
                default=None,
                key='hv_country_filter',
            )
        with col3:
            date_range = st.date_input(
                'Date Range',
                value=(df['Date'].min().date() if pd.notna(df['Date'].min()) else datetime.now().date(),
                       df['Date'].max().date() if pd.notna(df['Date'].max()) else datetime.now().date()),
                key='hv_date_range',
            )

        # Apply filters to high_value_df
        if selected_branches:
            high_value_df = high_value_df[high_value_df['Branch Name'].isin(selected_branches)]
        if selected_countries:
            high_value_df = high_value_df[high_value_df['Visiting Country'].isin(selected_countries)]
        if len(date_range) == 2:
            high_value_df = high_value_df[
                (high_value_df['Date'].dt.date >= date_range[0]) &
                (high_value_df['Date'].dt.date <= date_range[1])
            ]

    # Render KPIs
    render_kpi_grid([
        ('High Value Count', len(high_value_df)),
        ('Total Amount', human_readable_amount(high_value_df['EQV USD'].sum() if not high_value_df.empty else 0)),
        ('Structuring Alerts', len(structuring_df)),
        ('Highest Transaction', human_readable_amount(high_value_df['EQV USD'].max() if not high_value_df.empty else 0)),
    ])

    # Charts
    if not high_value_df.empty:
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            bins = [0, 10000, 25000, 50000, 100000, float('inf')]
            labels = ['<10K', '10K-25K', '25K-50K', '50K-100K', '>100K']
            df_dist = high_value_df.copy()
            df_dist['amount_bin'] = pd.cut(df_dist['EQV USD'], bins=bins, labels=labels)
            dist = summarize_cases(df_dist, 'amount_bin', 'EQV USD').sort_values('amount_bin')
            if len(dist) <= 1000:
                fig = _render_count_bar(dist, 'amount_bin', 'High-Value Case Distribution')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Chart disabled (exceeds 1000 points)")

        with chart_col2:
            if 'Branch Name' in high_value_df.columns:
                branch_exposure = summarize_cases(high_value_df, 'Branch Name', 'EQV USD').head(10)
                if len(branch_exposure) <= 1000:
                    fig = _render_count_bar(branch_exposure, 'Branch Name', 'Top 10 Branches by High-Value Case Count')
                    st.plotly_chart(fig, use_container_width=True)

    if not high_value_df.empty and 'Visiting Country' in high_value_df.columns:
        country_exposure = summarize_cases(high_value_df, 'Visiting Country', 'EQV USD').head(10)
        if len(country_exposure) <= 1000:
            fig = _render_count_pie(country_exposure, 'Visiting Country', 'Country Case Concentration (Top 10)')
            st.plotly_chart(fig, use_container_width=True)

    # Transaction Table
    if not high_value_df.empty:
        st.subheader('Suspicious High-Value Transactions')
        _render_investigation_table(high_value_df, key_prefix='hv_transactions')
    else:
        st.info('No high-value transactions detected for the selected filters.')

def _render_fatf_ofac_rule_ui(df: pd.DataFrame, flagged_df, summary):
    """Render the FATF/OFAC rule card."""
    with st.expander('🔍 Filters', expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            selected_fatf_type = st.multiselect(
                'OFAC / FATF Type',
                options=safe_sorted_unique(flagged_df['OFAC _ FATF']) if 'OFAC _ FATF' in flagged_df.columns else [],
                default=None,
                key='fatf_type_filter',
            )
        with col2:
            selected_branches = st.multiselect(
                'Branch',
                options=safe_sorted_unique(df['Branch Name']) if 'Branch Name' in df.columns else [],
                default=None,
                key='fatf_branch_filter',
            )
        with col3:
            selected_countries = st.multiselect(
                'Country',
                options=safe_sorted_unique(df['Visiting Country']) if 'Visiting Country' in df.columns else [],
                default=None,
                key='fatf_country_filter',
            )
        with col4:
            date_range = st.date_input(
                'Date Range',
                value=(df['Date'].min().date() if pd.notna(df['Date'].min()) else datetime.now().date(),
                       df['Date'].max().date() if pd.notna(df['Date'].max()) else datetime.now().date()),
                key='fatf_date_range',
            )

        if selected_fatf_type:
            flagged_df = flagged_df[flagged_df['OFAC _ FATF'].isin(selected_fatf_type)]
        if selected_branches:
            flagged_df = flagged_df[flagged_df['Branch Name'].isin(selected_branches)]
        if selected_countries:
            flagged_df = flagged_df[flagged_df['Visiting Country'].isin(selected_countries)]
        if len(date_range) == 2:
            flagged_df = flagged_df[
                (flagged_df['Date'].dt.date >= date_range[0]) &
                (flagged_df['Date'].dt.date <= date_range[1])
            ]

    # KPIs
    render_kpi_grid([
        ('Flagged Transaction Count', len(flagged_df)),
        ('Total Flagged Amount', human_readable_amount(flagged_df['Net Amt'].sum() if not flagged_df.empty else 0)),
        ('Affected Branches', summary['affected_branches']),
        ('Affected Countries', summary['affected_countries']),
    ])

    # Charts
    if not flagged_df.empty:
        chart_col2, chart_col3 = st.columns(2)

        with chart_col2:
            if 'Branch Name' in flagged_df.columns:
                branch_exp = summarize_cases(flagged_df, 'Branch Name', 'Net Amt').head(10)
                if len(branch_exp) <= 1000:
                    fig = _render_count_bar(branch_exp, 'Branch Name', 'Branch Alert Count')
                    st.plotly_chart(fig, use_container_width=True)

        with chart_col3:
            if 'Visiting Country' in flagged_df.columns:
                country_exp = summarize_cases(flagged_df, 'Visiting Country', 'Net Amt').head(10)
                if len(country_exp) <= 1000:
                    fig = _render_count_pie(country_exp, 'Visiting Country', 'Country Alert Concentration (Top 10)')
                    st.plotly_chart(fig, use_container_width=True)

    # Table
    if not flagged_df.empty:
        st.subheader('FATF / OFAC Flagged Transactions')
        _render_investigation_table(flagged_df, key_prefix='fatf_transactions')
    else:
        st.info('No FATF/OFAC flagged transactions detected for the selected filters.')

def _render_multiple_operators_rule_ui(df: pd.DataFrame, flagged_df, summary):
    """Render the Multiple Operators to Same Beneficiary rule card."""
    with st.expander('🔍 Filters', expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_operators = st.multiselect(
                'Operator',
                options=safe_sorted_unique(flagged_df['Corporate']) if not flagged_df.empty and 'Corporate' in flagged_df.columns else [],
                default=None,
                key='mult_op_operator_filter',
            )
        with col2:
            selected_beneficiaries = st.multiselect(
                'Beneficiary',
                options=safe_sorted_unique(flagged_df['Beneficiary Type Load or Reload']) if not flagged_df.empty and 'Beneficiary Type Load or Reload' in flagged_df.columns else [],
                default=None,
                key='mult_op_beneficiary_filter',
            )
        with col3:
            date_range = st.date_input(
                'Date Range',
                value=(df['Date'].min().date() if pd.notna(df['Date'].min()) else datetime.now().date(),
                       df['Date'].max().date() if pd.notna(df['Date'].max()) else datetime.now().date()),
                key='mult_op_date_range',
            )

        if selected_operators and not flagged_df.empty:
            flagged_df = flagged_df[flagged_df['Corporate'].isin(selected_operators)]
        if selected_beneficiaries and not flagged_df.empty:
            flagged_df = flagged_df[flagged_df['Beneficiary Type Load or Reload'].isin(selected_beneficiaries)]
        if len(date_range) == 2 and not flagged_df.empty:
            flagged_df = flagged_df[
                (flagged_df['Date'].dt.date >= date_range[0]) &
                (flagged_df['Date'].dt.date <= date_range[1])
            ]

    # KPIs
    render_kpi_grid([
        ('Suspicious Beneficiary Count', summary['suspicious_beneficiary_count']),
        ('Flagged Transactions', len(flagged_df)),
        ('Total Exposure', human_readable_amount(flagged_df['Net Amt'].sum() if not flagged_df.empty else 0)),
        ('Unique Operators Involved', flagged_df['Party Code'].nunique() if not flagged_df.empty and 'Party Code' in flagged_df.columns else 0),
    ])

    # Charts
    if not flagged_df.empty:
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            if 'Beneficiary Type Load or Reload' in flagged_df.columns:
                benef_conc = summarize_cases(flagged_df, 'Beneficiary Type Load or Reload', 'Net Amt').head(10)
                if len(benef_conc) <= 1000:
                    fig = _render_count_bar(benef_conc, 'Beneficiary Type Load or Reload', 'Top 10 Beneficiaries by Suspicious Case Count')
                    st.plotly_chart(fig, use_container_width=True)

        with chart_col2:
            if 'Corporate' in flagged_df.columns:
                op_conc = summarize_cases(flagged_df, 'Corporate', 'Net Amt').head(10)
                if len(op_conc) <= 1000:
                    fig = _render_count_bar(op_conc, 'Corporate', 'Top 10 Operators by Suspicious Case Count')
                    st.plotly_chart(fig, use_container_width=True)

    # Table
    if not flagged_df.empty:
        st.subheader('Suspicious Transactions')
        _render_investigation_table(flagged_df, key_prefix='mult_op_transactions')
    else:
        st.info('No suspicious transactions detected for the selected filters.')

def _render_high_frequency_rule_ui(df: pd.DataFrame, flagged_df, summary):
    """Render the High-Frequency Remittances rule card."""
    with st.expander('🔍 Filters', expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_operators = st.multiselect(
                'Operator',
                options=safe_sorted_unique(flagged_df['Corporate']) if not flagged_df.empty and 'Corporate' in flagged_df.columns else [],
                default=None,
                key='hf_operator_filter',
            )
        with col2:
            selected_beneficiaries = st.multiselect(
                'Beneficiary',
                options=safe_sorted_unique(flagged_df['Beneficiary Type Load or Reload']) if not flagged_df.empty and 'Beneficiary Type Load or Reload' in flagged_df.columns else [],
                default=None,
                key='hf_beneficiary_filter',
            )
        with col3:
            date_range = st.date_input(
                'Date Range',
                value=(df['Date'].min().date() if pd.notna(df['Date'].min()) else datetime.now().date(),
                       df['Date'].max().date() if pd.notna(df['Date'].max()) else datetime.now().date()),
                key='hf_date_range',
            )

        if selected_operators and not flagged_df.empty:
            flagged_df = flagged_df[flagged_df['Corporate'].isin(selected_operators)]
        if selected_beneficiaries and not flagged_df.empty:
            flagged_df = flagged_df[flagged_df['Beneficiary Type Load or Reload'].isin(selected_beneficiaries)]
        if len(date_range) == 2 and not flagged_df.empty:
            flagged_df = flagged_df[
                (flagged_df['Date'].dt.date >= date_range[0]) &
                (flagged_df['Date'].dt.date <= date_range[1])
            ]

    # KPIs
    render_kpi_grid([
        ('Repeat Operator-Beneficiary Pairs', summary['repeat_pair_count']),
        ('Flagged Transactions', len(flagged_df)),
        ('Total Exposure', human_readable_amount(flagged_df['Net Amt'].sum() if not flagged_df.empty else 0)),
        ('Avg Txns per Pair', round(len(flagged_df) / summary['repeat_pair_count']) if summary['repeat_pair_count'] > 0 else 0),
    ])

    # Charts
    if not flagged_df.empty:
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            if 'Date' in flagged_df.columns:
                trend = flagged_df.groupby(flagged_df['Date'].dt.date)['Net Amt'].agg(['size', 'sum', 'mean', 'max']).reset_index()
                trend.columns = ['Date', 'Count', 'Total Amount', 'Average Amount', 'Max Amount']
                trend['Previous Count'] = trend['Count'].shift(1).fillna(0).astype(int)
                trend['Count Change'] = trend['Count'] - trend['Previous Count']
                if len(trend) <= 1000:
                    fig = px.line(
                        trend,
                        x='Date',
                        y='Count',
                        title='Repeat Transaction Trend',
                        labels={'Date': 'Date', 'Count': 'Transaction Count'},
                        markers=True,
                        hover_data={
                            'Count': True,
                            'Total Amount': ':,.2f',
                            'Average Amount': ':,.2f',
                            'Max Amount': ':,.2f',
                            'Previous Count': True,
                            'Count Change': True,
                        },
                    )
                    fig.update_layout(height=300, showlegend=False)
                    st.plotly_chart(apply_enterprise_chart_style(fig), use_container_width=True)
                else:
                    st.warning("Chart disabled (exceeds 1000 points)")

        with chart_col2:
            if 'Corporate' in flagged_df.columns:
                op_conc = summarize_cases(flagged_df, 'Corporate', 'Net Amt').head(10)
                if len(op_conc) <= 1000:
                    fig = _render_count_bar(op_conc, 'Corporate', 'Top 10 Operators by Repeat Case Count')
                    st.plotly_chart(fig, use_container_width=True)

    # Table
    if not flagged_df.empty:
        st.subheader('High-Frequency Transactions')
        _render_investigation_table(flagged_df, key_prefix='hf_transactions')
    else:
        st.info('No high-frequency transactions detected for the selected filters.')

def render_transaction_risk_review_table(risk_df: pd.DataFrame, risk_flags: list):
    """Renders the consolidated Transaction Risk Review Table."""
    st.markdown("---")
    
    if 'review_search' not in st.session_state: st.session_state['review_search'] = ""
    if 'review_threshold' not in st.session_state: st.session_state['review_threshold'] = 0

    st.subheader("Transaction Risk Review Table")

    with st.expander("INVESTIGATE ALL TRANSACTIONS (Consolidated View)", expanded=False):
        # Filter Controls
        ctrl1, ctrl2, ctrl3 = st.columns([4, 3, 1])
        
        with ctrl1:
            search_query = st.text_input("Search (Name, Card, Mobile, Code, Beneficiary)", 
                                        value=st.session_state['review_search'], 
                                        key="review_search_input")
        with ctrl2:
            threshold = st.number_input("Minimum Risk Rules Triggered", 
                                       min_value=0, max_value=len(risk_flags), 
                                       value=st.session_state['review_threshold'],
                                       key="review_threshold_input")
        with ctrl3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Reset", use_container_width=True):
                st.session_state['review_search'] = ""
                st.session_state['review_threshold'] = 0
                st.rerun()

        # Update state
        st.session_state['review_search'] = search_query
        st.session_state['review_threshold'] = threshold

        # Filtering Logic
        display_df = risk_df.copy()
        display_df = display_df[display_df['Risk_Rule_Count'] >= threshold]
        
        if search_query:
            search_cols = ['Passenger Name', 'INSTRUMENTNO', 'MOBILENO', 'Corporate', 'Party Code', 'Beneficiary Type Load or Reload']
            cols_to_search = [c for c in search_cols if c in display_df.columns]
            if cols_to_search:
                mask = display_df[cols_to_search].astype(str).apply(
                    lambda x: x.str.contains(search_query, case=False, na=False)
                ).any(axis=1)
                display_df = display_df[mask]

        # Convert Booleans to checkmarks for view
        for flag in risk_flags:
            if flag in display_df.columns:
                display_df[flag] = display_df[flag].apply(lambda x: "✔" if x else "✘")
        
        if 'Any_Risk_Flag' in display_df.columns:
            display_df['Any_Risk_Flag'] = display_df['Any_Risk_Flag'].apply(lambda x: "TRUE" if x else "FALSE")

        st.markdown(f"**Showing {len(display_df):,} transactions matching filters.**")
        
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download filtered review table", data=csv, 
                           file_name="transaction_risk_review.csv", mime="text/csv")
        
        st.dataframe(display_df, use_container_width=True)

def render_transaction_monitoring_page(filtered_df, risk_df, risk_flags):
    """Main transaction monitoring page with isolated AML rule cards."""
    render_page_header(
        'Transaction Monitoring',
        'AML Surveillance Console — Investigate isolated risk rules with independent datasets and controls.',
        df=filtered_df, download_key='download_button_transaction_monitoring'
    )

    if filtered_df is None or filtered_df.empty:
        st.warning('No transaction data available. Check filters and try again.')
        return

    # Share OFAC file via session state
    ofac_file_bytes = st.session_state.get('shared_ofac_file', None)

    high_value_df, structuring_df, summary1 = detect_high_value_transactions(filtered_df)
    
    # Run FATF detection
    fatf_df, summary2 = detect_fatf_ofac(filtered_df, ofac_file_bytes)
    
    mult_op_df, summary3 = detect_multiple_operators_same_beneficiary(filtered_df)
    high_freq_df, summary4 = detect_high_frequency_remittances(filtered_df)
    
    max_days_in_period = max(1, (filtered_df['Date'].max() - filtered_df['Date'].min()).days) if not filtered_df['Date'].empty else 1
    threshold_days = st.session_state.get('load_refund_threshold', 1)
    
    freq_reload_df, freq_reload_sum = detect_configurable_load_refund_window(filtered_df, threshold_days)
    mult_card_contact_df, mult_card_contact_sum = detect_multiple_cards_contact(filtered_df)
    mult_card_trav_df, mult_card_trav_sum = detect_multiple_cards_traveller(filtered_df)
    mult_card_ops_df, mult_card_ops_sum = detect_multiple_cards_multi_operator(filtered_df)

    st.markdown('### Transaction Monitoring Summary')
    summary_data = [
        {
            'Risk Name': 'High Value Transaction',
            'Description': 'Identify transactions exceeding USD 25,000 threshold',
            'Flagged Count': len(high_value_df),
            'Total Exposure': summary1.get('high_value_exposure', 0)
        },
        {
            'Risk Name': 'FATF / OFAC Match',
            'Description': 'Identify transactions involving high-risk jurisdictions',
            'Flagged Count': len(fatf_df),
            'Total Exposure': summary2.get('flagged_amount', 0)
        },
        {
            'Risk Name': 'Multiple Operators to Same Beneficiary',
            'Description': 'Identify multiple operators remitting to same beneficiary',
            'Flagged Count': summary3.get('suspicious_beneficiary_count', 0),
            'Total Exposure': summary3.get('flagged_amount', 0)
        },
        {
            'Risk Name': 'High Frequency Remittances',
            'Description': 'Identify high frequency remittances to same beneficiary',
            'Flagged Count': summary4.get('repeat_pair_count', 0),
            'Total Exposure': summary4.get('flagged_amount', 0)
        },
        {
            'Risk Name': 'Configurable Load-to-Refund Window',
            'Description': f'Identify cards with load/reload and refund within {threshold_days} days',
            'Flagged Count': freq_reload_sum.get('events', 0),
            'Total Exposure': freq_reload_sum.get('exposure', 0)
        },
        {
            'Risk Name': 'Multiple Cards to Same Contact',
            'Description': 'Mobile numbers associated with 3 or more distinct cards',
            'Flagged Count': mult_card_contact_sum.get('count', 0),
            'Total Exposure': mult_card_contact_sum.get('exposure', 0)
        },
        {
            'Risk Name': 'Multiple Cards to Same Traveller',
            'Description': 'Travellers associated with 2 or more distinct cards',
            'Flagged Count': mult_card_trav_sum.get('count', 0),
            'Total Exposure': mult_card_trav_sum.get('exposure', 0)
        },
        {
            'Risk Name': 'Multi-Card Multi-Operator Use',
            'Description': 'Travellers using 2 or more cards across 2 or more operators',
            'Flagged Count': mult_card_ops_sum.get('count', 0),
            'Total Exposure': mult_card_ops_sum.get('exposure', 0)
        }
    ]
    
    summary_df = pd.DataFrame(summary_data)
    
    def style_summary(styler):
        styler.format({
            styler.columns[2]: '{:,}',
            styler.columns[3]: lambda x: f"₹ {x:,.0f}" if x > 0 else "₹ 0"
        })
        styler.set_properties(**{'text-align': 'left'}, subset=[styler.columns[0], styler.columns[1]])
        styler.set_properties(**{'text-align': 'right'}, subset=[styler.columns[2], styler.columns[3]])
        styler.set_table_styles([
            {'selector': 'th', 'props': [
                ('background-color', '#111111'), 
                ('color', '#ffffff'), 
                ('font-weight', 'bold'), 
                ('text-align', 'center'),
                ('text-transform', 'uppercase'), 
                ('font-size', '11px'),
                ('letter-spacing', '0.5px'),
                ('padding', '12px 15px'),
                ('border', '1px solid #444444')
            ]},
            {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#f8f9fa')]},
            {'selector': 'tr:hover', 'props': [('background-color', '#f1f3f5')]},
            {'selector': 'td', 'props': [
                ('padding', '10px 15px'), 
                ('border', '1px solid #dee2e6'),
                ('font-size', '13px')
            ]},
            {'selector': 'table', 'props': [
                ('border-collapse', 'collapse'), 
                ('width', '100%'),
                ('margin-bottom', '20px')
            ]}
        ])
        return styler

    st.table(summary_df.style.pipe(style_summary))

    st.markdown(
        '''
        ### AML Risk Rules
        Each rule below is independently isolated with its own filters, KPIs, and transaction tables.
        One rule does NOT affect another. Investigate each rule separately.
        '''
    )

    with st.expander(f"HIGH VALUE TRANSACTION ({len(high_value_df):,})", expanded=False):
        st.markdown('Detect and monitor transactions exceeding $25,000 USD threshold.')
        _render_high_value_rule_ui(filtered_df, high_value_df, structuring_df, summary1)

    fatf_count_str = f"{len(fatf_df):,}" if ofac_file_bytes is not None else "N/A"
    with st.expander(f"FATF / OFAC FLAGGED TRANSACTIONS ({fatf_count_str})", expanded=False):
        st.markdown('Monitor transactions flagged for FATF/OFAC exposure or high-risk geography.')
        ofac_file_ui = st.file_uploader("Upload OFAC_FATF COUNTRY UPDATED.xlsx", type=['xlsx', 'xls'], key="tm_fatf_uploader_widget")
        
        if ofac_file_ui is not None:
            st.session_state['shared_ofac_file'] = ofac_file_ui.getvalue()
            st.session_state['shared_ofac_filename'] = ofac_file_ui.name
            # Re-evaluate
            fatf_df, summary2 = detect_fatf_ofac(filtered_df, st.session_state['shared_ofac_file'])
        elif 'shared_ofac_file' in st.session_state:
            st.success(f"Using shared file: {st.session_state.get('shared_ofac_filename', 'OFAC_FATF COUNTRY UPDATED.xlsx')}")

        if st.session_state.get('shared_ofac_file', None) is None:
            st.warning("FATF / OFAC analysis unavailable. Please upload FATF reference file.")
        else:
            _render_fatf_ofac_rule_ui(filtered_df, fatf_df, summary2)

    with st.expander(f"MULTIPLE TOUR OPERATORS/REMITTERS TO SAME BENEFICIARY ({len(mult_op_df):,})", expanded=False):
        st.markdown('Detect multiple operators sending remittances to the same beneficiary.')
        _render_multiple_operators_rule_ui(filtered_df, mult_op_df, summary3)

    with st.expander(f"HIGH-FREQUENCY REMITTANCES TO SINGLE BENEFICIARY ({len(high_freq_df):,})", expanded=False):
        st.markdown('Detect single operator sending repeated remittances to same beneficiary.')
        _render_high_frequency_rule_ui(filtered_df, high_freq_df, summary4)

    with st.expander(f"CONFIGURABLE LOAD-TO-REFUND WINDOW ({len(freq_reload_df):,})", expanded=False):
        st.markdown('Identify cards where a refund occurs within a configurable number of days after a load/reload transaction.')
        
        st.session_state['load_refund_threshold'] = st.slider(
            "Load-to-Refund Interval Threshold (Days)",
            min_value=0,
            max_value=max_days_in_period,
            value=st.session_state.get('load_refund_threshold', 1),
            step=1,
            key='load_refund_threshold_slider'
        )
        
        # Re-run detection with threshold
        freq_reload_df, freq_reload_sum = detect_configurable_load_refund_window(filtered_df, st.session_state['load_refund_threshold'])

        render_kpi_grid([
            ('Total Flagged Cards', freq_reload_sum['count']),
            ('Same-Day Events', freq_reload_sum['events']),
            ('Same-Day Refunds', freq_reload_sum['same_day_refunds']),
            ('Average Refund Delay (Days)', f"{freq_reload_sum['avg_delay']:.2f}"),
            ('Minimum Refund Delay (Days)', f"{freq_reload_sum['min_delay']:.0f}"),
            ('Maximum Refund Delay (Days)', f"{freq_reload_sum['max_delay']:.0f}"),
            ('Exposure Amount', human_readable_amount(freq_reload_sum['exposure'])),
        ])
        
        if not freq_reload_df.empty:
            fig = px.histogram(freq_reload_df, x='WITHIN_DAYS', nbins=max_days_in_period + 1,
                               title='Distribution of Refund Delays',
                               labels={'WITHIN_DAYS': 'Days Between Load and Refund', 'count': 'Number of Events'})
            fig.update_layout(bargap=0.1)
            st.plotly_chart(apply_enterprise_chart_style(fig), use_container_width=True)
            
        _render_investigation_table(freq_reload_df, key_prefix='freq_reload')

    with st.expander(f"MULTIPLE CARDS LINKED TO SAME CONTACT INFORMATION ({len(mult_card_contact_df):,})", expanded=False):
        st.markdown('Identify mobile numbers associated with multiple card instruments (>=3 cards).')
        render_kpi_grid([
            ('Flagged Mobile Numbers', mult_card_contact_sum['count']),
            ('Total Linked Cards', f"{mult_card_contact_sum['total_cards']:,}"),
            ('Avg Cards per Mobile', f"{mult_card_contact_sum['total_cards'] / mult_card_contact_sum['count']:.2f}" if mult_card_contact_sum['count'] > 0 else "0.00"),
            ('Highest Card Count', mult_card_contact_sum['max_cards']),
        ])
        if not mult_card_contact_df.empty:
            fig = px.bar(mult_card_contact_df.sort_values('Card_Count', ascending=False).head(15), x='MOBILENO', y='Card_Count', title='Top Mobile Numbers by Linked Card Count')
            st.plotly_chart(apply_enterprise_chart_style(fig), use_container_width=True)
        _render_investigation_table(mult_card_contact_df, key_prefix='mult_card_contact')

    with st.expander(f"MULTIPLE CARDS LINKED TO SAME TRAVELLER NAME ({len(mult_card_trav_df):,})", expanded=False):
        st.markdown('Identify travellers holding multiple card instruments (>=2 cards).')
        render_kpi_grid([
            ('Flagged Travellers', mult_card_trav_sum['count']),
            ('Total Linked Cards', f"{mult_card_trav_sum['total_cards']:,}"),
            ('Avg Cards per Traveller', f"{mult_card_trav_sum['total_cards'] / mult_card_trav_sum['count']:.2f}" if mult_card_trav_sum['count'] > 0 else "0.00"),
            ('Highest Card Count', mult_card_trav_sum['max_cards']),
        ])
        if not mult_card_trav_df.empty:
            fig = px.bar(mult_card_trav_df.sort_values('Card_Count', ascending=False).head(15), x='PAXNAME', y='Card_Count', title='Top Travellers by Linked Card Count')
            st.plotly_chart(apply_enterprise_chart_style(fig), use_container_width=True)
        _render_investigation_table(mult_card_trav_df, key_prefix='mult_card_trav')

    with st.expander(f"MULTIPLE CARDS USED BY SAME TRAVELLER ACROSS DIFFERENT OPERATORS ({len(mult_card_ops_df):,})", expanded=False):
        st.markdown('Identify travellers appearing across multiple operators while using multiple cards (>=2 cards, >=2 operators).')
        render_kpi_grid([
            ('Flagged Travellers', mult_card_ops_sum['count']),
            ('Total Operators Involved', f"{mult_card_ops_sum['total_operators']:,}"),
            ('Total Cards Involved', f"{mult_card_ops_sum['total_cards']:,}"),
            ('Max Operator Count', mult_card_ops_sum['max_operators']),
        ])
        if not mult_card_ops_df.empty:
            fig = px.bar(mult_card_ops_df.sort_values('Operator_Count', ascending=False).head(15), x='PAXNAME', y='Operator_Count', title='Top Travellers by Operator Count')
            st.plotly_chart(apply_enterprise_chart_style(fig), use_container_width=True)
        _render_investigation_table(mult_card_ops_df, key_prefix='mult_card_ops')

    # Consolidated Review Section
    render_transaction_risk_review_table(risk_df, risk_flags)
