import { environment } from '../../../environments/environment';
import { Component, effect, inject, signal, computed } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { DataService } from '../../core/services/data.service';
import { ENTERPRISE_THEME } from '../../shared/chart-theme.service';
import { SharedTableComponent, ColumnDef } from '../../shared/components/shared-table/shared-table.component';
import { SharedChartComponent } from '../../shared/components/shared-chart/shared-chart.component';
import { HumanReadableAmountPipe } from '../../shared/pipes/human-readable-amount.pipe';

import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-agent-analysis',
  standalone: true,
  imports: [CommonModule, DecimalPipe, FormsModule, SharedTableComponent, SharedChartComponent, HumanReadableAmountPipe],
  templateUrl: './agent-analysis.component.html',
  styleUrls: ['./agent-analysis.component.scss']
})
export class AgentAnalysisComponent {
  dataService = inject(DataService);
  private http = inject(HttpClient);

  agentData = signal<any>(null);
  theme = ENTERPRISE_THEME;

  chartMetric = 'Count';
  trendAgg = 'DAILY';
  rule1Mode = '1_MANY';
  rule1ManyThresh = 10;
  rule1OneThresh = 10;
  rule2Thresh = 10;
  rule3Thresh = 10;
  rule4Thresh = 10;

  rule1ManySearch = '';
  rule1OneSearch = '';
  
  freqGraph: any;
  trendGraph: any;
  branchGraph: any;
  countryGraph: any;
  corpGraph: any;
  benefGraph: any;
  productGraph: any;
  purposeGraph: any;

  baseCols: ColumnDef[] = [
    { field: 'Category', header: 'ID / Name' },
    { field: 'Count', header: 'Count', type: 'number', align: 'right' },
    { field: 'Count %', header: 'Count %', type: 'number', format: '1.2-2', align: 'right' },
    { field: 'INRAMOUNT', header: 'Net Amount', type: 'amount', align: 'right' },
    { field: 'Net Amount %', header: 'Net Amount %', type: 'number', format: '1.2-2', align: 'right' }
  ];

  trendCols: ColumnDef[] = [
    { field: 'Category', header: 'Period' },
    { field: 'Count', header: 'Count', type: 'number', align: 'right' },
    { field: 'Count %', header: 'Count %', type: 'number', format: '1.2-2', align: 'right' },
    { field: 'INRAMOUNT', header: 'Net Amount', type: 'amount', align: 'right' },
    { field: 'Net Amount %', header: 'Net Amount %', type: 'number', format: '1.2-2', align: 'right' }
  ];

  rule1Cols: ColumnDef[] = [
    { field: 'AGENTCODE', header: 'AGENTCODE' },
    { field: 'Beneficiary', header: 'Beneficiary' },
    { field: 'Transaction Count', header: 'Transaction Count', type: 'number', align: 'right' },
    { field: 'INRAMOUNT', header: 'Net Amount', type: 'amount', align: 'right' },
    { field: 'Relationship Frequency', header: 'Relationship Frequency', type: 'number', align: 'right' }
  ];

  rule2Cols: ColumnDef[] = [
    { field: 'AGENTNAME', header: 'AGENTNAME' },
    { field: 'unique_targets', header: 'Corporate Count', type: 'number', align: 'right' },
    { field: 'txn_count', header: 'Transaction Count', type: 'number', align: 'right' },
    { field: 'total_amt', header: 'Total Net Amount', type: 'amount', align: 'right' }
  ];

  rule3Cols: ColumnDef[] = [
    { field: 'AGENTNAME', header: 'AGENTNAME' },
    { field: 'unique_targets', header: 'Branch Name Count', type: 'number', align: 'right' },
    { field: 'txn_count', header: 'Transaction Count', type: 'number', align: 'right' },
    { field: 'total_amt', header: 'Total Net Amount', type: 'amount', align: 'right' }
  ];

  rule4Cols: ColumnDef[] = [
    { field: 'AGENTNAME', header: 'AGENTNAME' },
    { field: 'unique_targets', header: 'Visiting Country Count', type: 'number', align: 'right' },
    { field: 'txn_count', header: 'Transaction Count', type: 'number', align: 'right' },
    { field: 'total_amt', header: 'Total Net Amount', type: 'amount', align: 'right' }
  ];

  detailedCols: ColumnDef[] = [
    { field: 'TXNDATE', header: 'TXNDATE', type: 'date' },
    { field: 'AGENTCODE', header: 'AGENTCODE' },
    { field: 'AGENTNAME', header: 'AGENTNAME' },
    { field: 'CUSTOMERNAME', header: 'CUSTOMERNAME' },
    { field: 'PAXNAME', header: 'PAXNAME' },
    { field: 'LOCATION', header: 'LOCATION' },
    { field: 'INRAMOUNT', header: 'INRAMOUNT', type: 'amount', align: 'right' },
    { field: 'Equivalent USD Amount', header: 'Equivalent USD Amount ($)', type: 'usd', align: 'right' },
    { field: 'TxnPurpose', header: 'TxnPurpose' },
    { field: 'Segment', header: 'Segment' }
  ];

  constructor() {
    effect(() => {
      const df = this.dataService.filteredDf();
      if (df && df.length > 0) {
        this.fetchData();
      }
    });
  }

