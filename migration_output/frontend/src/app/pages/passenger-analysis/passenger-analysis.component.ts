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
  selector: 'app-passenger-analysis',
  standalone: true,
  imports: [CommonModule, PlotlyViaWindowModule, HumanReadableAmountPipe, DecimalPipe, SharedTableComponent],
  templateUrl: './passenger-analysis.component.html',
  styleUrls: ['./passenger-analysis.component.scss']
})
export class PassengerAnalysisComponent {
  ruleACols: ColumnDef[] = [
    { field: 'PAXIDNO_CLEAN', header: 'PAX ID' },
    { field: 'PAXNAME', header: 'PAXNAME' },
    { field: 'EMAIL_CLEAN', header: 'Email ID' },
    { field: 'MOBILE_CLEAN', header: 'Mobile No' },
    { field: 'LOCATION', header: 'Branch' }
  ];

  ruleBCols: ColumnDef[] = [
    { field: 'PAXIDNO_CLEAN', header: 'PAX ID' },
    { field: 'PAXNAME', header: 'PAXNAME' },
    { field: 'EMAIL_CLEAN', header: 'Email ID' },
    { field: 'MOBILE_CLEAN', header: 'Mobile No' },
    { field: 'LOCATION', header: 'Branch' }
  ];

  ruleCCols: ColumnDef[] = [
    { field: 'PAXIDNO_CLEAN', header: 'PAX ID' },
    { field: 'PAXNAME', header: 'PAXNAME' },
    { field: 'EMAIL_CLEAN', header: 'Email ID' },
    { field: 'MOBILE_CLEAN', header: 'Mobile No' },
    { field: 'LOCATION', header: 'Branch' }
  ];

  missingKycCols: ColumnDef[] = [
    { field: 'PAXNAME', header: 'PAXNAME' },
    { field: 'PAXIDNO_CLEAN', header: 'PAX ID (Clean)' },
    { field: 'EMAIL_CLEAN', header: 'Email ID (Clean)' },
    { field: 'MOBILE_CLEAN', header: 'Mobile No (Clean)' },
    { field: 'LOCATION', header: 'Branch' }
  ];

  branchQualityCols: ColumnDef[] = [
    { field: 'LOCATION', header: 'LOCATION' },
    { field: 'Total_Records', header: 'Total Records', type: 'number', align: 'right' },
    { field: 'Invalid_ID', header: 'Invalid ID', type: 'number', align: 'right' },
    { field: 'Invalid_Mobile', header: 'Invalid Mobile', type: 'number', align: 'right' },
    { field: 'Invalid_Email', header: 'Invalid Email', type: 'number', align: 'right' },
    { field: 'Missing_KYC', header: 'Missing KYC', type: 'number', align: 'right' },
    { field: 'Total_Issues', header: 'Total Issues', type: 'number', align: 'right', isBold: true }
  ];

  detailedCols: ColumnDef[] = [
    { field: 'TXNDATE', header: 'TXNDATE', type: 'date' },
    { field: 'PAXNAME', header: 'PAXNAME' },
    { field: 'PAXIDNO', header: 'PAXIDNO' },
    { field: 'MOBILENO', header: 'MOBILENO' },
    { field: 'EMAILID', header: 'EMAILID' },
    { field: 'LOCATION', header: 'LOCATION' },
    { field: 'CUSTOMERNAME', header: 'CUSTOMERNAME' },
    { field: 'INRAMOUNT', header: 'INRAMOUNT', type: 'amount', align: 'right' },
    { field: 'Equivalent USD Amount', header: 'Equivalent USD Amount ($)', type: 'usd', align: 'right' },
    { field: 'TxnPurpose', header: 'TxnPurpose' }
  ];

  dataService = inject(DataService);
  private http = inject(HttpClient);

  paxData = signal<any>(null);
  theme = ENTERPRISE_THEME;

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
    this.http.post<any>(`${environment.apiBaseUrl}/api/pages/passenger-analysis`, {
      filtered_df: df
    }).subscribe(res => {
      this.paxData.set(res);
    });
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
