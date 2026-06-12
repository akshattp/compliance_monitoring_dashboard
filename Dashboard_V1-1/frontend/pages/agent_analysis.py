import pandas as pd
import streamlit as st
import plotly.express as px

from frontend.ui_helpers.ui import render_page_header, render_table_with_options, human_readable_amount

from backend.services.agent_analysis_service import (
    get_agent_kpis,
    get_agent_frequency_table,
    get_agent_trend_table,
    get_suspicious_agents_many,
    get_suspicious_agents1_many_relation,
    get_suspicious_agents1_one_relation
)

def render_agent_analysis_page(df: pd.DataFrame, risk_df: pd.DataFrame, risk_flags: list[str]):
    render_page_header('AGENT ANALYSIS', df=df, download_key='download_button_agent_analysis')
    agent_col = 'Agent Name' if 'Agent Name' in df.columns else ('Agent' if 'Agent' in df.columns else None)
    if not agent_col:
        st.warning('Agent or Agent Name column is required for agent analysis.')
        return

    branch_col = 'Branch Name' if 'Branch Name' in df.columns else ('Branch' if 'Branch' in df.columns else None)
    possible_benef_cols = ['Beneficiary Type Load or Reload', 'Benificiary Type Load or Reload', 'Beneficiary']
    benef_col = next((c for c in possible_benef_cols if c in df.columns), None)

    # Load calculated KPIs & subsets from Backend
    kpis = get_agent_kpis(df, agent_col, branch_col, benef_col)
    if not kpis:
        st.warning('No agent metrics could be retrieved.')
        return

    agent_df = kpis['agent_df']
    beneficiary_df = kpis['beneficiary_df']
    total_agents = kpis['total_agents']
    total_net_amt_agent = kpis['total_net_amt_agent']
    contrib_pct = kpis['contrib_pct']

    st.markdown('### Key Performance Indicators')
    st.markdown("""
    <style>
    .agent-kpi-card {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 20px;
        position: relative;
        height: 100%;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04);
        margin-bottom: 16px;
    }
    .agent-kpi-badge {
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
    .agent-kpi-title {
        font-size: 13px;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .agent-kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
        line-height: 1.2;
    }
    .agent-kpi-entity {
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 12px;
        line-height: 1.3;
        word-break: break-word;
    }
    .agent-kpi-stat {
        font-size: 14px;
        color: #475569;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
    }
    .agent-kpi-stat strong {
        font-weight: 600;
        color: #0f172a;
        margin-right: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    def _gen_basic_card(title, value1, value2=None):
        val2_html = f'<div class="agent-kpi-stat" style="margin-top: 8px;">{value2}</div>' if value2 else ''
        return f'''<div class="agent-kpi-card">
<div class="agent-kpi-title">{title}</div>
<div class="agent-kpi-value">{value1}</div>
{val2_html}
</div>'''

    def _gen_intel_card(title, entity, count, pct):
        badge = f'<div class="agent-kpi-badge">{pct:.1f}%</div>' if pct else ''
        return f'''<div class="agent-kpi-card">
{badge}
<div class="agent-kpi-title">{title}</div>
<div class="agent-kpi-entity">{entity}</div>
<div class="agent-kpi-stat"><strong>Agent Count:</strong> {count:,}</div>
</div>'''

    kpi_r1 = st.columns(4)
    with kpi_r1[0]: st.markdown(_gen_basic_card("Total Number of Agents", f"{total_agents:,}"), unsafe_allow_html=True)
    with kpi_r1[1]: st.markdown(_gen_basic_card("Total Agent Contribution", human_readable_amount(total_net_amt_agent)), unsafe_allow_html=True)
    with kpi_r1[2]: st.markdown(_gen_basic_card("Contribution to Net Amount", f"{contrib_pct:.1f}%"), unsafe_allow_html=True)
    
    seg_name, seg_count, seg_pct = kpis['seg']
    with kpi_r1[3]: st.markdown(_gen_intel_card("Segment with Most Agents", seg_name, seg_count, seg_pct), unsafe_allow_html=True)

    kpi_r2 = st.columns(4)
    prod_name, prod_count, prod_pct = kpis['product']
    purp_name, purp_count, purp_pct = kpis['purpose']
    br_name, br_count, br_pct = kpis['branch']
    ctry_name, ctry_count, ctry_pct = kpis['country']

    with kpi_r2[0]: st.markdown(_gen_intel_card("Product with Most Agents", prod_name, prod_count, prod_pct), unsafe_allow_html=True)
    with kpi_r2[1]: st.markdown(_gen_intel_card("Purpose with Most Agents", purp_name, purp_count, purp_pct), unsafe_allow_html=True)
    with kpi_r2[2]: st.markdown(_gen_intel_card("Branch with Most Agents", br_name, br_count, br_pct), unsafe_allow_html=True)
    with kpi_r2[3]: st.markdown(_gen_intel_card("Country with Most Agents", ctry_name, ctry_count, ctry_pct), unsafe_allow_html=True)

    st.markdown('---')
    col_c1, col_c2 = st.columns([3, 1])
    with col_c1:
        st.markdown('### 1. AGENT FREQUENCY')
    with col_c2:
        chart_metric = st.radio(
            'Chart Metric:', 
            ['Count', 'Net Amount'], 
            horizontal=True, 
            key='agent_chart_metric',
            label_visibility='collapsed'
        )

    y_col = 'Count' if chart_metric == 'Count' else 'Net_Amt'
    y_label = 'Transaction Count' if chart_metric == 'Count' else 'Net Amount'

    def _render_agent_chart_ui(df_in, group_col, title, x_label, prefix_key):
        if not group_col or group_col not in df_in.columns:
            return
        
        agg_df, display_table = get_agent_frequency_table(df_in, group_col, y_col)
        if agg_df.empty:
            return
            
        chart_df = agg_df.sort_values(y_col, ascending=False).head(20)
        chart_col, table_col = st.columns([65, 35])
        
        with chart_col:
            fig = px.bar(chart_df, x=group_col, y=y_col, title=title, 
                         custom_data=['Count', 'Net_Amt', '% Contribution'],
                         labels={y_col: y_label, group_col: x_label}, text=y_col)
            fig.update_traces(
                textposition='outside',
                texttemplate='%{text:,.0f}' if chart_metric == 'Count' else '%{text:,.3s}',
                hovertemplate=f'<b>{x_label}:</b> %{{x}}<br>Count: %{{customdata[0]:,}}<br>Net Amount: %{{customdata[1]:,.2f}}<br>Contribution: %{{customdata[2]:.2f}}%<extra></extra>'
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with table_col:
            st.markdown(f"**{title} Breakdown**")
            
            def highlight_total_row(row):
                if row['Category'] == '**TOTAL**':
                    return ['background-color: #f8fafc; font-weight: bold; border-top: 2px solid #e2e8f0;'] * len(row)
                return [''] * len(row)
                
            st.dataframe(
                display_table[['Category', 'Count', 'Count %', 'Net Amount', 'Net Amount %']].style.apply(highlight_total_row, axis=1).format({
                    'Count': '{:,.0f}',
                    'Count %': '{:.2f}%',
                    'Net Amount': lambda x: human_readable_amount(x) if isinstance(x, (int, float)) else x,
                    'Net Amount %': '{:.2f}%'
                }),
                use_container_width=True, hide_index=True
            )
            
        with st.expander("Show Records"):
            act_c1, act_c2 = st.columns([8, 2])
            with act_c1:
                st.markdown(f"**TOTAL RECORDS DISPLAYED: {len(df_in)}**")
            with act_c2:
                csv = df_in.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", data=csv, file_name=f"{prefix_key}_records.csv", mime="text/csv", key=f"dl_{prefix_key}")
            
            search_val = st.text_input("Search records...", key=f"search_{prefix_key}")
            display_records = df_in.copy()
            if search_val:
                mask = display_records.astype(str).apply(lambda col: col.str.contains(search_val, case=False, na=False)).any(axis=1)
                display_records = display_records[mask]
                
            st.dataframe(display_records, use_container_width=True)

    _render_agent_chart_ui(agent_df, agent_col, 'Agent Frequency (Top 20)', 'Agent', 'freq')

    st.markdown('---')
    if 'Date' in agent_df.columns:
        t_col1, t_col2 = st.columns([3, 1])
        with t_col1:
            st.markdown('### 2. OVERALL AGENT TREND')
        with t_col2:
            trend_agg = st.radio(
                'Select Aggregation:', 
                ['DAILY', 'WEEKLY'], 
                horizontal=True, 
                key='agent_trend_agg',
                label_visibility='collapsed'
            )
        
        trend_df, display_trend_table = get_agent_trend_table(agent_df, trend_agg)
        if not trend_df.empty:
            t_chart_col, t_table_col = st.columns([65, 35])
            
            with t_chart_col:
                fig2 = px.line(trend_df, x='Time', y=y_col, title=f'Agent Trend ({trend_agg})', markers=True, labels={y_col: y_label})
                st.plotly_chart(fig2, use_container_width=True)
                
            with t_table_col:
                st.markdown(f"**Overall Agent Trend Breakdown**")
                
                def highlight_total_row_trend(row):
                    if row['Category'] == '**TOTAL**':
                        return ['background-color: #f8fafc; font-weight: bold; border-top: 2px solid #e2e8f0;'] * len(row)
                    return [''] * len(row)
                    
                st.dataframe(
                    display_trend_table[['Category', 'Count', 'Count %', 'Net Amount', 'Net Amount %']].style.apply(highlight_total_row_trend, axis=1).format({
                        'Count': '{:,.0f}',
                        'Count %': '{:.2f}%',
                        'Net Amount': lambda x: human_readable_amount(x) if isinstance(x, (int, float)) else x,
                        'Net Amount %': '{:.2f}%'
                    }),
                    use_container_width=True, hide_index=True
                )
                
            with st.expander("Show Records"):
                act_c1, act_c2 = st.columns([8, 2])
                with act_c1:
                    st.markdown(f"**TOTAL RECORDS DISPLAYED: {len(agent_df)}**")
                with act_c2:
                    csv = agent_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download CSV", data=csv, file_name="agent_trend_records.csv", mime="text/csv", key="dl_agent_trend")
                
                search_val = st.text_input("Search records...", key="search_agent_trend")
                display_records = agent_df.copy()
                if search_val:
                    mask = display_records.astype(str).apply(lambda col: col.str.contains(search_val, case=False, na=False)).any(axis=1)
                    display_records = display_records[mask]
                    
                st.dataframe(display_records, use_container_width=True)
    else:
        st.markdown('### 2. OVERALL AGENT TREND')
        st.info('Date column not available for trend analysis.')
        
    st.markdown('---')
    st.markdown('### 3. BRANCH-WISE AGENT ANALYSIS')
    _render_agent_chart_ui(agent_df, branch_col, 'Branch-wise Agent Analysis', 'Branch', 'branch')
        
    st.markdown('---')
    st.markdown('### 4. VISITING COUNTRY-WISE AGENT ANALYSIS')
    _render_agent_chart_ui(agent_df, 'Visiting Country', 'Visiting Country-wise Agent Analysis', 'Visiting Country', 'country')
        
    st.markdown('---')
    st.markdown('### 5. CORPORATE-WISE AGENT ANALYSIS')
    _render_agent_chart_ui(agent_df, 'Corporate', 'Corporate-wise Agent Analysis', 'Corporate', 'corp')
        
    st.markdown('---')
    st.markdown('### 6. BENEFICIARY-WISE AGENT ANALYSIS')
    _render_agent_chart_ui(beneficiary_df, benef_col, 'Beneficiary-wise Agent Analysis', 'Beneficiary', 'benef')
    
    st.markdown('---')
    st.markdown('### 7. PRODUCT WISE AGENT ANALYSIS')
    _render_agent_chart_ui(agent_df, 'Product', 'Product Wise Agent Analysis', 'Product', 'product')
    
    st.markdown('---')
    st.markdown('### 8. PURPOSE WISE AGENT ANALYSIS')
    _render_agent_chart_ui(agent_df, 'Purpose', 'Purpose Wise Agent Analysis', 'Purpose', 'purpose')
        
    st.markdown('---')
    st.markdown('## SUSPICIOUS AGENT ANALYSIS')
    
    def render_investigation_section_ui(df_sub, group_col, target_col, title, rule_key):
        st.markdown(f'#### {title}')
        if target_col not in df_sub.columns:
            st.info(f'{target_col} column is missing.')
            return
        
        threshold = st.number_input('Enter Threshold', min_value=1, value=10, step=1, key=f'{rule_key}_thresh')
        
        suspicious_agents, related_records = get_suspicious_agents_many(df_sub, group_col, target_col, threshold)
        
        if suspicious_agents.empty:
            st.success('No suspicious records found for this rule.')
        else:
            st.warning(f'Found {len(suspicious_agents)} suspicious agents.')
            st.dataframe(suspicious_agents.rename(columns={'unique_targets': f'{target_col} Count', 'txn_count': 'Transaction Count', 'total_amt': 'Total Net Amount'}))
            
            render_table_with_options(related_records, key_prefix=f'{rule_key}_table')
            
            csv = related_records.to_csv(index=False).encode('utf-8')
            st.download_button('Download suspicious records', data=csv, file_name=f'{rule_key}_suspicious.csv', mime='text/csv', key=f'{rule_key}_dl')
            
    if benef_col:
        st.markdown('#### RULE 1: AGENT-BENEFICIARY RELATIONSHIP')
        
        rule1_mode = st.radio(
            'Rule 1 Mode:', 
            ['1 → Many', '1 → 1'], 
            horizontal=True, 
            key='rule1_mode',
            label_visibility='collapsed'
        )
        
        if rule1_mode == '1 → Many':
            st.markdown('**RULE 1: ONE AGENT FOR DIFFERENT BENEFICIARIES**')
            threshold = st.number_input('Enter Threshold', min_value=1, value=10, step=1, key='rule1_many_thresh')
            
            grp, display_df, sub_df = get_suspicious_agents1_many_relation(beneficiary_df, agent_col, benef_col, threshold)
            
            if grp.empty:
                st.success('No suspicious records found for this rule.')
            else:
                st.warning(f'Found {grp["Agent"].nunique()} suspicious agents.')
                
                search_query = st.text_input('Search suspicious records', key='rule1_many_search')
                if search_query:
                    mask = display_df.astype(str).apply(lambda col: col.str.contains(search_query, case=False, na=False)).any(axis=1)
                    mask.iloc[-1] = True
                    display_df = display_df[mask]
                    
                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button('Download suspicious records', data=csv, file_name='rule1_many_suspicious.csv', mime='text/csv', key='rule1_many_dl')
                
                def highlight_total_row(row):
                    if row['Agent'] == '**TOTAL**':
                        return ['background-color: #f8fafc; font-weight: bold; border-top: 2px solid #e2e8f0;'] * len(row)
                    return [''] * len(row)
                
                st.dataframe(
                    display_df.style.apply(highlight_total_row, axis=1).format({
                        'Transaction Count': '{:,.0f}',
                        'Net Amount': lambda x: human_readable_amount(x) if isinstance(x, (int, float)) else x
                    }),
                    use_container_width=True, hide_index=True
                )
                
                st.markdown("##### Related Transaction Records")
                render_table_with_options(sub_df, key_prefix='rule1_many_table')

        else:
            st.markdown('**RULE 1A: ONE AGENT TO ONE BENEFICIARY**')
            threshold = st.number_input('Enter Threshold', min_value=1, value=10, step=1, key='rule1_one_thresh')
            
            suspicious_pairs, display_df, sub_df = get_suspicious_agents1_one_relation(beneficiary_df, agent_col, benef_col, threshold)
            
            if suspicious_pairs.empty:
                st.success('No suspicious records found for this rule.')
            else:
                st.warning(f'Found {len(suspicious_pairs)} suspicious agent-beneficiary relationships.')
                
                search_query = st.text_input('Search suspicious records', key='rule1_one_search')
                if search_query:
                    mask = display_df.astype(str).apply(lambda col: col.str.contains(search_query, case=False, na=False)).any(axis=1)
                    mask.iloc[-1] = True
                    display_df = display_df[mask]
                    
                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button('Download suspicious records', data=csv, file_name='rule1_one_suspicious.csv', mime='text/csv', key='rule1_one_dl')
                
                def highlight_total_row(row):
                    if row['Agent'] == '**TOTAL**':
                        return ['background-color: #f8fafc; font-weight: bold; border-top: 2px solid #e2e8f0;'] * len(row)
                    return [''] * len(row)
                
                st.dataframe(
                    display_df.style.apply(highlight_total_row, axis=1).format({
                        'Transaction Count': '{:,.0f}',
                        'Net Amount': lambda x: human_readable_amount(x) if isinstance(x, (int, float)) else x
                    }),
                    use_container_width=True, hide_index=True
                )
                
                st.markdown("##### Related Transaction Records")
                render_table_with_options(sub_df, key_prefix='rule1_one_table')
        
        st.markdown('---')
        
    if 'Corporate' in beneficiary_df.columns:
        render_investigation_section_ui(beneficiary_df, agent_col, 'Corporate', 'RULE 2: ONE AGENT FOR DIFFERENT CORPORATES', 'rule2')
        st.markdown('---')
    if branch_col:
        render_investigation_section_ui(beneficiary_df, agent_col, branch_col, 'RULE 3: ONE AGENT FOR DIFFERENT BRANCHES', 'rule3')
        st.markdown('---')
    if 'Visiting Country' in beneficiary_df.columns:
        render_investigation_section_ui(beneficiary_df, agent_col, 'Visiting Country', 'RULE 4: ONE AGENT FOR DIFFERENT VISITING COUNTRIES', 'rule4')
