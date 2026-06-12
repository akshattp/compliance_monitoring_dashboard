import streamlit as st
import pandas as pd
import numpy as np
from frontend.ui_helpers.ui import human_readable_amount, render_table_with_options, render_kpi_grid

from backend.services.passenger_analysis_service import (
    prepare_passenger_data,
    get_passenger_kpis,
    get_passenger_anomalies,
    get_branch_quality_summary
)

def _render_kpis_ui(kpis):
    """Renders the main KPI section for passenger analysis."""
    st.markdown("### Passenger Data Quality Overview")
    total_records = kpis['total_records']

    pan_pct = kpis['pan_pct']
    passport_pct = kpis['passport_pct']
    invalid_pct = kpis['invalid_pct']
    blank_pct = kpis['blank_pct']

    kpi_cols1 = st.columns(3)
    kpi_cols1[0].metric("Total Records", f"{total_records:,}")
    kpi_cols1[1].metric("PAN Card IDs", f"{kpis['pan_count']:,}", f"{pan_pct:.1f}% of Total")
    kpi_cols1[2].metric("Passport IDs", f"{kpis['passport_count']:,}", f"{passport_pct:.1f}% of Total")

    kpi_cols2 = st.columns(3)
    kpi_cols2[0].metric("Invalid / Unknown IDs", f"{kpis['invalid_count']:,}", f"-{invalid_pct:.1f}% of Total")
    kpi_cols2[1].metric("Blank IDs", f"{kpis['blank_count']:,}", f"-{blank_pct:.1f}% of Total")
    
    with kpi_cols2[2]:
        st.markdown(f"""
        <div class="metric-container" style="text-align: center; height: 100%;">
            <div style="font-size: 0.8rem; color: #888;">MOST FREQUENT IDENTITY</div>
            <div style="font-size: 1.1rem; font-weight: bold; padding-top: 5px;">{kpis['most_freq_pax_id']} ({kpis['most_freq_doc_type']})</div>
            <div style="font-size: 0.9rem;">{kpis['most_freq_pax_name']}</div>
            <div style="font-size: 0.9rem; padding-top: 5px;">{kpis['most_freq_count']} times ({kpis['most_freq_pct']:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)

def _render_investigation_expander_ui(title: str, rule_key: str, flagged_df: pd.DataFrame, description: str, display_cols: list):
    """A generic expander for displaying anomaly rule results."""
    with st.expander(f"**{title}** ({len(flagged_df):,} records)"):
        st.markdown(description)
        if flagged_df.empty:
            st.success("No anomalies detected for this rule.")
        else:
            with st.expander("View Records"):
                display_data = flagged_df[display_cols].copy()
                if 'Passport' in display_data.columns:
                    display_data.rename(columns={'Passport': 'PAXIDNO'}, inplace=True)
                render_table_with_options(display_data, key_prefix=rule_key)

def _render_anomalies_ui(df: pd.DataFrame):
    """Container for all anomaly detection rules."""
    st.markdown("---")
    st.markdown("### Passenger Anomaly Detection")

    rule_i_threshold = st.number_input("Transaction Count Threshold for Frequent Passenger", min_value=2, value=10, step=1, key="rule_i_thresh_input_pax")
    
    anomalies = get_passenger_anomalies(df, rule_i_threshold=rule_i_threshold)

    # Rule A
    _render_investigation_expander_ui("Rule A: Same PAX ID, Different Emails", "rule_a", anomalies.get('rule_a', pd.DataFrame()),
                                   "Passengers with a single ID (PAN/Passport) associated with multiple distinct email addresses.",
                                   ['Passenger Name', 'Passport', 'EMAILID', 'Branch Name', 'Date', 'DOC_TYPE'])

    # Rule B
    _render_investigation_expander_ui("Rule B: Same PAX ID, Different Names", "rule_b", anomalies.get('rule_b', pd.DataFrame()),
                                   "A single ID (PAN/Passport) associated with multiple distinct passenger names.",
                                   ['Passport', 'Passenger Name', 'Branch Name', 'Date', 'DOC_TYPE'])

    # Rule C
    _render_investigation_expander_ui("Rule C: Same PAX ID, Different Mobiles", "rule_c", anomalies.get('rule_c', pd.DataFrame()),
                                   "A single ID (PAN/Passport) associated with multiple distinct mobile numbers.",
                                   ['Passenger Name', 'Passport', 'MOBILENO', 'Branch Name', 'Date', 'DOC_TYPE'])

    # Rule D
    _render_investigation_expander_ui("Rule D: Missing PAX ID with Contact Info", "rule_d", anomalies.get('rule_d', pd.DataFrame()),
                                   "Records where passenger name and email are present, but the PAX ID is missing.",
                                   ['Passenger Name', 'EMAILID', 'MOBILENO', 'Branch Name', 'Date'])

    # Rule E
    _render_investigation_expander_ui("Rule E: Same Email, Different PAX IDs", "rule_e", anomalies.get('rule_e', pd.DataFrame()),
                                   "A single email address associated with multiple distinct PAX IDs, indicating potential identity sharing.",
                                   ['EMAIL_CLEAN', 'Passenger Name', 'Passport', 'Branch Name', 'Date', 'DOC_TYPE'])

    # Rule F
    _render_investigation_expander_ui("Rule F: Same Mobile, Different PAX IDs", "rule_f", anomalies.get('rule_f', pd.DataFrame()),
                                   "A single mobile number associated with multiple distinct PAX IDs.",
                                   ['MOBILE_CLEAN', 'Passenger Name', 'Passport', 'Branch Name', 'Date', 'DOC_TYPE'])

    # Rule G
    _render_investigation_expander_ui("Rule G: Same Email, Different Names", "rule_g", anomalies.get('rule_g', pd.DataFrame()),
                                   "A single email address associated with multiple distinct passenger names.",
                                   ['EMAIL_CLEAN', 'Passenger Name', 'Passport', 'Branch Name', 'Date', 'DOC_TYPE'])

    # Rule H
    _render_investigation_expander_ui("Rule H: Same Mobile, Different Names", "rule_h", anomalies.get('rule_h', pd.DataFrame()),
                                   "A single mobile number associated with multiple distinct passenger names.",
                                   ['MOBILE_CLEAN', 'Passenger Name', 'Passport', 'Branch Name', 'Date', 'DOC_TYPE'])

    # Rule I: Frequent Passenger Activity
    with st.expander("**Rule I: Frequent Passenger Activity**"):
        rule_i_df = anomalies.get('rule_i', pd.DataFrame())
        st.markdown(f"Passengers with more than **{rule_i_threshold}** transactions.")
        if rule_i_df.empty:
            st.success("No passengers exceeded the transaction threshold.")
        else:
            with st.expander("View Records"):
                render_table_with_options(rule_i_df, key_prefix="rule_i")

    # Rule J: Missing KYC
    _render_investigation_expander_ui("Rule J: Missing KYC", "rule_j", anomalies.get('rule_j', pd.DataFrame()),
                                   "Records missing one or more of: PAX ID, Email, or Mobile.",
                                   ['Passenger Name', 'Passport', 'EMAILID', 'MOBILENO', 'Branch Name', 'Date'])

def _render_branch_quality_ui(df: pd.DataFrame):
    """Renders the branch data quality analysis section."""
    st.markdown("---")
    st.markdown("### Branch Data Quality Analysis")

    branch_summary, worst_kpis = get_branch_quality_summary(df)
    if branch_summary.empty:
        st.warning("Branch Name column not found, cannot perform branch quality analysis.")
        return

    # KPIs for worst branches
    kpi_cols = st.columns(4)
    if 'worst_id' in worst_kpis:
        kpi_cols[0].metric("Worst Branch (Invalid ID)", worst_kpis['worst_id']['Branch'], f"{worst_kpis['worst_id']['Count']:,} invalid")
    if 'worst_mobile' in worst_kpis:
        kpi_cols[1].metric("Worst Branch (Invalid Mobile)", worst_kpis['worst_mobile']['Branch'], f"{worst_kpis['worst_mobile']['Count']:,} invalid")
    if 'worst_email' in worst_kpis:
        kpi_cols[2].metric("Worst Branch (Invalid Email)", worst_kpis['worst_email']['Branch'], f"{worst_kpis['worst_email']['Count']:,} invalid")
    if 'worst_kyc' in worst_kpis:
        kpi_cols[3].metric("Worst Branch (Missing KYC)", worst_kpis['worst_kyc']['Branch'], f"{worst_kpis['worst_kyc']['Count']:,} missing")

    # Branch Quality Summary Table
    st.markdown("#### Branch Quality Summary Table")
    st.dataframe(
        branch_summary.style.format({
            'Total_Records': '{:,}',
            'Invalid_ID': '{:,}',
            'Invalid_Mobile': '{:,}',
            'Invalid_Email': '{:,}',
            'Missing_KYC': '{:,}',
            'Total_Issues': '{:,}',
        }).background_gradient(cmap='Reds', subset=['Total_Issues']),
        use_container_width=True,
        hide_index=True
    )

def render_passenger_analysis_page(filtered_df: pd.DataFrame, risk_df: pd.DataFrame, risk_flags: list[str]):
    """Main function to render the Passenger Analysis page."""
    st.title("Passenger Analysis")
    st.markdown("Identify data quality issues, potential duplicate identities, and suspicious customer profiling patterns.")

    if filtered_df.empty:
        st.warning("No data available for the current filter selection.")
        return

    # Prepare data with validations in backend
    with st.spinner("Analyzing passenger data..."):
        passenger_df = prepare_passenger_data(filtered_df)

    # Fetch and Render KPIs
    kpis = get_passenger_kpis(passenger_df)
    _render_kpis_ui(kpis)

    # Section 1: Valid vs Invalid PAX
    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### PAX ID Records Explorer")
    with col2:
        view_mode = st.radio(
            "Select view:",
            ("PAN Card", "Passport Number", "Unknown / Invalid"),
            horizontal=True,
            key="pax_view_toggle",
            label_visibility="collapsed"
        )

    if view_mode == "PAN Card":
        display_df = passenger_df[passenger_df['DOC_TYPE'] == 'PAN']
    elif view_mode == "Passport Number":
        display_df = passenger_df[passenger_df['DOC_TYPE'] == 'PASSPORT']
    else: # "Unknown / Invalid"
        display_df = passenger_df[passenger_df['DOC_TYPE'].isin(['INVALID', 'BLANK'])]

    with st.expander("View Records", expanded=False):
        table_data = display_df[['Passenger Name', 'Passport', 'DOC_TYPE', 'Branch Name', 'Date']].copy()
        table_data.rename(columns={'Passport': 'PAXIDNO'}, inplace=True)
        render_table_with_options(
            table_data,
            key_prefix="pax_explorer"
        )

    # Section 1.1: Mobile Number Records Explorer
    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Mobile Number Records Explorer")
    with col2:
        mobile_view_mode = st.radio(
            "Select view:",
            ("Valid", "Invalid", "Blank"),
            horizontal=True,
            key="mobile_view_toggle",
            label_visibility="collapsed"
        )
    
    if mobile_view_mode == "Valid":
        mobile_display_df = passenger_df[passenger_df['MOBILE_VALID']]
    elif mobile_view_mode == "Invalid":
        mobile_display_df = passenger_df[~passenger_df['MOBILE_VALID'] & passenger_df['MOBILE_CLEAN'].notna()]
    else: # "Blank"
        mobile_display_df = passenger_df[passenger_df['MOBILE_CLEAN'].isna()]
    
    with st.expander("View Records", expanded=False):
        mobile_table_data = mobile_display_df[['Passenger Name', 'MOBILENO', 'Branch Name', 'Date']].copy()
        render_table_with_options(
            mobile_table_data,
            key_prefix="mobile_explorer"
        )

    # Section 1.2: Email Records Explorer
    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Email Records Explorer")
    with col2:
        email_view_mode = st.radio(
            "Select view:",
            ("Valid", "Invalid", "Blank"),
            horizontal=True,
            key="email_view_toggle",
            label_visibility="collapsed"
        )
    
    if email_view_mode == "Valid":
        email_display_df = passenger_df[passenger_df['EMAIL_VALID']]
    elif email_view_mode == "Invalid":
        email_display_df = passenger_df[~passenger_df['EMAIL_VALID'] & passenger_df['EMAIL_CLEAN'].notna()]
    else: # "Blank"
        email_display_df = passenger_df[passenger_df['EMAIL_CLEAN'].isna()]
    
    with st.expander("View Records", expanded=False):
        email_table_data = email_display_df[['Passenger Name', 'EMAILID', 'Branch Name', 'Date']].copy()
        render_table_with_options(
            email_table_data,
            key_prefix="email_explorer"
        )

    # Section 2: Anomaly Detection
    _render_anomalies_ui(passenger_df)

    # Section 3: Branch Quality
    _render_branch_quality_ui(passenger_df)
