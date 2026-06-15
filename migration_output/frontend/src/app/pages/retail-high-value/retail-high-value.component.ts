import { environment } from '../../../environments/environment';
import { Component, computed, effect, inject, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { DataService } from '../../core/services/data.service';
import { HttpClient } from '@angular/common/http';
import { PlotlyViaWindowModule } from 'angular-plotly.js';
import { AgGridAngular } from 'ag-grid-angular';
import { KpiCardComponent } from '../../shared/components/kpi-card/kpi-card.component';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { HumanReadableAmountPipe } from '../../shared/pipes/human-readable-amount.pipe';
import { ENTERPRISE_THEME } from '../../shared/chart-theme.service';
import { FormsModule } from '@angular/forms';
import { SharedTableComponent, ColumnDef } from '../../shared/components/shared-table/shared-table.component';

@Component({
  selector: 'app-retail-high-value',
  standalone: true,
  imports: [
    CommonModule, 
    PlotlyViaWindowModule, 
    HumanReadableAmountPipe,
    DecimalPipe,
    FormsModule,
    SharedTableComponent
  ],
  templateUrl: './retail-high-value.component.html',
  styleUrls: ['./retail-high-value.component.scss']
})
export class RetailHighValueComponent {
  branchCols: ColumnDef[] = [
    { field: 'LOCATION', header: 'LOCATION' },
    { field: 'Count', header: 'Count', type: 'number', align: 'right' },
    { field: 'Count %', header: 'Count %', type: 'number', format: '1.2-2', align: 'right' },
    { field: 'Total_USD', header: 'Equivalent USD Amount ($)', type: 'usd', align: 'right' },
    { field: 'Net Amount %', header: 'Net Amount %', type: 'number', format: '1.2-2', align: 'right' }
  ];

  corpCols: ColumnDef[] = [
    { field: 'CUSTOMERNAME', header: 'CUSTOMERNAME' },
    { field: 'Count', header: 'Count', type: 'number', align: 'right' },
    { field: 'Count %', header: 'Count %', type: 'number', format: '1.2-2', align: 'right' },
    { field: 'Total_USD', header: 'Equivalent USD Amount ($)', type: 'usd', align: 'right' },
    { field: 'Net Amount %', header: 'Net Amount %', type: 'number', format: '1.2-2', align: 'right' }
  ];

  detailedCols: ColumnDef[] = [
    { field: 'TXNDATE', header: 'TXNDATE', type: 'date' },
    { field: 'PAXNAME', header: 'PAXNAME' },
    { field: 'PAXIDNO', header: 'PAXIDNO' },
    { field: 'CUSTOMERNAME', header: 'CUSTOMERNAME' },
    { field: 'LOCATION', header: 'LOCATION' },
    { field: 'CURRENCY', header: 'CURRENCY' },
    { field: 'INRAMOUNT', header: 'INRAMOUNT', type: 'amount', align: 'right' },
    { field: 'Equivalent USD Amount', header: 'Equivalent USD Amount ($)', type: 'usd', align: 'right' },
    { field: 'Retail_Risk_Level', header: 'Retail Risk Level' },
    { field: 'TxnPurpose', header: 'TxnPurpose' }
  ];
  dataService = inject(DataService);
  private http = inject(HttpClient);

  kpis = signal<any>({});
  branchData = signal<any[]>([]);
  corporateData = signal<any[]>([]);
  customerData = signal<any[]>([]);
  productData = signal<any[]>([]);
  currencyData = signal<any[]>([]);
  countryData = signal<any[]>([]);
  observations = signal<string>('');
  transactionTable = signal<any[]>([]);
  
  trendDataDaily = signal<any[]>([]);
  trendDataWeekly = signal<any[]>([]);
  riskDistribution = signal<any[]>([]);
  segmentDistribution = signal<any[]>([]);

  trendTime = signal<'DAILY' | 'WEEKLY'>('DAILY');
  trendMetric = signal<'COUNT' | 'NET AMOUNT'>('COUNT');

  theme = ENTERPRISE_THEME;

  formatAmt(val: number): string {
    if (val == null) return '0';
    if (val >= 10000000) return `$${(val / 1000000).toFixed(2)}M`;
    if (val >= 100000) return `$${(val / 1000).toFixed(2)}K`;
    return `$${val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  getParsedObservations(): string {
    const text = this.observations() || '';
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
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

  scrollLimitBranch = signal<number>(50);
  scrollLimitCorp = signal<number>(50);
  scrollLimitProd = signal<number>(50);
  scrollLimitTx = signal<number>(50);

  onTableScroll(event: any, type: 'branch' | 'corp' | 'prod' | 'tx') {
    const el = event.target;
    if (el.scrollHeight - el.scrollTop <= el.clientHeight + 150) {
      if (type === 'branch') this.scrollLimitBranch.update(l => l + 50);
      else if (type === 'corp') this.scrollLimitCorp.update(l => l + 50);
      else if (type === 'prod') this.scrollLimitProd.update(l => l + 50);
      else if (type === 'tx') this.scrollLimitTx.update(l => l + 50);
    }
  }

  riskColors: any = { 'HIGH': '#ef553b', 'MEDIUM': '#ffa15a', 'LOW': '#00cc96', 'UNKNOWN': '#636363' };

  riskDistChart = computed(() => {
    const data = this.riskDistribution();
    if (!data || data.length === 0) return null;
    return {
      data: [{
        type: 'pie',
        labels: data.map(d => d.Retail_Risk_Level),
        values: data.map(d => d.Net_Amount),
        hole: 0.4,
        textinfo: 'percent+label',
        marker: { colors: data.map(d => this.riskColors[d.Retail_Risk_Level] || '#636363') }
      }],
      layout: { ...this.theme, title: 'Risk Level Distribution (USD Exposure)', showlegend: true, legend: { orientation: 'h', x: 0, y: -0.2, font: { size: 10 } }, margin: { l: 40, r: 40, t: 50, b: 80 } }
    };
  });

  segmentRiskChart = computed(() => {
    const data = this.segmentDistribution();
    if (!data || data.length === 0) return null;

    const high = data.filter(d => d.Retail_Risk_Level === 'HIGH');
    const med = data.filter(d => d.Retail_Risk_Level === 'MEDIUM');
    const low = data.filter(d => d.Retail_Risk_Level === 'LOW');

    const getX = (arr: any[]) => arr.map(d => d.Segment);
    const getY = (arr: any[]) => arr.map(d => d.Count);

    return {
      data: [
        { type: 'bar', name: 'HIGH', x: getX(high), y: getY(high), marker: { color: this.riskColors['HIGH'] } },
        { type: 'bar', name: 'MEDIUM', x: getX(med), y: getY(med), marker: { color: this.riskColors['MEDIUM'] } },
        { type: 'bar', name: 'LOW', x: getX(low), y: getY(low), marker: { color: this.riskColors['LOW'] } }
      ],
      layout: { ...this.theme, title: 'Segment Level Risk Distribution', barmode: 'stack', showlegend: true, legend: { orientation: 'h', x: 0, y: -0.2, font: { size: 10 } }, margin: { l: 60, r: 20, t: 50, b: 120 }, xaxis: { automargin: true, tickangle: -45 } }
    };
  });

  branchExposureChart = computed(() => {
    const data = this.branchData().slice(0, 15);
    if (!data || data.length === 0) return null;
    return {
      data: [{ type: 'bar', orientation: 'h', y: data.map(d => d['LOCATION']), x: data.map(d => d.Total_USD), marker: { color: '#111111' } }],
      layout: { ...this.theme, title: 'Top Branches by High-Value USD Exposure', margin: { l: 180, r: 20, t: 50, b: 60 }, yaxis: { automargin: true } }
    };
  });

  corpExposureChart = computed(() => {
    const data = this.corporateData().slice(0, 15);
    if (!data || data.length === 0) return null;
    return {
      data: [{ type: 'bar', x: data.map(d => d.CUSTOMERNAME), y: data.map(d => d.Total_USD), marker: { color: '#444444' } }],
      layout: { ...this.theme, title: 'Top Corporates by High-Value USD Exposure', margin: { l: 80, r: 20, t: 50, b: 120 }, xaxis: { automargin: true, tickangle: -45 } }
    };
  });

  countryExposureChart = computed(() => {
    const data = this.countryData();
    if (!data || data.length === 0) return null;

    return {
      data: [
        {
          type: 'bar',
          name: 'USD Exposure Amount',
          x: data.map(d => d.CountryToTravel),
          y: data.map(d => d.Total_USD),
          marker: { color: '#111111', opacity: 0.8 }
        },
        {
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Transaction Count',
          x: data.map(d => d.CountryToTravel),
          y: data.map(d => d.Count),
          yaxis: 'y2',
          line: { color: '#ef553b', width: 3 }
        }
      ],
      layout: {
        ...this.theme,
        title: 'CountryToTravel High Risk Exposure',
        xaxis: { title: 'Country To Travel', tickangle: -45, automargin: true },
        yaxis: { title: 'Total Exposure Amount (USD)', side: 'left' },
        yaxis2: { title: 'Transaction Count', overlaying: 'y', side: 'right', showgrid: false },
        margin: { l: 80, r: 80, t: 60, b: 120 },
        legend: { orientation: 'h', y: -0.2 }
      }
    };
  });


  trendChart = computed(() => {
    const data = this.trendTime() === 'DAILY' ? this.trendDataDaily() : this.trendDataWeekly();
    if (!data || data.length === 0) return null;
    
    const yKey = this.trendMetric() === 'COUNT' ? 'Count' : 'Net_Amount';
    const yData = data.map(d => d[yKey]);
    
    return {
      data: [{ 
        type: 'scatter', 
        mode: 'lines+markers+text', 
        x: data.map(d => d.TXNDATE || d.Week), 
        y: yData, 
        text: yData.map(v => this.trendMetric() === 'COUNT' ? v : this.formatAmt(v)),
        textposition: 'top center',
        line: { color: '#111111', shape: 'spline' },
        fill: 'tozeroy',
        fillcolor: 'rgba(17, 17, 17, 0.1)'
      }],
      layout: { ...this.theme, title: `Transaction Trend (${this.trendTime()} | ${this.trendMetric()})`, margin: { l: 80, r: 20, t: 50, b: 80 }, xaxis: { automargin: true, tickangle: -45 } }
    };
  });


  constructor() {
    effect(() => {
      const df = this.dataService.filteredDf();
      if (df && df.length > 0) {
        this.fetchData(df);
      }
    });
  }

  fetchData(df: any[]) {
    this.http.post<any>(`${environment.apiBaseUrl}/api/pages/retail-high-value`, { filtered_df: df })
      .subscribe(res => {
        this.kpis.set(res.kpis);
        this.branchData.set(res.branch_data);
        this.corporateData.set(res.corporate_data);
        this.customerData.set(res.customer_data);
        this.productData.set(res.product_data);
        this.currencyData.set(res.currency_data);
        this.countryData.set(res.country_data);
        this.observations.set(res.observations);
        this.transactionTable.set(res.transaction_table);
        
        this.trendDataDaily.set(res.trend_data_daily);
        this.trendDataWeekly.set(res.trend_data_weekly);
        this.riskDistribution.set(res.risk_distribution);
        this.segmentDistribution.set(res.segment_distribution);
      });
  }
}
