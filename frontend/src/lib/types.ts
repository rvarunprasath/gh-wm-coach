export interface AllocationItem {
  asset_class: string;
  value: number;
  percentage: number;
}

export interface HoldingItem {
  id: string;
  asset_type: string;
  asset_name: string;
  symbol?: string;
  units?: number;
  avg_buy_price?: number;
  current_value: number;
  updated_at?: string;
}

export interface AccountItem {
  id: string;
  institution_name: string;
  account_type: string;
  account_number_masked?: string;
  balance: number;
  currency: string;
}

export interface GoalItem {
  id: string;
  title: string;
  category: string;
  target_amount: number;
  target_year: number;
  accumulated_amount: number;
  priority: string;
  status: string;
}

export interface PortfolioSnapshot {
  net_worth: number;
  monthly_income: number;
  monthly_expenses: number;
  monthly_savings: number;
  currency: string;
  allocations: AllocationItem[];
  holdings: HoldingItem[];
  accounts: AccountItem[];
  goals: GoalItem[];
}

export interface ReasoningTrace {
  graph_context_used: string[];
  accounts_consulted: string[];
  facts_extracted: string[];
}

export interface ChatMessage {
  id: string;
  sender: "user" | "coach";
  text: string;
  timestamp: string;
  reasoning_trace?: ReasoningTrace;
  isAudio?: boolean;
}

export interface GraphNode {
  id: string;
  label: string;
  name: string;
  properties: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  properties: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
