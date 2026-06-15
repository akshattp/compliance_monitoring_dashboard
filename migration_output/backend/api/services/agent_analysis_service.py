import pandas as pd
import numpy as np

def get_top_agent_entity(agent_df: pd.DataFrame, col: str, agent_col: str, total_agents: int) -> tuple:
    if not col or col not in agent_df.columns or agent_df.empty:
        return 'N/A', 0, 0
    agg = agent_df.groupby(col)[agent_col].nunique().reset_index()
    if agg.empty:
        return 'N/A', 0, 0
    agg = agg.sort_values(agent_col, ascending=False)
    top = agg.iloc[0]
    pct = (top[agent_col] / total_agents * 100) if total_agents > 0 else 0
    return top[col], top[agent_col], pct

def get_agent_kpis(df: pd.DataFrame, agent_col: str, branch_col: str, benef_col: str) -> dict:
    if agent_col not in df.columns:
        return {}
        
    agent_df = df[df[agent_col].notna() & (df[agent_col].astype(str).str.strip() != '')].copy()
    total_net_amt_all = df['INRAMOUNT'].sum(min_count=1) if 'INRAMOUNT' in df.columns else 0
    total_net_amt_agent = agent_df['INRAMOUNT'].sum(min_count=1) if 'INRAMOUNT' in agent_df.columns else 0
    total_agents = agent_df[agent_col].nunique()
    contrib_pct = (total_net_amt_agent / total_net_amt_all * 100) if total_net_amt_all > 0 else 0

    beneficiary_df = pd.DataFrame()
    if benef_col and benef_col in agent_df.columns:
        beneficiary_df = agent_df.copy()
        beneficiary_df[benef_col] = beneficiary_df[benef_col].astype(str).str.strip()
        beneficiary_df = beneficiary_df[beneficiary_df[benef_col].notna()]
        beneficiary_df = beneficiary_df[beneficiary_df[benef_col] != '']
        beneficiary_df = beneficiary_df[~beneficiary_df[benef_col].str.upper().isin(['NAN', 'NONE', 'NULL'])]

    # Top entities calculations
    seg_name, seg_count, seg_pct = get_top_agent_entity(agent_df, 'Segment', agent_col, total_agents)
    prod_name, prod_count, prod_pct = get_top_agent_entity(agent_df, 'PRODUCT', agent_col, total_agents)
    purp_name, purp_count, purp_pct = get_top_agent_entity(agent_df, 'TxnPurpose', agent_col, total_agents)
    
    br_col = branch_col if branch_col in agent_df.columns else None
    br_name, br_count, br_pct = get_top_agent_entity(agent_df, br_col, agent_col, total_agents) if br_col else ('N/A', 0, 0.0)
    
    ctry_name, ctry_count, ctry_pct = get_top_agent_entity(agent_df, 'CountryToTravel', agent_col, total_agents)

    return {
        'total_agents': total_agents,
        'total_net_amt_agent': total_net_amt_agent,
        'contrib_pct': contrib_pct,
        'agent_df': agent_df,
        'beneficiary_df': beneficiary_df,
        'seg': (seg_name, seg_count, seg_pct),
        'product': (prod_name, prod_count, prod_pct),
        'purpose': (purp_name, purp_count, purp_pct),
        'branch': (br_name, br_count, br_pct),
        'country': (ctry_name, ctry_count, ctry_pct),
    }

