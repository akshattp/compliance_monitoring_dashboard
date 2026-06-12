import streamlit as st
import pandas as pd
from frontend.ui_helpers.ui import human_readable_amount
from backend.services.simple_pages_service import get_migration_validation_metrics

def render_migration_validation_page(df: pd.DataFrame, source_row_count: int):
    st.title("Migration Validation Dashboard")
    st.info("This page validates the canonical dataset created from the raw TXN LINE MIS source.")

    st.markdown("### Row Count Validation")
    cols = st.columns(2)
    cols[0].metric("Source TXN MIS Row Count", f"{source_row_count:,}")
    cols[1].metric("Canonical Dataset Row Count", f"{len(df):,}")
    if source_row_count == len(df):
        st.success("✅ Row count is consistent throughout the pipeline.")
    else:
        st.error(f"🚨 Row count mismatch! Source: {source_row_count}, Canonical: {len(df)}")

    st.markdown("---")
    st.markdown("### Key Metrics from Canonical Dataset")
    
    metrics = get_migration_validation_metrics(df)
    
    kpi_cols = st.columns(4)
    kpi_cols[0].metric("Total Net Amount", human_readable_amount(metrics['total_net_amount']))
    kpi_cols[1].metric("Distinct Products", metrics['distinct_products'])
    kpi_cols[2].metric("Distinct Segments", metrics['distinct_segments'])
    kpi_cols[3].metric("Distinct Transaction Types", metrics['distinct_txn_types'])

    st.markdown("---")
    st.markdown("### Risk Category Distribution")
    risk_counts = metrics['risk_counts']
    risk_cols = st.columns(4)
    risk_cols[0].metric("High Risk Count", f"{risk_counts.get('High', 0):,}")
    risk_cols[1].metric("Medium Risk Count", f"{risk_counts.get('Medium', 0):,}")
    risk_cols[2].metric("Low Risk Count", f"{risk_counts.get('Low', 0):,}")
    risk_cols[3].metric("Unknown Risk Count", f"{risk_counts.get('Unknown', 0):,}")

    st.markdown("---")
    st.markdown("### Compliance Flag Counts")
    compliance_counts = metrics['compliance_counts']
    
    flag_cols = st.columns(4)
    flag_cols[0].metric("High Value Transaction (>25k) Count", f"{compliance_counts.get('high_value', 0):,}")
    flag_cols[1].metric("FATF Count", f"{compliance_counts.get('fatf', 0):,}")
    flag_cols[2].metric("OFAC Count", f"{compliance_counts.get('ofac', 0):,}")
    flag_cols[3].metric("CIS Country Count", f"{compliance_counts.get('cis', 0):,}")

    st.markdown("---")
    st.markdown("### Distinct Values for Key Fields")
    distinct_vals = metrics['distinct_values']
    
    exp_cols = st.columns(3)
    with exp_cols[0]:
        with st.expander("Distinct Segments"):
            st.dataframe(distinct_vals.get('segments', []))
    with exp_cols[1]:
        with st.expander("Distinct Transaction Types"):
            st.dataframe(distinct_vals.get('txn_types', []))
    with exp_cols[2]:
        with st.expander("Distinct Countries"):
            st.dataframe(distinct_vals.get('countries', []))
            
    st.markdown("---")
    st.subheader("Canonical Dataset Preview")
    st.dataframe(df.head(100))
