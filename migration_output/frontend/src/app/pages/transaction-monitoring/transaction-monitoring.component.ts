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
  selector: 'app-transaction-monitoring',
  standalone: true,
  imports: [
    CommonModule, 
    PlotlyViaWindowModule, 
    HumanReadableAmountPipe,
    DecimalPipe,
    FormsModule
  ],
  templateUrl: './transaction-monitoring.component.html',
  styleUrls: ['./transaction-monitoring.component.scss']
})
export class TransactionMonitoringComponent {
  dataService = inject(DataService);
  private http = inject(HttpClient);

  thresholdDays = signal<number>(1);
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
      threshold_days: this.thresholdDays()
    }).subscribe(res => {
      this.tmData.set(res);
    });
  }

  constructor() {
    effect(() => {
      const df = this.dataService.filteredDf();
      const threshold = this.thresholdDays();
      if (df && df.length > 0) {
        // Debounce slightly or just call
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
}
