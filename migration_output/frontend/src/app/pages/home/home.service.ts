import { environment } from '../../../environments/environment';
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { HomeRequestDto, HomeResponseDto } from './home.models';
import { DataService } from '../../core/services/data.service';

@Injectable({
  providedIn: 'root'
})
export class HomeService {
  private http = inject(HttpClient);
  private dataService = inject(DataService);
  private readonly API_URL = '/api/pages/home';
  private readonly MOCK_URL = '/assets/mock-data/home-mock-response.json';

  getHomeData(request: HomeRequestDto): Observable<HomeResponseDto> {
    if (this.dataService.isMockMode()) {
      return this.http.get<HomeResponseDto>(this.MOCK_URL);
    }
    return this.http.post<HomeResponseDto>(`${environment.apiBaseUrl}/api/pages/home`, request).pipe(
      catchError(err => {
        console.error('Backend call failed. Falling back to Mock data if available.');
        return this.http.get<HomeResponseDto>(this.MOCK_URL);
      })
    );
  }
}
