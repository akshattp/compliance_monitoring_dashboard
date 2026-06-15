import { Component, Input, ContentChild, TemplateRef, ViewChild } from '@angular/core';
import { CommonModule, DecimalPipe, DatePipe, formatNumber, formatDate } from '@angular/common';
import { HumanReadableAmountPipe } from '../../pipes/human-readable-amount.pipe';
import { AgGridAngular } from 'ag-grid-angular';
import { ColDef, GridReadyEvent, GridApi } from 'ag-grid-community';

export interface ColumnDef {
  field: string;
  header: string;
  type?: 'amount' | 'number' | 'text' | 'date' | 'usd';
  align?: 'left' | 'right' | 'center';
  format?: string;
  isBold?: boolean;
}

@Component({
  selector: 'app-shared-table',
  standalone: true,
  imports: [CommonModule, AgGridAngular, DecimalPipe, DatePipe, HumanReadableAmountPipe],
  templateUrl: './shared-table.component.html',
  styleUrls: ['./shared-table.component.scss'],
  providers: [HumanReadableAmountPipe]
})
export class SharedTableComponent {
  @Input() data: any[] | undefined | null = [];
  @Input() maxHeight: string = '350px';
  @Input() showDownload: boolean = true;
  @Input() downloadFilename: string = 'data.csv';

  @ContentChild('customRowTemplate') customRowTemplate!: TemplateRef<any>;

  private gridApi!: GridApi;
  public themeClass: string = "ag-theme-quartz";

  public defaultColDef: ColDef = {
    sortable: true,
    filter: true,
    resizable: true,
    flex: 1,
    minWidth: 100
  };

  private _columns: ColumnDef[] = [];
  public agColumns: ColDef[] = [];

  @Input()
  set columns(cols: ColumnDef[]) {
    this._columns = cols;
    this.agColumns = cols.map(col => {
      const colDef: ColDef = {
        field: col.field,
        headerName: col.header,
      };

      if (col.align === 'right') {
        colDef.cellStyle = { textAlign: 'right' };
        colDef.headerClass = 'ag-right-aligned-header';
      } else if (col.align === 'center') {
        colDef.cellStyle = { textAlign: 'center' };
        colDef.headerClass = 'ag-center-aligned-header';
      }

      if (col.isBold) {
        colDef.cellStyle = { ...colDef.cellStyle, fontWeight: '600' };
      }

      if (col.field === 'AgentName') {
        colDef.valueGetter = (params) => {
          return params.data?.Corporate || params.data?.['LOCATION'] || params.data?.['CountryToTravel'] || params.data?.Agent || 'Unknown';
        };
      }

      if (col.type === 'amount') {
        colDef.valueFormatter = (params) => {
          if (params.value == null) return '';
          return this.amountPipe.transform(params.value);
        };
      } else if (col.type === 'usd') {
        colDef.valueFormatter = (params) => {
          if (params.value == null) return '';
          return this.formatUsd(params.value);
        };
      } else if (col.type === 'number') {
        colDef.valueFormatter = (params) => {
          if (params.value == null) return '';
          return formatNumber(params.value, 'en-US', col.format || '1.0-0');
        };
      } else if (col.type === 'date') {
        colDef.valueFormatter = (params) => {
          if (!params.value) return '';
          return formatDate(params.value, col.format || 'mediumDate', 'en-US');
        };
      }

      return colDef;
    });
  }

  get columns(): ColumnDef[] {
    return this._columns;
  }

  constructor(private amountPipe: HumanReadableAmountPipe) {}

  onGridReady(params: GridReadyEvent) {
    this.gridApi = params.api;
  }

  downloadCSV() {
    if (this.gridApi) {
      this.gridApi.exportDataAsCsv({ fileName: this.downloadFilename });
    }
  }

  onSearch(event: any) {
    if (this.gridApi) {
      this.gridApi.setGridOption('quickFilterText', event.target.value);
    }
  }

  toggleFullScreen() {
    const elem = document.documentElement;
    if (!document.fullscreenElement) {
      elem.requestFullscreen().catch(err => {
        console.error(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
      });
    } else {
      document.exitFullscreen();
    }
  }

  get totalRecords(): number {
    return this.data ? this.data.length : 0;
  }

  formatUsd(value: any): string {
    if (value == null) return '$0.00';
    let val = typeof value === 'string' ? parseFloat(value.replace(/[^0-9.-]/g, '')) : value;
    if (isNaN(val)) return '$0.00';
    return '$' + val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  get numericTotals(): { header: string, value: string }[] {
    const totals: { header: string, value: string }[] = [];
    if (!this.data || this.data.length === 0) return totals;

    this.columns.forEach(col => {
      if (col.type === 'amount' || col.type === 'usd' || col.type === 'number') {
        let sum = 0;
        for (const row of this.data!) {
          let val = row[col.field];
          if (typeof val === 'string') {
            val = parseFloat(val.replace(/[^0-9.-]/g, ''));
          }
          const num = Number(val);
          if (!isNaN(num)) sum += num;
        }

        let formattedSum = '';
        if (col.type === 'amount') {
          formattedSum = this.amountPipe.transform(sum);
        } else if (col.type === 'usd') {
          formattedSum = this.formatUsd(sum);
        } else {
          formattedSum = formatNumber(sum, 'en-US', col.format || '1.0-0');
        }
        
        totals.push({ header: col.header, value: formattedSum });
      }
    });
    return totals;
  }
}
