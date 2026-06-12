from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from api.routes import pages
import pandas as pd
import numpy as np
import time
import re
import io
import os
import json
import json
import logging
from fastapi import Request

# Setup Logging
logger = logging.getLogger("api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
app = FastAPI(title="GlobalPay AML Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    logger.info(f"REQUEST => {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        logger.info(f"RESPONSE <= {response.status_code} {request.url.path} {process_time:.3f}s")
        return response
    except Exception as e:
        process_time = time.perf_counter() - start_time
        logger.error(f"RESPONSE <= ERROR {request.url.path} {process_time:.3f}s - {str(e)}")
        raise

app.include_router(pages.router)

class RowCountMismatchError(Exception):
    pass

def _validate_row_count(df, initial_count, step_name):
    if len(df) != initial_count:
        raise RowCountMismatchError(f"Row count changed after {step_name}. Initial: {initial_count}, After: {len(df)}")

def clean_mobile_number(val):
    if pd.isna(val) or str(val).strip().upper() in ['', 'NAN', 'NONE', 'NULL']:
        return np.nan
    s = str(val).strip()
    s = re.sub(r'\.0$', '', s)
    s = s.replace(' ', '')
    return s

def clean_identifier(val):
    if pd.isna(val) or str(val).strip().upper() in ['', 'NAN', 'NONE', 'NULL']:
        return np.nan
    s = str(val).strip()
    chars_to_remove = "'`~#*\""
    s = s.strip(chars_to_remove).strip()
    s = re.sub(r'\.0$', '', s)
    s = re.sub(r'[^\x20-\x7E]', '', s)
    return s

def standardize_identifier_columns(df: pd.DataFrame) -> pd.DataFrame:
    mobile_cols = ['MOBILENO']
    identifier_cols = [
        'INSTRUMENTNO', 'Instrument Number',
        'Party Code', 'CUSTOMERCODE', 'PARTYCODE', 
        'Agent', 'AGENTCODE', 
        'Passport', 'PASSPORTNO', 
        'DOCNO'
    ]

    for col in df.columns:
        if col in mobile_cols:
            df[col] = df[col].apply(clean_mobile_number)
        elif col in identifier_cols:
            df[col] = df[col].apply(clean_identifier)
            
    return df

def create_canonical_dataset(txn_df: pd.DataFrame, party_master_path: str, ofac_path: str):
    initial_row_count = len(txn_df)
    print(f"Source Row Count: {initial_row_count}")

    column_mapping = {
        'BRANCHCODE': 'Branch',
        'LOCATION': 'Branch Name',
        'TXNTYPE': 'Txn Type',
        'DOCNO': 'Doc Number',
        'TXNDATE': 'Date',
        'CUSTOMERCODE': 'Party Code',
        'CUSTOMERNAME': 'Corporate',
        'PAXNAME': 'Passenger Name',
        'PAXIDNO': 'Passport',
        'AGENTCODE': 'Agent',
        'AGENTNAME': 'Agent Name',
        'TxnPurpose': 'Purpose',
        'CURRENCY': 'Currency',
        'PRODUCT': 'Product',
        'ISSUER': 'Issuer',
        'SELLRATE': 'Rate',
        'CountryToTravel': 'Visiting Country',
        'INSTRUMENTNO': 'INSTRUMENTNO',
        'LoadReload': 'LoadReload',
        'Segment': 'Segment',
        'BENEFICIARY': 'Beneficiary Type Load or Reload',
        'INRAMOUNT': 'Net Amt',
        'EMAILID': 'EMAILID',
        'MOBILENO': 'MOBILENO',
    }

    df = txn_df[[col for col in column_mapping.keys() if col in txn_df.columns]].copy()
    df.rename(columns=column_mapping, inplace=True)

    df = standardize_identifier_columns(df)

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Net Amt'] = pd.to_numeric(df['Net Amt'], errors='coerce').fillna(0)
    df['Rate'] = pd.to_numeric(df['Rate'], errors='coerce')

    df['Day'] = df['Date'].dt.day.fillna(0).astype(int)
    df['Week'] = df['Date'].dt.isocalendar().week.fillna(0).astype(int)
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    df['Year'] = df['Date'].dt.year.fillna(0).astype(int)
    df['Weekday'] = df['Date'].dt.day_name().fillna('Unknown')

    pm_start = time.perf_counter()
    if os.path.exists(party_master_path):
        pm_df = pd.read_csv(party_master_path)
        pm_df.rename(columns={'Customer Code': 'CUSTOMERCODE', 'RISKCATEGORY': 'RISKCATEGORY_PM'}, inplace=True)
        pm_mapping = pm_df[['CUSTOMERCODE', 'RISKCATEGORY_PM']].copy()
        pm_mapping['CUSTOMERCODE'] = pm_mapping['CUSTOMERCODE'].apply(clean_identifier)
        pm_mapping.drop_duplicates(subset=['CUSTOMERCODE'], inplace=True)

        df = pd.merge(df, pm_mapping, left_on='Party Code', right_on='CUSTOMERCODE', how='left', validate="many_to_one")
        _validate_row_count(df, initial_row_count, "Party Master Lookup")
        print("Row count validated after Party Master Lookup.")
        
        def map_risk_category(risk):
            if pd.isna(risk):
                return 'Unknown'
            risk = str(risk).upper()
            if 'HIGH' in risk:
                return 'High'
            if 'MEDIUM' in risk:
                return 'Medium'
            if 'LOW' in risk:
                return 'Low'
            return 'Unknown'

        df['Risk Category'] = df['RISKCATEGORY_PM'].apply(map_risk_category)
        df.drop(columns=['CUSTOMERCODE', 'RISKCATEGORY_PM'], inplace=True, errors='ignore')
    else:
        df['Risk Category'] = 'Unknown'
        print("Party Master file not found, skipping enrichment.")
        
    print(f"Party Master Lookup Time: {round(time.perf_counter() - pm_start, 2)}s")

    ofac_start = time.perf_counter()
    if os.path.exists(ofac_path):
        ofac_df = pd.read_excel(ofac_path, sheet_name='UPDATED FILE')
        ofac_mapping = ofac_df[['COUNTRY', 'Segment']].copy()
        ofac_mapping.rename(columns={'Segment': 'OFAC_FATF_Segment'}, inplace=True)
        ofac_mapping['COUNTRY'] = ofac_mapping['COUNTRY'].astype(str).str.strip().str.upper()
        ofac_mapping.drop_duplicates(subset=['COUNTRY'], inplace=True)

        df['Visiting Country_upper'] = df['Visiting Country'].astype(str).str.strip().str.upper()
        df = pd.merge(df, ofac_mapping, left_on='Visiting Country_upper', right_on='COUNTRY', how='left', validate="many_to_one")
        _validate_row_count(df, initial_row_count, "OFAC FATF Lookup")
        print("Row count validated after OFAC FATF Lookup.")

        df['OFAC_FATF'] = df['OFAC_FATF_Segment'].fillna('NOT FLAGGED')
        df.drop(columns=['Visiting Country_upper', 'COUNTRY', 'OFAC_FATF_Segment'], inplace=True, errors='ignore')
    else:
        df['OFAC_FATF'] = 'NOT FLAGGED'
        print("OFAC FATF file not found, skipping enrichment.")
        
    print(f"OFAC Lookup Time: {round(time.perf_counter() - ofac_start, 2)}s")

    eqv_start = time.perf_counter()
    df['DateOnly'] = df['Date'].dt.date
    usd_rates = df[df['Currency'] == 'USD'].groupby('DateOnly')['Rate'].mean().reset_index()
    usd_rates.rename(columns={'Rate': 'Daily_USD_Avg_Rate'}, inplace=True)
    
    df = pd.merge(df, usd_rates, on='DateOnly', how='left')
    df['Daily_USD_Avg_Rate'] = df['Daily_USD_Avg_Rate'].ffill().bfill()

    df['Equivalent USD Amount'] = df['Net Amt'] / df['Daily_USD_Avg_Rate']
    df.drop(columns=['DateOnly', 'Daily_USD_Avg_Rate'], inplace=True)
    
    _validate_row_count(df, initial_row_count, "Equivalent USD Amount Calculation")
    print("Row count validated after Equivalent USD Amount Calculation.")
    print(f"EQV USD Calculation Time: {round(time.perf_counter() - eqv_start, 2)}s")

    df['High Value Transaction'] = df['Equivalent USD Amount'] > 25000
    df['FATF / OFAC Flag'] = df['OFAC_FATF'] != 'NOT FLAGGED'
    
    df.rename(columns={
        'Equivalent USD Amount': 'EQV USD',
        'OFAC_FATF': 'OFAC _ FATF',
        'Risk Category': 'Risk  Category' 
    }, inplace=True)

    if 'Segment' in df.columns:
        SEGMENT_STANDARDIZATION_MAP = {
            'Students Credila': 'EDUCATION',
            'Students Non-Credila': 'EDUCATION',
            'Corporate': 'CORPORATE',
            'Tour Remittance': 'TOUR OPERATOR',
            'Leisure': 'OTHER',
            'Other Remittance': 'OTHER',
            'Wholesale': 'OTHER',
            'Inter-Branch': 'OTHER',
            'Referral': 'OTHER',
            'Others': 'OTHER'
        }

        df['Grouped Segment'] = (
            df['Segment']
            .astype(str)
            .str.strip()
            .map(SEGMENT_STANDARDIZATION_MAP)
            .fillna('OTHER')
        )
        
        df['Segments'] = df['Grouped Segment']
        _validate_row_count(df, initial_row_count, "Segment Standardization")
        print("Row count validated after Segment Standardization.")
        df.drop(columns=['Grouped Segment'], inplace=True)

    TEXT_COLUMNS = [
        'Passport',
        'Issuer',
        'Party Code',
        'Corporate',
        'Passenger Name',
        'EMAILID',
        'MOBILENO',
        'Beneficiary Type Load or Reload',
        'Instrument Number'
    ]
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str)

    _validate_row_count(df, initial_row_count, "Final Derived Fields")
    print(f"Canonical dataset created successfully. Final row count: {len(df)}")

    return df

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    if file.filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(contents))
    else:
        df = pd.read_excel(io.BytesIO(contents))
        
    # We don't have these files lying around directly in this PR unless mounted,
    # so we pass dummy paths that don't exist to gracefully skip
    party_master_path = "party_master.csv"
    ofac_path = "ofac.xlsx"
    
    df = create_canonical_dataset(df, party_master_path, ofac_path)
    
    parsed_data = json.loads(df.to_json(orient="records", date_format="iso"))
    
    return {"filename": file.filename, "row_count": len(df), "data": parsed_data}

@app.post("/api/upload/party-master")
async def upload_party_master(file: UploadFile = File(...), filtered_df: str = Form(...)):
    contents = await file.read()
    if file.filename.endswith('.csv'):
        pm_df = pd.read_csv(io.BytesIO(contents))
    else:
        pm_df = pd.read_excel(io.BytesIO(contents))
        
    data = json.loads(filtered_df)
    df = pd.DataFrame(data)
    
    from api.services.high_risk_corporate_service import enrich_corporate_data
    try:
        enriched_df = enrich_corporate_data(df, pm_df)
        parsed_data = json.loads(enriched_df.to_json(orient="records", date_format="iso"))
        return {"enriched_data": parsed_data}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/upload/ofac")
async def upload_ofac(file: UploadFile = File(...), filtered_df: str = Form(...)):
    contents = await file.read()
    if file.filename.endswith('.csv'):
        ofac_df = pd.read_csv(io.BytesIO(contents))
    else:
        ofac_df = pd.read_excel(io.BytesIO(contents), sheet_name=0) # Read first sheet

    data = json.loads(filtered_df)
    df = pd.DataFrame(data)
    
    try:
        if 'COUNTRY' not in ofac_df.columns or 'Segment' not in ofac_df.columns:
            return {"error": "OFAC file must contain 'COUNTRY' and 'Segment' columns."}
            
        ofac_mapping = ofac_df[['COUNTRY', 'Segment']].copy()
        ofac_mapping.rename(columns={'Segment': 'OFAC_FATF_Segment'}, inplace=True)
        ofac_mapping['COUNTRY'] = ofac_mapping['COUNTRY'].astype(str).str.strip().str.upper()
        ofac_mapping.drop_duplicates(subset=['COUNTRY'], inplace=True)

        if 'Visiting Country' in df.columns:
            df['Visiting Country_upper'] = df['Visiting Country'].astype(str).str.strip().str.upper()
            
            # If the column already exists, drop it to avoid _x _y suffixes
            if 'OFAC_FATF_Segment' in df.columns:
                df.drop(columns=['OFAC_FATF_Segment'], inplace=True)
                
            df = pd.merge(df, ofac_mapping, left_on='Visiting Country_upper', right_on='COUNTRY', how='left')
            df['FATF / OFAC Flag'] = df['OFAC_FATF_Segment'].notna() & (df['OFAC_FATF_Segment'] != 'NOT FLAGGED')
            df['OFAC _ FATF'] = df['OFAC_FATF_Segment'].fillna('NOT FLAGGED')
            df.drop(columns=['Visiting Country_upper', 'COUNTRY', 'OFAC_FATF_Segment'], inplace=True, errors='ignore')

        parsed_data = json.loads(df.to_json(orient="records", date_format="iso"))
        return {"enriched_data": parsed_data}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

