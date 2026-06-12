from .home_page import render_home_page
from .transaction_summary import render_transaction_summary_page
from .tour_operator import render_tour_operator_page
from .retail_high_value_txn import render_retail_high_value_txn_page
from .high_risk_corporate import render_high_risk_corporate_page
from .fatf import render_fatf_page
from .bank_book import render_bank_book_page
from .cash_analysis import render_cash_analysis_page
from .transaction_monitoring import render_transaction_monitoring_page
from .currency_ratio import render_currency_ratio_page
from .agent_analysis import render_agent_analysis_page
from .mltf import render_mltf_page
from .passenger_analysis import render_passenger_analysis_page

PAGE_NAMES = [
    'HOME PAGE',
    'TRANSACTION SUMMARY',
    'TOUR OPERATOR',
    'RETAIL HIGH VALUE TXN',
    'HIGH RISK CORPORATE',
    'FATF',
    'TRANSACTION MONITORING',
    'AGENT ANALYSIS',
    'PASSENGER ANALYSIS',
    # 'BANK BOOK',
    # 'CASH ANALYSIS',
    # 'CURRENCY RATIO',
]

PAGE_RENDERERS = {
    'HOME PAGE': render_home_page,
    'TRANSACTION SUMMARY': render_transaction_summary_page,
    'TOUR OPERATOR': render_tour_operator_page,
    'RETAIL HIGH VALUE TXN': render_retail_high_value_txn_page,
    'HIGH RISK CORPORATE': render_high_risk_corporate_page,
    'FATF': render_fatf_page,
    'TRANSACTION MONITORING': render_transaction_monitoring_page,
    'AGENT ANALYSIS': render_agent_analysis_page,
    'PASSENGER ANALYSIS': render_passenger_analysis_page,
    'BANK BOOK': render_bank_book_page,
    'CASH ANALYSIS': render_cash_analysis_page,
    'CURRENCY RATIO': render_currency_ratio_page,
}

PAGE_CONFIG = {
    'HOME PAGE': {
        'filter_columns': ['Branch Name', 'Product', 'Purpose', 'Txn Type', 'Corporate', 'Visiting Country', 'Risk  Category', 'Currency', 'Agent Name', 'OFAC _ FATF', 'Segments'],
        'default_filters': {},
        'description': 'Executive overview of monthly transactions for the full AML compliance workflow.',
    },
    'TRANSACTION SUMMARY': {
        'filter_columns': ['Branch Name', 'Txn Type', 'Purpose', 'Currency', 'Risk  Category', 'Segments', 'Product'],
        'default_filters': {},
        'description': 'Summarize total transactions, value and count for the month.',
    },
    'TOUR OPERATOR': {
        'filter_columns': ['Branch Name', 'Purpose', 'Txn Type', 'Corporate', 'Agent Name', 'Visiting Country', 'Currency', 'Segments'],
        'default_filters': {'Purpose': [
            'REMITTANCE BY TOUR OPERATORS', 
            'MICE -REMITANCE BY TOUR OPERATORS'
        ]},
        'description': 'Analyze tour operator remittances and concentration for compliance review.',
    },
    'RETAIL HIGH VALUE TXN': {
        'filter_columns': ['Branch Name', 'Purpose', 'Txn Type', 'Corporate', 'Currency', 'Agent Name', 'Segments'],
        'default_filters': {},
        'description': 'Review high-value retail transactions that require additional compliance attention.',
    },
    'HIGH RISK CORPORATE': {
        'filter_columns': ['Branch Name', 'Corporate', 'Risk  Category', 'Purpose', 'Agent Name', 'Currency', 'Segments', 'Product'],
        'default_filters': {'Risk  Category': ['HIGH']},
        'description': 'Monitor transactions involving high-risk corporates, trusts and societies.',
    },
    'FATF': {
        'filter_columns': ['Branch Name', 'Visiting Country', 'OFAC _ FATF', 'Purpose', 'Corporate', 'Currency', 'Segments'],
        'default_filters': {'OFAC _ FATF': ['YES', 'OFAC', 'FATF', 'FLAG']},
        'description': 'Track OFAC / FATF exposures and flagged geographies for compliance review.',
    },
    'BANK BOOK': {
        'filter_columns': ['Branch Name', 'Txn Type', 'Currency', 'Corporate', 'Purpose', 'Segments'],
        'default_filters': {},
        'description': 'Bank book review for transaction flow, cash and remittance balances.',
    },
    'CASH ANALYSIS': {
        'filter_columns': ['Branch Name', 'Txn Type', 'Corporate', 'Purpose', 'Currency', 'Segments'],
        'default_filters': {'Txn Type': ['PB', 'PS']},
        'description': 'Highlight cash-like transactions and regulatory threshold behavior.',
    },
    'TRANSACTION MONITORING': {
        'filter_columns': ['Branch Name', 'Corporate', 'Agent Name', 'Party Code', 'Passport', 'Purpose', 'Txn Type', 'Visiting Country', 'Segments'],
        'default_filters': {},
        'description': 'Automated AML parameter monitoring for suspicious transaction detection.',
    },
    'CURRENCY RATIO': {
        'filter_columns': ['Branch Name', 'Currency', 'Purpose', 'Agent Name', 'Segments'],
        'default_filters': {},
        'description': 'Currency mix and replenishment ratio analysis for the month.',
    },
    'AGENT ANALYSIS': {
        'filter_columns': ['Agent Name', 'Agent', 'Branch Name', 'Branch', 'Txn Type', 'Corporate', 'Visiting Country', 'Product', 'Purpose'],
        'default_filters': {},
        'description': 'Analyze agent activity and suspicious multi-entity involvement.',
    },
    'MLTF': {
        'filter_columns': ['Branch Name', 'Risk  Category', 'OFAC _ FATF', 'Purpose', 'Segments'],
        'default_filters': {},
        'description': 'Monitor Money Laundering and Terrorist Financing risks.',
    },
    'PASSENGER ANALYSIS': {
        'filter_columns': ['Branch Name', 'Segments', 'Txn Type'],
        'default_filters': {},
        'description': 'Analyze passenger data quality and identity anomalies.'
    },
}
