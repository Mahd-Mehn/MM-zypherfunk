/**
 * TypeScript types for API responses
 */

// ============= Auth Types =============
export type UserType = 'trader' | 'follower' | 'admin' | 'moderator'

export interface User {
  id: string
  email: string
  wallet_address: string | null
  user_type: UserType
  created_at: string
}

export interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface MagicLinkRequest {
  email: string
}

export interface MagicLinkResponse {
  message: string
  email: string
  expires_in: number
  is_new_user: boolean
}

export interface MagicLinkVerify {
  token: string
}

export interface WalletConnectRequest {
  wallet_address: string
}

// ============= Exchange Types =============
export type ExchangeStatus = 'active' | 'invalid' | 'testing' | 'suspended'

export interface ExchangeConnection {
  id: string
  user_id: string
  exchange: string
  status: ExchangeStatus
  last_synced_at: string | null
  last_sync_error: string | null
  consecutive_errors: number
  created_at: string
  updated_at: string
}

export interface ExchangeConnectionCreate {
  exchange: string
  api_key: string
  api_secret: string
  is_signal_provider?: boolean
}

export interface ExchangeConnectionUpdate {
  api_key?: string
  api_secret?: string
}

export interface ExchangeConnectionTest {
  success: boolean
  message: string
  error?: string
  tested_at: string
  connection_status: ExchangeStatus
}

export interface SupportedExchange {
  name: string
  display_name: string
  description: string
  features: string[]
  api_docs_url: string
  required_permissions: string[]
  setup_instructions: string[]
}

export interface ExchangeListResponse {
  connections: ExchangeConnection[]
  total: number
}

// ============= Subscription Types =============
export type SubscriptionStatus = 'active' | 'paused' | 'cancelled'

export interface Subscription {
  id: string
  follower_id: string
  trader_id: string
  status: SubscriptionStatus
  max_capital_pct: number
  max_position_size: number | null
  stop_loss_pct: number | null
  take_profit_pct: number | null
  created_at: string
  updated_at: string
  paused_at: string | null
  cancelled_at: string | null
}

export interface SubscriptionCreate {
  trader_id: string
  max_capital_pct: number
  max_position_size?: number
  stop_loss_pct?: number
  take_profit_pct?: number
}

export interface SubscriptionUpdate {
  max_capital_pct?: number
  max_position_size?: number
  stop_loss_pct?: number
  take_profit_pct?: number
}

export interface SubscriptionListResponse {
  subscriptions: Subscription[]
  total: number
}

export interface TraderFollower {
  follower_id: string
  follower_email: string | null
  follower_address: string | null
  status: SubscriptionStatus
  max_capital_pct: number
  max_position_size?: number | null
  stop_loss_pct?: number | null
  take_profit_pct?: number | null
  total_trades_copied: number
  total_profit_loss: number
  created_at: string
  updated_at: string
}

export interface TraderFollowerListResponse {
  followers: TraderFollower[]
  total: number
}

// ============= Trader Types =============
export interface TraderProfile {
  id: string
  address: string
  display_name: string
  bio: string
  avatar_url: string | null
  verification_types?: string[]
  win_rate: number
  total_trades: number
  verified_trades: number
  total_pnl: number
  followers: number
  performance_fee: number
  chains?: string[]
  exchanges?: string[]
  trust_tier: number
  joined_date: string
}

export interface TraderPerformance {
  trader_id: string
  timeframe: string
  total_pnl: number
  win_rate: number
  total_trades: number
  avg_trade_size: number
  sharpe_ratio: number
  max_drawdown: number
  performance_data: Array<{
    date: string
    value: number
  }>
}

export interface Trade {
  id: string
  trader_id: string
  timestamp: string
  asset_in: string
  asset_out: string
  amount_in: number
  amount_out: number
  pnl: number
  pnl_percentage: number
  verification_type: string
  chain?: string
  exchange: string
  tx_hash?: string
}

export interface LeaderboardResponse {
  traders: TraderProfile[]
  total: number
  limit: number
  offset: number
}

// ============= Portfolio Types =============
export interface PortfolioPosition {
  symbol: string
  exchange: string
  quantity: number
  average_price: number
  current_price: number
  market_value_usd: number
  unrealized_pnl_usd: number
  unrealized_pnl_percentage: number
  trader_id?: string
  last_updated: string
}

export interface PortfolioOverview {
  user_id: string
  total_value_usd: number
  total_pnl_usd: number
  total_pnl_percentage: number
  positions: PortfolioPosition[]
  active_subscriptions: number
  last_updated: string
}

export interface PortfolioAllocation {
  by_asset: Array<{
    name: string
    value_usd: number
    percentage: number
    count?: number
  }>
  by_exchange: Array<{
    name: string
    value_usd: number
    percentage: number
    count?: number
  }>
  by_trader: Array<{
    name: string
    value_usd: number
    percentage: number
    count?: number
  }>
  cash_percentage: number
  total_allocated_usd: number
}

export interface PortfolioPerformance {
  timeframe: string
  total_return_usd: number
  total_return_percentage: number
  sharpe_ratio: number
  max_drawdown_percentage: number
  win_rate: number
  profit_factor: number
  historical_pnl: Array<{
    date: string
    value: number
  }>
  performance_by_trader: Array<{
    trader_id: string
    pnl: number
    roi: number
  }>
  performance_by_exchange: Array<{
    exchange: string
    pnl: number
    roi: number
  }>
  risk_metrics: Record<string, number>
}

export interface Alert {
  id: string
  type: string
  title: string
  message: string
  is_read: boolean
  created_at: string
  metadata?: Record<string, any>
}

export interface AlertsResponse {
  alerts: Alert[]
  total_count: number
  unread_count: number
}

export interface RecentActivity {
  id: string
  type: string
  description: string
  timestamp: string
  metadata: Record<string, any>
}

export interface DashboardData {
  portfolio_value_usd: number
  portfolio_pnl_usd: number
  portfolio_pnl_percentage: number
  active_subscriptions: number
  recent_activities: RecentActivity[]
  alerts_count: number
  last_updated: string
}

// ============= Execution Types =============
export type ExecutionStatus = 'pending' | 'executing' | 'completed' | 'failed' | 'cancelled'

export interface Execution {
  id: string
  user_id: string
  trader_id: string
  subscription_id: string
  original_trade_id: string
  status: ExecutionStatus
  exchange: string
  symbol: string
  side: 'buy' | 'sell'
  order_type: string
  quantity: number
  price: number | null
  executed_price: number | null
  executed_quantity: number | null
  pnl: number | null
  error_message: string | null
  created_at: string
  executed_at: string | null
}

export interface ExecutionListResponse {
  executions: Execution[]
  total: number
}

export interface ExecutionStats {
  total_executions: number
  successful_executions: number
  failed_executions: number
  total_pnl: number
  success_rate: number
  avg_execution_time: number
}

// ============= Rate Limit Types =============
export interface RateLimitStatus {
  tier: string
  limits: {
    requests_per_minute: number
    requests_per_hour: number
  }
  current_usage: {
    minute: number
    hour: number
  }
  remaining: {
    minute: number
    hour: number
  }
  reset_at: {
    minute: string
    hour: string
  }
}

// ============= System Types =============
export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy'
  version: string
  timestamp: string
  services: {
    database: boolean
    redis: boolean
    sentinel: boolean
    conductor: boolean
    alchemist: boolean
  }
}
