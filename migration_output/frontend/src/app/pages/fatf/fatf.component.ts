import { environment } from '../../../environments/environment';
import { Component, effect, inject, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { DataService } from '../../core/services/data.service';
import { PlotlyViaWindowModule } from 'angular-plotly.js';
import { ENTERPRISE_THEME } from '../../shared/chart-theme.service';
import { HumanReadableAmountPipe } from '../../shared/pipes/human-readable-amount.pipe';
import { SharedTableComponent, ColumnDef } from '../../shared/components/shared-table/shared-table.component';

@Component({
  selector: 'app-fatf',
  standalone: true,
  imports: [CommonModule, PlotlyViaWindowModule, HumanReadableAmountPipe, DecimalPipe, SharedTableComponent],
  templateUrl: './fatf.component.html',
  styleUrls: ['./fatf.component.scss']
})
export class FatfComponent {
  flaggedCols: ColumnDef[] = [
    { field: 'TXNDATE', header: 'TXNDATE', type: 'date' },
    { field: 'CUSTOMERNAME', header: 'CUSTOMERNAME' },
    { field: 'PAXNAME', header: 'PAXNAME' },
    { field: 'LOCATION', header: 'LOCATION' },
    { field: 'CountryToTravel', header: 'CountryToTravel' },
    { field: 'Segment', header: 'Segment' },
    { field: 'OFAC_FATF', header: 'OFAC / FATF' },
    { field: 'INRAMOUNT', header: 'INRAMOUNT', type: 'amount', align: 'right' },
    { field: 'Equivalent USD Amount', header: 'Equivalent USD Amount ($)', type: 'usd', align: 'right' },
    { field: 'TxnPurpose', header: 'TxnPurpose' }
  ];

  branchCols: ColumnDef[] = [
    { field: 'LOCATION', header: 'LOCATION' },
    { field: 'Count', header: 'Txn Count', type: 'number', align: 'right' },
    { field: 'Net_Amount', header: 'Exposure Amount', type: 'amount', align: 'right' }
  ];

  countryCols: ColumnDef[] = [
    { field: 'CountryToTravel', header: 'CountryToTravel' },
    { field: 'Count', header: 'Txn Count', type: 'number', align: 'right' },
    { field: 'Net_Amount', header: 'Exposure Amount', type: 'amount', align: 'right' }
  ];

  purposeCols: ColumnDef[] = [
    { field: 'TxnPurpose', header: 'TxnPurpose' },
    { field: 'Count', header: 'Txn Count', type: 'number', align: 'right' },
    { field: 'Count %', header: 'Count %', type: 'number', format: '1.2-2', align: 'right' },
    { field: 'Net_Amount', header: 'Net Amount', type: 'amount', align: 'right' },
    { field: 'Net Amount %', header: 'Net Amount %', type: 'number', format: '1.2-2', align: 'right' }
  ];

  dataService = inject(DataService);
  private http = inject(HttpClient);

  fatfData = signal<any>(null);
  theme = ENTERPRISE_THEME;
  trendAgg = signal<'DAILY' | 'WEEKLY'>('DAILY');

  constructor() {
    effect(() => {
      const df = this.dataService.filteredDf();
      const agg = this.trendAgg();
      if (df && df.length > 0) {
        this.fetchData();
      }
    });
  }

  fetchData() {
    const df = this.dataService.filteredDf();
    this.http.post<any>(`${environment.apiBaseUrl}/api/pages/fatf`, {
      filtered_df: df,
      trend_agg: this.trendAgg()
    }).subscribe(res => {
      this.fatfData.set(res);
      this.buildCharts(res);
    });
  }

  branchSegChart: any = null;
  countrySegChart: any = null;
  purposeChart: any = null;
  trendChart: any = null;

  buildCharts(res: any) {
    if (!res) return;
    this.branchSegChart = this.buildGroupedBarChart(res.branch_seg_summary, 'LOCATION');
    this.countrySegChart = this.buildGroupedBarChart(res.country_seg_summary, 'CountryToTravel');
    this.purposeChart = this.buildBarChart(res.purpose_counts, 'TxnPurpose', 'Net_Amount', 'Flagged Exposure by Purpose');
    this.trendChart = this.buildLineChart(res.trend, 'Time', 'Net_Amount', 'Flagged Transaction Trend');
  }


  buildGroupedBarChart(data: any[], categoryKey: string) {
    if (!data || data.length === 0) return null;
    const segmentMap = new Map<string, {x: string[], y: number[]}>();
    const categories = Array.from(new Set(data.map(d => d[categoryKey]))).slice(0, 10);
    const filteredData = data.filter(d => categories.includes(d[categoryKey]));
    
    filteredData.forEach(row => {
      const seg = row['Segment'] || 'Unknown';
      if (!segmentMap.has(seg)) segmentMap.set(seg, {x: [], y: []});
      segmentMap.get(seg)!.x.push(row[categoryKey]);
      segmentMap.get(seg)!.y.push(row['Count']);
    });

    const traces: any[] = [];
    segmentMap.forEach((val, key) => {
      traces.push({ x: val.x, y: val.y, name: key, type: 'bar' });
    });

    return {
      data: traces,
      layout: {
        title: { text: `Count by ${categoryKey} & Segment`, font: { family: this.theme.font.family, color: this.theme.font.color, size: 16 } },
        barmode: 'group', colorway: this.theme.colorway,
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        margin: { l: 80, r: 20, t: 50, b: 120 },
        xaxis: { tickfont: { family: this.theme.font.family }, tickangle: -45, automargin: true },
        yaxis: { tickfont: { family: this.theme.font.family }, automargin: true },
        legend: { orientation: 'h', y: -0.2 }
      }
    };
  }

  buildBarChart(data: any[], xKey: string, yKey: string, title: string) {
    if (!data || data.length === 0) return null;
    return {
      data: [{ x: data.map(d => d[xKey]), y: data.map(d => d[yKey]), type: 'bar', marker: { color: this.theme.colorway[0] } }],
      layout: {
        title: { text: title, font: { family: this.theme.font.family, color: this.theme.font.color, size: 16 } },
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        margin: { l: 80, r: 20, t: 50, b: 120 },
        xaxis: { tickfont: { family: this.theme.font.family }, tickangle: -45, automargin: true },
        yaxis: { tickfont: { family: this.theme.font.family }, automargin: true }
      }
    };
  }

  buildLineChart(data: any[], xKey: string, yKey: string, title: string) {
    if (!data || data.length === 0) return null;
    const yData = data.map(d => d[yKey]);
    return {
      data: [{ 
        x: data.map(d => d[xKey]), 
        y: yData, 
        type: 'scatter', 
        mode: 'lines+markers+text', 
        text: yData.map(v => this.formatAmt(v)),
        textposition: 'top center',
        line: { color: this.theme.colorway[2], width: 3, shape: 'spline' },
        fill: 'tozeroy',
        fillcolor: 'rgba(17, 17, 17, 0.1)'
      }],
      layout: {
        title: { text: `${title} (${this.trendAgg()})`, font: { family: this.theme.font.family, color: this.theme.font.color, size: 16 } },
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        margin: { l: 80, r: 20, t: 50, b: 100 },
        xaxis: { tickfont: { family: this.theme.font.family }, tickangle: -45, automargin: true },
        yaxis: { tickfont: { family: this.theme.font.family }, automargin: true }
      }
    };
  }

  onOfacFileSelected(event: any) {
    const file: File = event.target.files[0];
    if (file) {
      this.dataService.uploadOfac(file);
    }
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

  formatAmt(val: number): string {
    if (val == null) return '0';
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)}Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)}L`;
    return `₹${val.toLocaleString()}`;
  }
}
