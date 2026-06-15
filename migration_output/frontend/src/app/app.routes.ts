import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'landing', pathMatch: 'full' },
  { path: 'landing', loadComponent: () => import('./pages/landing/landing.component').then(m => m.LandingComponent) },
  { path: 'home', loadComponent: () => import('./pages/home/home.component') },
  { 
    path: 'transaction-summary', 
    loadComponent: () => import('./pages/transaction-summary/transaction-summary.component').then(m => m.TransactionSummaryComponent) 
  },
  { 
    path: 'tour-operator', 
    loadComponent: () => import('./pages/tour-operator/tour-operator.component').then(m => m.TourOperatorComponent) 
  },
  { 
    path: 'retail-high-value', 
    loadComponent: () => import('./pages/retail-high-value/retail-high-value.component').then(m => m.RetailHighValueComponent) 
  },
  { 
    path: 'high-risk-corporate', 
    loadComponent: () => import('./pages/high-risk-corporate/high-risk-corporate.component').then(m => m.HighRiskCorporateComponent) 
  },
  { 
    path: 'transaction-monitoring', 
    loadComponent: () => import('./pages/transaction-monitoring/transaction-monitoring.component').then(m => m.TransactionMonitoringComponent) 
  },
  {
    path: 'fatf',
    loadComponent: () => import('./pages/fatf/fatf.component').then(m => m.FatfComponent)
  },
  {
    path: 'agent-analysis',
    loadComponent: () => import('./pages/agent-analysis/agent-analysis.component').then(m => m.AgentAnalysisComponent)
  },
  {
    path: 'passenger-analysis',
    loadComponent: () => import('./pages/passenger-analysis/passenger-analysis.component').then(m => m.PassengerAnalysisComponent)
  }
];
