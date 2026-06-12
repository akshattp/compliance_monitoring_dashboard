import streamlit as st
import pandas as pd
import plotly.express as px

from frontend.charts import plot_bar, plot_donut, plot_trend, plot_branch_comparison
from frontend.charts.theme import apply_enterprise_chart_style
from frontend.ui_helpers.ui import human_readable_amount, render_table_with_options

from backend.services.home_service import get_home_kpis, get_home_trends, get_home_breakdowns

def build_download_button(df: pd.DataFrame):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label='Download filtered transactions',
        data=csv,
        file_name='filtered_transactions.csv',
        mime='text/csv',
    )

def render_kpi_cards(kpis: dict):
    # ROW 1
    cols1 = st.columns(5)
    cols1[0].metric('Total Transactions Recorded', f"{kpis['total_transactions']:,}")
    cols1[1].metric('Total Transaction Amount', human_readable_amount(kpis['total_net_amt']))
    cols1[2].metric('Average Transaction Value', human_readable_amount(kpis['average_transaction']))
    cols1[3].metric('Highest Single Transaction Value', human_readable_amount(kpis['highest_transaction']), f"{kpis['highest_pct']:.2f}% of Total Amount")
    cols1[4].metric('Lowest Single Transaction Value', human_readable_amount(kpis['lowest_transaction']), f"-{kpis['lowest_pct']:.2f}% of Total Amount")

    st.markdown('---')
    
    # ROW 2
    cols2 = st.columns(4)
    cols2[0].metric('PS Count', f"{kpis['ps_count']:,}", f"{kpis['ps_count_pct']:.1f}%")
    cols2[1].metric('Total PS Amount', human_readable_amount(kpis['ps_amount']), f"{kpis['ps_amt_pct']:.1f}%")
    cols2[2].metric('PB Count', f"{kpis['pb_count']:,}", f"-{kpis['pb_count_pct']:.1f}%")
    cols2[3].metric('Total PB Amount', human_readable_amount(kpis['pb_amount']), f"-{kpis['pb_amt_pct']:.1f}%")
    
    st.markdown('---')
    
    # ROW 3
    cols3 = st.columns(3)
    cols3[0].metric('Date Range', kpis['date_range'])
    cols3[1].metric('Best Segment', f"{kpis['best_segment_name']} | {human_readable_amount(kpis['best_segment_amt'])}", f"{kpis['best_segment_pct']:.1f}% of Total Amount")
    cols3[2].metric('Best Branch', f"{kpis['best_branch_name']} | {human_readable_amount(kpis['best_branch_amt'])}", f"{kpis['best_branch_pct']:.1f}% of Total Amount")

def render_overall_highlights(df: pd.DataFrame):
    if 'Date' not in df.columns or df['Date'].isna().all():
        st.warning('Date field is missing or invalid for trend analysis.')
        return

    col_title, col_toggle = st.columns([3, 1])
    with col_title:
        st.markdown('### Transaction Trend Highlights')
    with col_toggle:
        trend_agg = st.radio(
            'Select Aggregation:', 
            ['DAILY', 'WEEKLY'], 
            horizontal=True, 
            key='home_trend_agg',
            label_visibility='collapsed'
        )

    trends = get_home_trends(df, trend_agg)
    if not trends:
        st.info("Trend data is empty.")
        return

    agg_df = trends['agg_df']
    time_label = 'Day' if trend_agg == 'DAILY' else 'Week'
    
    highest_amount_time = trends['highest_amount_time']
    lowest_amount_time = trends['lowest_amount_time']
    highest_count_time = trends['highest_count_time']
    lowest_count_time = trends['lowest_count_time']

    def format_time(t):
        if hasattr(t, 'strftime'):
            return t.strftime('%Y-%m-%d')
        return str(t)

    cols = st.columns(4)
    cols[0].metric(f'Highest Amount {time_label}', format_time(highest_amount_time['Time']) if highest_amount_time is not None else 'N/A', human_readable_amount(highest_amount_time['Transaction_Amount']) if highest_amount_time is not None else '0')
    cols[1].metric(f'Lowest Amount {time_label}', format_time(lowest_amount_time['Time']) if lowest_amount_time is not None else 'N/A', human_readable_amount(lowest_amount_time['Transaction_Amount']) if lowest_amount_time is not None else '0')
    cols[2].metric(f'Highest Transaction {time_label}', format_time(highest_count_time['Time']) if highest_count_time is not None else 'N/A', int(highest_count_time['Transaction_Count']) if highest_count_time is not None else 0)
    cols[3].metric(f'Lowest Transaction {time_label}', format_time(lowest_count_time['Time']) if lowest_count_time is not None else 'N/A', int(lowest_count_time['Transaction_Count']) if lowest_count_time is not None else 0)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.plotly_chart(plot_trend(agg_df, 'Time', 'Transaction_Amount', f'{time_label.capitalize()} Transaction Amount Trend'), use_container_width=True)
    with chart_col2:
        st.plotly_chart(plot_trend(agg_df, 'Time', 'Transaction_Count', f'{time_label.capitalize()} Transaction Count Trend'), use_container_width=True)

