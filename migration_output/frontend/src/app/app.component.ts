import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environments/environment';
import { SidebarComponent } from './shared/components/sidebar/sidebar.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, SidebarComponent],
  templateUrl: './app.component.html',
  styles: [`
    .nav-link {
      color: #5f5e5e; /* text-secondary */
    }
    .nav-link:hover {
      background-color: #f3f3f3; /* hover:bg-surface-container-low */
    }
    .active-pill {
      background-color: #000000 !important; /* bg-primary */
      color: #ffffff !important; /* text-on-primary */
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }
  `]
})
export class AppComponent implements OnInit {
  title = 'frontend_temp';
  private http = inject(HttpClient);
  
  backendStatus = signal<'checking' | 'connected' | 'offline'>('checking');

  ngOnInit() {
    this.checkBackendHealth();
  }

  checkBackendHealth() {
    this.http.get<{status: string}>(`${environment.apiBaseUrl}/api/health`).subscribe({
      next: (res) => {
        if (res.status === 'ok') {
          this.backendStatus.set('connected');
        } else {
          this.backendStatus.set('offline');
        }
      },
      error: () => {
        this.backendStatus.set('offline');
      }
    });
  }
}
