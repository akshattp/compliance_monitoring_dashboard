from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import math

def clean_dict_for_json(d):
    if isinstance(d, dict):
        return {k: clean_dict_for_json(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [clean_dict_for_json(v) for v in d]
    elif isinstance(d, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(d)
    elif isinstance(d, (np.floating, np.float64, np.float32, np.float16)):
        if np.isnan(d) or np.isinf(d):
            return 0.0
        return float(d)
    elif isinstance(d, float):
        if math.isnan(d) or math.isinf(d):
            return 0.0
    elif pd.isna(d):
        return None
    return d

from api.services.home_service import get_home_kpis, get_home_trends, get_home_breakdowns
from api.services.transaction_summary_service import get_transaction_type_kpis, get_transaction_type_breakdown, get_purpose_summary_table

router = APIRouter()    

class HomeRequestDto(BaseModel):
    filtered_df: List[Dict[str, Any]]
    trend_agg: Optional[str] = 'DAILY'
    breakdown_metric_agg: Optional[str] = 'NET AMOUNT'
    purpose_threshold: Optional[float] = 1.0

class HomeResponseDto(BaseModel):
    kpis: Dict[str, Any]
    trends: Dict[str, Any]
    breakdowns: Dict[str, Any]

@router.post("/api/pages/home", response_model=HomeResponseDto)
def home_page_data(request: HomeRequestDto = Body(...)):
    if not request.filtered_df:
        return HomeResponseDto(kpis={}, trends={}, breakdowns={})
        
    df = pd.DataFrame(request.filtered_df)
    
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
    # Validate required columns implicitly by filling missing with defaults or letting service handle it
    
    kpis = get_home_kpis(df)
    
    trends = get_home_trends(df, request.trend_agg)
    
    is_count = (request.breakdown_metric_agg == 'COUNT')
    breakdowns = get_home_breakdowns(df, is_count, request.purpose_threshold)
    
    return HomeResponseDto(
        kpis=kpis,
        trends=trends,
        breakdowns=breakdowns
    )

from api.services.transaction_summary_service import (
    get_transaction_type_kpis, 
    get_transaction_type_breakdown, 
    get_purpose_summary_table,
    get_txn_composition_data
)

class TransactionSummaryRequestDto(BaseModel):
    filtered_df: List[Dict[str, Any]]
    global_metric: Optional[str] = "Count"
    selected_txns: Optional[List[str]] = []

class TransactionSummaryResponseDto(BaseModel):
    kpis: Dict[str, Any]
    breakdown: Dict[str, Any]
    purpose_summary: List[Dict[str, Any]]
    branch_composition: Dict[str, Any]
    product_composition: Dict[str, Any]
    segment_composition: Dict[str, Any]

@router.post("/api/pages/transaction-summary", response_model=TransactionSummaryResponseDto)
def transaction_summary_data(request: TransactionSummaryRequestDto = Body(...)):
    if not request.filtered_df:
        return TransactionSummaryResponseDto(
            kpis={}, breakdown={'txn_by_type': [], 'display_table': []}, purpose_summary=[],
            branch_composition={}, product_composition={}, segment_composition={}
        )
        
    df = pd.DataFrame(request.filtered_df)
    
    kpis = get_transaction_type_kpis(df)
    breakdown = get_transaction_type_breakdown(df)
    purpose_summary = get_purpose_summary_table(df)
    
    y_col = 'Count' if request.global_metric == 'Count' else 'Total_Amount'
    
    branch_comp = get_txn_composition_data(df, 'Branch Name', request.selected_txns, y_col)
    product_comp = get_txn_composition_data(df, 'Product', request.selected_txns, y_col)
    segment_comp = get_txn_composition_data(df, 'Segments', request.selected_txns, y_col)
    
    # Need to convert DataFrames to dicts for JSON
    def _clean_comp(comp):
        if not comp: return {}
        return {
            'chart_df': comp['chart_df'].replace([float('inf'), float('-inf'), float('nan')], None).to_dict('records') if 'chart_df' in comp else [],
            'display_table': comp['display_table'].replace([float('inf'), float('-inf'), float('nan')], None).to_dict('records') if 'display_table' in comp else [],
            'total_count': float(comp.get('total_count', 0)),
            'total_amount': float(comp.get('total_amount', 0)),
            'records_count': int(comp.get('records_count', 0))
        }
    
    return TransactionSummaryResponseDto(
        kpis=kpis,
        breakdown=breakdown,
        purpose_summary=purpose_summary,
        branch_composition=_clean_comp(branch_comp),
        product_composition=_clean_comp(product_comp),
        segment_composition=_clean_comp(segment_comp)
    )

from api.services.tour_operator_service import (
    get_tour_operator_kpis,
    get_operator_intelligence,
    get_purpose_mix_data,
    get_branch_composition_data,
    get_corporate_composition_data,
    get_country_combo_data,
    get_tour_operator_observation,
)

class TourOperatorRequestDto(BaseModel):
    filtered_df: List[Dict[str, Any]]

class TourOperatorResponseDto(BaseModel):
    kpis: Dict[str, Any]
    intelligence: Dict[str, Any]
    purpose_mix: List[Dict[str, Any]]
    branch_composition: Dict[str, Any]
    corporate_composition: Dict[str, Any]
    country_combo: List[Dict[str, Any]]
    observation: str

@router.post("/api/pages/tour-operator", response_model=TourOperatorResponseDto)
def tour_operator_data(request: TourOperatorRequestDto = Body(...)):
    if not request.filtered_df:
        return TourOperatorResponseDto(
            kpis={}, intelligence={}, purpose_mix=[],
            branch_composition={'branch_data': [], 'display_table': []},
            corporate_composition={'corp_data': [], 'display_table': [], 'total_count': 0, 'total_amt': 0},
            country_combo=[], observation=""
        )
        
    df = pd.DataFrame(request.filtered_df)
    
    kpis = get_tour_operator_kpis(df)
    intelligence = get_operator_intelligence(df)
    purpose_mix = get_purpose_mix_data(df)
    branch_composition = get_branch_composition_data(df)
    corporate_composition = get_corporate_composition_data(df)
    country_combo = get_country_combo_data(df)
    observation = get_tour_operator_observation(df)
    
    return TourOperatorResponseDto(
        kpis=kpis,
        intelligence=intelligence,
        purpose_mix=purpose_mix,
        branch_composition=branch_composition,
        corporate_composition=corporate_composition,
        country_combo=country_combo,
        observation=observation
    )

from api.services.retail_high_value_service import (
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

class RetailHighValueRequestDto(BaseModel):
    filtered_df: List[Dict[str, Any]]

class RetailHighValueResponseDto(BaseModel):
    kpis: Dict[str, Any]
    branch_data: List[Dict[str, Any]]
    corporate_data: List[Dict[str, Any]]
    customer_data: List[Dict[str, Any]]
    product_data: List[Dict[str, Any]]
    currency_data: List[Dict[str, Any]]
    observations: str
    transaction_table: List[Dict[str, Any]]
    trend_data_daily: List[Dict[str, Any]]
    trend_data_weekly: List[Dict[str, Any]]
    risk_distribution: List[Dict[str, Any]]
    segment_distribution: List[Dict[str, Any]]

@router.post("/api/pages/retail-high-value", response_model=RetailHighValueResponseDto)
def retail_high_value_data(request: RetailHighValueRequestDto = Body(...)):
    if not request.filtered_df:
        return RetailHighValueResponseDto(
            kpis={}, branch_data=[], corporate_data=[], customer_data=[],
            product_data=[], currency_data=[], observations="", transaction_table=[],
            trend_data_daily=[], trend_data_weekly=[], risk_distribution=[], segment_distribution=[]
        )
        
    df = pd.DataFrame(request.filtered_df)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    df = add_retail_risk_classification(df)
    hv_df = identify_high_value_transactions(df)
    
    kpis = calculate_kpis(hv_df)
    branch_data = branch_wise_analysis(hv_df)
    corporate_data = corporate_wise_analysis(hv_df)
    customer_data = customer_concentration(hv_df)
    product_data = product_wise_analysis(hv_df)
    currency_data = currency_wise_analysis(hv_df)
    observations = generate_observations(hv_df, kpis)
    transaction_table = format_transaction_table(hv_df)
    
    # Simple risk dist
    risk_dist = []
    if 'Retail_Risk_Level' in hv_df.columns:
        agg = hv_df.groupby('Retail_Risk_Level').agg(Count=('EQV USD', 'size'), Net_Amount=('EQV USD', 'sum')).reset_index()
        risk_dist = agg.replace([float('inf'), float('-inf'), float('nan')], None).to_dict('records')
        
    seg_dist = []
    if 'Segments' in hv_df.columns and 'Retail_Risk_Level' in hv_df.columns:
        agg = hv_df.groupby(['Segments', 'Retail_Risk_Level']).agg(Count=('EQV USD', 'size'), Net_Amount=('EQV USD', 'sum')).reset_index()
        seg_dist = agg.replace([float('inf'), float('-inf'), float('nan')], None).to_dict('records')
    
    trend_daily = []
    if 'Date' in hv_df.columns:
        agg = hv_df.groupby(hv_df['Date'].dt.date).agg(Count=('EQV USD', 'size'), Net_Amount=('EQV USD', 'sum')).reset_index()
        agg['Date'] = agg['Date'].astype(str)
        trend_daily = agg.replace([float('inf'), float('-inf'), float('nan')], None).to_dict('records')
        
    trend_weekly = []
    if 'Week' in hv_df.columns:
        agg = hv_df.groupby('Week').agg(Count=('EQV USD', 'size'), Net_Amount=('EQV USD', 'sum')).reset_index()
        trend_weekly = agg.replace([float('inf'), float('-inf'), float('nan')], None).to_dict('records')

    return RetailHighValueResponseDto(
        kpis=kpis,
        branch_data=branch_data,
        corporate_data=corporate_data,
        customer_data=customer_data,
        product_data=product_data,
        currency_data=currency_data,
        observations=observations,
        transaction_table=transaction_table,
        trend_data_daily=trend_daily,
        trend_data_weekly=trend_weekly,
        risk_distribution=risk_dist,
        segment_distribution=seg_dist
    )

from api.services.high_risk_corporate_service import (
    get_corporate_risk_kpis,
    get_risk_distribution,
    get_top_corporates,
    get_branch_exposure,
    get_country_exposure,
    get_product_exposure_details,
    get_trend_exposure,
    get_transactions_table
)

class HighRiskCorporateRequestDto(BaseModel):
    enriched_df: List[Dict[str, Any]]
    trend_agg: Optional[str] = "DAILY"
    target_metric: Optional[str] = "COUNT"

class HighRiskCorporateResponseDto(BaseModel):
    kpis: Dict[str, Any]
    risk_distribution: List[Dict[str, Any]]
    top_corporates: List[Dict[str, Any]]
    branch_exposure: List[Dict[str, Any]]
    country_exposure: List[Dict[str, Any]]
    product_exposure: Dict[str, Any]
    trend_exposure: List[Dict[str, Any]]
    transactions_table: List[Dict[str, Any]]

@router.post("/api/pages/high-risk-corporate", response_model=HighRiskCorporateResponseDto)
def high_risk_corporate_data(request: HighRiskCorporateRequestDto = Body(...)):
    if not request.enriched_df:
        return HighRiskCorporateResponseDto(
            kpis={}, risk_distribution=[], top_corporates=[], branch_exposure=[],
            country_exposure=[], product_exposure={'product_data': [], 'display_prod_table': []},
            trend_exposure=[], transactions_table=[]
        )
        
    df = pd.DataFrame(request.enriched_df)
    
    kpis = get_corporate_risk_kpis(df)
    risk_dist = get_risk_distribution(df)
    top_corp = get_top_corporates(df)
    branch_exp = get_branch_exposure(df)
    country_exp = get_country_exposure(df)
    product_exp = get_product_exposure_details(df)
    trend_exp = get_trend_exposure(df, request.trend_agg)
    tx_table = get_transactions_table(df)
    
    return HighRiskCorporateResponseDto(
        kpis=kpis,
        risk_distribution=risk_dist,
        top_corporates=top_corp,
        branch_exposure=branch_exp,
        country_exposure=country_exp,
        product_exposure=product_exp,
        trend_exposure=trend_exp,
        transactions_table=tx_table
    )

from api.services.transaction_monitoring_service import (
    detect_high_value_transactions,
    detect_fatf_ofac,
    detect_multiple_operators_same_beneficiary,
    detect_high_frequency_remittances,
    detect_configurable_load_refund_window,
    detect_multiple_cards_contact,
    detect_multiple_cards_traveller,
    detect_multiple_cards_multi_operator
)

class TransactionMonitoringRequestDto(BaseModel):
    filtered_df: List[Dict[str, Any]]
    threshold_days: Optional[int] = 1

@router.post("/api/pages/transaction-monitoring")
def transaction_monitoring_data(request: TransactionMonitoringRequestDto = Body(...)):
    if not request.filtered_df:
        return {}
        
    df = pd.DataFrame(request.filtered_df)
    
    hv_df, str_df, hv_sum = detect_high_value_transactions(df)
    fatf_df, fatf_sum = detect_fatf_ofac(df)
    mult_op_df, mult_op_sum = detect_multiple_operators_same_beneficiary(df)
    high_freq_df, high_freq_sum = detect_high_frequency_remittances(df)
    freq_reload_df, freq_reload_sum = detect_configurable_load_refund_window(df, request.threshold_days)
    mult_card_contact_df, mult_card_contact_sum = detect_multiple_cards_contact(df)
    mult_card_trav_df, mult_card_trav_sum = detect_multiple_cards_traveller(df)
    mult_card_ops_df, mult_card_ops_sum = detect_multiple_cards_multi_operator(df)
    
    return clean_dict_for_json({
        "high_value": {"data": hv_df, "structuring": str_df, "summary": hv_sum},
        "fatf_ofac": {"data": fatf_df, "summary": fatf_sum},
        "multiple_operators": {"data": mult_op_df, "summary": mult_op_sum},
        "high_frequency": {"data": high_freq_df, "summary": high_freq_sum},
        "load_refund_window": {"data": freq_reload_df, "summary": freq_reload_sum},
        "multiple_cards_contact": {"data": mult_card_contact_df, "summary": mult_card_contact_sum},
        "multiple_cards_traveller": {"data": mult_card_trav_df, "summary": mult_card_trav_sum},
        "multi_card_multi_operator": {"data": mult_card_ops_df, "summary": mult_card_ops_sum}
    })
from api.services.fatf_service import (
    get_fatf_flagged_transactions,
    get_fatf_kpis,
    get_fatf_branch_seg_summary,
    get_fatf_country_seg_summary,
    get_fatf_purpose_counts,
    get_fatf_trend
)

class FATFRequestDto(BaseModel):
    filtered_df: List[Dict[str, Any]]
    
class FATFResponseDto(BaseModel):
    kpis: Dict[str, Any]
    branch_seg_summary: List[Dict[str, Any]]
    country_seg_summary: List[Dict[str, Any]]
    purpose_counts: List[Dict[str, Any]]
    trend: List[Dict[str, Any]]
    flagged_transactions: List[Dict[str, Any]]

@router.post("/api/pages/fatf", response_model=FATFResponseDto)
def fatf_data(request: FATFRequestDto = Body(...)):
    if not request.filtered_df:
        return FATFResponseDto(kpis={}, branch_seg_summary=[], country_seg_summary=[], purpose_counts=[], trend=[], flagged_transactions=[])
    
    df = pd.DataFrame(request.filtered_df)
    
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
    flagged = get_fatf_flagged_transactions(df)
    kpis = get_fatf_kpis(flagged, df)
    
    branch_seg = get_fatf_branch_seg_summary(flagged).replace([float('inf'), float('-inf'), float('nan')], None).to_dict('records')
    country_seg = get_fatf_country_seg_summary(flagged).replace([float('inf'), float('-inf'), float('nan')], None).to_dict('records')
    purpose_c = get_fatf_purpose_counts(flagged).replace([float('inf'), float('-inf'), float('nan')], None).to_dict('records')
    
    trend = []
    if not flagged.empty and 'Date' in flagged.columns:
        trend_df = flagged.groupby(flagged['Date'].dt.date).agg(Total_Amount=('Net Amt', 'sum')).reset_index()
        trend_df['Date'] = trend_df['Date'].astype(str)
        trend = trend_df.replace([float('inf'), float('-inf'), float('nan')], None).to_dict('records')

    # Dates format in flagged
    for col in flagged.columns:
        if pd.api.types.is_datetime64_any_dtype(flagged[col]):
            flagged[col] = flagged[col].astype(str)

    flagged_records = flagged.replace([float('inf'), float('-inf'), float('nan')], None).to_dict('records')
    
    return FATFResponseDto(
        kpis=kpis,
        branch_seg_summary=branch_seg,
        country_seg_summary=country_seg,
        purpose_counts=purpose_c,
        trend=trend,
        flagged_transactions=flagged_records
    )

from api.services.agent_analysis_service import (
    get_agent_kpis,
    get_agent_frequency_table,
    get_agent_trend_table,
    get_suspicious_agents_many,
    get_suspicious_agents1_many_relation,
    get_suspicious_agents1_one_relation
)

class AgentAnalysisRequestDto(BaseModel):
    filtered_df: List[Dict[str, Any]]
    agent_col: Optional[str] = "Agent"
    branch_col: Optional[str] = "Branch Name"
    beneficiary_col: Optional[str] = "Beneficiary Type Load or Reload"
    trend_agg: Optional[str] = "DAILY"

@router.post("/api/pages/agent-analysis")
def agent_analysis_data(request: AgentAnalysisRequestDto = Body(...)):
    if not request.filtered_df:
        return {}
        
    df = pd.DataFrame(request.filtered_df)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
    kpis = get_agent_kpis(df, request.agent_col, request.branch_col, request.beneficiary_col)
    
    if not kpis:
        return {}
        
    agent_df = kpis.pop('agent_df', pd.DataFrame())
    beneficiary_df = kpis.pop('beneficiary_df', pd.DataFrame())
    
    freq_df, freq_disp = get_agent_frequency_table(agent_df, request.agent_col, "Count")
    trend_df, trend_disp = get_agent_trend_table(agent_df, request.trend_agg)
    
    # Suspicious panels
    susp_complex, _ = get_suspicious_agents_many(agent_df, request.agent_col, 'Party Code', 5)
    susp_many, _, _ = get_suspicious_agents1_many_relation(beneficiary_df, request.agent_col, request.beneficiary_col, 5)
    susp_one, _, _ = get_suspicious_agents1_one_relation(beneficiary_df, request.agent_col, request.beneficiary_col, 5)
    
    def _clean_df(d):
        for col in d.columns:
            if pd.api.types.is_datetime64_any_dtype(d[col]):
                d[col] = d[col].astype(str)
        return d.replace([float('inf'), float('-inf'), float('nan')], None).to_dict('records')

    return clean_dict_for_json({
        "kpis": kpis,
        "frequency_table": _clean_df(freq_disp),
        "trend_table": _clean_df(trend_disp),
        "suspicious_complex": _clean_df(susp_complex),
        "suspicious_many": _clean_df(susp_many),
        "suspicious_one": _clean_df(susp_one)
    })

from api.services.passenger_analysis_service import (
    prepare_passenger_data,
    get_passenger_kpis,
    get_passenger_anomalies,
    get_branch_quality_summary
)

class PassengerAnalysisRequestDto(BaseModel):
    filtered_df: List[Dict[str, Any]]
    
@router.post("/api/pages/passenger-analysis")
def passenger_analysis_data(request: PassengerAnalysisRequestDto = Body(...)):
    if not request.filtered_df:
        return {}
        
    df = pd.DataFrame(request.filtered_df)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
    prep_df = prepare_passenger_data(df)
    kpis = get_passenger_kpis(prep_df)
    anomalies = get_passenger_anomalies(prep_df)
    branch_summary, worst_kpis = get_branch_quality_summary(prep_df)
    
    def _clean_df(d):
        for col in d.columns:
            if pd.api.types.is_datetime64_any_dtype(d[col]):
                d[col] = d[col].astype(str)
        return d.replace([float('inf'), float('-inf'), float('nan')], None).to_dict('records')

    cleaned_anomalies = {k: _clean_df(v) for k, v in anomalies.items()}
    
    return clean_dict_for_json({
        "kpis": kpis,
        "anomalies": cleaned_anomalies,
        "branch_summary": _clean_df(branch_summary),
        "worst_kpis": worst_kpis
    })
