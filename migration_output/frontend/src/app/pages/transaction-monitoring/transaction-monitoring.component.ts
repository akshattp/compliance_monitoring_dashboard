import { environment } from '../../../environments/environment';
import { Component, computed, effect, inject, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { DataService } from '../../core/services/data.service';
import { HttpClient } from '@angular/common/http';
import { PlotlyViaWindowModule } from 'angular-plotly.js';
import { AgGridAngular } from 'ag-grid-angular';
import { KpiCardComponent } from '../../shared/components/kpi-card/kpi-card.component';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { SharedTableComponent, ColumnDef } from '../../shared/components/shared-table/shared-table.component';
import { HumanReadableAmountPipe } from '../../shared/pipes/human-readable-amount.pipe';
import { ENTERPRISE_THEME } from '../../shared/chart-theme.service';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-transaction-monitoring',
  standalone: true,
  imports: [
    CommonModule, 
    PlotlyViaWindowModule, 
    HumanReadableAmountPipe,
    DecimalPipe,
    FormsModule,
    SharedTableComponent
  ],
  templateUrl: './transaction-monitoring.component.html',
  styleUrls: ['./transaction-monitoring.component.scss']
})
export class TransactionMonitoringComponent {
  dataService = inject(DataService);
  private http = inject(HttpClient);

  thresholdDays = signal<number>(1);
  highValueThreshold = signal<number>(25000);
  freqThreshold = signal<number>(5);
  tmData = signal<any>(null);

  theme = ENTERPRISE_THEME;

