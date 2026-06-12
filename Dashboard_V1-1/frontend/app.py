import io
import sys
from pathlib import Path
import time
import pandas as pd
import streamlit as st

frontend_root = Path(__file__).resolve().parent
project_root = frontend_root.parent

sys.path.insert(0, str(frontend_root))
sys.path.insert(0, str(project_root))

from frontend.charts.theme import setup_global_chart_theme
from backend.data_access.canonical_dataset import create_canonical_dataset, RowCountMismatchError
from frontend.pages import PAGE_NAMES, PAGE_RENDERERS, PAGE_CONFIG
from frontend.pages.migration_validation import render_migration_validation_page
from backend.rules.monitoring_engine import build_transaction_risk_profile
from backend.utils.filters import (
    apply_filters,
    get_filter_options,
    normalize_default_filters,
)
from frontend.ui_helpers.ui import (
    apply_dashboard_style,
    inject_toggle_style,
)

# @st.cache_data(show_spinner="Loading transaction data...")
def _cached_load_data(file_bytes):
    return pd.read_excel(io.BytesIO(file_bytes))

# @st.cache_data(show_spinner="Computing risk profile...")
def _cached_build_risk(df):
    return build_transaction_risk_profile(df)

# @st.cache_data(show_spinner=False)
def _cached_get_filter_options(df, columns):
    return get_filter_options(df, columns)

def filter_dataset(df, selected_filters, date_range):
    filters = selected_filters.copy()
    fatf_status = filters.pop('_fatf_status', 'All')
    filtered_df = apply_filters(df, filters, date_range)

    if fatf_status != 'All' and 'FATF / OFAC Flag' in filtered_df.columns:
        if fatf_status == 'Flagged':
            filtered_df = filtered_df[filtered_df['FATF / OFAC Flag']]
        else:
            filtered_df = filtered_df[~filtered_df['FATF / OFAC Flag']]

    return filtered_df

def build_page_filters(page_name: str, df: pd.DataFrame):
    config = PAGE_CONFIG.get(page_name, {})
    columns = config.get('filter_columns', [])
    options = _cached_get_filter_options(df, tuple(columns))
    defaults = normalize_default_filters(config.get('default_filters', {}), options)

    with st.sidebar.expander(f'{page_name} Filters', expanded=False):
        selected_filters: dict = {}
        for column in columns:
            if column in options:
                all_opts = options[column]
                display_options = ["Select All"] + list(all_opts)
                
                orig_default = defaults.get(column, all_opts)
                if len(orig_default) == len(all_opts):
                    ui_default = ["Select All"]
                else:
                    ui_default = orig_default
                
                selected_ui = st.multiselect(column, display_options, default=ui_default, key=f'{page_name}__{column}')
                
                if "Select All" in selected_ui:
                    selected_actual = all_opts
                else:
                    selected_actual = [x for x in selected_ui if x != "Select All"]
                
                if selected_actual and len(selected_actual) < len(all_opts):
                    selected_filters[column] = selected_actual
 
        date_range = None
        if 'Date' in df.columns:
            valid_dates = df['Date'].dropna()
            if not valid_dates.empty:
                start_date = st.date_input('Start Date', valid_dates.min().date(), key=f'{page_name}__start_date')
                end_date = st.date_input('End Date', valid_dates.max().date(), key=f'{page_name}__end_date')
                if start_date and end_date:
                    date_range = (pd.to_datetime(start_date), pd.to_datetime(end_date))

        fatf_status = st.radio('FATF / OFAC Status', ['All', 'Flagged', 'Not Flagged'], index=0, key=f'{page_name}__fatf_status')
        selected_filters['_fatf_status'] = fatf_status

    return selected_filters, date_range


