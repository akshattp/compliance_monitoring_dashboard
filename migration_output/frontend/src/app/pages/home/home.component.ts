import { Component, OnInit, inject, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PlotlyViaWindowModule } from 'angular-plotly.js';

import { HomeService } from './home.service';
import { HomeKpis, HomeTrends, HomeBreakdowns } from './home.models';
import { DataService } from '../../core/services/data.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, FormsModule, PlotlyViaWindowModule],
  providers: [HomeService],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss'
})
export default class HomeComponent implements OnInit {
  private homeService = inject(HomeService);
  public dataService = inject(DataService); // Made public for HTML access

  kpis = signal<HomeKpis | null>(null);
  trends = signal<HomeTrends | null>(null);
  breakdowns = signal<HomeBreakdowns | null>(null);

  trendAgg = signal<'DAILY' | 'WEEKLY'>('DAILY');
  breakdownAgg = signal<'NET AMOUNT' | 'COUNT'>('NET AMOUNT');
  purposeThreshold = signal<number>(1.0);

  // Chart configs
  trendAmountChart = signal<any>(null);
  trendCountChart = signal<any>(null);
  purposePieChart = signal<any>(null);
  productPieChart = signal<any>(null);
  branchBarChart = signal<any>(null);
  countryBarChart = signal<any>(null);

  // Table State
  tableSearchQuery = signal<string>('');
  filteredTableCount = signal<number>(0);
  
  tableHeaders = signal<string[]>([]);
  filteredTransactions = signal<any[]>([]);
  
  // Infinite scroll state
  visibleLimit = signal<number>(50);

  get scrollableTransactions() {
    return this.filteredTransactions().slice(0, this.visibleLimit());
  }

  onTableScroll(event: any) {
    const element = event.target;
    // If scrolled near bottom, load more
    if (element.scrollHeight - element.scrollTop <= element.clientHeight + 150) {
      if (this.visibleLimit() < this.filteredTransactions().length) {
        this.visibleLimit.update(l => l + 50);
      }
    }
  }

  topTransactionsRaw = signal<any[]>([]);

  constructor() {
    // Reactively fetch data when parameters change OR when dataService.filteredDf changes
    effect(() => {
      const data = this.dataService.filteredDf();
      // Only fetch if we have data or if in mock mode
      if (data.length > 0) {
        this.fetchData();
      }
    }, { allowSignalWrites: true });

    effect(() => {
      // Re-fetch when toggles change (simulating API call with new params)
      const tAgg = this.trendAgg();
      const bAgg = this.breakdownAgg();
      const pThresh = this.purposeThreshold();
      if (this.dataService.filteredDf().length > 0) {
        this.fetchData();
      }
    }, { allowSignalWrites: true });
    
    effect(() => {
      // Re-build table when search query changes or data arrives
      const q = this.tableSearchQuery().toLowerCase();
      const topT = this.topTransactionsRaw();
      if (topT && topT.length > 0) {
        if (this.tableHeaders().length === 0) {
          this.tableHeaders.set(Object.keys(topT[0]));
        }
        
        const filtered = topT.filter(row => {
          return Object.values(row).some(val => 
            String(val).toLowerCase().includes(q)
          );
        });
        
        this.filteredTableCount.set(filtered.length);
        this.filteredTransactions.set(filtered);
        this.visibleLimit.set(50); // Reset infinite scroll on search
      } else {
        this.filteredTableCount.set(0);
        this.filteredTransactions.set([]);
      }
    }, { allowSignalWrites: true });
  }

  ngOnInit(): void {
  }

  fetchData() {
    const req = {
      filtered_df: this.dataService.filteredDf(),
      trend_agg: this.trendAgg(),
      breakdown_metric_agg: this.breakdownAgg(),
      purpose_threshold: this.purposeThreshold()
    };

    this.homeService.getHomeData(req).subscribe(res => {
      this.kpis.set(res.kpis);
      this.trends.set(res.trends);
      this.breakdowns.set(res.breakdowns);

      // Use the raw data from dataService and sort it by Net Amt for the top transactions table
      const rawData = this.dataService.filteredDf();
      const sorted = [...rawData].sort((a: any, b: any) => {
        const valA = parseFloat(a['INRAMOUNT']) || 0;
        const valB = parseFloat(b['INRAMOUNT']) || 0;
        return valB - valA;
      });
      
      this.topTransactionsRaw.set(sorted);
      
      // Trigger effect by setting headers
      if (sorted.length > 0) {
        this.tableHeaders.set(Object.keys(sorted[0]));
      }

      this.buildCharts(res.trends, res.breakdowns);
    });
  }

