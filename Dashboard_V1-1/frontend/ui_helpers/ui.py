import streamlit as st
from backend.utils.formatters import human_readable_amount

# UI components for the Streamlit frontend
def apply_dashboard_style():
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #ffffff;
                color: #111111;
            }

            .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
            }

            /* Sidebar */
            section[data-testid="stSidebar"] {
                background-color: #f8f8f8;
                border-right: 1px solid #e5e5e5;
            }

            /* Header unification */
            header[data-testid="stHeader"] {
                background-color: rgba(255, 255, 255, 0.95) !important;
                backdrop-filter: blur(16px) !important;
                border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
                box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
                z-index: 999998 !important;
            }

            /* Hide Deploy Button */
            .stDeployButton, [data-testid="stAppDeployButton"] {
                display: none !important;
            }

            /* Navigation - Enterprise Pill-Style Sticky Top Bar */
            div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type {
                position: fixed !important;
                top: 0.55rem !important;
                left: 50% !important;
                transform: translateX(-50%) !important;
                z-index: 999999 !important;
                width: max-content !important;
                max-width: 60vw !important;
                margin: 0 !important;
                padding: 0 !important;
                display: flex;
                justify-content: center;
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }

            div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] {
                display: flex !important;
                flex-wrap: nowrap !important; /* Force single line */
                overflow-x: auto !important; /* Enable horizontal scrolling */
                justify-content: flex-start !important;
                background-color: transparent !important;
                border: none !important;
                gap: 4px !important;
                max-width: 100% !important;
                scrollbar-width: none !important; /* Hide scrollbar for Firefox */
                -ms-overflow-style: none !important; /* Hide scrollbar for IE/Edge */
            }

            /* Hide scrollbar for Chrome/Safari/Edge */
            div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"]::-webkit-scrollbar {
                display: none !important; 
            }

            div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label[data-baseweb="radio"] {
                border-radius: 9999px !important; /* Pill shape */
                padding: 8px 16px !important;
                border: none !important;
                background: transparent !important;
                margin: 0 !important;
                cursor: pointer !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                box-shadow: none !important;
                white-space: nowrap !important; /* Prevent text wrap */
            }

            /* Hover State */
            div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label[data-baseweb="radio"]:hover {
                background-color: rgba(0, 0, 0, 0.05) !important;
                transform: translateY(-1px) !important;
            }

            /* Active State */
            div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked),
            div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"] {
                background-color: #111111 !important;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
                transform: translateY(-1px) !important;
            }

            /* Text Styling */
            div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label[data-baseweb="radio"] p {
                color: #555555 !important;
                font-weight: 500 !important;
                font-size: 14px !important;
                margin: 0 !important;
                transition: color 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            }

            /* Hover Text */
            div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label[data-baseweb="radio"]:hover p {
                color: #111111 !important;
            }

            /* Active Text */
            div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) p,
            div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"] p {
                color: #ffffff !important;
                font-weight: 600 !important;
            }

            /* Hide Native Radio Circle completely */
            div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label[data-baseweb="radio"] div:first-child {
                display: none !important;
            }
            div[data-testid="stAppViewContainer"] main div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label[data-baseweb="radio"] div[data-testid="stMarkdownContainer"] {
                display: block !important;
            }

            /* Cards */
            .metric-card,
            .dashboard-card {
                background: #ffffff;
                border: 1px solid #e5e5e5;
                border-radius: 12px;
                padding: 16px;
                box-shadow: none;
            }

            /* Streamlit metrics */
            div[data-testid="metric-container"] {
                background: #ffffff;
                border: 1px solid #e5e5e5;
                padding: 14px;
                border-radius: 10px;
                box-shadow: none;
            }
            
            /* Prevent metric truncation */
            div[data-testid="stMetricValue"] > div {
                white-space: normal !important;
                word-break: break-word !important;
                font-size: 1.4rem !important;
                line-height: 1.2 !important;
            }
            div[data-testid="stMetricLabel"] > div {
                white-space: normal !important;
                word-break: break-word !important;
            }

            /* Tables */
            .stDataFrame {
                border: 1px solid #e5e5e5;
                border-radius: 10px;
            }

            /* Buttons */
            .stButton > button {
                background: #111111;
                color: white;
                border-radius: 8px;
                border: none;
                padding: 0.45rem 1rem;
            }

            .stButton > button:hover {
                background: #333333;
            }

            /* Download Button right-aligned with title */
            .stDownloadButton > button {
                background: #111111 !important;
                color: #ffffff !important;
                font-weight: 600 !important;
                border-radius: 8px !important;
                border: none !important;
                padding: 0.45rem 1.2rem !important;
                float: right !important;
                margin-top: 0.5rem !important;
                transition: all 0.2s ease-in-out !important;
            }
            
            /* Force inner text elements (like p, span) to inherit white bold text */
            .stDownloadButton > button p, 
            .stDownloadButton > button span {
                color: #ffffff !important;
                font-weight: 600 !important;
            }
            
            .stDownloadButton > button:hover {
                background: #333333 !important;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15) !important;
            }
            .stDownloadButton > button:hover p,
            .stDownloadButton > button:hover span {
                color: #ffffff !important;
            }

            /* Text */
            h1, h2, h3, h4, h5, h6, p, span, label {
                color: #111111 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

def inject_toggle_style():
    st.markdown(
        """
        <style>
        /* Isolated ChatGPT-Style Segmented Control Toggle */
        div[role="radiogroup"]:has(label[data-baseweb="radio"]) {
            display: inline-flex;
            background-color: #f1f1f2 !important; /* Soft gray container */
            border-radius: 8px !important;
            padding: 4px !important;
            gap: 2px !important;
            border: none !important;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.02) !important;
        }

        div[role="radiogroup"] label[data-baseweb="radio"] {
            background-color: transparent !important;
            border-radius: 6px !important;
            padding: 6px 18px !important;
            border: none !important;
            margin: 0 !important;
            cursor: pointer !important;
            transition: all 0.2s ease-in-out !important;
            box-shadow: none !important;
        }

        /* Unselected Hover */
        div[role="radiogroup"] label[data-baseweb="radio"]:hover {
            background-color: rgba(0, 0, 0, 0.05) !important;
        }

        /* Selected State - Black Pill */
        div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked),
        div[role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"] {
            background-color: #111111 !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2), 0 1px 2px rgba(0, 0, 0, 0.1) !important;
        }

        /* Text Styling */
        div[role="radiogroup"] label[data-baseweb="radio"] p {
            color: #666666 !important;
            font-weight: 500 !important;
            font-size: 14px !important;
            margin: 0 !important;
            transition: color 0.2s ease-in-out !important;
        }

        /* Selected Text Styling - White */
        div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) p,
        div[role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"] p {
            color: #ffffff !important;
            font-weight: 600 !important;
            text-shadow: 0 0 8px rgba(255,255,255,0.2) !important; /* subtle glow */
        }

        /* Hide Native Radio Circle */
        div[role="radiogroup"] label[data-baseweb="radio"] div:first-child {
            display: none !important;
        }
        div[role="radiogroup"] label[data-baseweb="radio"] div[data-testid="stMarkdownContainer"] {
            display: block !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_page_header(title: str, subtitle: str = None, df=None, download_key=None):
    apply_dashboard_style()
    
    if df is not None:
        col_title, col_btn = st.columns([8, 2])
        with col_title:
            st.title(title)
        with col_btn:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label='📥 Download',
                data=csv,
                file_name='filtered_transactions.csv',
                mime='text/csv',
                key=download_key
            )
    else:
        st.title(title)

    if subtitle:
        st.markdown(f'**{subtitle}**')
    st.markdown('---')


def render_download_button(df, label='Download filtered transactions', key=None):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label=label, data=csv, file_name='filtered_transactions.csv', mime='text/csv', key=key)


def render_observation_card(text: str):
    if not text:
        return
    st.markdown('### Automated Observations')
    st.info(text)


def render_kpi_grid(metrics, columns: int = 4):
    """Render KPI cards in a consistent horizontal responsive grid.

    Each metric can be a (label, value), (label, value, help), or dict with
    label/value/delta/help keys.
    """
    if not metrics:
        return

    columns = max(1, min(columns, 4))
    for start in range(0, len(metrics), columns):
        row = metrics[start:start + columns]
        cols = st.columns(columns)
        for col, metric in zip(cols, row):
            if isinstance(metric, dict):
                label = metric.get('label', '')
                value = metric.get('value', '')
                delta = metric.get('delta')
                help_text = metric.get('help')
            else:
                label = metric[0] if len(metric) > 0 else ''
                value = metric[1] if len(metric) > 1 else ''
                delta = metric[2] if len(metric) > 2 and len(metric) > 3 else None
                help_text = metric[2] if len(metric) == 3 else (metric[3] if len(metric) > 3 else None)
            col.metric(label, value, delta=delta, help=help_text)


def render_table_with_options(df, key_prefix: str = None, default_show_all: bool = True):
    """Render a dataframe with a rows-to-view selector and total count.

    - Default behavior: show all rows (scrollable with max height).
    - User can choose 20 / 40 / 60 rows for a compact view.
    """
    if df is None or df.empty:
        st.info('No records available.')
        st.markdown('**TOTAL RECORDS DISPLAYED: 0**')
        return

    display_df = df.copy()
    if 'Risk Score' in display_df.columns:
        display_df = display_df.drop(columns=['Risk Score'])

    with st.expander('Show Table'):
        search_key = f"{key_prefix}__table_search" if key_prefix else None
        search_query = st.text_input('Search records...', key=search_key)
        
        if search_query:
            query = search_query.strip()
            if query:
                mask = display_df.astype(str).apply(
                    lambda column: column.str.contains(query, case=False, na=False, regex=False)
                ).any(axis=1)
                display_df = display_df[mask]
                
        st.markdown(f'**TOTAL RECORDS DISPLAYED: {len(display_df)}**')
        st.dataframe(display_df, use_container_width=True)
