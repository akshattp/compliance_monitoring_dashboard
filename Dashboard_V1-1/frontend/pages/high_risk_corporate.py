import pandas as pd
import streamlit as st
import plotly.express as px
from frontend.ui_helpers.ui import render_page_header, render_table_with_options, human_readable_amount

from backend.services.high_risk_corporate_service import (
    enrich_corporate_data,
    get_corporate_risk_kpis,
    get_risk_distribution,
    get_top_corporates,
    get_branch_exposure,
    get_country_exposure,
    get_product_exposure_details,
    get_trend_exposure,
)

def render_high_risk_corporate_page(df: pd.DataFrame, risk_df: pd.DataFrame, risk_flags: list[str]):
    render_page_header('HIGH RISK CORPORATE', 'Automate corporate risk categorization and identify high-risk exposure using the Party Master.', df=df, download_key='download_hrc')

    # ========================================================================
    # 2. PARTY MASTER FILE UPLOAD & ENRICHMENT
    # ========================================================================
    st.markdown('### Party Master Integration')
    col_pm, _ = st.columns([1, 1])
    with col_pm:
        pm_file = st.file_uploader("Upload Party Master New report.csv", type=['csv'], key='pm_uploader')

    if not pm_file:
        st.info("Please upload the **Party Master New report.csv** file to enrich corporate risk categories.")
        return

    try:
        pm_df = pd.read_csv(pm_file)
    except Exception as e:
        st.error(f"Error reading Party Master file: {e}")
        return

    try:
        enriched_df = enrich_corporate_data(df, pm_df)
    except Exception as exc:
        st.error(str(exc))
        return

    # Calculate KPIs in Backend
    kpis = get_corporate_risk_kpis(enriched_df)

    st.markdown('---')
    st.markdown('### Corporate Risk Overview')

    st.markdown("""
    <style>
    .hrc-kpi-card {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 20px;
        position: relative;
        height: 100%;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04);
        margin-bottom: 16px;
    }
    .hrc-kpi-badge {
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
    .hrc-kpi-title {
        font-size: 13px;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .hrc-kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
        line-height: 1.2;
    }
    .hrc-kpi-entity {
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 12px;
        line-height: 1.3;
        word-break: break-word;
    }
    .hrc-kpi-stat {
        font-size: 14px;
        color: #475569;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
    }
    .hrc-kpi-stat strong {
        font-weight: 600;
        color: #0f172a;
        margin-right: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    def _gen_basic_card(title, value1, value2=None):
        val2_html = f'<div class="hrc-kpi-stat" style="margin-top: 8px;">{value2}</div>' if value2 else ''
        return f'''<div class="hrc-kpi-card">
<div class="hrc-kpi-title">{title}</div>
<div class="hrc-kpi-value">{value1}</div>
{val2_html}
</div>'''

    def _gen_intel_card(title, entity, count, exposure, pct):
        badge = f'<div class="hrc-kpi-badge">{pct:.1f}%</div>' if pct else ''
        return f'''<div class="hrc-kpi-card">
{badge}
<div class="hrc-kpi-title">{title}</div>
<div class="hrc-kpi-entity">{entity}</div>
<div class="hrc-kpi-stat"><strong>Count:</strong> {count:,}</div>
<div class="hrc-kpi-stat"><strong>Net Amount:</strong> {human_readable_amount(exposure)}</div>
</div>'''

    kpi_r1 = st.columns(3)
    with kpi_r1[0]: st.markdown(_gen_basic_card("Total Corporates Analyzed", f"{kpis['base_total_corps']:,}"), unsafe_allow_html=True)
    with kpi_r1[1]: st.markdown(_gen_basic_card("High Risk", f"{kpis['high_risk_count']:,}", f"Contribution: {kpis['high_risk_pct']:.1f}%"), unsafe_allow_html=True)
    with kpi_r1[2]: st.markdown(_gen_basic_card("High Risk Amount", human_readable_amount(kpis['high_risk_amount'])), unsafe_allow_html=True)

    kpi_r2 = st.columns(4)
    with kpi_r2[0]: st.markdown(_gen_intel_card("Highest Risk Corporate", kpis['top_corp']['name'], kpis['top_corp']['count'], kpis['top_corp']['exposure'], kpis['top_corp']['pct']), unsafe_allow_html=True)
    with kpi_r2[1]: st.markdown(_gen_intel_card("Highest Risk Product", kpis['top_product']['name'], kpis['top_product']['count'], kpis['top_product']['exposure'], kpis['top_product']['pct']), unsafe_allow_html=True)
    with kpi_r2[2]: st.markdown(_gen_intel_card("Highest Risk Segment", kpis['top_segment']['name'], kpis['top_segment']['count'], kpis['top_segment']['exposure'], kpis['top_segment']['pct']), unsafe_allow_html=True)
    with kpi_r2[3]: st.markdown(_gen_intel_card("Highest Risk Branch", kpis['top_branch']['name'], kpis['top_branch']['count'], kpis['top_branch']['exposure'], kpis['top_branch']['pct']), unsafe_allow_html=True)

    # ========================================================================
    # 5. CHART METRIC CONTROLS
    # ========================================================================
    st.markdown('---')
    col_empty, col_metric = st.columns([3, 1])
    
    with col_metric:
        chart_metric = st.radio(
            "Chart Metric:",
            ["Count", "Net Amount"],
            horizontal=True,
            label_visibility='collapsed',
            key='hrc_metric_toggle'
        )

    # Dynamic variables based on toggle
    target_y = 'Net_Amt' if chart_metric == 'Net Amount' else 'Transaction_Count'
    y_label = 'Net Amount' if chart_metric == 'Net Amount' else 'Count of Transactions'

    st.markdown('---')

    if enriched_df.empty:
        st.warning("No records match the current Risk Category selection.")
        return

    # ========================================================================
    # 5. ADDITIONAL ANALYTICS & CHARTS
    # ========================================================================
    ch_c1, ch_c2 = st.columns(2)

    with ch_c1:
        st.markdown("#### 1. Risk Category Distribution")
        dist_data = get_risk_distribution(enriched_df, target_y)
        fig_dist = px.bar(
            dist_data, x='Risk Classification', y=target_y,
            title="Risk Category Overview",
            text=target_y, labels={target_y: y_label},
            hover_data={'Net_Amt': ':,.2f', 'Transaction_Count': True}
        )
        fig_dist.update_traces(textposition='outside')
        st.plotly_chart(fig_dist, use_container_width=True)

    with ch_c2:
        st.markdown("#### 2. Corporate Concentration (Top 15)")
        corp_data = get_top_corporates(enriched_df, target_y)
        fig_corp = px.bar(
            corp_data, x='Corporate_Code', y=target_y,
            title="Top Corporates by Target Metric",
            text=target_y, labels={target_y: y_label, 'Corporate_Code': 'Corporate Code'},
            hover_data={'Net_Amt': ':,.2f', 'Transaction_Count': True}
        )
        fig_corp.update_traces(textposition='outside')
        st.plotly_chart(fig_corp, use_container_width=True)

    ch_c3, ch_c4 = st.columns(2)

    with ch_c3:
        st.markdown("#### 3. Branch-wise Risk Exposure")
        branch_data = get_branch_exposure(enriched_df, target_y)
        if not branch_data.empty:
            fig_branch = px.bar(
                branch_data.head(30), x=branch_data.columns[0], y=target_y, color='Risk Classification',
                title="Branch Exposure Profile",
                labels={target_y: y_label},
                hover_data={'Net_Amt': ':,.2f', 'Transaction_Count': True}
            )
            st.plotly_chart(fig_branch, use_container_width=True)

    with ch_c4:
        st.markdown("#### 4. Visiting Country-wise Risk Exposure")
        country_data = get_country_exposure(enriched_df, target_y)
        if not country_data.empty:
            fig_country = px.bar(
                country_data.head(30), x='Visiting Country', y=target_y, color='Risk Classification',
                title="Country Exposure Profile",
                labels={target_y: y_label},
                hover_data={'Net_Amt': ':,.2f', 'Transaction_Count': True}
            )
            st.plotly_chart(fig_country, use_container_width=True)

    ch_c5, ch_c6 = st.columns(2)

    with ch_c5:
        st.markdown("#### 5. Product-wise Risk Exposure")
        prod_exposure_details = get_product_exposure_details(enriched_df, target_y)
        if prod_exposure_details:
            product_data = prod_exposure_details['product_data']
            display_prod_table = prod_exposure_details['display_prod_table']
            
            fig_product = px.bar(
                product_data.head(30), x='Product', y=target_y, color='Risk Classification',
                title="Product Exposure Profile",
                labels={target_y: y_label},
                hover_data={'Net_Amt': ':,.2f', 'Transaction_Count': True}
            )
            st.plotly_chart(fig_product, use_container_width=True)
            
            st.markdown("#### Product Breakdown")
            def highlight_total_row(row):
                if row['Product'] == 'TOTAL' or row['Product'] == '**TOTAL**':
                    return [
                        'background-color: #f8fafc; font-weight: bold; border-top: 2px solid #e2e8f0;'
                    ] * len(row)
                return [''] * len(row)
                
            st.dataframe(
                display_prod_table.style.apply(highlight_total_row, axis=1).format({
                    'Count': '{:,.0f}',
                    'Count %': '{:.2f}%',
                    'Net Amount': '${:,.0f}',
                    'Net Amount %': '{:.2f}%'
                }),
                use_container_width=True, hide_index=True
            )

    with ch_c6:
        st.markdown("#### 6. Daily / Weekly Risk Trend")
        if 'Date' in enriched_df.columns:
            trend_agg = st.radio("Trend Aggregation:", ["DAILY", "WEEKLY"], horizontal=True, label_visibility='collapsed', key='hrc_trend_agg')
            trend_data = get_trend_exposure(enriched_df, trend_agg)
            if not trend_data.empty:
                fig_trend = px.line(trend_data, x='Time', y=target_y, color='Risk Classification', title=f"Risk Trend ({trend_agg})", markers=True, labels={target_y: y_label}, hover_data={'Net_Amt': ':,.2f', 'Transaction_Count': True})
                st.plotly_chart(fig_trend, use_container_width=True)

    # ========================================================================
    # 6. TABLE REQUIREMENTS
    # ========================================================================
    st.markdown('---')
    st.markdown('### Related Transaction Records')

    display_df = enriched_df.drop(columns=['Corporate_Code', 'CUSTOMERCODE', 'RISKCATEGORY'], errors='ignore')
    render_table_with_options(display_df, key_prefix='hrc_transactions')
