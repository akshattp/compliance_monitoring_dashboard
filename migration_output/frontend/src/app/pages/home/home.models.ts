export interface HomeKpis {
  total_transactions: number;
  total_net_amt: number;
  ps_amount: number;
  pb_amount: number;
  ps_count: number;
  pb_count: number;
  ps_count_pct: number;
  ps_amt_pct: number;
  pb_count_pct: number;
  pb_amt_pct: number;
  average_transaction: number;
  highest_transaction: number;
  lowest_transaction: number;
  highest_pct: number;
  lowest_pct: number;
  date_range: string;
  best_segment_name: string;
  best_segment_amt: number;
  best_segment_pct: number;
  best_branch_name: string;
  best_branch_amt: number;
  best_branch_pct: number;
}

export interface TrendTimePoint {
  Time: string;
  Transaction_Amount: number;
  Transaction_Count: number;
}

export interface HomeTrends {
  agg_df: TrendTimePoint[];
  highest_amount_time: TrendTimePoint | null;
  lowest_amount_time: TrendTimePoint | null;
  highest_count_time: TrendTimePoint | null;
  lowest_count_time: TrendTimePoint | null;
}

export interface BreakdownData {
  Purpose?: string;
  Product?: string;
  'Branch Name'?: string;
  Branch?: string;
  'Visiting Country'?: string;
  Count: number;
  'Net Amt': number;
  Percentage?: number;
  '% Count'?: number;
  '% Net Amount'?: number;
  is_other?: boolean;
}

export interface HomeBreakdowns {
  purpose_df: BreakdownData[];
  purpose_summary_table: BreakdownData[];
  product_df: BreakdownData[];
  product_summary_table: BreakdownData[];
  branch_df: BreakdownData[];
  country_df: BreakdownData[];
}

export interface HomeRequestDto {
  filtered_df: any[]; // List of transaction objects
  trend_agg?: 'DAILY' | 'WEEKLY';
  breakdown_metric_agg?: 'NET AMOUNT' | 'COUNT';
  purpose_threshold?: number;
}

export interface HomeResponseDto {
  kpis: HomeKpis;
  trends: HomeTrends;
  breakdowns: HomeBreakdowns;
  top_transactions: any[];
}
