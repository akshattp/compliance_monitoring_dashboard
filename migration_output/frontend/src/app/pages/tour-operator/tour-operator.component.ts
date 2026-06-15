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
import { SharedTableComponent, ColumnDef } from '../../shared/components/shared-table/shared-table.component';

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
    DecimalPipe,
    SharedTableComponent
  ],
  templateUrl: './tour-operator.component.html',
  styleUrls: ['./tour-operator.component.scss']
})
export class TourOperatorComponent {
  branchCols: ColumnDef[] = [
    { field: 'LOCATION', header: 'LOCATION' },
    { field: 'Count', header: 'Count', type: 'number', align: 'right' },
    { field: 'Count %', header: 'Count %', type: 'number', format: '1.2-2', align: 'right' },
    { field: 'INRAMOUNT', header: 'INRAMOUNT', type: 'amount', align: 'right' },
    { field: 'Net Amt %', header: 'Net Amt %', type: 'number', format: '1.2-2', align: 'right' }
  ];

  corpCols: ColumnDef[] = [
    { field: 'Operator', header: 'Operator' },
    { field: 'Count', header: 'Count', type: 'number', align: 'right' },
    { field: 'Count %', header: 'Count %', type: 'number', format: '1.2-2', align: 'right' },
    { field: 'INRAMOUNT', header: 'Net Amount', type: 'amount', align: 'right' },
    { field: 'Net Amount %', header: 'Net Amount %', type: 'number', format: '1.2-2', align: 'right' }
  ];

  detailedCols: ColumnDef[] = [
    { field: 'TXNDATE', header: 'TXNDATE', type: 'date' },
    { field: 'CUSTOMERNAME', header: 'CUSTOMERNAME' },
    { field: 'PAXNAME', header: 'PAXNAME' },
    { field: 'BENEFICIARY', header: 'BENEFICIARY' },
    { field: 'LOCATION', header: 'LOCATION' },
    { field: 'PRODUCT', header: 'PRODUCT' },
    { field: 'INRAMOUNT', header: 'INRAMOUNT', type: 'amount', align: 'right' },
    { field: 'Equivalent USD Amount', header: 'Equivalent USD Amount ($)', type: 'usd', align: 'right' },
    { field: 'TxnPurpose', header: 'TxnPurpose' }
  ];

  tourOperatorTxns = computed(() => {
    return this.dataService.filteredDf().filter((r: any) => String(r.Segment).toUpperCase() === 'TOUR OPERATOR');
  });

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
        labels: data.map((d: any) => d.TxnPurpose),
        values: data.map((d: any) => d.Total_Amount),
        hole: 0,
        textinfo: 'percent+label',
        marker: {
          colors: data.map((d: any) => d.TxnPurpose.includes('MICE') ? '#888888' : '#111111')
        }
      }],
      layout: {
        ...this.theme,
        title: 'Tour Operator Purpose Mix',
        showlegend: true,
        legend: { orientation: 'h', x: 0, y: -0.2, font: { size: 10 } },
        margin: { l: 20, r: 20, t: 45, b: 80 }
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
          y: miceData.map((d: any) => d['LOCATION']),
          x: miceData.map((d: any) => d.Count),
          marker: { color: '#888888' }
        },
        {
          type: 'bar',
          orientation: 'h',
          name: 'REMITTANCE',
          y: remitData.map((d: any) => d['LOCATION']),
          x: remitData.map((d: any) => d.Count),
          marker: { color: '#111111' }
        }
      ],
      layout: {
        ...this.theme,
        title: 'Top Tour Operator Branches',
        barmode: 'stack',
        margin: { l: 180, r: 20, t: 60, b: 60 },
        yaxis: { automargin: true }
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
          y: miceData.map((d: any) => d.CUSTOMERNAME),
          x: miceData.map((d: any) => d.Count),
          marker: { color: '#888888' }
        },
        {
          type: 'bar',
          orientation: 'h',
          name: 'REMITTANCE',
          y: remitData.map((d: any) => d.CUSTOMERNAME),
          x: remitData.map((d: any) => d.Count),
          marker: { color: '#111111' }
        }
      ],
      layout: {
        ...this.theme,
        title: 'Top Tour Operator Corporates',
        barmode: 'stack',
        margin: { l: 180, r: 20, t: 60, b: 60 },
        yaxis: { automargin: true }
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
          x: cd.map(d => d['CountryToTravel']),
          y: cd.map(d => d['MICE_Count']),
          line: { color: '#636EFA', width: 3 }
        },
        {
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Remittance (Count)',
          x: cd.map(d => d['CountryToTravel']),
          y: cd.map(d => d['Remit_Count']),
          line: { color: '#EF553B', width: 3 }
        },
        {
          type: 'bar',
          name: 'Total Amount (USD)',
          x: cd.map(d => d['CountryToTravel']),
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
        xaxis: { automargin: true, tickangle: -45 },
        margin: { l: 80, r: 80, t: 60, b: 100 }
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
        
        if (res.branch_composition) {
          const cleanTable = (res.branch_composition.display_table || []).filter(
            (row: any) => row['LOCATION'] !== '**TOTAL**'
          );
          this.branchComposition.set({
            branch_data: res.branch_composition.branch_data || [],
            display_table: cleanTable
          });
        } else {
          this.branchComposition.set({ branch_data: [], display_table: [] });
        }

        this.corporateComposition.set(res.corporate_composition);
        this.countryCombo.set(res.country_combo);
        this.observation.set(res.observation);
      });
  }
}
