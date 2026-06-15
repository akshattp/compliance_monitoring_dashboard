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
  selector: 'app-high-risk-corporate',
  standalone: true,
  imports: [
    CommonModule, 
    PlotlyViaWindowModule, 
    HumanReadableAmountPipe,
    DecimalPipe,
    FormsModule,
    SharedTableComponent
  ],
  templateUrl: './high-risk-corporate.component.html',
  styleUrls: ['./high-risk-corporate.component.scss']
})
export class HighRiskCorporateComponent {
  prodCols: ColumnDef[] = [
    { field: 'PRODUCT', header: 'PRODUCT' },
    { field: 'Count', header: 'Count', type: 'number', align: 'right' },
    { field: 'Count %', header: 'Count %', type: 'number', format: '1.2-2', align: 'right' },
    { field: 'INRAMOUNT', header: 'Net Amount', type: 'amount', align: 'right' },
    { field: 'Net Amount %', header: 'Net Amount %', type: 'number', format: '1.2-2', align: 'right' }
  ];

  txCols: ColumnDef[] = [
    { field: 'TXNDATE', header: 'TXNDATE', type: 'date' },
    { field: 'CUSTOMERNAME', header: 'CUSTOMERNAME' },
    { field: 'PAXNAME', header: 'PAXNAME' },
    { field: 'PAXIDNO', header: 'PAXIDNO' },
    { field: 'LOCATION', header: 'LOCATION' },
    { field: 'Segment', header: 'Segment' },
    { field: 'INRAMOUNT', header: 'INRAMOUNT', type: 'amount', align: 'right' },
    { field: 'Equivalent USD Amount', header: 'Equivalent USD Amount ($)', type: 'usd', align: 'right' },
    { field: 'Risk Classification', header: 'Risk Classification' },
    { field: 'CountryToTravel', header: 'CountryToTravel' }
  ];
  dataService = inject(DataService);
  private http = inject(HttpClient);

  pmFile = signal<File | null>(null);
  enrichedDf = signal<any[]>([]);

  kpis = signal<any>({});
  riskDistribution = signal<any[]>([]);
  topCorporates = signal<any[]>([]);
  branchExposure = signal<any[]>([]);
  countryExposure = signal<any[]>([]);
  productExposure = signal<{ product_data: any[], display_prod_table: any[] }>({ product_data: [], display_prod_table: [] });
  trendExposure = signal<any[]>([]);
  transactionsTable = signal<any[]>([]);

  trendAgg = signal<'DAILY' | 'WEEKLY'>('DAILY');
  chartMetric = signal<'COUNT' | 'NET AMOUNT'>('COUNT');

  theme = ENTERPRISE_THEME;
  riskColors: any = { 'High Risk': '#ef553b', 'Medium Risk': '#ffa15a', 'Low Risk': '#00cc96', 'Unknown Risk': '#636363' };

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

  scrollLimitProd = signal<number>(50);
  scrollLimitTx = signal<number>(50);

  onTableScroll(event: any, type: 'prod' | 'tx') {
    const el = event.target;
    if (el.scrollHeight - el.scrollTop <= el.clientHeight + 150) {
      if (type === 'prod') this.scrollLimitProd.update(l => l + 50);
      else if (type === 'tx') this.scrollLimitTx.update(l => l + 50);
    }
  }

