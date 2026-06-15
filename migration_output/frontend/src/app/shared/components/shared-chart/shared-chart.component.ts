import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PlotlyViaWindowModule } from 'angular-plotly.js';

@Component({
  selector: 'app-shared-chart',
  standalone: true,
  imports: [CommonModule, PlotlyViaWindowModule],
  templateUrl: './shared-chart.component.html',
  styleUrls: ['./shared-chart.component.scss']
})
export class SharedChartComponent {
  @Input() chartData: any = null;
  @Input() height: string = '350px';
}
