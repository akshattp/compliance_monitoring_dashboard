import pandas as pd
from api.routes.pages import transaction_monitoring_data, TransactionMonitoringRequestDto, fatf_data, FATFRequestDto, agent_analysis_data, AgentAnalysisRequestDto, passenger_analysis_data, PassengerAnalysisRequestDto

df = pd.DataFrame([{
    "Date": "2023-01-01", 
    "Net Amt": 100, 
    "Txn Type": "PS", 
    "Corporate": "Test Corp", 
    "Branch Name": "HQ", 
    "Passenger Name": "John Doe",
    "Beneficiary Type Load or Reload": "B",
    "Passport": "A1234567"
}])
records = df.to_dict('records')

print("Testing Transaction Monitoring...")
try:
    transaction_monitoring_data(TransactionMonitoringRequestDto(filtered_df=records))
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()

print("Testing FATF...")
try:
    fatf_data(FATFRequestDto(filtered_df=records))
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()

print("Testing Agent Analysis...")
try:
    res = agent_analysis_data(AgentAnalysisRequestDto(filtered_df=records, agent_col="Corporate"))
    print("Success", type(res))
except Exception as e:
    import traceback
    traceback.print_exc()

print("Testing Passenger Analysis...")
try:
    passenger_analysis_data(PassengerAnalysisRequestDto(filtered_df=records))
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
