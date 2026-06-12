import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from frontend.charts import plot_bar, plot_donut, plot_trend
from frontend.ui_helpers.ui import human_readable_amount, render_page_header, render_download_button, render_kpi_grid, render_table_with_options

from backend.services.tour_operator_service import (
    get_tour_operator_kpis,
    get_operator_intelligence,
    get_purpose_mix_data,
    get_branch_composition_data,
    get_corporate_composition_data,
    get_country_combo_data,
    get_tour_operator_observation,
)

def plot_purpose_split(filtered_df: pd.DataFrame):
    purpose_data = get_purpose_mix_data(filtered_df)
    if purpose_data.empty:
        return None
    
    fig = px.pie(
        purpose_data,
        names='Purpose',
        values='Total_Amount',
        title='Tour Operator Purpose Mix',
        color='Purpose',
        color_discrete_map={
            'REMITTANCE BY TOUR OPERATORS': '#111111',
            'MICE - REMITTANCE BY TOUR OPERATORS': '#888888'
        }
    )
    fig.update_traces(textinfo='percent+label', pull=[0.05]*len(purpose_data))
    fig.update_layout(margin={'l': 15, 'r': 15, 't': 45, 'b': 80})
    return fig

def plot_branch_count(branch_data: pd.DataFrame):
    if branch_data.empty:
        return None
    
    fig = px.bar(
        branch_data,
        x='Count',
        y='Branch Name',
        color='Purpose Type',
        orientation='h',
        title='Top Tour Operator Branches (by Occurrence)',
        labels={'Count': 'Transaction Count', 'Branch Name': 'Branch', 'Purpose Type': 'Purpose'},
        text='Count',
        barmode='stack',
        color_discrete_map={
            'REMITTANCE BY TOUR OPERATORS': '#111111',
            'MICE - REMITTANCE BY TOUR OPERATORS': '#888888'
        },
        custom_data=['Purpose Type', 'Formatted_Amt', '% Contribution']
    )
    
    fig.update_traces(
        textposition='inside',
        hovertemplate='<b>%{y}</b><br>Purpose: %{customdata[0]}<br>Count: %{x}<br>Net Amount: %{customdata[1]}<br>Contribution: %{customdata[2]:.1f}%<extra></extra>'
    )
    
    fig.update_layout(
        margin={'l': 150, 'r': 15, 't': 60, 'b': 15},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            title=None
        )
    )
    return fig

def plot_corporate_count(corp_data: pd.DataFrame):
    if corp_data.empty:
        return None
    
    fig = px.bar(
        corp_data,
        x='Count',
        y='Corporate',
        color='Purpose Type',
        orientation='h',
        title='Top Tour Operator',
        labels={'Count': 'Transaction Count', 'Corporate': 'Operator', 'Purpose Type': 'Purpose'},
        text='Count',
        barmode='stack',
        color_discrete_map={
            'REMITTANCE BY TOUR OPERATORS': '#111111',
            'MICE - REMITTANCE BY TOUR OPERATORS': '#888888'
        },
        custom_data=['Purpose Type', 'Formatted_Amt', '% Contribution']
    )
    
    fig.update_traces(
        textposition='inside',
        hovertemplate='<b>%{y}</b><br>Purpose: %{customdata[0]}<br>Count: %{x}<br>Net Amount: %{customdata[1]}<br>Contribution: %{customdata[2]:.1f}%<extra></extra>'
    )
    
    fig.update_layout(
        margin={'l': 150, 'r': 15, 't': 60, 'b': 15},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            title=None
        )
    )
    return fig

