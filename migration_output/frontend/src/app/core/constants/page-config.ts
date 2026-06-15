export const PAGE_CONFIG: Record<string, { filter_columns: string[], default_filters: Record<string, string[]>, description: string }> = {
    'HOME PAGE': {
        'filter_columns': ['LOCATION', 'PRODUCT', 'TxnPurpose', 'TXNTYPE', 'CUSTOMERNAME', 'CountryToTravel', 'Risk Category', 'Currency', 'AGENTNAME', 'OFAC_FATF', 'Segment'],
        'default_filters': {},
        'description': 'Executive overview of monthly transactions for the full AML compliance workflow.',
    },
    'TRANSACTION SUMMARY': {
        'filter_columns': ['LOCATION', 'TXNTYPE', 'TxnPurpose', 'Currency', 'Risk Category', 'Segment', 'PRODUCT'],
        'default_filters': {},
        'description': 'Summarize total transactions, value and count for the month.',
    },
    'TOUR OPERATOR': {
        'filter_columns': ['LOCATION', 'TxnPurpose', 'TXNTYPE', 'CUSTOMERNAME', 'AGENTNAME', 'CountryToTravel', 'Currency', 'Segment'],
        'default_filters': {'TxnPurpose': [
            'REMITTANCE BY TOUR OPERATORS', 
            'MICE -REMITANCE BY TOUR OPERATORS'
        ]},
        'description': 'Analyze tour operator remittances and concentration for compliance review.',
    },
    'RETAIL HIGH VALUE TXN': {
        'filter_columns': ['LOCATION', 'TxnPurpose', 'TXNTYPE', 'CUSTOMERNAME', 'Currency', 'AGENTNAME', 'Segment'],
        'default_filters': {},
        'description': 'Review high-value retail transactions that require additional compliance attention.',
    },
    'HIGH RISK CORPORATE': {
        'filter_columns': ['LOCATION', 'CUSTOMERNAME', 'Risk Category', 'TxnPurpose', 'AGENTNAME', 'Currency', 'Segment', 'PRODUCT'],
        'default_filters': {},
        'description': 'Monitor transactions involving high-risk corporates, trusts and societies.',
    },
    'FATF': {
        'filter_columns': ['LOCATION', 'CountryToTravel', 'OFAC_FATF', 'TxnPurpose', 'CUSTOMERNAME', 'Currency', 'Segment'],
        'default_filters': {'OFAC_FATF': ['YES', 'OFAC', 'FATF', 'FLAG']},
        'description': 'Track OFAC / FATF exposures and flagged geographies for compliance review.',
    },
    'BANK BOOK': {
        'filter_columns': ['LOCATION', 'TXNTYPE', 'Currency', 'CUSTOMERNAME', 'TxnPurpose', 'Segment'],
        'default_filters': {},
        'description': 'Bank book review for transaction flow, cash and remittance balances.',
    },
    'CASH ANALYSIS': {
        'filter_columns': ['LOCATION', 'TXNTYPE', 'CUSTOMERNAME', 'TxnPurpose', 'Currency', 'Segment'],
        'default_filters': {'TXNTYPE': ['PB', 'PS']},
        'description': 'Highlight cash-like transactions and regulatory threshold behavior.',
    },
    'TRANSACTION MONITORING': {
        'filter_columns': ['LOCATION', 'CUSTOMERNAME', 'AGENTNAME', 'CUSTOMERCODE', 'PAXIDNO', 'TxnPurpose', 'TXNTYPE', 'CountryToTravel', 'Segment'],
        'default_filters': {},
        'description': 'Automated AML parameter monitoring for suspicious transaction detection.',
    },
    'CURRENCY RATIO': {
        'filter_columns': ['LOCATION', 'Currency', 'TxnPurpose', 'AGENTNAME', 'Segment'],
        'default_filters': {},
        'description': 'Currency mix and replenishment ratio analysis for the month.',
    },
    'AGENT ANALYSIS': {
        'filter_columns': ['AGENTNAME', 'AGENTCODE', 'LOCATION', 'Branch', 'TXNTYPE', 'CUSTOMERNAME', 'CountryToTravel', 'PRODUCT', 'TxnPurpose'],
        'default_filters': {},
        'description': 'Analyze agent activity and suspicious multi-entity involvement.',
    },
    'MLTF': {
        'filter_columns': ['LOCATION', 'Risk Category', 'OFAC_FATF', 'TxnPurpose', 'Segment'],
        'default_filters': {},
        'description': 'Monitor Money Laundering and Terrorist Financing risks.',
    },
    'PASSENGER ANALYSIS': {
        'filter_columns': ['LOCATION', 'Segment', 'TXNTYPE'],
        'default_filters': {},
        'description': 'Analyze passenger data quality and identity anomalies.'
    },
};
