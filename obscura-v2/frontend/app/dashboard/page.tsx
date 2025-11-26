"use client"

import { useState, useEffect, useMemo } from "react"
import Link from "next/link"
import { Header } from "@/components/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { VerificationBadge } from "@/components/verification-badge"
import {
  TrendingUp,
  TrendingDown,
  Users,
  Settings,
  ExternalLink,
  Copy,
  X,
  ArrowUpRight,
  Shield,
  Clock,
  Target,
  CheckCircle2,
  BarChart3,
  Wallet,
  ArrowRight,
  Inbox,
  Loader2,
  AlertCircle,
} from "lucide-react"
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts"
import { useAuthContext } from "@/components/providers/auth-provider"
import { useExchanges } from "@/hooks/use-exchanges"
import { usePortfolio, usePortfolioPerformance, useDashboard, useAlerts } from "@/hooks/use-portfolio"
import { useSubscriptions } from "@/hooks/use-subscriptions"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { executionsAPI } from "@/lib/api"
import type { Trade, Execution, Subscription } from "@/lib/api/types"
import { shortenIdentifier } from "@/lib/utils"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { TraderFollower } from "@/lib/api/types"
import { ArciumPrivateOrder } from "@/components/solana/arcium-widget"
import { LiveActivityFeed } from "@/components/dashboard/LiveActivityFeed"

const formatCurrency = (
  value: number,
  options: { minimumFractionDigits?: number; maximumFractionDigits?: number } = {}
) => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 1,
    ...options,
  }).format(value)
}

const formatPercent = (value: number = 0, digits: number = 1) => {
  return `${value.toFixed(digits)}%`
}

const formatDateTime = (value?: string) => {
  if (!value) return "—"
  return new Date(value).toLocaleString()
}

const formatNumber = (value?: number | null, opts: Intl.NumberFormatOptions = {}) => {
  if (value === undefined || value === null) return "—"
  return new Intl.NumberFormat("en-US", opts).format(value)
}

const PAGE_SIZE = 5

