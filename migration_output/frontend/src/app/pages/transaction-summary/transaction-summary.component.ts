import { Component, OnInit, inject, signal, effect, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PlotlyViaWindowModule } from 'angular-plotly.js';

import { TransactionSummaryService } from './transaction-summary.service';
import { DataService } from '../../core/services/data.service';

@Component({
  selector: 'app-transaction-summary',
  standalone: true,
  imports: [CommonModule, FormsModule, PlotlyViaWindowModule],
  providers: [TransactionSummaryService],
  templateUrl: './transaction-summary.component.html',
  styleUrl: './transaction-summary.component.scss'
})
export class TransactionSummaryComponent implements OnInit {
  private tsService = inject(TransactionSummaryService);
  public dataService = inject(DataService);

  kpis = signal<{ [key: string]: { count: number, amount: number } | undefined }>({});
  breakdown = signal<{ txn_by_type: any[], display_table: any[] }>({ txn_by_type: [], display_table: [] });
  purposeSummary = signal<any[]>([]);
  branchComposition = signal<{chart_df: any[], display_table: any[], total_count: number, total_amount: number, records_count: number}>({chart_df: [], display_table: [], total_count: 0, total_amount: 0, records_count: 0});
  productComposition = signal<{chart_df: any[], display_table: any[], total_count: number, total_amount: number, records_count: number}>({chart_df: [], display_table: [], total_count: 0, total_amount: 0, records_count: 0});
  segmentComposition = signal<{chart_df: any[], display_table: any[], total_count: number, total_amount: number, records_count: number}>({chart_df: [], display_table: [], total_count: 0, total_amount: 0, records_count: 0});

  getKpi(type: string) {
    return this.kpis()[type] || { count: 0, amount: 0 };
  }

  // Page specific controls
  globalMetric = signal<'Count' | 'Net Amount'>('Count');
  availableTxns = signal<string[]>([]);
  selectedTxns = signal<string[]>([]);

  // Charts
  typePieChart = signal<any>(null);
  branchChart = signal<any>(null);
  productChart = signal<any>(null);
  segmentChart = signal<any>(null);

  // Expandable Table States
  branchRecords = signal<any[]>([]);
  productRecords = signal<any[]>([]);
  segmentRecords = signal<any[]>([]);

  constructor() {
    effect(() => {
      const data = this.dataService.filteredDf();
      const metric = this.globalMetric();
      const selected = this.selectedTxns();
      if (data.length > 0) {
        this.fetchData();
        this.updateAvailableTxns(data);
      }
    }, { allowSignalWrites: true });
  }

  ngOnInit(): void {}

  fetchData() {
    const req = {
      filtered_df: this.dataService.filteredDf(),
      global_metric: this.globalMetric(),
      selected_txns: this.selectedTxns()
    };

    this.tsService.getData(req).subscribe(res => {
      this.kpis.set(res.kpis || {});
      this.breakdown.set(res.breakdown || { txn_by_type: [], display_table: [] });
      this.purposeSummary.set(res.purpose_summary || []);
      
      if (res.branch_composition) this.branchComposition.set(res.branch_composition);
      if (res.product_composition) this.productComposition.set(res.product_composition);
      if (res.segment_composition) this.segmentComposition.set(res.segment_composition);
      
      this.buildTypePieChart(res.breakdown?.txn_by_type || []);
      this.buildCompositionCharts();
    });
  }

  updateAvailableTxns(data: any[]) {
    const types = new Set<string>();
    data.forEach(d => {
      if (d['Txn Type'] && String(d['Txn Type']).trim() !== '') {
        types.add(String(d['Txn Type']));
      }
    });
    this.availableTxns.set(Array.from(types).sort());
  }

  toggleTxnSelection(txn: string) {
    const current = this.selectedTxns();
    if (current.includes(txn)) {
      this.selectedTxns.set(current.filter(t => t !== txn));
    } else {
      this.selectedTxns.set([...current, txn]);
    }
  }

  theme = {
    colorway: ['#111111', '#444444', '#777777', '#999999', '#bbbbbb'],
    font: { family: 'Inter, Segoe UI, sans-serif', color: '#111111', size: 13 },
    paper_bgcolor: '#ffffff',
    plot_bgcolor: '#ffffff',
    margin: { t: 40, b: 40, l: 150, r: 20 }
  };

  buildTypePieChart(txnByType: any[]) {
    if (!txnByType.length) return;
    const labels = txnByType.map(t => t['Txn Type']);
    const values = txnByType.map(t => t['Amount']);
    
    this.typePieChart.set({
      data: [{
        labels, values, type: 'pie', hole: 0.4,
        textinfo: 'percent+label', textposition: 'inside'
      }],
      layout: { ...this.theme, title: 'Transaction Amount by Type', showlegend: false, margin: { t: 40, b: 20, l: 20, r: 20 } }
    });
  }

  buildCompositionCharts() {
    const metric = this.globalMetric();
    this.branchChart.set(this.formatPlotlyBar(this.branchComposition().chart_df, 'Branch Name', 'Branch', metric));
    this.productChart.set(this.formatPlotlyBar(this.productComposition().chart_df, 'Product', 'Product', metric));
    this.segmentChart.set(this.formatPlotlyBar(this.segmentComposition().chart_df, 'Segments', 'Segment', metric));
  }

  formatPlotlyBar(chartDf: any[], groupCol: string, titlePrefix: string, metric: 'Count' | 'Net Amount') {
    if (!chartDf || !chartDf.length) return null;

    const uniqueGroups = Array.from(new Set(chartDf.map(r => r[groupCol] || 'Unknown')));
    const uniqueTxnTypes = Array.from(new Set(chartDf.map(r => r['Txn Type'] || 'Unknown')));

    const y_col = metric === 'Count' ? 'Count' : 'Total_Amount';

    const traces = uniqueTxnTypes.map((txnType, idx) => {
      const typeData = chartDf.filter(r => r['Txn Type'] === txnType);
      const y = uniqueGroups;
      const x = uniqueGroups.map(g => {
        const row = typeData.find(r => r[groupCol] === g);
        return row ? row[y_col] : 0;
      });

      return {
        y, x, name: txnType, type: 'bar', orientation: 'h',
        marker: { color: this.theme.colorway[idx % this.theme.colorway.length] }
      };
    });

    return {
      data: traces,
      layout: {
        ...this.theme,
        title: `${titlePrefix}-wise Transaction Type`,
        barmode: 'stack',
        height: Math.max(400, uniqueGroups.length * 35 + 100),
        xaxis: { title: metric }
      }
    };
  }

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

  // Scroll limit state for the multiple tables
  scrollLimitBranch = signal<number>(50);
  scrollLimitProduct = signal<number>(50);
  scrollLimitSegment = signal<number>(50);

  onTableScroll(event: any, type: 'branch' | 'product' | 'segment') {
    const el = event.target;
    if (el.scrollHeight - el.scrollTop <= el.clientHeight + 150) {
      if (type === 'branch') this.scrollLimitBranch.update(l => l + 50);
      else if (type === 'product') this.scrollLimitProduct.update(l => l + 50);
      else if (type === 'segment') this.scrollLimitSegment.update(l => l + 50);
    }
  }
}
