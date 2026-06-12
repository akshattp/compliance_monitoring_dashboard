import { Component, inject, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';
import { DataService } from '../../../core/services/data.service';
import { PAGE_CONFIG } from '../../../core/constants/page-config';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent {
  dataService = inject(DataService);
  router = inject(Router);

  isCollapsed = false;
  currentPageName = '';

  // Local state for dragging
  isDragging = false;

  constructor() {
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: any) => {
      this.updateCurrentPageConfig(event.urlAfterRedirects);
    });
    
    // Initial check
    this.updateCurrentPageConfig(this.router.url);
  }

  get pageConfig() {
    return PAGE_CONFIG[this.currentPageName];
  }

  updateCurrentPageConfig(url: string) {
    if (url.includes('/home')) this.currentPageName = 'HOME PAGE';
    else if (url.includes('/transaction-summary')) this.currentPageName = 'TRANSACTION SUMMARY';
    else if (url.includes('/tour-operator')) this.currentPageName = 'TOUR OPERATOR';
    else if (url.includes('/retail-high-value')) this.currentPageName = 'RETAIL HIGH VALUE TXN';
    else if (url.includes('/high-risk-corporate')) this.currentPageName = 'HIGH RISK CORPORATE';
    else if (url.includes('/fatf')) this.currentPageName = 'FATF';
    else if (url.includes('/transaction-monitoring')) this.currentPageName = 'TRANSACTION MONITORING';
    else if (url.includes('/agent-analysis')) this.currentPageName = 'AGENT ANALYSIS';
    else if (url.includes('/passenger-analysis')) this.currentPageName = 'PASSENGER ANALYSIS';
    else this.currentPageName = '';

    // Apply default filters for the new page
    if (this.pageConfig && this.pageConfig.default_filters) {
      this.dataService.activeFilters.set({...this.pageConfig.default_filters});
    } else {
      this.dataService.activeFilters.set({});
    }
  }

  toggleSidebar() {
    this.isCollapsed = !this.isCollapsed;
  }

  // --- Upload Logic ---
  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragging = true;
  }
  
  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragging = false;
  }
  
  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragging = false;
    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      this.dataService.uploadFile(event.dataTransfer.files[0]);
    }
  }
  
  onFileSelected(event: any) {
    const file: File = event.target.files[0];
    if (file) {
      this.dataService.uploadFile(file);
    }
  }

  onOfacSelected(event: any) {
    const file: File = event.target.files[0];
    if (file) {
      this.dataService.uploadOfac(file);
    }
  }

  clearDataset() {
    this.dataService.rawDf.set([]);
    this.dataService.currentFile.set(null);
    this.dataService.rowCount.set(0);
    this.dataService.isMockMode.set(true);
  }

  // --- Filter Logic ---
  get selectedStartDate() { return this.dataService.globalFilters().startDate; }
  set selectedStartDate(v: string) { this.dataService.globalFilters.set({...this.dataService.globalFilters(), startDate: v}); }

  get selectedEndDate() { return this.dataService.globalFilters().endDate; }
  set selectedEndDate(v: string) { this.dataService.globalFilters.set({...this.dataService.globalFilters(), endDate: v}); }

  get ofacStatus() { return this.dataService.globalFilters().ofacStatus; }
  set ofacStatus(v: string) { this.dataService.globalFilters.set({...this.dataService.globalFilters(), ofacStatus: v}); }

  onFilterChange(column: string, event: Event) {
    const selectElement = event.target as HTMLSelectElement;
    const selectedOptions = Array.from(selectElement.selectedOptions).map(opt => opt.value);
    
    const filters = { ...this.dataService.activeFilters() };
    if (selectedOptions.length === 0 || selectedOptions.includes('ALL')) {
      delete filters[column];
    } else {
      filters[column] = selectedOptions;
    }
    this.dataService.activeFilters.set(filters);
  }

  isFilterSelected(column: string, val: string): boolean {
    const active = this.dataService.activeFilters()[column];
    return active ? active.includes(val) : false;
  }
}
