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

@Component({
  selector: 'app-retail-high-value',
  standalone: true,
  imports: [
    CommonModule, 
    PlotlyViaWindowModule, 
    HumanReadableAmountPipe,
    DecimalPipe,
    FormsModule
  ],
  templateUrl: './retail-high-value.component.html',
  styleUrls: ['./retail-high-value.component.scss']
})
export class RetailHighValueComponent {
  dataService = inject(DataService);
  private http = inject(HttpClient);

  kpis = signal<any>({});
  branchData = signal<any[]>([]);
  corporateData = signal<any[]>([]);
  customerData = signal<any[]>([]);
  productData = signal<any[]>([]);
  currencyData = signal<any[]>([]);
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
      layout: { ...this.theme, title: 'Risk Level Distribution (USD Exposure)', margin: { l: 15, r: 15, t: 45, b: 15 } }
    };
  });

  segmentRiskChart = computed(() => {
    const data = this.segmentDistribution();
    if (!data || data.length === 0) return null;

    const high = data.filter(d => d.Retail_Risk_Level === 'HIGH');
    const med = data.filter(d => d.Retail_Risk_Level === 'MEDIUM');
    const low = data.filter(d => d.Retail_Risk_Level === 'LOW');

    const getX = (arr: any[]) => arr.map(d => d.Segments);
    const getY = (arr: any[]) => arr.map(d => d.Count);

    return {
      data: [
        { type: 'bar', name: 'HIGH', x: getX(high), y: getY(high), marker: { color: this.riskColors['HIGH'] } },
        { type: 'bar', name: 'MEDIUM', x: getX(med), y: getY(med), marker: { color: this.riskColors['MEDIUM'] } },
        { type: 'bar', name: 'LOW', x: getX(low), y: getY(low), marker: { color: this.riskColors['LOW'] } }
      ],
      layout: { ...this.theme, title: 'Segment Level Risk Distribution', barmode: 'stack', margin: { l: 15, r: 15, t: 45, b: 15 } }
    };
  });

  branchExposureChart = computed(() => {
    const data = this.branchData().slice(0, 15);
    if (!data || data.length === 0) return null;
    return {
      data: [{ type: 'bar', orientation: 'h', y: data.map(d => d['Branch Name']), x: data.map(d => d.Total_USD), marker: { color: '#111111' } }],
      layout: { ...this.theme, title: 'Top Branches by High-Value USD Exposure', margin: { l: 150, r: 15, t: 45, b: 15 } }
    };
  });

  corpExposureChart = computed(() => {
    const data = this.corporateData().slice(0, 15);
    if (!data || data.length === 0) return null;
    return {
      data: [{ type: 'bar', x: data.map(d => d.Corporate), y: data.map(d => d.Total_USD), marker: { color: '#444444' } }],
      layout: { ...this.theme, title: 'Top Corporates by High-Value USD Exposure', margin: { l: 15, r: 15, t: 45, b: 80 } }
    };
  });

  trendChart = computed(() => {
    const data = this.trendTime() === 'DAILY' ? this.trendDataDaily() : this.trendDataWeekly();
    if (!data || data.length === 0) return null;
    
    const yKey = this.trendMetric() === 'COUNT' ? 'Count' : 'Net_Amount';
    
    return {
      data: [{ type: 'scatter', mode: 'lines+markers', x: data.map(d => d.Date || d.Week), y: data.map(d => d[yKey]), line: { color: '#111111' } }],
      layout: { ...this.theme, title: `Transaction Trend (${this.trendTime()} | ${this.trendMetric()})`, margin: { l: 40, r: 15, t: 45, b: 40 } }
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
        this.observations.set(res.observations);
        this.transactionTable.set(res.transaction_table);
        
        this.trendDataDaily.set(res.trend_data_daily);
        this.trendDataWeekly.set(res.trend_data_weekly);
        this.riskDistribution.set(res.risk_distribution);
        this.segmentDistribution.set(res.segment_distribution);
      });
  }
}