def render_breakdowns(df: pd.DataFrame):
    col_title, col_toggle = st.columns([3, 1])
    with col_title:
        st.markdown('### Breakdowns')
    with col_toggle:
        metric_agg = st.radio(
            'Select Breakdown Metric:', 
            ['NET AMOUNT', 'COUNT'], 
            horizontal=True, 
            key='home_breakdowns_agg',
            label_visibility='collapsed'
        )

    is_count = (metric_agg == 'COUNT')
    agg_col = 'Count' if is_count else 'Net Amt'
    
    # Enter Threshold UI input
    threshold = 1.0
    row_purpose_col, _ = st.columns([2, 2])
    with row_purpose_col:
        if 'Purpose' in df.columns:
            threshold = st.number_input('Enter Threshold %', min_value=0.0, max_value=100.0, value=1.0, step=0.5, key='purpose_thresh')

    breakdowns = get_home_breakdowns(df, is_count, threshold)

    def render_custom_pie(df_plot, names, title):
        df_plot_copy = df_plot.copy()
        df_plot_copy['Formatted Amt'] = df_plot_copy['Net Amt'].apply(human_readable_amount)
        
        fig = px.pie(
            df_plot_copy,
            values=agg_col,
            names=names,
            title=title,
            hole=0.4,
            custom_data=['Count', 'Formatted Amt']
        )
        hovertemplate = f'<b>%{{label}}</b><br>Count: %{{customdata[0]:,}}<br>Net Amt: %{{customdata[1]}}<br>Share: %{{percent}}<extra></extra>'
        fig.update_traces(
            hovertemplate=hovertemplate,
            textinfo='percent+label',
            textposition='outside'
        )
        fig.update_layout(
            margin=dict(t=60, b=20, l=20, r=20),
            showlegend=False
        )
        try:
            return apply_enterprise_chart_style(fig)
        except Exception:
            return fig

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        if 'Purpose' in df.columns:
            plot_df = breakdowns['purpose_df'].copy()
            title = f'Purpose-wise {"Transaction Count" if is_count else "Amount"} Share'
            
            plot_df['Formatted Net Amt'] = plot_df['Net Amt'].apply(human_readable_amount)
            fig = px.pie(
                plot_df,
                values=agg_col,
                names='Purpose',
                title=title,
                hole=0.4,
                custom_data=['Count', 'Formatted Net Amt']
            )
            fig.update_traces(
                hovertemplate='<b>%{label}</b><br>Count: %{customdata[0]:,}<br>Net Amount: %{customdata[1]}<br>Percentage Share: %{percent}<extra></extra>',
                textinfo='percent+label',
                textposition='outside'
            )
            fig.update_layout(
                margin=dict(t=50, b=20, l=20, r=20),
                showlegend=False
            )
            try:
                fig = apply_enterprise_chart_style(fig)
            except Exception:
                pass
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("#### Purpose Wise Breakdown")
            
            def highlight_others(row):
                return ['background-color: #fafafa' if row['is_other'] else '' for _ in row.index]

            st.dataframe(
                breakdowns['purpose_summary_table'].style.apply(highlight_others, axis=1)
                              .format({
                                  'Count': '{:,.0f}', '% Count': '{:.2f}%',
                                  'Net Amt': lambda x: human_readable_amount(x), '% Net Amount': '{:.2f}%'
                              })
                              .hide(axis='columns', subset=['is_other']),
                use_container_width=True, hide_index=True
            )
            st.info("NOTE: Rows highlighted in gray are grouped into the 'Others' category in the chart above.")

    with row1_col2:
        if 'Product' in df.columns:
            product_summary = breakdowns['product_df']
            title = f'Product-wise {"Transaction Count" if is_count else "Amount"} Summary'
            st.plotly_chart(render_custom_pie(product_summary, 'Product', title), use_container_width=True)

            st.markdown("#### Product Wise Breakdown")
            st.dataframe(
                breakdowns['product_summary_table'].style.format({
                    'Count': '{:,.0f}', '% Count': '{:.2f}%',
                    'Net Amt': lambda x: human_readable_amount(x), '% Net Amount': '{:.2f}%'
                }),
                use_container_width=True, hide_index=True
            )

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        branch_field = 'Branch Name' if 'Branch Name' in df.columns else 'Branch'
        if branch_field in df.columns:
            branch_summary = breakdowns['branch_df'].copy()
            title = f'Branch-wise Transaction {"Count" if is_count else "Amount"}'
            
            branch_summary['Formatted Amt'] = branch_summary['Net Amt'].apply(human_readable_amount)
            text_col_val = branch_summary['Formatted Amt'] if not is_count else branch_summary['Count'].apply(lambda x: f'{x:,}')

            fig_branch = px.bar(
                branch_summary, x=agg_col, y=branch_field, orientation='h', title=title,
                text=text_col_val, custom_data=['Count', 'Formatted Amt']
            )
            fig_branch.update_traces(
                textposition='outside',
                hovertemplate=f'<b>%{{y}}</b><br>Count: %{{customdata[0]:,}}<br>Net Amount: %{{customdata[1]}}<extra></extra>'
            )
            fig_branch.update_layout(yaxis={'categoryorder':'total ascending'})
            try:
                fig_branch = apply_enterprise_chart_style(fig_branch)
            except Exception: pass
            st.plotly_chart(fig_branch, use_container_width=True)
            
    with row2_col2:
        if 'Visiting Country' in df.columns:
            country_summary = breakdowns['country_df'].copy()
            title = f'Visiting Country-wise Transaction {"Count" if is_count else "Amount"}'

            country_summary['Formatted Amt'] = country_summary['Net Amt'].apply(human_readable_amount)
            text_col_val = country_summary['Formatted Amt'] if not is_count else country_summary['Count'].apply(lambda x: f'{x:,}')

            fig_country = px.bar(
                country_summary, x=agg_col, y='Visiting Country', orientation='h', title=title,
                text=text_col_val, custom_data=['Count', 'Formatted Amt']
            )
            fig_country.update_traces(
                textposition='outside',
                hovertemplate=f'<b>%{{y}}</b><br>Count: %{{customdata[0]:,}}<br>Net Amount: %{{customdata[1]}}<extra></extra>'
            )
            fig_country.update_layout(yaxis={'categoryorder':'total ascending'})
            try:
                fig_country = apply_enterprise_chart_style(fig_country)
            except Exception: pass
            st.plotly_chart(fig_country, use_container_width=True)

def render_home_page(filtered_df: pd.DataFrame, risk_df: pd.DataFrame, risk_flags: list[str]):
    st.title('Home Page')
    
    # Calculate KPIs in backend
    kpis = get_home_kpis(filtered_df)
    render_kpi_cards(kpis)
    build_download_button(filtered_df)
    st.markdown('---')
    render_overall_highlights(filtered_df)
    st.markdown('---')
    render_breakdowns(filtered_df)
    st.markdown('---')
    st.subheader('Top Transactions')
    render_table_with_options(filtered_df.sort_values('Net Amt', ascending=False), key_prefix='pages_top_transactions')
