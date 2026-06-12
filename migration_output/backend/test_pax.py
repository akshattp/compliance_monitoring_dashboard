import pandas as pd
from api.routes.pages import passenger_analysis_data, PassengerAnalysisRequestDto
df = pd.DataFrame([{
    "Date": "2023-01-01", 
    "Net Amt": 100, 
    "Txn Type": "PS", 
    "Corporate": "Test Corp", 
    "Branch Name": "HQ", 
    "Passenger Name": "John Doe",
    "Beneficiary Type Load or Reload": "B"
}])
records = df.to_dict('records')
res = passenger_analysis_data(PassengerAnalysisRequestDto(filtered_df=records))
print("Result:", res)
