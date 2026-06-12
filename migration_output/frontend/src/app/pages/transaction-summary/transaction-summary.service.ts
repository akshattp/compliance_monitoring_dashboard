import { environment } from '../../../environments/environment';
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class TransactionSummaryService {
  constructor(private http: HttpClient) {}

  getData(req: { filtered_df: any[] }): Observable<any> {
    return this.http.post<any>(`${environment.apiBaseUrl}/api/pages/transaction-summary`, req);
  }
}
