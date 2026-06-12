import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from frontend.ui_helpers.ui import human_readable_amount, render_page_header, render_download_button, render_kpi_grid, render_table_with_options
from frontend.charts import plot_bar, plot_donut, plot_trend

from backend.services.retail_high_value_service import (
    classify_retail_risk_level,
    add_retail_risk_classification,
    identify_high_value_transactions,
    calculate_kpis,
    branch_wise_analysis,
    corporate_wise_analysis,
    customer_concentration,
    product_wise_analysis,
    currency_wise_analysis,
    generate_observations,
    format_transaction_table,
)

def plot_risk_distribution(high_value_df):
    if high_value_df.empty or 'Retail_Risk_Level' not in high_value_df.columns:
        return None
    
    risk_dist = high_value_df['Retail_Risk_Level'].value_counts().reset_index()
    risk_dist.columns = ['Risk Level', 'Count']
    
    color_map = {'HIGH': '#ef553b', 'MEDIUM': '#ffa15a', 'LOW': '#00cc96', 'UNKNOWN': '#636363'}
    
    fig = go.Figure(data=[go.Pie(
        labels=risk_dist['Risk Level'],
        values=risk_dist['Count'],
        hole=0.4,
        marker=dict(colors=[color_map.get(level, '#636363') for level in risk_dist['Risk Level']]),
        textposition='inside',
        textinfo='percent+label'
    )])
    fig.update_layout(title='Risk Level Distribution', margin={'l': 15, 'r': 15, 't': 45, 'b': 15})
    return fig

def plot_branch_exposure(branch_data):
    if branch_data.empty:
        return None
    
    top_branches = branch_data.head(15)
    fig = px.bar(
        top_branches,
        x='Total_USD',
        y='Branch Name',
        orientation='h',
        title='Top Branches by High-Value USD Exposure',
        labels={'Total_USD': 'Total USD', 'Branch Name': 'Branch'},
        text='Total_USD'
    )
    fig.update_layout(margin={'l': 120, 'r': 15, 't': 45, 'b': 15})
    return fig

def plot_corporate_exposure(corporate_data):
    if corporate_data.empty:
        return None
    
    top_corps = corporate_data.head(15)
    fig = px.bar(
        top_corps,
        x='Corporate',
        y='Total_USD',
        title='Top Corporates by High-Value USD Exposure',
        labels={'Total_USD': 'Total USD', 'Corporate': 'Corporate'},
        text='Total_USD'
    )
    fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig.update_layout(margin={'l': 15, 'r': 15, 't': 45, 'b': 60}, xaxis_tickangle=-45)
    return fig

def plot_customer_concentration(customer_data):
    if customer_data.empty:
        return None
    
    fig = px.scatter(
        customer_data.head(20),
        x='Transaction_Count',
        y='Total_USD',
        size='Max_USD',
        hover_data=['Passenger Name', 'Avg_USD', 'Branch_Count'],
        title='Top Customers: Transaction Count vs Total USD',
        labels={'Transaction_Count': '# Transactions', 'Total_USD': 'Total USD'},
    )
    fig.update_layout(margin={'l': 15, 'r': 15, 't': 45, 'b': 15})
    return fig

def plot_product_exposure(product_data):
    if product_data.empty:
        return None
    
    fig = px.bar(
        product_data,
        x='Product',
        y='Total_USD',
        title='Product-wise High-Value Exposure',
        labels={'Total_USD': 'Total USD'},
        text='Total_USD'
    )
    fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig.update_layout(margin={'l': 15, 'r': 15, 't': 45, 'b': 60}, xaxis_tickangle=-45)
    return fig

