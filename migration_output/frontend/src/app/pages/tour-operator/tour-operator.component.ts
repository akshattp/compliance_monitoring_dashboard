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

@Component({
  selector: 'app-tour-operator',
  standalone: true,
  imports: [
    CommonModule, 
    PlotlyViaWindowModule, 
    AgGridAngular, 
    KpiCardComponent, 
    PageHeaderComponent,
    HumanReadableAmountPipe,
    DecimalPipe
  ],
  templateUrl: './tour-operator.component.html',
  styleUrls: ['./tour-operator.component.scss']
})
export class TourOperatorComponent {
  dataService = inject(DataService);
  private http = inject(HttpClient);

  kpis = signal<any>({});
  intelligence = signal<any>({});
  purposeMix = signal<any[]>([]);
  branchComposition = signal<{ branch_data: any[], display_table: any[] }>({ branch_data: [], display_table: [] });
  corporateComposition = signal<{ corp_data: any[], display_table: any[], total_count: number, total_amt: number }>({ corp_data: [], display_table: [], total_count: 0, total_amt: 0 });
  countryCombo = signal<any[]>([]);
  observation = signal<string>('');

  theme = ENTERPRISE_THEME;



  purposeMixChart = computed(() => {
    const data = this.purposeMix();
    if (!data || data.length === 0) return null;
    return {
      data: [{
        type: 'pie',
        labels: data.map((d: any) => d.Purpose),
        values: data.map((d: any) => d.Total_Amount),
        hole: 0,
        textinfo: 'percent+label',
        marker: {
          colors: data.map((d: any) => d.Purpose.includes('MICE') ? '#888888' : '#111111')
        }
      }],
      layout: {
        ...this.theme,
        title: 'Tour Operator Purpose Mix',
        margin: { l: 15, r: 15, t: 45, b: 80 }
      }
    };
  });

  branchChart = computed(() => {
    const bd = this.branchComposition().branch_data;
    if (!bd || bd.length === 0) return null;
    
    // Group by Purpose Type
    const miceData = bd.filter((d: any) => d['Purpose Type'].includes('MICE'));
    const remitData = bd.filter((d: any) => !d['Purpose Type'].includes('MICE'));

    return {
      data: [
        {
          type: 'bar',
          orientation: 'h',
          name: 'MICE',
          y: miceData.map((d: any) => d['Branch Name']),
          x: miceData.map((d: any) => d.Count),
          marker: { color: '#888888' }
        },
        {
          type: 'bar',
          orientation: 'h',
          name: 'REMITTANCE',
          y: remitData.map((d: any) => d['Branch Name']),
          x: remitData.map((d: any) => d.Count),
          marker: { color: '#111111' }
        }
      ],
      layout: {
        ...this.theme,
        title: 'Top Tour Operator Branches',
        barmode: 'stack',
        margin: { l: 150, r: 15, t: 60, b: 15 }
      }
    };
  });

  corpChart = computed(() => {
    const cd = this.corporateComposition().corp_data;
    if (!cd || cd.length === 0) return null;
    
    const miceData = cd.filter((d: any) => d['Purpose Type'].includes('MICE'));
    const remitData = cd.filter((d: any) => !d['Purpose Type'].includes('MICE'));

    return {
      data: [
        {
          type: 'bar',
          orientation: 'h',
          name: 'MICE',
          y: miceData.map((d: any) => d.Corporate),
          x: miceData.map((d: any) => d.Count),
          marker: { color: '#888888' }
        },
        {
          type: 'bar',
          orientation: 'h',
          name: 'REMITTANCE',
          y: remitData.map((d: any) => d.Corporate),
          x: remitData.map((d: any) => d.Count),
          marker: { color: '#111111' }
        }
      ],
      layout: {
        ...this.theme,
        title: 'Top Tour Operator Corporates',
        barmode: 'stack',
        margin: { l: 150, r: 15, t: 60, b: 15 }
      }
    };
  });

  countryChart = computed(() => {
    const cd = this.countryCombo();
    if (!cd || cd.length === 0) return null;

    return {
      data: [
        {
          type: 'scatter',
          mode: 'lines+markers',
          name: 'MICE (Count)',
          x: cd.map(d => d['Visiting Country']),
          y: cd.map(d => d['MICE_Count']),
          line: { color: '#636EFA', width: 3 }
        },
        {
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Remittance (Count)',
          x: cd.map(d => d['Visiting Country']),
          y: cd.map(d => d['Remit_Count']),
          line: { color: '#EF553B', width: 3 }
        },
        {
          type: 'bar',
          name: 'Total Amount (USD)',
          x: cd.map(d => d['Visiting Country']),
          y: cd.map(d => d['Total_Amount']),
          yaxis: 'y2',
          marker: { color: '#00CC96', opacity: 0.6 }
        }
      ],
      layout: {
        ...this.theme,
        title: 'Country Operator: Remittance Count & Amount',
        yaxis: { title: 'Transaction Count' },
        yaxis2: { title: 'Amount (USD)', overlaying: 'y', side: 'right' },
        margin: { l: 15, r: 60, t: 60, b: 80 }
      }
    };
  });

  constructor() {
    effect(() => {
      const df = this.dataService.filteredDf();
      // Only fetch if we have data, but remember that tour operator data might be a subset.
      // We will let the backend filter if necessary, but ideally we send the df.
      if (df && df.length > 0) {
        this.fetchData(df);
      }
    });
  }

  fetchData(df: any[]) {
    this.http.post<any>(`${environment.apiBaseUrl}/api/pages/tour-operator`, { filtered_df: df })
      .subscribe(res => {
        this.kpis.set(res.kpis);
        this.intelligence.set(res.intelligence);
        this.purposeMix.set(res.purpose_mix);
        this.branchComposition.set(res.branch_composition);
        this.corporateComposition.set(res.corporate_composition);
        this.countryCombo.set(res.country_combo);
        this.observation.set(res.observation);
      });
  }
}
