import { environment } from '../../../environments/environment';
import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface GlobalFilters {
  startDate: string;
  endDate: string;
  ofacStatus: string;
}

@Injectable({
  providedIn: 'root'
})
export class DataService {
  isMockMode = signal<boolean>(true);
  currentFile = signal<File | null>(null);
  rowCount = signal<number>(0);
  
  rawDf = signal<any[]>([]); 
  isUploading = signal<boolean>(false);
  uploadStatus = signal<string>('');

  partyFile = signal<File | null>(null);
  ofacFile = signal<File | null>(null);

  // Active filters for current page
  activeFilters = signal<Record<string, string[]>>({});
  
  // Global filters
  globalFilters = signal<GlobalFilters>({
    startDate: '',
    endDate: '',
    ofacStatus: 'All'
  });

  // Unique options for each column found in rawDf
  filterOptions = computed(() => {
    const data = this.rawDf();
    const options: Record<string, string[]> = {};
    if (!data || data.length === 0) return options;
    
    // We only compute options for keys that exist in the first few rows to be safe, 
    // or we can just iterate all keys.
    // Let's gather all unique keys:
    const keys = new Set<string>();
    data.slice(0, 100).forEach(row => {
      Object.keys(row).forEach(k => keys.add(k));
    });

    for (const key of Array.from(keys)) {
      const uniqueVals = new Set<string>();
      data.forEach(row => {
        const val = row[key];
        if (val !== null && val !== undefined && val !== '') {
          uniqueVals.add(String(val));
        }
      });
      options[key] = Array.from(uniqueVals).sort();
    }
    return options;
  });

  filteredDf = computed(() => {
    let data = this.rawDf();
    if (!data || data.length === 0) return [];

    const globals = this.globalFilters();
    if (globals.startDate && globals.endDate) {
      data = data.filter(r => {
        if (!r['TXNDATE']) return true; // keep if no date
        const rDate = String(r['TXNDATE']).split(' ')[0]; // Handle datetime strings
        return rDate >= globals.startDate && rDate <= globals.endDate;
      });
    }

    if (globals.ofacStatus === 'Flagged') {
      data = data.filter(r => {
        const val = String(r['OFAC_FATF'] || '').toUpperCase();
        return ['YES', 'OFAC', 'FATF', 'FLAG'].includes(val);
      });
    } else if (globals.ofacStatus === 'Not Flagged') {
      data = data.filter(r => {
        const val = String(r['OFAC_FATF'] || '').toUpperCase();
        return val === 'NOT FLAGGED' || !val;
      });
    }

    const filters = this.activeFilters();
    for (const key of Object.keys(filters)) {
      const selectedValues = filters[key];
      if (selectedValues && selectedValues.length > 0) {
        data = data.filter(r => selectedValues.includes(String(r[key])));
      }
    }
    return data;
  });

  constructor(private http: HttpClient) {}

  uploadFile(file: File) {
    this.currentFile.set(file);
    this.isUploading.set(true);
    this.uploadStatus.set('Uploading and processing file on backend...');

    const formData = new FormData();
    formData.append('file', file);

    this.http.post<any>(`${environment.apiBaseUrl}/api/upload`, formData).subscribe({
      next: (res) => {
        this.rowCount.set(res.row_count);
        this.rawDf.set(res.data);
        // Reset filters on new upload
        this.activeFilters.set({});
        this.uploadStatus.set(`File processed successfully. Loaded ${res.row_count} rows.`);
        this.isMockMode.set(false);
        this.isUploading.set(false);
      },
      error: (err) => {
        console.error(err);
        this.uploadStatus.set('Upload failed. Please check console.');
        this.isUploading.set(false);
      }
    });
  }

  uploadOfac(file: File) {
    if (this.rawDf().length === 0) {
      alert("Please upload the main dataset first.");
      return;
    }
    this.isUploading.set(true);
    this.uploadStatus.set('Uploading and processing OFAC file...');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('filtered_df', JSON.stringify(this.rawDf())); // Apply to raw data

    this.http.post<any>(`${environment.apiBaseUrl}/api/upload/ofac`, formData).subscribe({
      next: (res) => {
        if (res.error) {
          this.uploadStatus.set(`OFAC Processing Error: ${res.error}`);
          this.isUploading.set(false);
          return;
        }
        this.ofacFile.set(file);
        this.rawDf.set(res.enriched_data);
        this.uploadStatus.set('OFAC List applied successfully.');
        this.isUploading.set(false);
      },
      error: (err) => {
        console.error(err);
        this.uploadStatus.set('OFAC Upload failed. Please check console.');
        this.isUploading.set(false);
      }
    });
  }

  uploadPartyMaster(file: File) {
    if (this.rawDf().length === 0) {
      alert("Please upload the main dataset first.");
      return;
    }
    this.isUploading.set(true);
    this.uploadStatus.set('Uploading and processing Party Master file...');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('filtered_df', JSON.stringify(this.rawDf()));

    this.http.post<any>(`${environment.apiBaseUrl}/api/upload/party-master`, formData).subscribe({
      next: (res) => {
        if (res.error) {
          this.uploadStatus.set(`Party Master Processing Error: ${res.error}`);
          this.isUploading.set(false);
          return;
        }
        this.partyFile.set(file);
        this.rawDf.set(res.enriched_data);
        this.uploadStatus.set('Party Master applied successfully.');
        this.isUploading.set(false);
      },
      error: (err) => {
        console.error(err);
        this.uploadStatus.set('Party Master Upload failed. Please check console.');
        this.isUploading.set(false);
      }
    });
  }
}