export default function DashboardPage() {
  const { user } = useAuthContext()
  const { connections } = useExchanges()
  const [activeView, setActiveView] = useState<"overview" | "trades" | "copied" | "following" | "subscribers">("overview")
  const [executions, setExecutions] = useState<Execution[]>([])
  const [executionsLoading, setExecutionsLoading] = useState(false)
  const [executionsError, setExecutionsError] = useState<string | null>(null)
  const [tradeExchangeFilter, setTradeExchangeFilter] = useState("all")
  const [tradeVerificationFilter, setTradeVerificationFilter] = useState("all")
  const [tradesPage, setTradesPage] = useState(1)
  const [executionStatusFilter, setExecutionStatusFilter] = useState("all")
  const [executionExchangeFilter, setExecutionExchangeFilter] = useState("all")
  const [executionsPage, setExecutionsPage] = useState(1)
  const [subscriptionStatusFilter, setSubscriptionStatusFilter] = useState("all")
  const [followingPage, setFollowingPage] = useState(1)
  const {
    overview,
    loading: overviewLoading,
    error: overviewError,
  } = usePortfolio()
  const {
    performance,
    loading: performanceLoading,
    error: performanceError,
  } = usePortfolioPerformance("30d")
  const {
    dashboard: dashboardData,
    loading: dashboardLoading,
    error: dashboardError,
  } = useDashboard()
  const {
    subscriptions,
    followers,
    isTrader: isTraderFromSubscriptions,
    loading: subscriptionsLoading,
    error: subscriptionsError,
  } = useSubscriptions()

  const {
    alerts: alertsList,
    loading: alertsLoading,
  } = useAlerts()

  const isTrader = user?.user_type === "trader"
  const followingTabId = isTrader ? "subscribers" : "following"

  // Check if user has completed onboarding
  // Either they have connections OR they've completed the onboarding flow
  const hasCompletedOnboarding = 
    (connections && connections.length > 0) || 
    (typeof window !== 'undefined' && localStorage.getItem('onboarding_complete') === 'true')

  useEffect(() => {
    if (!hasCompletedOnboarding) return
    let cancelled = false

    const fetchExecutions = async () => {
      try {
        setExecutionsLoading(true)
        const data = await executionsAPI.getExecutions({ limit: 10 })
        if (cancelled) return
        setExecutions(data.executions)
        setExecutionsError(null)
      } catch (err: any) {
        if (cancelled) return
        setExecutionsError(err.message)
      } finally {
        if (!cancelled) {
          setExecutionsLoading(false)
        }
      }
    }

    fetchExecutions()
    return () => {
      cancelled = true
    }
  }, [hasCompletedOnboarding])

  const performanceData = useMemo(() => {
    const series = performance?.historical_pnl ?? []
    return series.map((point: any) => ({
      date: point.date,
      value: typeof point.value === "number" ? point.value : Number(point.pnl_usd ?? 0),
    }))
  }, [performance])

  const performanceByTrader = useMemo(() => {
    return (performance?.performance_by_trader ?? []).map((item: any) => ({
      trader_id: item.trader_id,
      trader_name: item.trader_name,
      roi: typeof item.roi === "number" ? item.roi : Number(item.total_pnl_percentage ?? 0),
      pnl: Number(item.total_profit_loss ?? item.pnl ?? 0),
    }))
  }, [performance])
  
  // Map recent activities to trades for display
  const recentTrades = useMemo(() => {
    const activities = dashboardData?.recent_activities ?? []
    return activities
      .filter((activity) => activity.type === "trade")
      .map((activity) => {
        const metadata = activity.metadata || {}
        const symbol = metadata.symbol || ""
        const [symbolIn, symbolOut] = symbol.includes("/") ? symbol.split("/") : [undefined, undefined]
        const assetIn = metadata.asset_in || metadata.base_asset || symbolIn || "Unknown"
        const assetOut = metadata.asset_out || metadata.quote_asset || symbolOut || "Unknown"

        const parseNumber = (value: any, fallback = 0) => {
          const numeric = Number(value)
          return Number.isFinite(numeric) ? numeric : fallback
        }

        const amountIn = parseNumber(metadata.amount_in ?? metadata.amount_in_usd ?? metadata.quantity)
        const amountOut = parseNumber(metadata.amount_out ?? metadata.amount_out_usd)
        const pnl = parseNumber(metadata.pnl_usd ?? metadata.pnl ?? metadata.running_pnl)
        const pnlPct = parseNumber(metadata.pnl_percentage ?? metadata.pnl_pct)

        return {
          id: activity.id,
          timestamp: activity.timestamp,
          trader_id: metadata.trader_id || "unknown",
          asset_in: assetIn,
          asset_out: assetOut,
          amount_in: amountIn,
          amount_out: amountOut,
          pnl,
          pnl_percentage: pnlPct,
          exchange: metadata.exchange || "Unknown",
          verification_type: metadata.verification_type || metadata.status || "Unknown",
          chain: metadata.chain,
          ...metadata,
        } as unknown as Trade
      })
  }, [dashboardData])

  const activeSubscriptions = subscriptions || []
  const alerts = alertsList || []
  const recentActivities = dashboardData?.recent_activities ?? []
  
  const summary = useMemo(() => {
    if (overview) {
      return {
        total_value: Number(overview.total_value_usd),
        total_pnl: Number(overview.total_pnl_usd),
        pnl_percentage: overview.total_pnl_percentage,
        active_positions: overview.positions?.length || 0,
        active_subscriptions: overview.active_subscriptions
      }
    }
    if (dashboardData) {
      return {
        total_value: Number(dashboardData.portfolio_value_usd),
        total_pnl: Number(dashboardData.portfolio_pnl_usd),
        pnl_percentage: dashboardData.portfolio_pnl_percentage,
        active_positions: 0,
        active_subscriptions: dashboardData.active_subscriptions
      }
    }
    return null
  }, [overview, dashboardData])

  const monthlyStats = useMemo(() => {
    if (!performance) {
      return {
        label: "This Month",
        profit: 0,
        trades: 0,
        winRate: 0,
        pctChange: 0,
      }
    }

    const label = performance.timeframe === "30d" ? "Last 30 Days" : `Last ${performance.timeframe}`
    const riskMetrics = performance.risk_metrics || {}

    return {
      label,
      profit: Number(performance.total_return_usd ?? 0),
      trades: Number(riskMetrics.trade_count ?? riskMetrics.total_trades ?? 0),
      winRate: Number(performance.win_rate ?? 0),
      pctChange: Number(performance.total_return_percentage ?? 0),
    }
  }, [performance])

  const activityFeed = useMemo(() => {
    return recentActivities.map((activity) => {
      const metadata = activity.metadata || {}
      const base = {
        text: activity.description,
        time: formatDateTime(activity.timestamp),
        value: metadata.pnl_usd !== undefined
          ? formatCurrency(Number(metadata.pnl_usd))
          : metadata.status || metadata.exchange || "—",
        icon: CheckCircle2,
        color: "text-muted-foreground",
        bg: "bg-muted",
      }

      switch (activity.type) {
        case "trade":
          return {
            ...base,
            icon: CheckCircle2,
            color: metadata.status === "failed" ? "text-destructive" : "text-success",
            bg: metadata.status === "failed" ? "bg-destructive/10" : "bg-success/10",
          }
        case "follower":
          return {
            ...base,
            icon: Users,
            color: "text-primary",
            bg: "bg-primary/10",
            value: metadata.count ? `+${metadata.count}` : "+1",
          }
        case "verification":
          return {
            ...base,
            icon: Shield,
            color: "text-primary",
            bg: "bg-primary/10",
            value: metadata.layer || metadata.status || "Verified",
          }
        default:
          return base
      }
    })
  }, [recentActivities])

  const tradeExchangeOptions = useMemo(
    () => Array.from(new Set(recentTrades.map((trade) => trade.exchange))).filter(Boolean),
    [recentTrades]
  )
  const tradeVerificationOptions = useMemo(
    () => Array.from(new Set(recentTrades.map((trade) => trade.verification_type))).filter(Boolean),
    [recentTrades]
  )
  const executionStatusOptions = useMemo(
    () => Array.from(new Set(executions.map((execution) => execution.status))).filter(Boolean),
    [executions]
  )
  const executionExchangeOptions = useMemo(
    () => Array.from(new Set(executions.map((execution) => execution.exchange))).filter(Boolean),
    [executions]
  )
  const subscriptionStatusOptions = useMemo(
    () => Array.from(new Set(activeSubscriptions.map((sub) => sub.status))).filter(Boolean),
    [activeSubscriptions]
  )

  const filteredTrades = useMemo(
    () =>
      recentTrades.filter((trade) => {
        const matchesExchange = tradeExchangeFilter === "all" || trade.exchange === tradeExchangeFilter
        const matchesVerification = tradeVerificationFilter === "all" || trade.verification_type === tradeVerificationFilter
        return matchesExchange && matchesVerification
      }),
    [recentTrades, tradeExchangeFilter, tradeVerificationFilter]
  )
  const totalTradePages = Math.max(1, Math.ceil(filteredTrades.length / PAGE_SIZE) || 1)
  const paginatedTrades = useMemo(() => {
    const start = (tradesPage - 1) * PAGE_SIZE
    return filteredTrades.slice(start, start + PAGE_SIZE)
  }, [filteredTrades, tradesPage])

  const filteredExecutions = useMemo(
    () =>
      executions.filter((execution) => {
        const matchesStatus = executionStatusFilter === "all" || execution.status === executionStatusFilter
        const matchesExchange = executionExchangeFilter === "all" || execution.exchange === executionExchangeFilter
        return matchesStatus && matchesExchange
      }),
    [executions, executionStatusFilter, executionExchangeFilter]
  )
  const totalExecutionPages = Math.max(1, Math.ceil(filteredExecutions.length / PAGE_SIZE) || 1)
  const paginatedExecutions = useMemo(() => {
    const start = (executionsPage - 1) * PAGE_SIZE
    return filteredExecutions.slice(start, start + PAGE_SIZE)
  }, [filteredExecutions, executionsPage])

  const filteredSubscriptions = useMemo(
    () =>
      activeSubscriptions.filter((sub) => {
        return subscriptionStatusFilter === "all" || sub.status === subscriptionStatusFilter
      }),
    [activeSubscriptions, subscriptionStatusFilter]
  )
  const totalFollowingPages = Math.max(1, Math.ceil(filteredSubscriptions.length / PAGE_SIZE) || 1)
  const paginatedSubscriptions = useMemo(() => {
    const start = (followingPage - 1) * PAGE_SIZE
    return filteredSubscriptions.slice(start, start + PAGE_SIZE)
  }, [filteredSubscriptions, followingPage])

  const followingTabLabel = isTrader
    ? `Subscribers (${followers.length})`
    : `Following (${filteredSubscriptions.length})`

  const displayName = user?.email?.split("@")[0] || user?.id || "Obscura Trader"
  const userAddress = user?.wallet_address
    ? shortenIdentifier(user.wallet_address)
    : "Wallet not connected"

  const totalValue = summary?.total_value ?? 0
  const totalPnL = summary?.total_pnl ?? 0
  const activePositions = summary?.active_positions ?? 0
  const activeFollowers = summary?.active_subscriptions ?? 0
  const returnPct = performance?.total_return_percentage ?? 0
  const heroActiveMetricValue = isTrader ? followers.length : activeFollowers
  const heroActiveMetricLabel = isTrader ? "Active Subscribers" : "Active Subscriptions"

  const heroLoading = overviewLoading || performanceLoading || dashboardLoading
  const dataErrors = [overviewError, performanceError, dashboardError, subscriptionsError, executionsError].filter(Boolean) as string[]

  const hasTrades = filteredTrades.length > 0
  const hasCopiedTrades = filteredExecutions.length > 0
  const hasFollowing = filteredSubscriptions.length > 0

  useEffect(() => {
    setTradesPage(1)
  }, [tradeExchangeFilter, tradeVerificationFilter])

  useEffect(() => {
    setTradesPage((prev) => (prev > totalTradePages ? totalTradePages : prev))
  }, [totalTradePages])

  useEffect(() => {
    setExecutionsPage(1)
  }, [executionExchangeFilter, executionStatusFilter])

  useEffect(() => {
    setExecutionsPage((prev) => (prev > totalExecutionPages ? totalExecutionPages : prev))
  }, [totalExecutionPages])

  useEffect(() => {
    setFollowingPage(1)
  }, [subscriptionStatusFilter])

  useEffect(() => {
    setFollowingPage((prev) => (prev > totalFollowingPages ? totalFollowingPages : prev))
  }, [totalFollowingPages])

  const renderLoadingState = (label: string) => (
    <div className="flex items-center gap-3 rounded-xl border border-border/50 px-4 py-3 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" />
      {label}
    </div>
  )

  const renderTraderPerformance = () => {
    if (performanceLoading) return renderLoadingState("Loading trader performance...")
    if (!performanceByTrader.length) return null

    return (
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-lg font-medium">Performance by Trader</CardTitle>
          <CardDescription>PnL breakdown for your active subscriptions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {performanceByTrader.map((item) => (
              <div key={item.trader_id} className="flex items-center justify-between p-3 rounded-lg border border-border/50 bg-background/50">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Users className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">Trader {shortenIdentifier(item.trader_id, { prefixLength: 8, suffixLength: 0, separator: "" })}</p>
                    <p className="text-xs text-muted-foreground">ROI: {formatPercent(item.roi)}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-medium ${item.pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                    {item.pnl >= 0 ? "+" : ""}{formatCurrency(item.pnl)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  const renderPagination = (
    page: number,
    totalPages: number,
    onChange: (page: number) => void,
  ) => {
    if (totalPages <= 1) return null

    return (
      <div className="flex flex-col gap-2 pt-4 sm:flex-row sm:items-center sm:justify-between">
        <span className="text-xs text-muted-foreground">
          Page {page} of {totalPages}
        </span>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" disabled={page === 1} onClick={() => onChange(page - 1)}>
            Previous
          </Button>
          <Button variant="outline" size="sm" disabled={page === totalPages} onClick={() => onChange(page + 1)}>
            Next
          </Button>
        </div>
      </div>
    )
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        <Header />

        {/* Empty State for New Users */}
        {!hasCompletedOnboarding && (
          <div className="container mx-auto px-4 lg:px-8 py-20">
            <Card className="max-w-3xl mx-auto border-2 text-center">
              <CardContent className="p-12 space-y-6">
                <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                  <Inbox className="h-10 w-10 text-primary" />
                </div>
                <div>
                  <h2 className="text-3xl font-bold mb-3">Welcome to Obscura!</h2>
                  <p className="text-muted-foreground text-lg">
                    Get started by connecting your exchange accounts to begin trading
                  </p>
                </div>
                <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                  <Button size="lg" asChild className="h-12 px-8">
                    <Link href="/onboarding">
                      <Wallet className="mr-2 h-5 w-5" />
                      Connect Exchange
                    </Link>
                  </Button>
                  <Button size="lg" variant="outline" asChild className="h-12 px-8">
                    <Link href="/marketplace">
                      <Users className="mr-2 h-5 w-5" />
                      Browse Traders
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Dashboard Content - Only show if onboarded */}
        {hasCompletedOnboarding && (
          <>
            <div className="relative border-b overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 via-primary/5 to-background" />
              <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />

              <div className="container relative mx-auto px-4 lg:px-8 py-12 lg:py-16">
                {heroLoading && (
                  <div className="mb-6 flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/80">
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                    Syncing your performance data...
                  </div>
                )}
                {dataErrors.length > 0 && (
                  <div className="mb-6 flex items-start gap-3 rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    <AlertCircle className="h-4 w-4" />
                    <div>
                      <p className="font-semibold">Some data failed to load</p>
                      <p className="text-destructive/80">Showing latest cached values. Try refreshing.</p>
                    </div>
                  </div>
                )}
                <div className="grid lg:grid-cols-2 gap-8 items-center">
                  <div className="space-y-6">
                    <div className="flex items-center gap-4">
                      <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-purple-600 via-primary to-purple-400 flex items-center justify-center text-3xl font-bold text-white shadow-xl shadow-purple-500/30">
                        {displayName.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <h1 className="text-4xl font-bold mb-2">{displayName}</h1>
                        {isTrader && (
                          <Badge className="bg-gradient-to-r from-purple-500/20 to-primary/20 text-purple-400 border-purple-500/30">
                            <Shield className="h-3.5 w-3.5 mr-1.5" />
                            Verified Trader
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-3 pt-2">
                      <Button
                        variant="outline"
                        className="bg-gradient-to-r from-purple-500/10 to-primary/10 backdrop-blur-sm border-2 border-purple-500/30 hover:bg-purple-500/20 hover:border-purple-500/50"
                        asChild
                      >
                        <Link href="/onboarding">
                          <Settings className="mr-2 h-4 w-4" />
                          Settings
                        </Link>
                      </Button>
                      {isTrader && user?.wallet_address && (
                        <Button
                          className="bg-gradient-to-r from-purple-600 to-primary hover:from-purple-700 hover:to-primary/90 shadow-lg shadow-purple-500/30"
                          asChild
                        >
                          <Link href={`/trader/${user.wallet_address}`}>
                            <ExternalLink className="mr-2 h-4 w-4" />
                            Public Profile
                          </Link>
                        </Button>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <Card className="border-success/30 bg-gradient-to-br from-success/10 to-card backdrop-blur-xl shadow-lg hover:shadow-xl hover:shadow-success/20 transition-all">
                      <CardContent className="p-6 text-center">
                        <div className="text-4xl font-bold text-success mb-1">{formatCurrency(totalPnL, { maximumFractionDigits: 0 })}</div>
                        <div className="text-sm text-muted-foreground">Lifetime PnL</div>
                      </CardContent>
                    </Card>
                    <Card className="border-purple-500/30 bg-gradient-to-br from-purple-500/10 to-card backdrop-blur-xl shadow-lg hover:shadow-xl hover:shadow-purple-500/20 transition-all">
                      <CardContent className="p-6 text-center">
                        <div className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-primary bg-clip-text text-transparent mb-2">
                          {formatPercent(returnPct)}
                        </div>
                        <div className="text-sm text-muted-foreground">Win Rate</div>
                      </CardContent>
                    </Card>
                    <Card className="border-primary/30 bg-gradient-to-br from-primary/10 to-card backdrop-blur-xl shadow-lg hover:shadow-xl hover:shadow-primary/20 transition-all">
                      <CardContent className="p-6 text-center">
                        <div className="text-4xl font-bold text-primary mb-2">{activePositions}</div>
                        <div className="text-sm text-muted-foreground">Active Positions</div>
                      </CardContent>
                    </Card>
                    <Card className="border-purple-500/30 bg-gradient-to-br from-purple-500/10 to-card backdrop-blur-xl shadow-lg hover:shadow-xl hover:shadow-purple-500/20 transition-all">
                      <CardContent className="p-6 text-center">
                        <div className="text-4xl font-bold bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent mb-2">
                          {heroActiveMetricValue}
                        </div>
                        <div className="text-sm text-muted-foreground">{heroActiveMetricLabel}</div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </div>
            </div>

            <div className="container mx-auto px-4 lg:px-8 py-8 lg:py-12">
              <div className="flex items-center gap-3 mb-10 overflow-x-auto pb-2">
                {(() => {
                  const tabs = [
                    { id: "overview", label: "Overview", icon: BarChart3 },
                  ]
                  // Traders see "My Trades", Followers see "Copied Trades"
                  if (isTrader) {
                    tabs.push({ id: "trades", label: "My Trades", icon: TrendingUp })
                  } else {
                    tabs.push({ id: "copied", label: "Copied Trades", icon: Copy })
                  }
                  tabs.push({ id: followingTabId, label: followingTabLabel, icon: Users })
                  return tabs
                })().map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveView(tab.id as any)}
                    className={`flex items-center gap-2.5 px-6 py-3 rounded-xl text-sm font-semibold transition-all whitespace-nowrap ${activeView === tab.id
                      ? "bg-gradient-to-r from-purple-600 to-primary text-white shadow-lg shadow-purple-500/30"
                      : "bg-card border border-border/50 text-muted-foreground hover:text-foreground hover:border-purple-500/30 hover:bg-purple-500/5"
                      }`}
                  >
                    <tab.icon className="h-4 w-4" />
                    {tab.label}
                  </button>
                ))}
              </div>

              {activeView === "overview" && (
                <div className="space-y-8">
                  <div className="grid lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-8">
                      {/* Recent activity */}
                      <LiveActivityFeed />
                    </div>

                    {/* Sidebar - Quick actions and CTA */}
                    <div className="space-y-6">
                      <Card className="border-border/50">
                        <CardHeader className="border-b">
                          <CardTitle className="text-lg">Quick Actions</CardTitle>
                        </CardHeader>
                        <CardContent className="pt-6 space-y-3">
                          <Button className="w-full justify-start h-12 bg-transparent" variant="outline" asChild>
                            <Link href="/marketplace">
                              <Users className="mr-3 h-5 w-5" />
                              Browse Traders
                            </Link>
                          </Button>
                          <Button className="w-full justify-start h-12 bg-transparent" variant="outline" asChild>
                            <Link href="/onboarding">
                              <Wallet className="mr-3 h-5 w-5" />
                              Link Exchange
                            </Link>
                          </Button>
                          <Button className="w-full justify-start h-12 bg-transparent" variant="outline" asChild>
                            <Link href="/docs">
                              <ExternalLink className="mr-3 h-5 w-5" />
                              Documentation
                            </Link>
                          </Button>
                        </CardContent>
                      </Card>

                      {/* Arcium Private Execution Widget */}
                      <ArciumPrivateOrder />

                      {/* Only show "Become a Signal Provider" for followers */}
                      {user?.user_type === 'follower' && (
                        <Card className="border-2 border-purple-500/40 bg-gradient-to-br from-purple-500/20 via-primary/10 to-card shadow-xl">
                          <CardContent className="p-8 space-y-6">
                            <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-purple-500/30 to-primary/20 flex items-center justify-center shadow-lg shadow-purple-500/20">
                              <Shield className="h-8 w-8 text-purple-400" />
                            </div>
                            <div>
                              <h3 className="text-xl font-bold mb-2">Become a Signal Provider</h3>
                              <p className="text-sm text-muted-foreground leading-relaxed">
                                Share your trades and earn performance fees from followers
                              </p>
                            </div>
                            <Button
                              className="w-full h-11 bg-gradient-to-r from-purple-600 to-primary hover:from-purple-700 hover:to-primary/90 shadow-lg shadow-purple-500/30"
                              asChild
                            >
                              <Link href="/onboarding?type=provider">
                                Get Started
                                <ArrowRight className="ml-2 h-4 w-4" />
                              </Link>
                            </Button>
                          </CardContent>
                        </Card>
                      )}

                      {/* Stats summary card */}
                      <Card className="border-border/50 bg-gradient-to-br from-success/5 to-card">
                        <CardContent className="p-6 space-y-4">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">{monthlyStats.label}</span>
                            <Badge className="bg-success/10 text-success border-success/20">
                              <ArrowUpRight className="h-3 w-3 mr-1" />
                              {formatPercent(monthlyStats.pctChange)}
                            </Badge>
                          </div>
                          <div className="space-y-3">
                            <div className="flex items-center justify-between">
                              <span className="text-sm">Profit</span>
                              <span className="font-bold text-success">{formatCurrency(monthlyStats.profit)}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-sm">Trades</span>
                              <span className="font-bold">{formatNumber(monthlyStats.trades)}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-sm">Win Rate</span>
                              <span className="font-bold">{formatPercent(monthlyStats.winRate)}</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  </div>
                </div>
              )}

              {activeView === "trades" && (
                <Card className="border-border/50 shadow-xl">
                  <CardHeader className="border-b">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-2xl">My Trading Activity</CardTitle>
                      <Badge variant="outline" className="text-sm font-semibold">
                        {formatNumber(filteredTrades.length)} trades
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-6 space-y-4">
                    <div className="flex flex-wrap items-center gap-3 justify-between">
                      <div className="flex flex-wrap gap-3">
                        <Select value={tradeExchangeFilter} onValueChange={setTradeExchangeFilter}>
                          <SelectTrigger className="w-[160px]">
                            <SelectValue placeholder="Exchange" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Exchanges</SelectItem>
                            {tradeExchangeOptions.map((exchange) => (
                              <SelectItem key={exchange} value={exchange}>
                                {exchange}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Select value={tradeVerificationFilter} onValueChange={setTradeVerificationFilter}>
                          <SelectTrigger className="w-[160px]">
                            <SelectValue placeholder="Verification" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Verification</SelectItem>
                            {tradeVerificationOptions.map((type) => (
                              <SelectItem key={type} value={type}>
                                {type}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <span className="text-xs text-muted-foreground">Showing {paginatedTrades.length} of {filteredTrades.length}</span>
                    </div>

                    {dashboardLoading && renderLoadingState("Loading your recent trades...")}
                    {!dashboardLoading && !hasTrades && (
                      <div className="text-center py-16 text-muted-foreground">
                        <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No recent trades available</p>
                      </div>
                    )}
                    {paginatedTrades.map((trade: Trade) => (
                      <div
                        key={trade.id}
                        className="flex items-center justify-between p-6 border-2 border-border/50 rounded-2xl hover:border-primary/30 hover:shadow-lg transition-all duration-300 group"
                      >
                        <div className="flex items-center gap-5">
                          <div
                            className={`h-14 w-14 rounded-2xl flex items-center justify-center ${trade.pnl > 0
                              ? "bg-success/10 group-hover:bg-success/20"
                              : "bg-destructive/10 group-hover:bg-destructive/20"
                              } transition-colors`}
                          >
                            {trade.pnl > 0 ? (
                              <TrendingUp className="h-7 w-7 text-success" />
                            ) : (
                              <TrendingDown className="h-7 w-7 text-destructive" />
                            )}
                          </div>
                          <div>
                            <div className="font-bold text-lg mb-1.5">
                              {trade.asset_in} → {trade.asset_out}
                            </div>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <span>{trade.exchange}</span>
                              {trade.chain && (
                                <>
                                  <span>•</span>
                                  <span>{trade.chain}</span>
                                </>
                              )}
                              <span>•</span>
                              <span>{formatDateTime(trade.timestamp)}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-8">
                          <div className="text-right">
                            <div className={`font-bold text-2xl ${trade.pnl > 0 ? "text-success" : "text-destructive"}`}>
                              {trade.pnl > 0 ? "+" : ""}{formatCurrency(trade.pnl)}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {trade.pnl_percentage > 0 ? "+" : ""}
                              {formatPercent(trade.pnl_percentage)}
                            </div>
                          </div>

                          <VerificationBadge type={trade.verification_type} showLabel={false} />

                          {trade.tx_hash && (
                            <Button variant="ghost" size="icon" className="h-10 w-10" asChild>
                              <a href={`https://arbiscan.io/tx/${trade.tx_hash}`} target="_blank" rel="noopener noreferrer">
                                <ExternalLink className="h-5 w-5" />
                              </a>
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                    {renderPagination(tradesPage, totalTradePages, setTradesPage)}
                  </CardContent>
                </Card>
              )}

              {activeView === "copied" && !isTrader && (
                <Card className="border-border/50 shadow-xl">
                  <CardHeader className="border-b">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-2xl">Copied Trades</CardTitle>
                      <Badge variant="outline" className="text-sm font-semibold">
                        {formatNumber(filteredExecutions.length)} executions
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-6 space-y-4">
                    <div className="flex flex-wrap items-center gap-3 justify-between">
                      <div className="flex flex-wrap gap-3">
                        <Select value={executionStatusFilter} onValueChange={setExecutionStatusFilter}>
                          <SelectTrigger className="w-[160px]">
                            <SelectValue placeholder="Status" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Statuses</SelectItem>
                            {executionStatusOptions.map((status) => (
                              <SelectItem key={status} value={status}>
                                {status}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Select value={executionExchangeFilter} onValueChange={setExecutionExchangeFilter}>
                          <SelectTrigger className="w-[160px]">
                            <SelectValue placeholder="Exchange" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Exchanges</SelectItem>
                            {executionExchangeOptions.map((exchange) => (
                              <SelectItem key={exchange} value={exchange}>
                                {exchange}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <span className="text-xs text-muted-foreground">Showing {paginatedExecutions.length} of {filteredExecutions.length}</span>
                    </div>

                    {executionsLoading && renderLoadingState("Syncing execution feed...")}
                    {!executionsLoading && !hasCopiedTrades && (
                      <div className="text-center py-16 text-muted-foreground">
                        <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No copied trades yet—start following a trader to see activity here.</p>
                      </div>
                    )}
                    {paginatedExecutions.map((execution) => (
                      <div
                        key={execution.id}
                        className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between p-6 border-2 border-border/50 rounded-2xl hover:border-primary/30 hover:shadow-lg transition-all duration-300"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center gap-3 text-sm text-muted-foreground">
                            <Badge variant="secondary" className="uppercase tracking-[2px]">
                              {execution.exchange}
                            </Badge>
                            <span>{execution.symbol}</span>
                            <span>•</span>
                            <span>{formatDateTime(execution.created_at)}</span>
                          </div>
                          <div className="text-lg font-semibold">
                            Copying <Link href={`/trader/${execution.trader_id}`} className="text-primary hover:underline">#{shortenIdentifier(execution.trader_id, { prefixLength: 6, suffixLength: 0, separator: "" })}</Link>
                          </div>
                          <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
                            <span>Side: <strong className="text-foreground uppercase">{execution.side}</strong></span>
                            <span>Qty: <strong className="text-foreground">{execution.quantity.toLocaleString()}</strong></span>
                            {execution.executed_price && (
                              <span>Price: <strong className="text-foreground">{formatCurrency(execution.executed_price)}</strong></span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-6">
                          <div className="text-right">
                            <div className={`text-xl font-bold ${execution.pnl && execution.pnl > 0 ? "text-success" : execution.pnl && execution.pnl < 0 ? "text-destructive" : "text-muted-foreground"}`}>
                              {execution.pnl ? `${execution.pnl > 0 ? "+" : ""}${formatCurrency(execution.pnl)}` : "Pending"}
                            </div>
                            <div className="text-xs text-muted-foreground capitalize">{execution.status}</div>
                          </div>
                          <Badge variant={execution.status === "completed" ? "secondary" : execution.status === "failed" ? "destructive" : "outline"} className="capitalize">
                            {execution.status}
                          </Badge>
                        </div>
                      </div>
                    ))}
                    {renderPagination(executionsPage, totalExecutionPages, setExecutionsPage)}
                  </CardContent>
                </Card>
              )}

              {activeView === "following" && !isTrader && (
                <div className="space-y-4">
                  <div className="flex flex-wrap items-center gap-3 justify-between">
                    <Select value={subscriptionStatusFilter} onValueChange={setSubscriptionStatusFilter}>
                      <SelectTrigger className="w-[200px]">
                        <SelectValue placeholder="Status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Statuses</SelectItem>
                        {subscriptionStatusOptions.map((status) => (
                          <SelectItem key={status} value={status}>
                            {status}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <span className="text-xs text-muted-foreground">Showing {paginatedSubscriptions.length} of {filteredSubscriptions.length}</span>
                  </div>

                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {subscriptionsLoading && renderLoadingState("Loading subscriptions...")}
                    {!subscriptionsLoading && !hasFollowing && (
                      <Card className="sm:col-span-2 lg:col-span-3 border-dashed border-2 border-border/60">
                        <CardContent className="py-16 text-center space-y-4 text-muted-foreground">
                          <Users className="h-10 w-10 mx-auto opacity-60" />
                          <p className="text-base font-medium">You aren't following any traders yet.</p>
                          <p className="text-sm">Browse the marketplace to start copying signals.</p>
                          <Button asChild variant="default" className="mt-2">
                            <Link href="/marketplace">Find Traders</Link>
                          </Button>
                        </CardContent>
                      </Card>
                    )}
                    {!subscriptionsLoading && hasFollowing && paginatedSubscriptions.map((sub: Subscription) => (
                      <Card
                        key={sub.id}
                        className="border-2 border-border/50 hover:border-primary/30 hover:shadow-2xl transition-all duration-300"
                      >
                        <CardContent className="p-6 space-y-5">
                          <div className="flex items-start justify-between">
                            <div>
                              <p className="text-xs uppercase tracking-[3px] text-muted-foreground">Trader</p>
                              <Link href={`/trader/${sub.trader_id}`} className="text-lg font-bold text-foreground hover:text-primary transition">
                                {shortenIdentifier(sub.trader_id, { prefixLength: 8, suffixLength: 0, separator: "" })}
                              </Link>
                              <p className="text-xs text-muted-foreground">Following since {new Date(sub.created_at).toLocaleDateString()}</p>
                            </div>
                            <Badge variant={sub.status === "active" ? "secondary" : "outline"} className="capitalize">
                              {sub.status}
                            </Badge>
                          </div>

                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <p className="text-muted-foreground text-xs">Max Capital %</p>
                              <p className="font-semibold">{sub.max_capital_pct}%</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground text-xs">Max Position Size</p>
                              <p className="font-semibold">{sub.max_position_size ? formatCurrency(sub.max_position_size) : "—"}</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground text-xs">Stop Loss %</p>
                              <p className="font-semibold">{sub.stop_loss_pct ?? "—"}</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground text-xs">Take Profit %</p>
                              <p className="font-semibold">{sub.take_profit_pct ?? "—"}</p>
                            </div>
                          </div>

                          <div className="flex gap-3">
                            <Button variant="default" className="flex-1" asChild>
                              <Link href={`/copy/${sub.trader_id}`}>Adjust Settings</Link>
                            </Button>
                            <Button variant="outline" className="flex-1" asChild>
                              <Link href={`/trader/${sub.trader_id}`}>
                                View Profile
                                <ExternalLink className="ml-2 h-4 w-4" />
                              </Link>
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {renderPagination(followingPage, totalFollowingPages, setFollowingPage)}
                </div>
              )}

              {activeView === "subscribers" && isTrader && (
                <div className="space-y-6">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <CardTitle className="text-2xl">Active Subscribers</CardTitle>
                      <CardDescription>Copy traders currently mirroring your strategies.</CardDescription>
                    </div>
                    <Badge variant="outline" className="text-sm">
                      {followers.length} total
                    </Badge>
                  </div>

                  {subscriptionsLoading && renderLoadingState("Loading subscribers...")}
                  {subscriptionsError && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{subscriptionsError}</AlertDescription>
                    </Alert>
                  )}

                  {!subscriptionsLoading && followers.length === 0 && !subscriptionsError && (
                    <Card className="border-dashed border-2 border-border/60">
                      <CardContent className="py-10 text-center text-muted-foreground">
                        No subscribers yet. Share your public profile to attract copy traders.
                      </CardContent>
                    </Card>
                  )}

                  <div className="grid gap-4">
                    {followers.map((follower: TraderFollower) => (
                      <Card key={follower.follower_id} className="border-border/60">
                        <CardContent className="p-4 flex items-center justify-between">
                          <div>
                            <p className="font-semibold">
                              {follower.follower_email || shortenIdentifier(follower.follower_address) || "Anonymous"}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Subscribed {new Date(follower.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <Badge variant={follower.status === "active" ? "default" : "outline"} className="capitalize">
                            {follower.status}
                          </Badge>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </ProtectedRoute>
  )
}