  onFileChange(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.pmFile.set(file);
    }
  }

  enrichData() {
    const file = this.pmFile();
    if (!file) {
      alert('Please upload Party Master CSV first.');
      return;
    }
    this.dataService.uploadPartyMaster(file);
  }

  fetchCharts() {
    const edf = this.dataService.filteredDf();
    if (!edf || edf.length === 0) return;

    this.http.post<any>(`${environment.apiBaseUrl}/api/pages/high-risk-corporate`, {
      enriched_df: edf,
      trend_agg: this.trendAgg(),
      target_metric: this.chartMetric()
    }).subscribe(res => {
      this.kpis.set(res.kpis);
      this.riskDistribution.set(res.risk_distribution);
      this.topCorporates.set(res.top_corporates);
      this.branchExposure.set(res.branch_exposure);
      this.countryExposure.set(res.country_exposure);
      this.productExposure.set(res.product_exposure);
      this.trendExposure.set(res.trend_exposure);
      this.transactionsTable.set(res.transactions_table);
    });
  }

  // Refetch when trend changes or data changes
  constructor() {
    effect(() => {
      const agg = this.trendAgg();
      const df = this.dataService.filteredDf();
      if (df.length > 0) {
        this.fetchCharts();
      }
    });
  }

  // Charts
  distChart = computed(() => {
    const data = this.riskDistribution();
    if (!data || data.length === 0) return null;
    const yKey = this.chartMetric() === 'COUNT' ? 'Transaction_Count' : 'Net_Amt';
    return {
      data: [{ type: 'bar', x: data.map(d => d['Risk Classification']), y: data.map(d => d[yKey]), marker: { color: data.map(d => this.riskColors[d['Risk Classification']] || '#636363') } }],
      layout: { ...this.theme, title: 'Risk Category Overview', margin: { l: 80, r: 20, t: 50, b: 100 }, xaxis: { automargin: true, tickangle: -45 } }
    };
  });

  corpChart = computed(() => {
    const data = this.topCorporates();
    if (!data || data.length === 0) return null;
    const yKey = this.chartMetric() === 'COUNT' ? 'Transaction_Count' : 'Net_Amt';
    return {
      data: [{ type: 'bar', x: data.map(d => d['Corporate_Code']), y: data.map(d => d[yKey]), marker: { color: '#111111' } }],
      layout: { ...this.theme, title: 'Top Corporates', margin: { l: 80, r: 20, t: 50, b: 100 }, xaxis: { automargin: true, tickangle: -45 } }
    };
  });

  branchChart = computed(() => {
    const data = this.branchExposure().slice(0, 30);
    if (!data || data.length === 0) return null;
    const yKey = this.chartMetric() === 'COUNT' ? 'Transaction_Count' : 'Net_Amt';
    
    const traces = ['High Risk', 'Medium Risk', 'Low Risk', 'Unknown Risk'].map(risk => {
      const filtered = data.filter(d => d['Risk Classification'] === risk);
      return {
        type: 'bar', name: risk,
        x: filtered.map(d => d['LOCATION']),
        y: filtered.map(d => d[yKey]),
        marker: { color: this.riskColors[risk] }
      };
    });

    return {
      data: traces,
      layout: { ...this.theme, title: 'Branch Exposure Profile', barmode: 'stack', margin: { l: 80, r: 20, t: 50, b: 120 }, xaxis: { automargin: true, tickangle: -45 } }
    };
  });

  countryChart = computed(() => {
    const data = this.countryExposure().slice(0, 30);
    if (!data || data.length === 0) return null;
    const yKey = this.chartMetric() === 'COUNT' ? 'Transaction_Count' : 'Net_Amt';
    
    const traces = ['High Risk', 'Medium Risk', 'Low Risk', 'Unknown Risk'].map(risk => {
      const filtered = data.filter(d => d['Risk Classification'] === risk);
      return {
        type: 'bar', name: risk,
        x: filtered.map(d => d['CountryToTravel']),
        y: filtered.map(d => d[yKey]),
        marker: { color: this.riskColors[risk] }
      };
    });

    return {
      data: traces,
      layout: { ...this.theme, title: 'Country Exposure Profile', barmode: 'stack', margin: { l: 80, r: 20, t: 50, b: 120 }, xaxis: { automargin: true, tickangle: -45 } }
    };
  });

  prodChart = computed(() => {
    const data = this.productExposure().product_data.slice(0, 30);
    if (!data || data.length === 0) return null;
    const yKey = this.chartMetric() === 'COUNT' ? 'Transaction_Count' : 'Net_Amt';
    
    const traces = ['High Risk', 'Medium Risk', 'Low Risk', 'Unknown Risk'].map(risk => {
      const filtered = data.filter((d: any) => d['Risk Classification'] === risk);
      return {
        type: 'bar', name: risk,
        x: filtered.map((d: any) => d['PRODUCT']),
        y: filtered.map((d: any) => d[yKey]),
        marker: { color: this.riskColors[risk] }
      };
    });

    return {
      data: traces,
      layout: { ...this.theme, title: 'Product Exposure Profile', barmode: 'stack', margin: { l: 80, r: 20, t: 50, b: 120 }, xaxis: { automargin: true, tickangle: -45 } }
    };
  });

  trendChartObj = computed(() => {
    const data = this.trendExposure();
    if (!data || data.length === 0) return null;
    const yKey = this.chartMetric() === 'COUNT' ? 'Transaction_Count' : 'Net_Amt';
    
    const traces = ['High Risk', 'Medium Risk', 'Low Risk', 'Unknown Risk'].map(risk => {
      const filtered = data.filter(d => d['Risk Classification'] === risk);
      const yData = filtered.map(d => d[yKey]);
      return {
        type: 'scatter', mode: 'lines+markers+text', name: risk,
        x: filtered.map(d => d['Time']),
        y: yData,
        text: yData.map(v => this.chartMetric() === 'COUNT' ? v : this.formatAmt(v)),
        textposition: 'top center',
        line: { color: this.riskColors[risk], shape: 'spline' },
        fill: 'tozeroy'
      };
    });

    return {
      data: traces,
      layout: { ...this.theme, title: `Risk Trend (${this.trendAgg()})`, margin: { l: 80, r: 20, t: 50, b: 100 }, xaxis: { automargin: true, tickangle: -45 } }
    };
  });

}