  downloadCSV(data: any[], filename: string) {
    if (!data || data.length === 0) return;
    
    const headers = Object.keys(data[0]);
    const csvRows = [];
    
    // Header row
    csvRows.push(headers.join(','));
    
    // Data rows
    for (const row of data) {
      const values = headers.map(header => {
        let val = row[header];
        if (val === null || val === undefined) val = '';
        const strVal = String(val).replace(/"/g, '""'); // escape double quotes
        return `"${strVal}"`; // wrap in quotes to handle commas
      });
      csvRows.push(values.join(','));
    }
    
    const csvString = csvRows.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    
    URL.revokeObjectURL(url);
  }

  buildCharts(trends: HomeTrends, breakdowns: HomeBreakdowns) {
    const theme = {
      colorway: ['#111111', '#444444', '#777777', '#999999', '#bbbbbb'],
      font: { family: 'Inter, Segoe UI, sans-serif', color: '#111111', size: 13 },
      paper_bgcolor: '#ffffff',
      plot_bgcolor: '#ffffff'
    };

    if (trends && trends.agg_df) {
      const times = trends.agg_df.map(t => t.Time);
      const amounts = trends.agg_df.map(t => t.Transaction_Amount);
      const counts = trends.agg_df.map(t => t.Transaction_Count);
      const timeLabel = this.trendAgg() === 'DAILY' ? 'Daily' : 'Weekly';

      this.trendAmountChart.set({
        data: [{ 
          x: times, 
          y: amounts, 
          type: 'scatter', 
          mode: 'lines+markers+text', 
          text: amounts.map(a => this.formatAmt(a)),
          textposition: 'top center',
          line: { color: '#111111', shape: 'spline' }, 
          fill: 'tozeroy', 
          fillcolor: 'rgba(17, 17, 17, 0.1)' 
        }],
        layout: { ...theme, title: `${timeLabel} Transaction Amount Trend`, margin: { t: 40, b: 80, l: 60, r: 20 }, xaxis: { automargin: true, tickangle: -45 } }
      });

      this.trendCountChart.set({
        data: [{ 
          x: times, 
          y: counts, 
          type: 'scatter', 
          mode: 'lines+markers+text', 
          text: counts,
          textposition: 'top center',
          line: { color: '#111111', shape: 'spline' }, 
          fill: 'tozeroy', 
          fillcolor: 'rgba(17, 17, 17, 0.1)' 
        }],
        layout: { ...theme, title: `${timeLabel} Transaction Count Trend`, margin: { t: 40, b: 80, l: 60, r: 20 }, xaxis: { automargin: true, tickangle: -45 } }
      });
    }

    if (breakdowns) {
      const isCount = this.breakdownAgg() === 'COUNT';

      if (breakdowns.purpose_df && breakdowns.purpose_df.length) {
        const labels = breakdowns.purpose_df.map(d => d.TxnPurpose);
        const values = breakdowns.purpose_df.map(d => isCount ? d.Count : d['INRAMOUNT']);
        this.purposePieChart.set({
          data: [{ labels, values, type: 'pie', hole: 0.4, textinfo: 'percent', textposition: 'inside' }],
          layout: { ...theme, showlegend: true, legend: { orientation: 'h', x: 0, y: -0.2, font: { size: 10 } }, margin: { t: 40, b: 80, l: 20, r: 20 } }
        });
      }

      if (breakdowns.product_df && breakdowns.product_df.length) {
        const labels = breakdowns.product_df.map(d => d.PRODUCT);
        const values = breakdowns.product_df.map(d => isCount ? d.Count : d['INRAMOUNT']);
        this.productPieChart.set({
          data: [{ labels, values, type: 'pie', hole: 0.4, textinfo: 'percent', textposition: 'inside' }],
          layout: { ...theme, showlegend: true, legend: { orientation: 'h', x: 0, y: -0.2, font: { size: 10 } }, margin: { t: 40, b: 80, l: 20, r: 20 } }
        });
      }

      if (breakdowns.branch_df && breakdowns.branch_df.length) {
        const dfRev = [...breakdowns.branch_df].reverse();
        const y = dfRev.map(d => d['LOCATION'] || d.Branch);
        const x = dfRev.map(d => isCount ? d.Count : d['INRAMOUNT']);
        this.branchBarChart.set({
          data: [{ y, x, type: 'bar', orientation: 'h', marker: { color: '#111111' }, text: x.map(v => isCount ? v : this.formatAmt(v)), textposition: 'outside' }],
          layout: { ...theme, margin: { t: 20, l: 150, r: 80, b: 40 } }
        });
      }

      if (breakdowns.country_df && breakdowns.country_df.length) {
        const dfRev = [...breakdowns.country_df].reverse();
        const y = dfRev.map(d => d['CountryToTravel']);
        const x = dfRev.map(d => isCount ? d.Count : d['INRAMOUNT']);
        this.countryBarChart.set({
          data: [{ y, x, type: 'bar', orientation: 'h', marker: { color: '#111111' }, text: x.map(v => isCount ? v : this.formatAmt(v)), textposition: 'outside' }],
          layout: { ...theme, margin: { t: 20, l: 150, r: 80, b: 40 } }
        });
      }
    }
  }

  formatAmt(val: number): string {
    if (val == null) return '0';
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)}Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)}L`;
    return `₹${val.toLocaleString()}`;
  }
}