def render_top_navigation(page_names, df=None, uploaded_file=None):
    apply_dashboard_style()
    if st.session_state.get('top_page_selector') not in page_names:
        st.session_state['top_page_selector'] = page_names[0]

    # Add Migration Validation page to the list
    if 'Migration Validation' not in page_names:
        page_names.insert(0, 'Migration Validation')

    active_page = st.session_state['top_page_selector']
    try:
        active_idx = page_names.index(active_page) + 1
    except ValueError:
        active_idx = 1
        
    # Inject dynamic CSS to guarantee active state persists strictly across rerenders
    st.markdown(f"""
        <style>
        div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label[data-baseweb="radio"]:nth-child({active_idx}) {{
            background-color: #111111 !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
            transform: translateY(-1px) !important;
        }}
        div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label[data-baseweb="radio"]:nth-child({active_idx}) p {{
            color: #ffffff !important;
            font-weight: 600 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    return st.radio(
        'Dashboard modules',
        page_names,
        key='top_page_selector',
        horizontal=True,
        label_visibility='collapsed',
    )


def main():
    setup_global_chart_theme()
    st.set_page_config(
        page_title='GlobalPay Dashboard',   
        page_icon=str(project_root / 'favicon-black.png'),
        layout='wide',
        initial_sidebar_state='expanded',
    )
    st.logo(str(project_root / 'global-pay-logo1.jpg'))
    st.markdown("""
        <style>
            [data-testid="stLogo"] img {
                max-height: 180px !important;
                width: auto !important;
            }
        </style>
    """, unsafe_allow_html=True)
    apply_dashboard_style()
    inject_toggle_style()
    # Hide Streamlit's automatic Pages navigation in the sidebar (we use our own selector)
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"]{display:none}
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.title('GlobalPay Compliance Dashboard')
    st.sidebar.markdown('### Control Center')
    st.sidebar.markdown('Upload evidence, then refine the active module through grouped investigation filters.')

    uploaded_file = st.sidebar.file_uploader('Upload `TXN LINE MIS` workbook', type=['xlsx', 'xls'])
    st.sidebar.markdown('---')

    if uploaded_file is None:
        if 'current_file_id' in st.session_state:
            st.session_state.clear()
        st.title('GlobalPay Compliance Monitoring')
        st.info('Please upload the monthly base transaction workbook to begin the automated review process.')
        return

    file_id = uploaded_file.file_id if hasattr(uploaded_file, 'file_id') else uploaded_file.name
    if 'current_file_id' not in st.session_state or st.session_state['current_file_id'] != file_id:
        st.session_state.clear()
        st.session_state['current_file_id'] = file_id
        try:
            start_load = time.perf_counter()
            file_bytes = uploaded_file.getvalue()
            raw_df = _cached_load_data(file_bytes)
            print(f"Data Load Time: {round(time.perf_counter() - start_load, 2)}s")
            
            st.session_state['source_row_count'] = len(raw_df)
            if raw_df.empty:
                st.warning('Uploaded file contains no records. Upload a valid monthly transaction workbook.')
                return

            # Create Canonical Dataset
            with st.spinner("Building Canonical Compliance Dataset..."):
                start_canonical = time.perf_counter()
                canonical_df = create_canonical_dataset(
                    raw_df,
                    party_master_path=str(project_root / 'data' / 'Party Master New Report.csv'),
                    ofac_path=str(project_root / 'data' / 'OFAC_FATF COUNTRY UPDATED.xlsx')
                )
                print(f"Canonical Dataset Creation Time: {round(time.perf_counter() - start_canonical, 2)}s")

            # Build and capture the enriched Risk Profile dataframe
            with st.spinner("Computing Transaction Risk Profile..."):
                start_risk = time.perf_counter()
                risk_df, risk_flags = _cached_build_risk(canonical_df)
                print(f"Risk Profile Generation Time: {round(time.perf_counter() - start_risk, 2)}s")
                st.session_state['risk_df'] = risk_df
                st.session_state['risk_flags'] = risk_flags

        except (Exception, RowCountMismatchError) as exc:
            st.error(f'Unable to load transaction file: {exc}')
            return

    risk_df = st.session_state['risk_df']
    risk_flags = st.session_state['risk_flags']

    selected_page = render_top_navigation(PAGE_NAMES, risk_df, uploaded_file)

    # Handle validation page separately as it has a different signature
    if selected_page == 'Migration Validation':
        render_migration_validation_page(risk_df, st.session_state.get('source_row_count', 0))
        return

    page_selected_filters, page_date_range = build_page_filters(selected_page, risk_df)
    page_filtered_df = filter_dataset(risk_df, page_selected_filters, page_date_range)

    if page_filtered_df.empty:
        st.warning('No records matched the selected filters for this page. Adjust the filters and try again.')
        return

    renderer = PAGE_RENDERERS.get(selected_page)
    if renderer is None:
        st.info('This page is not yet implemented.')
        return

    start_render = time.perf_counter()
    renderer(page_filtered_df, risk_df, risk_flags)
    print(f"Page Renderer ({selected_page}) Time: {round(time.perf_counter() - start_render, 2)}s")


if __name__ == '__main__':
    main()
