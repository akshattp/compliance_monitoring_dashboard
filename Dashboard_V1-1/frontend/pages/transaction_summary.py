import streamlit as st
import pandas as pd
import plotly.express as px
from frontend.ui_helpers.ui import human_readable_amount, render_page_header, render_kpi_grid, render_table_with_options

from backend.services.transaction_summary_service import (
    get_transaction_type_kpis,
    get_transaction_type_breakdown,
    get_txn_composition_data,
    get_purpose_summary_table,
)

def render_transaction_summary_page(filtered_df: pd.DataFrame, risk_df=None, risk_flags=None):
    render_page_header('Transaction Summary', 'Monthly summary of transaction volumes and exposure metrics.', df=filtered_df, download_key='download_button_transaction_summary')

    # --- 1. KPI Section ---
    st.markdown("### Transaction Type Summary")

    st.markdown("""
    <style>
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 20px;
        text-align: left;
        height: 100%;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04);
        margin-bottom: 16px;
    }
    .kpi-title {
        font-size: 15px;
        font-weight: 600;
        color: #555555;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-count {
        font-size: 32px;
        font-weight: 700;
        color: #111111;
        line-height: 1.2;
        margin-bottom: 8px;
    }
    .kpi-amount {
        font-size: 16px;
        font-weight: 500;
        color: #666666;
    }
    </style>
    """, unsafe_allow_html=True)

    txn_types_to_show = ['PS', 'PB', 'CB', 'FB', 'FS', 'BB', 'BS', 'BT']
    kpi_data = get_transaction_type_kpis(filtered_df)

    # Display KPIs in a grid
    for i in range(0, len(txn_types_to_show), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(txn_types_to_show):
                txn_type = txn_types_to_show[i + j]
                data = kpi_data[txn_type]
                with cols[j]:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-title">{txn_type} Transactions</div>
                        <div class="kpi-count">{data['count']:,}</div>
                        <div class="kpi-amount">Amount: {human_readable_amount(data['amount'])}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # --- 2 & 3. Pie Chart and Breakdown Table ---
    st.markdown("---")
    st.subheader("Transaction Analysis by Type")
    
    breakdown = get_transaction_type_breakdown(filtered_df)
    if breakdown:
        txn_by_type = breakdown['txn_by_type']
        display_table = breakdown['display_table']
        
        chart_col, table_col = st.columns([2, 3])

        with chart_col:
            fig_pie = px.pie(
                txn_by_type, names='Txn Type', values='Amount', title='Transaction Amount by Type', hole=0.4,
                custom_data=['Count', 'Amount', '% Contribution']
            )
            fig_pie.update_traces(
                textposition='inside', textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Count: %{customdata[0]:,}<br>Net Amount: %{customdata[1]:,.2f}<br>Contribution: %{customdata[2]:.2f}%<extra></extra>'
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with table_col:
            st.dataframe(
                display_table[['Txn Type', 'Count', 'Count %', 'Amount', 'Amount %']].style.format({
                    'Count': '{:,.0f}', 'Count %': '{:.2f}%', 'Amount': lambda x: human_readable_amount(x), 'Amount %': '{:.2f}%'
                }),
                use_container_width=True, hide_index=True
            )

    # --- 4. Branch & Product Transaction Summary ---
    st.markdown("---")
    
    col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
    with col_c1:
        st.subheader("Transaction Composition Analysis")
    with col_c2:
        global_metric = st.radio(
            "Chart Metric:", ["Count", "Net Amount"], 
            horizontal=True, key='txn_summary_global_metric',
            label_visibility='collapsed'
        )
    with col_c3:
        available_txns = sorted([t for t in filtered_df['Txn Type'].dropna().unique() if str(t).strip()]) if 'Txn Type' in filtered_df.columns else []
        selected_txns = st.multiselect(
            "Transaction Type Filter:",
            options=available_txns,
            default=[],
            key='txn_summary_global_txns',
            label_visibility='collapsed',
            placeholder="All Txn Types (Legend Filter)"
        )

    is_count = (global_metric == 'Count')
    y_col = 'Count' if is_count else 'Total_Amount'
    y_label = 'Transaction Count' if is_count else 'Net Amount'

    def _render_composition_section(group_col, title, x_label, prefix_key):
        comp_data = get_txn_composition_data(filtered_df, group_col, selected_txns, y_col)
        if not comp_data:
            st.info(f"No records available for {title} under current selection.")
            return

        chart_df = comp_data['chart_df']
        display_table = comp_data['display_table']
        total_count = comp_data['total_count']
        total_amt = comp_data['total_amount']
        records_count = comp_data['records_count']

        chart_col, table_col = st.columns([65, 35])
        
        with chart_col:
            unique_groups = len(chart_df[group_col].unique())
            fig_height = max(400, unique_groups * 32 + 100)
            fig = px.bar(
                chart_df, x=y_col, y=group_col, color='Txn Type', orientation='h',
                title=f'{title} Analysis',
                labels={y_col: y_label, group_col: x_label},
                custom_data=['Txn Type', 'Count', 'Count %', 'Total_Amount', 'Net Amount %'],
                barmode='stack'
            )
            fig.update_traces(
                hovertemplate=f'<b>%{{y}}</b><br>Transaction Type: %{{customdata[0]}}<br>Count: %{{customdata[1]:,}}<br>Count %: %{{customdata[2]:.2f}}%<br>Net Amount: %{{customdata[3]:,.2f}}<br>Net Amount %: %{{customdata[4]:.2f}}%<extra></extra>'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, margin={'l': 150}, height=fig_height)
            st.plotly_chart(fig, use_container_width=True)
            
        with table_col:
            st.markdown(f"**{title} Breakdown**")
            st.dataframe(
                display_table[[group_col, 'Count', 'Count %', 'Net Amount', 'Net Amount %']].style.format({
                    'Count': '{:,.0f}',
                    'Count %': '{:.2f}%',
                    'Net Amount': lambda x: human_readable_amount(x) if isinstance(x, (int, float)) else x,
                    'Net Amount %': '{:.2f}%'
                }),
                use_container_width=True, hide_index=True
            )
            
            st.markdown(f"""
            <div style="background-color: #f8fafc; padding: 12px 16px; border: 1px solid #e5e5e5; border-radius: 8px; font-weight: 700; color: #111111; display: flex; justify-content: space-between; font-size: 13px; margin-top: -12px; margin-bottom: 16px;">
                <div>TOTAL RECORDS: {records_count:,}</div>
                <div>TOTAL COUNT: {total_count:,.0f}</div>
                <div>TOTAL NET AMOUNT: {human_readable_amount(total_amt)}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with st.expander("Show Records"):
            search_val = st.text_input("Search records...", key=f"search_{prefix_key}")
            display_records = filtered_df.copy()
            if selected_txns:
                display_records = display_records[display_records['Txn Type'].isin(selected_txns)]

            if 'Risk Score' in display_records.columns:
                display_records = display_records.drop(columns=['Risk Score'])
                
            if search_val:
                mask = display_records.astype(str).apply(lambda col: col.str.contains(search_val, case=False, na=False)).any(axis=1)
                display_records = display_records[mask]
                
            act_c1, act_c2 = st.columns([8, 2])
            with act_c1:
                st.markdown(f"**TOTAL RECORDS DISPLAYED: {len(display_records)}**")
            with act_c2:
                csv = display_records.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", data=csv, file_name=f"{prefix_key}_records.csv", mime="text/csv", key=f"dl_{prefix_key}")
                
            st.dataframe(display_records, use_container_width=True)

    _render_composition_section('Branch Name', 'Branch-wise Transaction Type', 'Branch', 'branch')
    
    st.markdown("---")
    _render_composition_section('Product', 'Product-wise Transaction Type', 'Product', 'product')

    st.markdown("---")
    _render_composition_section('Segments', 'Segment-wise Transaction Type', 'Segment', 'segment')

    st.markdown("---")
    st.subheader('Purpose Summary Table')
    summary = get_purpose_summary_table(filtered_df)
    render_table_with_options(summary, key_prefix='txn_summary_purpose')

    stale = pd.to_datetime(filtered_df['Date']).max() if 'Date' in filtered_df.columns else None
    if stale is not None:
        st.caption(f"Latest transaction date in selection: {stale.date()}")