def render_retail_high_value_txn_page(filtered_df, risk_df=None, risk_flags=None):
    render_page_header(
        'Retail High Value TXN',
        'Automated monitoring of high-value retail transactions using USD equivalent thresholds.',
        df=filtered_df, download_key='download_button_retail_high_value_txn'
    )
    
    # Add risk classification and structuring detection
    filtered_df = add_retail_risk_classification(filtered_df)
    
    # Filter high-value transactions (>= 10,000 USD)
    high_value_df = identify_high_value_transactions(filtered_df)
    
    if high_value_df.empty:
        st.warning('No transactions above $10,000 USD are available under the current filters.')
        return
    
    # Calculate KPIs in backend
    kpis = calculate_kpis(high_value_df)
    
    # ========================================================================
    # KPI SECTION
    # ========================================================================
    st.markdown('## High Risk Exposure & Key Performance Indicators')
    
    st.markdown("""
    <style>
    .rhv-kpi-card {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 20px;
        position: relative;
        height: 100%;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04);
        margin-bottom: 16px;
    }
    .rhv-kpi-badge {
        position: absolute;
        top: 16px;
        right: 16px;
        background-color: #f8fafc;
        color: #0f172a;
        font-size: 12px;
        font-weight: 700;
        padding: 4px 8px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
    }
    .rhv-kpi-title {
        font-size: 13px;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .rhv-kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
        line-height: 1.2;
    }
    .rhv-kpi-entity {
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 12px;
        line-height: 1.3;
        word-break: break-word;
    }
    .rhv-kpi-stat {
        font-size: 14px;
        color: #475569;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
    }
    .rhv-kpi-stat strong {
        font-weight: 600;
        color: #0f172a;
        margin-right: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    hr_df = high_value_df[high_value_df['Retail_Risk_Level'] == 'HIGH']
    hr_count = len(hr_df)
    hr_exposure = hr_df['EQV USD'].sum() if not hr_df.empty else 0
    hr_max = hr_df['EQV USD'].max() if not hr_df.empty else 0
    hr_avg = hr_df['EQV USD'].mean() if not hr_df.empty else 0

    def _gen_r1_card(title, value):
        return f'''<div class="rhv-kpi-card">
<div class="rhv-kpi-title">{title}</div>
<div class="rhv-kpi-value">{value}</div>
</div>'''

    def _gen_r2_card(title, entity, count, exposure, pct):
        badge = f'<div class="rhv-kpi-badge">{pct:.1f}%</div>' if pct else ''
        return f'''<div class="rhv-kpi-card">
{badge}
<div class="rhv-kpi-title">{title}</div>
<div class="rhv-kpi-entity">{entity}</div>
<div class="rhv-kpi-stat"><strong>Count:</strong> {count:,}</div>
<div class="rhv-kpi-stat"><strong>USD Exposure:</strong> ${exposure:,.2f}</div>
</div>'''

    kpi_r1 = st.columns(4)
    with kpi_r1[0]: st.markdown(_gen_r1_card("High Risk", f"{hr_count:,}"), unsafe_allow_html=True)
    with kpi_r1[1]: st.markdown(_gen_r1_card("High Risk Exposure", f"${hr_exposure:,.2f}"), unsafe_allow_html=True)
    with kpi_r1[2]: st.markdown(_gen_r1_card("Highest Exposure", f"${hr_max:,.2f}"), unsafe_allow_html=True)
    with kpi_r1[3]: st.markdown(_gen_r1_card("Avg Exposure", f"${hr_avg:,.2f}"), unsafe_allow_html=True)

    def get_top_risk_entity(col):
        if col not in hr_df.columns or hr_df.empty:
            return 'N/A', 0, 0, 0
        agg = hr_df.groupby(col).agg(Count=('EQV USD', 'size'), Exp=('EQV USD', 'sum')).reset_index()
        if agg.empty:
            return 'N/A', 0, 0, 0
        agg = agg.sort_values('Exp', ascending=False)
        top = agg.iloc[0]
        pct = (top['Exp'] / hr_exposure * 100) if hr_exposure > 0 else 0
        return top[col], top['Count'], top['Exp'], pct

    seg_n, seg_c, seg_e, seg_p = get_top_risk_entity('Segments')
    prod_n, prod_c, prod_e, prod_p = get_top_risk_entity('Product')
    br_n, br_c, br_e, br_p = get_top_risk_entity('Branch Name')
    corp_n, corp_c, corp_e, corp_p = get_top_risk_entity('Corporate')

    kpi_r2 = st.columns(4)
    with kpi_r2[0]: st.markdown(_gen_r2_card("Highest Risk Segment", seg_n, seg_c, seg_e, seg_p), unsafe_allow_html=True)
    with kpi_r2[1]: st.markdown(_gen_r2_card("Highest Risk Product", prod_n, prod_c, prod_e, prod_p), unsafe_allow_html=True)
    with kpi_r2[2]: st.markdown(_gen_r2_card("Highest Risk Branch", br_n, br_c, br_e, br_p), unsafe_allow_html=True)
    with kpi_r2[3]: st.markdown(_gen_r2_card("Highest Risk Corporate", corp_n, corp_c, corp_e, corp_p), unsafe_allow_html=True)
    
    st.markdown('---')
    
    # ========================================================================
    # AUTOMATED OBSERVATIONS
    # ========================================================================
    observations = generate_observations(high_value_df, kpis)
    st.markdown('## Automated Compliance Observations')
    st.info(observations)
    
    st.markdown('---')
    
    # ========================================================================
    # RISK ANALYSIS SECTION
    # ========================================================================
    st.markdown('## Risk Analysis & Distribution')
    
    risk_df_filtered = high_value_df[high_value_df['Retail_Risk_Level'].isin(['HIGH', 'MEDIUM', 'LOW'])].copy()
    
    risk_col1, risk_col2 = st.columns(2)
    
    with risk_col1:
        st.markdown('### Risk Level Distribution')
        r_agg = risk_df_filtered.groupby('Retail_Risk_Level').agg(
            Count=('EQV USD', 'size'),
            Net_Amount=('EQV USD', 'sum')
        ).reset_index()
        
        if not r_agg.empty:
            total_r_count = r_agg['Count'].sum()
            total_r_amt = r_agg['Net_Amount'].sum()
            r_agg['Percentage'] = (r_agg['Net_Amount'] / total_r_amt * 100) if total_r_amt > 0 else 0
            
            fig_r = px.pie(
                r_agg, values='Net_Amount', names='Retail_Risk_Level', 
                hole=0.4, title='Risk Level Distribution (USD Exposure)',
                custom_data=['Count', 'Net_Amount', 'Percentage'],
                color='Retail_Risk_Level',
                color_discrete_map={'HIGH': '#ef553b', 'MEDIUM': '#ffa15a', 'LOW': '#00cc96'}
            )
            fig_r.update_traces(
                textposition='inside', textinfo='percent+label',
                hovertemplate='Risk Level: %{label}<br>Count: %{customdata[0]:,}<br>USD Exposure: $%{customdata[1]:,.2f}<br>% Contribution: %{customdata[2]:.2f}%<extra></extra>'
            )
            
            try:
                fig_r = apply_enterprise_chart_style(fig_r)
            except Exception: pass
            
            st.plotly_chart(fig_r, use_container_width=True)
            
            st.markdown('#### Risk Level Breakdown')
            r_table = r_agg.copy()
            r_table['Count %'] = (r_table['Count'] / total_r_count * 100) if total_r_count > 0 else 0
            r_table['Net Amount %'] = (r_table['Net_Amount'] / total_r_amt * 100) if total_r_amt > 0 else 0
            
            r_table_disp = r_table[['Retail_Risk_Level', 'Count', 'Count %', 'Net_Amount', 'Net Amount %']].rename(columns={'Retail_Risk_Level': 'Risk Level', 'Net_Amount': 'Net Amount'})
            total_r_row = pd.DataFrame({'Risk Level': ['**TOTAL**'], 'Count': [total_r_count], 'Count %': [100.0], 'Net Amount': [total_r_amt], 'Net Amount %': [100.0]})
            r_display_table = pd.concat([r_table_disp, total_r_row], ignore_index=True)
            
            st.dataframe(
                r_display_table.style.format({
                    'Count': '{:,.0f}', 'Count %': '{:.2f}%',
                    'Net Amount': '${:,.2f}', 'Net Amount %': '{:.2f}%'
                }),
                use_container_width=True, hide_index=True
            )
    
    with risk_col2:
        st.markdown('### Segment Level Risk')
        if 'Segments' in risk_df_filtered.columns:
            s_agg = risk_df_filtered.groupby(['Segments', 'Retail_Risk_Level']).agg(
                Count=('EQV USD', 'size'),
                Net_Amount=('EQV USD', 'sum')
            ).reset_index()
            
            if not s_agg.empty:
                s_totals = s_agg.groupby('Segments')['Net_Amount'].transform('sum')
                s_agg['% Contribution'] = (s_agg['Net_Amount'] / s_totals * 100).fillna(0)
                s_agg_sort = s_agg.groupby('Segments')['Net_Amount'].sum().reset_index().sort_values('Net_Amount', ascending=False)
                
                fig_s = px.bar(
                    s_agg, x='Segments', y='Count', color='Retail_Risk_Level',
                    title='Segment Level Risk Distribution',
                    barmode='stack', text='Count',
                    custom_data=['Retail_Risk_Level', 'Net_Amount', '% Contribution'],
                    category_orders={'Segments': s_agg_sort['Segments'].tolist()},
                    color_discrete_map={'HIGH': '#ef553b', 'MEDIUM': '#ffa15a', 'LOW': '#00cc96'}
                )
                fig_s.update_traces(
                    textposition='inside',
                    hovertemplate='Segment: %{x}<br>Risk Level: %{customdata[0]}<br>Count: %{y:,}<br>USD Exposure: $%{customdata[1]:,.2f}<br>% Contribution: %{customdata[2]:.1f}%<extra></extra>'
                )
                
                try:
                    fig_s = apply_enterprise_chart_style(fig_s)
                except Exception: pass
                
                st.plotly_chart(fig_s, use_container_width=True)
                
                st.markdown('#### Segment Level Breakdown')
                seg_table = risk_df_filtered.groupby('Segments').agg(Count=('EQV USD', 'size'), Net_Amount=('EQV USD', 'sum')).reset_index().sort_values('Net_Amount', ascending=False)
                total_s_count = seg_table['Count'].sum()
                total_s_amt = seg_table['Net_Amount'].sum()
                
                seg_table['Count %'] = (seg_table['Count'] / total_s_count * 100) if total_s_count > 0 else 0
                seg_table['Net Amount %'] = (seg_table['Net_Amount'] / total_s_amt * 100) if total_s_amt > 0 else 0
                
                seg_table_disp = seg_table[['Segments', 'Count', 'Count %', 'Net_Amount', 'Net Amount %']].rename(columns={'Segments': 'Segment', 'Net_Amount': 'Net Amount'})
                total_s_row = pd.DataFrame({'Segment': ['**TOTAL**'], 'Count': [total_s_count], 'Count %': [100.0], 'Net Amount': [total_s_amt], 'Net Amount %': [100.0]})
                s_display_table = pd.concat([seg_table_disp, total_s_row], ignore_index=True)
                
                st.dataframe(
                    s_display_table.style.format({
                        'Count': '{:,.0f}', 'Count %': '{:.2f}%',
                        'Net Amount': '${:,.2f}', 'Net Amount %': '{:.2f}%'
                    }),
                    use_container_width=True, hide_index=True
                )
        else:
            st.info("Segment data not available for this view.")
    
    st.markdown('---')
    
    # ========================================================================
    # BRANCH & CORPORATE ANALYSIS
    # ========================================================================
    st.markdown('## Branch & Corporate Exposure')
    
    branch_data = branch_wise_analysis(high_value_df)
    corporate_data = corporate_wise_analysis(high_value_df)
    
    branch_col, corp_col = st.columns(2)
    
    with branch_col:
        branch_fig = plot_branch_exposure(branch_data)
        if branch_fig:
            st.plotly_chart(branch_fig, use_container_width=True)
    
    with corp_col:
        corp_fig = plot_corporate_exposure(corporate_data)
        if corp_fig:
            st.plotly_chart(corp_fig, use_container_width=True)
    
    # Branch data table
    with st.expander('📊 Branch-wise Detailed Analysis'):
        if not branch_data.empty:
            render_table_with_options(branch_data, key_prefix='retail_branch_data')
    
    # Corporate data table
    with st.expander('📊 Corporate-wise Detailed Analysis'):
        if not corporate_data.empty:
            render_table_with_options(corporate_data, key_prefix='retail_corporate_data')
    
    st.markdown('---')
    
    # ========================================================================
    # GEOGRAPHIC & CUSTOMER ANALYSIS
    # ========================================================================
    st.markdown('## Geographic & Customer Analysis')
    
    customer_data = customer_concentration(high_value_df)
    
    geo_col1, geo_col2 = st.columns(2)
    
    with geo_col1:
        if 'Visiting Country' in high_value_df.columns:
            st.markdown('### Country Wise High Value Exposure')
            
            country_agg = high_value_df.groupby('Visiting Country').agg(
                Count=('Net Amt', 'size') if 'Net Amt' in high_value_df.columns else ('EQV USD', 'size'),
                Net_Amount=('Net Amt', 'sum') if 'Net Amt' in high_value_df.columns else ('EQV USD', 'sum'),
                EQV_USD=('EQV USD', 'sum')
            ).reset_index()
            
            country_agg = country_agg.sort_values('Count', ascending=False)
            total_count = country_agg['Count'].sum()
            country_agg['Percentage'] = (country_agg['Count'] / total_count * 100) if total_count > 0 else 0
            
            fig_country = px.bar(
                country_agg.head(15), 
                x='Visiting Country', 
                y='Count',
                title='Country Wise High Value Exposure (Top 15)',
                text='Count',
                custom_data=['Net_Amount', 'EQV_USD', 'Percentage']
            )
            
            fig_country.update_traces(
                textposition='outside',
                hovertemplate=(
                    'Visiting Country: %{x}<br>'
                    'Count: %{y}<br>'
                    'Net Amount: %{customdata[0]:,.2f}<br>'
                    'EQV USD: %{customdata[1]:,.2f}<br>'
                    '% Contribution: %{customdata[2]:.2f}%<extra></extra>'
                )
            )
            fig_country.update_layout(
                margin=dict(t=50, b=20, l=20, r=20),
                xaxis_title='Visiting Country',
                yaxis_title='Transaction Count'
            )
            
            try:
                fig_country = apply_enterprise_chart_style(fig_country)
            except Exception:
                pass
                
            st.plotly_chart(fig_country, use_container_width=True)
    
    with geo_col2:
        customer_fig = plot_customer_concentration(customer_data)
        if customer_fig:
            st.plotly_chart(customer_fig, use_container_width=True)
    
    # Customer concentration table
    with st.expander('👥 Top Customers by Total USD Amount'):
        if not customer_data.empty:
            render_table_with_options(customer_data, key_prefix='retail_customer_data')
    
    st.markdown('---')
    
    # ========================================================================
    # TREND ANALYSIS
    # ========================================================================
    st.markdown('## Transaction Trends')
    
    col_time, col_metric = st.columns(2)
    with col_time:
        trend_time = st.radio(
            'Time Aggregation:', 
            ['DAILY', 'WEEKLY'], 
            horizontal=True, 
            key='rhv_trend_time',
            label_visibility='collapsed'
        )
    with col_metric:
        trend_metric = st.radio(
            'Metric Aggregation:', 
            ['COUNT', 'NET AMOUNT'], 
            horizontal=True, 
            key='rhv_trend_metric',
            label_visibility='collapsed'
        )

    if trend_time == 'DAILY':
        if 'Date' in high_value_df.columns:
            trend_df = high_value_df.groupby(high_value_df['Date'].dt.date).agg(
                Count=('EQV USD', 'size'), 
                Net_Amt=('Net Amt', 'sum') if 'Net Amt' in high_value_df.columns else ('EQV USD', 'sum')
            ).reset_index()
            trend_df.rename(columns={'Date': 'Time'}, inplace=True)
        else:
            trend_df = pd.DataFrame()
    else:
        if 'Week' in high_value_df.columns:
            trend_df = high_value_df.groupby('Week').agg(
                Count=('EQV USD', 'size'), 
                Net_Amt=('Net Amt', 'sum') if 'Net Amt' in high_value_df.columns else ('EQV USD', 'sum')
            ).reset_index()
            trend_df.rename(columns={'Week': 'Time'}, inplace=True)
        elif 'Date' in high_value_df.columns:
            trend_df = high_value_df.groupby(pd.Grouper(key='Date', freq='W-MON')).agg(
                Count=('EQV USD', 'size'), 
                Net_Amt=('Net Amt', 'sum') if 'Net Amt' in high_value_df.columns else ('EQV USD', 'sum')
            ).reset_index()
            trend_df['Date'] = trend_df['Date'].dt.date
            trend_df.rename(columns={'Date': 'Time'}, inplace=True)
        else:
            trend_df = pd.DataFrame()

    if not trend_df.empty:
        is_count = (trend_metric == 'COUNT')
        y_col = 'Count' if is_count else 'Net_Amt'
        y_label = 'Transaction Count' if is_count else 'Net Amount'

        fig_trend = px.line(
            trend_df, 
            x='Time', 
            y=y_col, 
            title=f'Transaction Trend ({trend_time} | {trend_metric})', 
            markers=True,
            labels={'Time': 'Date / Week', y_col: y_label}
        )

        try:
            fig_trend = apply_enterprise_chart_style(fig_trend)
        except Exception:
            pass
            
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Time series data not available for trends.")
    
    st.markdown('---')
    
    # ========================================================================
    # PRODUCT & CURRENCY ANALYSIS
    # ========================================================================
    st.markdown('## Product & Currency Exposure')
    
    product_data = product_wise_analysis(high_value_df)
    
    prod_col, curr_col = st.columns(2)
    
    with prod_col:
        product_fig = plot_product_exposure(product_data)
        if product_fig:
            st.plotly_chart(product_fig, use_container_width=True)

            st.markdown("#### Product Breakdown")
            prod_table_data = product_data.copy()

            total_count = prod_table_data['Transaction_Count'].sum()
            total_usd = prod_table_data['Total_USD'].sum()

            prod_table_data['Count %'] = (
                prod_table_data['Transaction_Count'] / total_count * 100
            ) if total_count > 0 else 0

            prod_table_data['USD Exposure %'] = (
                prod_table_data['Total_USD'] / total_usd * 100
            ) if total_usd > 0 else 0

            prod_table_data = prod_table_data.rename(
                columns={
                    'Transaction_Count': 'Count',
                    'Total_USD': 'USD Exposure'
                }
            )

            total_row = pd.DataFrame({
                'Product': ['TOTAL'],
                'Count': [total_count],
                'Count %': [100.0],
                'USD Exposure': [total_usd],
                'USD Exposure %': [100.0]
            })

            display_prod_table = pd.concat(
                [
                    prod_table_data[
                        ['Product', 'Count', 'Count %', 'USD Exposure', 'USD Exposure %']
                    ],
                    total_row
                ],
                ignore_index=True
            )

            def highlight_total_row(row):
                if row['Product'] == '**TOTAL**':
                    return [
                        'background-color: #f8fafc; font-weight: bold; border-top: 2px solid #e2e8f0;'
                    ] * len(row)
                return [''] * len(row)

            st.dataframe(
                display_prod_table.style.apply(
                    highlight_total_row, axis=1
                ).format({
                    'Count': '{:,.0f}',
                    'Count %': '{:.2f}%',
                    'USD Exposure': '${:,.2f}',
                    'USD Exposure %': '{:.2f}%'
                }),
                use_container_width=True,
                hide_index=True
            )
    
    with curr_col:
        if 'Currency' in high_value_df.columns:
            st.markdown('### Currency Wise High Value Exposure')
            
            curr_agg = high_value_df.groupby('Currency').agg(
                Count=('EQV USD', 'size'),
                Net_Amount=('Net Amt', 'sum') if 'Net Amt' in high_value_df.columns else ('EQV USD', 'sum')
            ).reset_index()
            
            curr_agg = curr_agg.sort_values('Net_Amount', ascending=False)
            total_val = curr_agg['Net_Amount'].sum()
            curr_agg['Percentage'] = (curr_agg['Net_Amount'] / total_val * 100) if total_val > 0 else 0
            
            threshold = st.number_input('Enter Threshold %', min_value=0.0, max_value=100.0, value=1.0, step=0.5, key='rhv_currency_thresh')
            
            below_thresh = curr_agg['Percentage'] < threshold
            others_df = curr_agg[below_thresh].copy()
            main_df = curr_agg[~below_thresh].copy()
            
            if not others_df.empty:
                others_row = pd.DataFrame([{
                    'Currency': 'Others',
                    'Count': others_df['Count'].sum(),
                    'Net_Amount': others_df['Net_Amount'].sum(),
                    'Percentage': others_df['Percentage'].sum()
                }])
                plot_df = pd.concat([main_df, others_row], ignore_index=True)
            else:
                plot_df = main_df.copy()
                
            fig_curr = px.pie(
                plot_df,
                values='Net_Amount',
                names='Currency',
                title='Currency Wise Amount Share',
                hole=0.4,
                custom_data=['Count', 'Net_Amount']
            )
            
            fig_curr.update_traces(
                hovertemplate='Currency: %{label}<br>Transaction Count: %{customdata[0]}<br>Net Amount: %{customdata[1]:,.2f}<br>Percentage Share: %{percent}<extra></extra>',
                textinfo='percent+label',
                textposition='outside'
            )
            fig_curr.update_layout(margin=dict(t=50, b=20, l=20, r=20), showlegend=False)
            
            try:
                fig_curr = apply_enterprise_chart_style(fig_curr)
            except Exception:
                pass
                
            st.plotly_chart(fig_curr, use_container_width=True)
            
            if not others_df.empty:
                st.markdown('**Others Category Breakdown**')
                display_df = others_df[['Currency', 'Count', 'Net_Amount', 'Percentage']].copy()
                display_df.rename(columns={'Net_Amount': 'Net Amount', 'Percentage': 'Percentage Contribution'}, inplace=True)
                display_df['Percentage Contribution'] = display_df['Percentage Contribution'].apply(lambda x: f"{x:.2f}%")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                st.info("NOTE: The 'Others' category contains currencies whose contribution falls below the selected threshold percentage.")
    
    st.markdown('---')
    
    # ========================================================================
    # DETAILED TRANSACTION TABLE
    # ========================================================================
    st.markdown('## Detailed High-Value Transaction Listing')
    
    transaction_table = format_transaction_table(high_value_df)
    if not transaction_table.empty:
        render_table_with_options(transaction_table, key_prefix='retail_transaction_table')
    
    st.markdown('---')
    
    # ========================================================================
    # DOWNLOAD DETAILED REPORT
    # ========================================================================
    st.markdown('## Export Data')
    col_export1, col_export2 = st.columns(2)
    
    with col_export1:
        if not high_value_df.empty:
            csv_data = high_value_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label='📥 Download High-Value Transactions',
                data=csv_data,
                file_name='high_value_transactions.csv',
                mime='text/csv',
                key='download_hvt'
            )
    
    with col_export2:
        if not customer_data.empty:
            csv_data = customer_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label='📥 Download Customer Concentration',
                data=csv_data,
                file_name='customer_concentration.csv',
                mime='text/csv',
                key='download_cust'
            )