def plot_country_combo(country_data: pd.DataFrame):
    if country_data.empty:
        return None
    
    # Create combo figure
    fig = go.Figure()
    
    # Add MICE line
    fig.add_trace(go.Scatter(
        x=country_data['Visiting Country'],
        y=country_data['MICE_Count'],
        name='MICE Remittance (Count)',
        mode='lines+markers',
        yaxis='y',
        line=dict(color='#636EFA', width=3)
    ))
    
    # Add Remittance line
    fig.add_trace(go.Scatter(
        x=country_data['Visiting Country'],
        y=country_data['Remit_Count'],
        name='Remittance (Count)',
        mode='lines+markers',
        yaxis='y',
        line=dict(color='#EF553B', width=3)
    ))
    
    # Add amount bars (secondary y-axis)
    fig.add_trace(go.Bar(
        x=country_data['Visiting Country'],
        y=country_data['Total_Amount'],
        name='Total Amount (USD)',
        yaxis='y2',
        marker=dict(color='#00CC96', opacity=0.6),
        text=['$' + f"{amt:,.0f}" for amt in country_data['Total_Amount']],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Country Operator: Remittance Count (Lines) & Amount (Bars)',
        xaxis=dict(title='Visiting Country'),
        yaxis=dict(title=dict(text='Transaction Count', font=dict(color='#636EFA'))),
        yaxis2=dict(title=dict(text='Amount (USD)', font=dict(color='#00CC96')), overlaying='y', side='right'),
        hovermode='x unified',
        xaxis_tickangle=-45,
        margin={'l': 15, 'r': 60, 't': 60, 'b': 80},
        legend=dict(x=0.01, y=0.99)
    )
    return fig

def render_tour_operator_page(filtered_df: pd.DataFrame, risk_df=None, risk_flags=None):
    render_page_header('Tour Operator', 'Tour operator remittance review with branch, corporate and country concentration analysis.', df=filtered_df, download_key='download_button_tour_operator')

    kpi = get_tour_operator_kpis(filtered_df, risk_df)
    render_kpi_grid([
        ('Tour Operator Txn Count', kpi['total_txn']),
        ('Tour Operator Amount', human_readable_amount(kpi['total_amount'])),
        ('Contribution to PS %', f"{kpi['contribution_to_ps']:.1f}%", 'Tour Operator amount / Total PS amount * 100'),
    ])

    st.markdown("""
    <style>
    .to-kpi-card {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 20px;
        position: relative;
        height: 100%;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04);
        margin-bottom: 16px;
    }
    .to-kpi-title {
        font-size: 14px;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .to-kpi-entity {
        font-size: 18px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 12px;
        line-height: 1.3;
        word-break: break-word;
    }
    .to-kpi-stat {
        font-size: 16px;
        color: #475569;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
    }
    .to-kpi-stat strong {
        font-weight: 600;
        color: #0f172a;
        margin-right: 6px;
        
    }
    </style>
    """, unsafe_allow_html=True)

    def _generate_intelligence_card(title, entity_name, count, count_pct, amount, amount_pct):
        return f"""<div class="to-kpi-card">
<div class="to-kpi-title">{title}</div>
<div class="to-kpi-entity">{entity_name}</div>
<div class="to-kpi-stat"><strong>Count:</strong> {count:,}</div>
<div class="to-kpi-stat"><strong>Count %:</strong> {count_pct:.2f}%</div>
<div class="to-kpi-stat" style="margin-top: 12px;"><strong>Amount:</strong> {human_readable_amount(amount)}</div>
<div class="to-kpi-stat"><strong>Amount %:</strong> {amount_pct:.2f}%</div>
</div>"""

    intel = get_operator_intelligence(filtered_df)

    st.markdown('### Operator Intelligence')
    int_cols = st.columns(4)
    with int_cols[0]:
        st.markdown(_generate_intelligence_card('Best Tour Operator', intel['best_operator']['name'], intel['best_operator']['count'], intel['best_operator']['count_pct'], intel['best_operator']['amount'], intel['best_operator']['amount_pct']), unsafe_allow_html=True)
    with int_cols[1]:
        st.markdown(_generate_intelligence_card('Best Beneficiary', intel['best_beneficiary']['name'], intel['best_beneficiary']['count'], intel['best_beneficiary']['count_pct'], intel['best_beneficiary']['amount'], intel['best_beneficiary']['amount_pct']), unsafe_allow_html=True)
    with int_cols[2]:
        st.markdown(_generate_intelligence_card('Best Branch by Occurrence', intel['best_branch']['name'], intel['best_branch']['count'], intel['best_branch']['count_pct'], intel['best_branch']['amount'], intel['best_branch']['amount_pct']), unsafe_allow_html=True)
    with int_cols[3]:
        st.markdown(_generate_intelligence_card('Best Visiting Country', intel['best_country']['name'], intel['best_country']['count'], intel['best_country']['count_pct'], intel['best_country']['amount'], intel['best_country']['amount_pct']), unsafe_allow_html=True)

    st.markdown('---')

    # Charts
    purpose_fig = plot_purpose_split(filtered_df)
    if purpose_fig:
        st.plotly_chart(purpose_fig, use_container_width=True)

    branch_col, corp_col = st.columns(2)
    
    with branch_col:
        branch_res = get_branch_composition_data(filtered_df)
        if branch_res:
            branch_fig = plot_branch_count(branch_res['branch_data'])
            if branch_fig is not None:
                st.plotly_chart(branch_fig, use_container_width=True)
            st.markdown("**Branch Segment Breakdown**")
            st.dataframe(
                branch_res['display_table'].style.format({
                    'Count': '{:,.0f}', 'Count %': '{:.2f}%',
                    'Net Amt': lambda x: human_readable_amount(x) if isinstance(x, (int, float)) else x,
                    'Net Amt %': '{:.2f}%'
                }),
                use_container_width=True, hide_index=True
            )
    
    with corp_col:
        corp_res = get_corporate_composition_data(filtered_df)
        if corp_res:
            corp_fig = plot_corporate_count(corp_res['corp_data'])
            if corp_fig is not None:
                st.plotly_chart(corp_fig, use_container_width=True)
            st.markdown("**Operator Breakdown**")
            st.dataframe(
                corp_res['display_table'].style.format({
                    'Count': '{:,.0f}', 'Count %': '{:.2f}%',
                    'Net Amount': lambda x: human_readable_amount(x) if isinstance(x, (int, float)) else x,
                    'Net Amount %': '{:.2f}%'
                }),
                use_container_width=True, hide_index=True
            )
            
            st.markdown(f"""
            <div style="background-color: #f8fafc; padding: 12px 16px; border: 1px solid #e5e5e5; border-radius: 8px; font-weight: 700; color: #111111; display: flex; justify-content: space-between; font-size: 13px; margin-top: -12px; margin-bottom: 16px;">
                <div>TOTAL RECORDS: {int(corp_res['total_count']):,}</div>
                <div>TOTAL COUNT: {int(corp_res['total_count']):,}</div>
                <div>TOTAL NET AMOUNT: {human_readable_amount(corp_res['total_amt'])}</div>
            </div>
            """, unsafe_allow_html=True)

    # Country combo chart
    country_data = get_country_combo_data(filtered_df)
    country_fig = plot_country_combo(country_data)
    if country_fig:
        st.plotly_chart(country_fig, use_container_width=True)

    # Trend
    if 'Date' in filtered_df.columns:
        trend_df = filtered_df.groupby('Date').agg(Total_Amount=('Net Amt', 'sum')).reset_index()
        st.plotly_chart(plot_trend(trend_df, 'Date', 'Total_Amount', 'Tour Operator Amount Trend'), use_container_width=True)

    st.markdown('### Drilldown Table')
    render_table_with_options(filtered_df.sort_values('Net Amt', ascending=False), key_prefix='tourop_drilldown')
    st.markdown('### Automated Observation')
    st.info(get_tour_operator_observation(filtered_df))