  fetchData() {
    const df = this.dataService.filteredDf();
    this.http.post<any>(`${environment.apiBaseUrl}/api/pages/agent-analysis`, {
      filtered_df: df,
      agent_col: 'AGENTNAME',
      chart_metric: this.chartMetric,
      trend_agg: this.trendAgg,
      rule1_many_thresh: this.rule1ManyThresh,
      rule1_one_thresh: this.rule1OneThresh,
      rule2_thresh: this.rule2Thresh,
      rule3_thresh: this.rule3Thresh,
      rule4_thresh: this.rule4Thresh
    }).subscribe(res => {
      if (res) {
        const cleanTable = (tbl: any[], keyField: string) => {
          if (!tbl) return [];
          return tbl.filter(row => row[keyField] !== '**TOTAL**');
        };
        
        res.frequency_table = cleanTable(res.frequency_table, 'Category');
        res.trend_table = cleanTable(res.trend_table, 'Category');
        res.branch_table = cleanTable(res.branch_table, 'Category');
        res.country_table = cleanTable(res.country_table, 'Category');
        res.corp_table = cleanTable(res.corp_table, 'Category');
        res.benef_table = cleanTable(res.benef_table, 'Category');
        res.product_table = cleanTable(res.product_table, 'Category');
        res.purpose_table = cleanTable(res.purpose_table, 'Category');
        res.suspicious_many = cleanTable(res.suspicious_many, 'AGENTCODE');
        res.suspicious_one = cleanTable(res.suspicious_one, 'AGENTCODE');
      }
      this.agentData.set(res);
      this.generateCharts(res);
    });
  }

  onParamChange() {
    this.fetchData();
  }

  generateCharts(data: any) {
    const yCol = this.chartMetric === 'Count' ? 'Count' : 'INRAMOUNT';
    const numFmt = this.chartMetric === 'Count' ? ',.0f' : ',.3s';

    this.freqGraph = this.buildBarChart(data.frequency_table, 'Category', yCol, 'Agent Frequency (Top 20)', 'AGENTCODE', yCol, numFmt);
    this.trendGraph = this.buildLineChart(data.trend_table, 'Category', yCol, `Agent Trend (${this.trendAgg})`, 'Time', yCol);
    this.branchGraph = this.buildBarChart(data.branch_table, 'Category', yCol, 'Branch-wise Agent Analysis', 'Branch', yCol, numFmt);
    this.countryGraph = this.buildBarChart(data.country_table, 'Category', yCol, 'Visiting Country-wise Agent Analysis', 'CountryToTravel', yCol, numFmt);
    this.corpGraph = this.buildBarChart(data.corp_table, 'Category', yCol, 'Corporate-wise Agent Analysis', 'CUSTOMERNAME', yCol, numFmt);
    this.benefGraph = this.buildBarChart(data.benef_table, 'Category', yCol, 'Beneficiary-wise Agent Analysis', 'Beneficiary', yCol, numFmt);
    this.productGraph = this.buildBarChart(data.product_table, 'Category', yCol, 'Product Wise Agent Analysis', 'PRODUCT', yCol, numFmt);
    this.purposeGraph = this.buildBarChart(data.purpose_table, 'Category', yCol, 'Purpose Wise Agent Analysis', 'TxnPurpose', yCol, numFmt);
  }

  buildBarChart(tableData: any[], xField: string, yField: string, title: string, xAxisTitle: string, yAxisTitle: string, numFmt: string) {
    if (!tableData) return null;
    const chartData = tableData.filter(d => d[xField] !== '**TOTAL**').slice(0, 20);
    return {
      data: [{
        x: chartData.map(d => String(d[xField])),
        y: chartData.map(d => Number(d[yField])),
        type: 'bar',
        text: chartData.map(d => Number(d[yField])),
        textposition: 'outside',
        texttemplate: `%{text:${numFmt}}`,
        marker: { color: this.theme.colorway[0] }
      }],
      layout: {
        title: { text: title, font: this.theme.font },
        xaxis: { title: xAxisTitle, tickangle: -45, automargin: true },
        yaxis: { title: yAxisTitle, automargin: true },
        margin: { t: 50, r: 20, l: 80, b: 120 },
        height: 350,
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent'
      }
    };
  }

  buildLineChart(tableData: any[], xField: string, yField: string, title: string, xAxisTitle: string, yAxisTitle: string) {
    if (!tableData) return null;
    const chartData = tableData.filter(d => d[xField] !== '**TOTAL**');
    const yData = chartData.map(d => Number(d[yField]));
    return {
      data: [{
        x: chartData.map(d => String(d[xField])),
        y: yData,
        type: 'scatter',
        mode: 'lines+markers+text',
        text: yData.map(v => this.chartMetric === 'Count' ? v : this.formatAmt(v)),
        textposition: 'top center',
        line: { color: this.theme.colorway[0], width: 3, shape: 'spline' },
        fill: 'tozeroy',
        fillcolor: 'rgba(17, 17, 17, 0.1)',
        marker: { size: 6 }
      }],
      layout: {
        title: { text: title, font: this.theme.font },
        xaxis: { title: xAxisTitle, tickangle: -45, automargin: true },
        yaxis: { title: yAxisTitle, automargin: true },
        margin: { t: 50, r: 20, l: 80, b: 100 },
        height: 350,
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent'
      }
    };
  }

  formatAmt(val: number): string {
    if (val == null) return '0';
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)}Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)}L`;
    return `₹${val.toLocaleString()}`;
  }
}