  formatAmt(val: number): string {
    if (val == null) return '0';
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)}Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)}L`;
    return `₹${val.toLocaleString()}`;
  }

  downloadCSV(data: any[] | undefined, filename: string) {
    if (!data || data.length === 0) return;
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
    
    for (const row of data) {
      const values = headers.map(header => {
        let val = row[header];
        if (val === null || val === undefined) val = '';
        const strVal = String(val).replace(/"/g, '""');
        return `"${strVal}"`;
      });
      csvRows.push(values.join(','));
    }
    
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  expandedRule = signal<string | null>(null);

  toggleRule(rule: string) {
    if (this.expandedRule() === rule) {
      this.expandedRule.set(null);
    } else {
      this.expandedRule.set(rule);
    }
  }

  fetchData() {
    const df = this.dataService.filteredDf();
    if (!df || df.length === 0) return;

    this.http.post<any>(`${environment.apiBaseUrl}/api/pages/transaction-monitoring`, {
      filtered_df: df,
      threshold_days: this.thresholdDays(),
      high_value_threshold: this.highValueThreshold(),
      freq_threshold: this.freqThreshold()
    }).subscribe(res => {
      this.tmData.set(res);
    });
  }

  constructor() {
    effect(() => {
      const df = this.dataService.filteredDf();
      const threshold = this.thresholdDays();
      const hv = this.highValueThreshold();
      const fq = this.freqThreshold();
      if (df && df.length > 0) {
        this.fetchData();
      }
    });
  }

  // --- Helpers for Summary Table ---
  summaryTable = computed(() => {
    const data = this.tmData();
    if (!data) return [];
    
    return [
      {
        ruleName: 'High Value Transaction',
        description: 'Identify transactions exceeding USD 25,000 threshold',
        flaggedCount: data.high_value.summary.high_value_count,
        totalExposure: data.high_value.summary.high_value_exposure
      },
      {
        ruleName: 'FATF / OFAC Match',
        description: 'Identify transactions involving high-risk jurisdictions',
        flaggedCount: data.fatf_ofac.summary.flagged_count,
        totalExposure: data.fatf_ofac.summary.flagged_amount
      },
      {
        ruleName: 'Multiple Operators to Same Beneficiary',
        description: 'Identify multiple operators remitting to same beneficiary',
        flaggedCount: data.multiple_operators.summary.suspicious_beneficiary_count,
        totalExposure: data.multiple_operators.summary.flagged_amount
      },
      {
        ruleName: 'High Frequency Remittances',
        description: 'Identify high frequency remittances to same beneficiary',
        flaggedCount: data.high_frequency.summary.repeat_pair_count,
        totalExposure: data.high_frequency.summary.flagged_amount
      },
      {
        ruleName: 'Configurable Load-to-Refund Window',
        description: `Identify cards with load/reload and refund within ${this.thresholdDays()} days`,
        flaggedCount: data.load_refund_window.summary.events,
        totalExposure: data.load_refund_window.summary.exposure
      },
      {
        ruleName: 'Multiple Cards to Same Contact',
        description: 'Mobile numbers associated with 3 or more distinct cards',
        flaggedCount: data.multiple_cards_contact.summary.count,
        totalExposure: data.multiple_cards_contact.summary.exposure
      },
      {
        ruleName: 'Multiple Cards to Same Traveller',
        description: 'Travellers associated with 2 or more distinct cards',
        flaggedCount: data.multiple_cards_traveller.summary.count,
        totalExposure: data.multiple_cards_traveller.summary.exposure
      },
      {
        ruleName: 'Multi-Card Multi-Operator Use',
        description: 'Travellers using 2 or more cards across 2 or more operators',
        flaggedCount: data.multi_card_multi_operator.summary.count,
        totalExposure: data.multi_card_multi_operator.summary.exposure
      }
    ];
  });

  // --- Chart Helpers ---
  getBranchChart(data: any[]) {
    if (!data || data.length === 0) return null;
    const counts = new Map<string, number>();
    
    let colToUse = 'LOCATION';
    if (data[0] && !(colToUse in data[0])) {
      if ('CUSTOMERNAME' in data[0]) colToUse = 'CUSTOMERNAME';
      else if ('AGENTNAME' in data[0]) colToUse = 'AGENTNAME';
      else colToUse = Object.keys(data[0])[0] || 'Unknown';
    }

    data.forEach(row => {
      const val = row[colToUse] || 'Unknown';
      counts.set(val, (counts.get(val) || 0) + 1);
    });
    
    const sorted = Array.from(counts.entries()).sort((a, b) => b[1] - a[1]).slice(0, 10);
    return {
      data: [{
        x: sorted.map(d => d[0]),
        y: sorted.map(d => d[1]),
        type: 'bar',
        marker: { color: this.theme.colorway[0] }
      }],
      layout: {
        title: { text: `Flagged by ${colToUse}`, font: { family: this.theme.font.family, color: this.theme.font.color, size: 14 } },
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        margin: { l: 50, r: 20, t: 45, b: 100 },
        xaxis: { tickfont: { family: this.theme.font.family }, tickangle: -45, automargin: true },
        yaxis: { tickfont: { family: this.theme.font.family } }
      }
    };
  }

  getRiskPieChart(data: any[]) {
    if (!data || data.length === 0) return null;
    const counts = new Map<string, number>();
    
    let colToUse = 'Risk Category';
    if (data[0] && !('Risk Category' in data[0]) && ('Retail_Risk_Level' in data[0])) {
       colToUse = 'Retail_Risk_Level';
    }

    data.forEach(row => {
      const val = row[colToUse] || row['Risk Category'] || 'Unknown Risk';
      counts.set(val, (counts.get(val) || 0) + 1);
    });

    return {
      data: [{
        labels: Array.from(counts.keys()),
        values: Array.from(counts.values()),
        type: 'pie',
        hole: 0.4,
        marker: { colors: this.theme.colorway }
      }],
      layout: {
        title: { text: 'Risk Category Distribution', font: { family: this.theme.font.family, color: this.theme.font.color, size: 14 } },
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        margin: { l: 20, r: 20, t: 45, b: 80 },
        legend: { orientation: 'h', y: -0.2 }
      }
    };
  }

  ruleCharts = computed(() => {
    const data = this.tmData();
    if (!data) return null;
    
    return {
      hvBranch: this.getBranchChart(data.high_value?.data),
      hvRisk: this.getRiskPieChart(data.high_value?.data),
      fatfBranch: this.getBranchChart(data.fatf_ofac?.data),
      fatfRisk: this.getRiskPieChart(data.fatf_ofac?.data),
      multOpBranch: this.getBranchChart(data.multiple_operators?.data),
      multOpRisk: this.getRiskPieChart(data.multiple_operators?.data),
      highFreqBranch: this.getBranchChart(data.high_frequency?.data),
      highFreqRisk: this.getRiskPieChart(data.high_frequency?.data),
      lrwBranch: this.getBranchChart(data.load_refund_window?.data),
      lrwRisk: this.getRiskPieChart(data.load_refund_window?.data),
      mcContactBranch: this.getBranchChart(data.multiple_cards_contact?.data),
      mcContactRisk: this.getRiskPieChart(data.multiple_cards_contact?.data),
      mcTravellerBranch: this.getBranchChart(data.multiple_cards_traveller?.data),
      mcTravellerRisk: this.getRiskPieChart(data.multiple_cards_traveller?.data),
      mcMoBranch: this.getBranchChart(data.multi_card_multi_operator?.data),
      mcMoRisk: this.getRiskPieChart(data.multi_card_multi_operator?.data),
    }
  });

  // --- Table Columns ---
  summaryCols: ColumnDef[] = [
    { field: 'ruleName', header: 'Risk Name', isBold: true },
    { field: 'description', header: 'Description' },
    { field: 'flaggedCount', header: 'Flagged Count', type: 'number', align: 'right' },
    { field: 'totalExposure', header: 'Total Exposure', type: 'amount', align: 'right' }
  ];

  hvCols: ColumnDef[] = [
    { field: 'TXNDATE', header: 'TXNDATE', type: 'date' },
    { field: 'CUSTOMERNAME', header: 'CUSTOMERNAME' },
    { field: 'PAXNAME', header: 'PAXNAME' },
    { field: 'LOCATION', header: 'LOCATION' },
    { field: 'INRAMOUNT', header: 'INRAMOUNT', type: 'amount', align: 'right' },
    { field: 'Equivalent USD Amount', header: 'Equivalent USD Amount ($)', type: 'usd', align: 'right' }
  ];

  fatfCols: ColumnDef[] = [
    { field: 'TXNDATE', header: 'TXNDATE', type: 'date' },
    { field: 'CUSTOMERNAME', header: 'CUSTOMERNAME' },
    { field: 'CountryToTravel', header: 'CountryToTravel' },
    { field: 'OFAC_FATF', header: 'OFAC / FATF' },
    { field: 'INRAMOUNT', header: 'INRAMOUNT', type: 'amount', align: 'right' }
  ];

  multOpCols: ColumnDef[] = [
    { field: 'TXNDATE', header: 'TXNDATE', type: 'date' },
    { field: 'CUSTOMERNAME', header: 'CUSTOMERNAME' },
    { field: 'BENEFICIARY', header: 'Beneficiary / Card Number' },
    { field: 'INRAMOUNT', header: 'INRAMOUNT', type: 'amount', align: 'right' }
  ];


  lrwCols: ColumnDef[] = [
    { field: 'INSTRUMENTNO', header: 'Card Number' },
    { field: 'WITHIN_DAYS', header: 'Within Days', type: 'number', align: 'right' },
    { field: 'LOAD_DATE', header: 'Load Date', type: 'date' },
    { field: 'REFUND_DATE', header: 'Refund Date', type: 'date' },
    { field: 'LOAD_AMOUNT', header: 'Load Amount', type: 'amount', align: 'right' },
    { field: 'REFUND_AMOUNT', header: 'Refund Amount', type: 'amount', align: 'right' }
  ];

  mcContactCols: ColumnDef[] = [
    { field: 'MOBILENO', header: 'Mobile Number' },
    { field: 'Distinct_Cards', header: 'Distinct Cards', type: 'number', align: 'right' },
    { field: 'Transactions', header: 'Transactions', type: 'number', align: 'right' },
    { field: 'Exposure', header: 'Exposure', type: 'amount', align: 'right' }
  ];

  mcTravellerCols: ColumnDef[] = [
    { field: 'PAXIDNO', header: 'Traveller ID' },
    { field: 'PAXNAME', header: 'Traveller Name' },
    { field: 'Distinct_Cards', header: 'Distinct Cards', type: 'number', align: 'right' },
    { field: 'Transactions', header: 'Transactions', type: 'number', align: 'right' },
    { field: 'Exposure', header: 'Exposure', type: 'amount', align: 'right' }
  ];

  mcMoCols: ColumnDef[] = [
    { field: 'PAXIDNO', header: 'Traveller ID' },
    { field: 'PAXNAME', header: 'Traveller Name' },
    { field: 'Distinct_Cards', header: 'Distinct Cards', type: 'number', align: 'right' },
    { field: 'Distinct_Operators', header: 'Distinct Operators', type: 'number', align: 'right' },
    { field: 'Transactions', header: 'Transactions', type: 'number', align: 'right' },
    { field: 'Exposure', header: 'Exposure', type: 'amount', align: 'right' }
  ];

  reviewCols: ColumnDef[] = [
    { field: 'TXNDATE', header: 'TXNDATE', type: 'date' },
    { field: 'CUSTOMERNAME', header: 'CUSTOMERNAME' },
    { field: 'PAXNAME', header: 'PAXNAME' },
    { field: 'PAXIDNO', header: 'PAXIDNO' },
    { field: 'LOCATION', header: 'LOCATION' },
    { field: 'INRAMOUNT', header: 'INRAMOUNT', type: 'amount', align: 'right' },
    { field: 'Equivalent USD Amount', header: 'Equivalent USD Amount ($)', type: 'usd', align: 'right' },
    { field: 'Risk_Rule_Count', header: 'Rules Triggered', type: 'number', align: 'right', isBold: true },
    { field: 'R1_HV', header: 'R1 (HV)', align: 'center' },
    { field: 'R2_FATF', header: 'R2 (FATF)', align: 'center' },
    { field: 'R3_MultOp', header: 'R3 (MultOp)', align: 'center' },
    { field: 'R4_HighFreq', header: 'R4 (HighFreq)', align: 'center' },
    { field: 'R5_Lrw', header: 'R5 (LoadRefund)', align: 'center' },
    { field: 'R6_McContact', header: 'R6 (MultiCardContact)', align: 'center' },
    { field: 'R7_McTrav', header: 'R7 (MultiCardTraveller)', align: 'center' },
    { field: 'R8_McMo', header: 'R8 (MultiCardOperator)', align: 'center' }
  ];
}
