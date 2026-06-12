import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-page-header',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-header">
      <h1 class="page-title">{{ title }}</h1>
      <p class="page-subtitle" *ngIf="subtitle">{{ subtitle }}</p>
    </div>
  `,
  styles: [`
    .page-header {
      margin-bottom: 32px;
      padding-bottom: 16px;
      border-bottom: 1px solid #e5e5e5;
    }
    .page-title {
      font-size: 24px;
      font-weight: 700;
      color: #111;
      margin: 0 0 8px 0;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .page-subtitle {
      font-size: 14px;
      color: #666;
      margin: 0;
    }
  `]
})
export class PageHeaderComponent {
  @Input() title: string = '';
  @Input() subtitle?: string;
}
