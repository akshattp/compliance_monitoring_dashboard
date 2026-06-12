import { environment } from '../../../environments/environment';
import { Component, effect, inject, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { DataService } from '../../core/services/data.service';
import { PlotlyViaWindowModule } from 'angular-plotly.js';
import { ENTERPRISE_THEME } from '../../shared/chart-theme.service';
import { HumanReadableAmountPipe } from '../../shared/pipes/human-readable-amount.pipe';

@Component({
  selector: 'app-fatf',
  standalone: true,
  imports: [CommonModule, PlotlyViaWindowModule, HumanReadableAmountPipe, DecimalPipe],
  templateUrl: './fatf.component.html',
  styleUrls: ['./fatf.component.scss']
})
export class FatfComponent {
  dataService = inject(DataService);
  private http = inject(HttpClient);

  fatfData = signal<any>(null);
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
    this.http.post<any>(`${environment.apiBaseUrl}/api/pages/fatf`, {
      filtered_df: df
    }).subscribe(res => {
      this.fatfData.set(res);
    });
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
