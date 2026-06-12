import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-kpi-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="kpi-card">
      <div class="kpi-title">{{ title }}</div>
      <div class="kpi-value">{{ value }}</div>
      <div class="kpi-delta" *ngIf="delta" [class.positive]="deltaPositive" [class.negative]="deltaNegative">
        {{ delta }}
      </div>
    </div>
  `,
  styles: [`
    .kpi-card {
      background-color: #ffffff;
      border: 1px solid #e5e5e5;
      border-radius: 8px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    .kpi-title {
      font-size: 14px;
      font-weight: 500;
      color: #666;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .kpi-value {
      font-size: 28px;
      font-weight: 600;
      color: #111;
    }
    .kpi-delta {
      font-size: 13px;
      margin-top: 8px;
      color: #666;
    }
    .positive { color: #10b981; }
    .negative { color: #ef4444; }
  `]
})
export class KpiCardComponent {
  @Input() title: string = '';
  @Input() value: any = '';
  @Input() delta?: string;
  @Input() deltaPositive?: boolean = false;
  @Input() deltaNegative?: boolean = false;
}