def get_agent_frequency_table(df_in: pd.DataFrame, group_col: str, y_col: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (table_data, display_table_with_total) for rendering."""
    if not group_col or group_col not in df_in.columns:
        return pd.DataFrame(), pd.DataFrame()

    agg_df = df_in.groupby(group_col).agg(Count=('INRAMOUNT', 'size'), Net_Amt=('INRAMOUNT', 'sum')).reset_index()
    total_y = agg_df[y_col].sum()
    agg_df['% Contribution'] = (agg_df[y_col] / total_y * 100).fillna(0) if total_y > 0 else 0
    
    table_data = agg_df.copy()
    total_count = table_data['Count'].sum()
    total_amt = table_data['Net_Amt'].sum()
    
    table_data['Count %'] = (table_data['Count'] / total_count * 100) if total_count > 0 else 0
    table_data['Net Amount %'] = (table_data['Net_Amt'] / total_amt * 100) if total_amt > 0 else 0
    table_data = table_data.sort_values(y_col, ascending=False)
    
    total_row = pd.DataFrame({
        group_col: ['**TOTAL**'],
        'Count': [total_count],
        'Count %': [100.0],
        'Net_Amt': [total_amt],
        'Net Amount %': [100.0]
    })
    
    display_table = pd.concat([table_data, total_row], ignore_index=True)
    display_table = display_table.rename(columns={'Net_Amt': 'INRAMOUNT', group_col: 'Category'})
    
    return agg_df, display_table

def get_agent_trend_table(agent_df: pd.DataFrame, trend_agg: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    if 'TXNDATE' not in agent_df.columns:
        return pd.DataFrame(), pd.DataFrame()
        
    agent_df['TXNDATE'] = pd.to_datetime(agent_df['TXNDATE'], errors='coerce')
    # Exclude Sundays
    agent_df = agent_df[agent_df['TXNDATE'].dt.dayofweek != 6]
        
    if trend_agg == 'DAILY':
        trend_df = agent_df.groupby(agent_df['TXNDATE'].dt.date).agg(Count=('INRAMOUNT', 'size'), Net_Amt=('INRAMOUNT', 'sum')).reset_index()
        trend_df.rename(columns={'TXNDATE': 'Time'}, inplace=True)
    else:
        if 'Week' in agent_df.columns:
            trend_df = agent_df.groupby('Week').agg(Count=('INRAMOUNT', 'size'), Net_Amt=('INRAMOUNT', 'sum')).reset_index()
            trend_df.rename(columns={'Week': 'Time'}, inplace=True)
        else:
            trend_df = agent_df.groupby(pd.Grouper(key='TXNDATE', freq='W-MON')).agg(Count=('INRAMOUNT', 'size'), Net_Amt=('INRAMOUNT', 'sum')).reset_index()
            trend_df['TXNDATE'] = trend_df['TXNDATE'].dt.date
            trend_df.rename(columns={'TXNDATE': 'Time'}, inplace=True)
            
    table_data = trend_df.copy()
    total_count = table_data['Count'].sum()
    total_amt = table_data['Net_Amt'].sum()
    
    table_data['Count %'] = (table_data['Count'] / total_count * 100) if total_count > 0 else 0
    table_data['Net Amount %'] = (table_data['Net_Amt'] / total_amt * 100) if total_amt > 0 else 0
    table_data = table_data.sort_values('Time', ascending=False)
    
    total_row = pd.DataFrame({
        'Time': ['**TOTAL**'],
        'Count': [total_count],
        'Count %': [100.0],
        'Net_Amt': [total_amt],
        'Net Amount %': [100.0]
    })
    
    display_table = pd.concat([table_data, total_row], ignore_index=True)
    display_table = display_table.rename(columns={'Net_Amt': 'INRAMOUNT', 'Time': 'Category'})
    
    return trend_df, display_table

def get_suspicious_agents_many(df_sub: pd.DataFrame, group_col: str, target_col: str, threshold: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    if target_col not in df_sub.columns or group_col not in df_sub.columns:
        return pd.DataFrame(), pd.DataFrame()

    grp = df_sub.groupby(group_col).agg(
        unique_targets=(target_col, 'nunique'),
        txn_count=('INRAMOUNT', 'size'),
        total_amt=('INRAMOUNT', 'sum')
    ).reset_index()
    
    suspicious_agents = grp[grp['unique_targets'] >= threshold].copy()
    if suspicious_agents.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    related_records = df_sub[df_sub[group_col].isin(suspicious_agents[group_col])].copy()
    return suspicious_agents, related_records

def get_suspicious_agents1_many_relation(beneficiary_df: pd.DataFrame, agent_col: str, benef_col: str, threshold: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    agent_counts = beneficiary_df.groupby(agent_col)[benef_col].nunique().reset_index()
    suspicious_agents = agent_counts[agent_counts[benef_col] >= threshold][agent_col]
    
    if suspicious_agents.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    sub_df = beneficiary_df[beneficiary_df[agent_col].isin(suspicious_agents)].copy()
    grp = sub_df.groupby([agent_col, benef_col]).agg(
        Transaction_Count=('INRAMOUNT', 'size'),
        Net_Amount=('INRAMOUNT', 'sum')
    ).reset_index()
    
    agent_freq_map = sub_df.groupby(agent_col)[benef_col].nunique().to_dict()
    grp['Relationship Frequency'] = grp[agent_col].map(agent_freq_map)
    
    grp = grp.rename(columns={
        agent_col: 'AGENTCODE',
        benef_col: 'Beneficiary',
        'Transaction_Count': 'Transaction Count',
        'Net_Amount': 'INRAMOUNT'
    })
    
    total_count = grp['Transaction Count'].sum()
    total_amt = grp['INRAMOUNT'].sum()
    total_records = len(grp)
    
    total_row = pd.DataFrame({
        'AGENTCODE': ['**TOTAL**'],
        'Beneficiary': [f'**Total Records: {total_records}**'],
        'Transaction Count': [total_count],
        'INRAMOUNT': [total_amt],
        'Relationship Frequency': ['']
    })
    
    display_df = pd.concat([grp, total_row], ignore_index=True)
    return grp, display_df, sub_df

def get_suspicious_agents1_one_relation(beneficiary_df: pd.DataFrame, agent_col: str, benef_col: str, threshold: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    grp = beneficiary_df.groupby([agent_col, benef_col]).agg(
        Transaction_Count=('INRAMOUNT', 'size'),
        Net_Amount=('INRAMOUNT', 'sum')
    ).reset_index()
    
    suspicious_pairs = grp[grp['Transaction_Count'] >= threshold].copy()
    if suspicious_pairs.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    suspicious_pairs['Relationship Frequency'] = suspicious_pairs['Transaction_Count']
    keys_df = suspicious_pairs[[agent_col, benef_col]].copy()
    
    suspicious_pairs = suspicious_pairs.rename(columns={
        agent_col: 'AGENTCODE',
        benef_col: 'Beneficiary',
        'Transaction_Count': 'Transaction Count',
        'Net_Amount': 'INRAMOUNT'
    })
    
    total_count = suspicious_pairs['Transaction Count'].sum()
    total_amt = suspicious_pairs['INRAMOUNT'].sum()
    total_records = len(suspicious_pairs)
    
    total_row = pd.DataFrame({
        'AGENTCODE': ['**TOTAL**'],
        'Beneficiary': [f'**Total Records: {total_records}**'],
        'Transaction Count': [total_count],
        'INRAMOUNT': [total_amt],
        'Relationship Frequency': ['']
    })
    
    display_df = pd.concat([suspicious_pairs, total_row], ignore_index=True)
    sub_df = beneficiary_df.merge(keys_df, on=[agent_col, benef_col], how='inner')
    return suspicious_pairs, display_df, sub_df
