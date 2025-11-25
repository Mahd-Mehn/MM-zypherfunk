"use client"

import Link from "next/link"
import { Header } from "@/components/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { VerificationBadge } from "@/components/verification-badge"
import TraderCard from "@/components/reusable/TraderCard"
import {
  ArrowLeft,
  Copy,
  ExternalLink,
  TrendingUp,
  TrendingDown,
  Calendar,
  Users,
  Shield,
  Target,
  Activity,
  Award,
  Sparkles,
  Loader2,
  AlertCircle,
} from "lucide-react"
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts"
import { useTraderProfile, useTraderPerformance, useTraderTrades } from "@/hooks/use-traders"
import { shortenIdentifier } from "@/lib/utils"

const formatCurrency = (value?: number) => {
  if (value === undefined || value === null) return "—"
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value)
}

const formatPercent = (value?: number) => {
  if (value === undefined || value === null) return "—"
  return `${value.toFixed(1)}%`
}

export default function TraderProfilePage({ params }: { params: { id: string } }) {
  const traderId = params.id
  const {
    trader,
    loading: traderLoading,
    error: traderError,
  } = useTraderProfile(traderId)
  const {
    performance,
    loading: performanceLoading,
    error: performanceError,
  } = useTraderPerformance(traderId, "30d")
  const {
    trades,
    loading: tradesLoading,
    error: tradesError,
  } = useTraderTrades(traderId, 25)

  const performanceData = performance?.performance_data ?? []
  const heroLoading = traderLoading || performanceLoading
  const dataErrors = [traderError, performanceError, tradesError].filter(Boolean) as string[]

  if (!trader && traderLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto px-4 py-20 text-center">
          <Loader2 className="mx-auto mb-4 h-10 w-10 animate-spin text-primary" />
          <div className="text-lg text-muted-foreground">Loading trader profile...</div>
        </div>
      </div>
    )
  }

  if (!trader) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto px-4 py-20 text-center space-y-4">
          <h1 className="text-2xl font-bold">Trader Not Found</h1>
          {traderError && <p className="text-muted-foreground">{traderError}</p>}
          <Button asChild>
            <Link href="/marketplace">Back to Marketplace</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <div className="relative border-b bg-gradient-to-br from-primary/5 via-background to-background overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,hsl(var(--border))_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border))_1px,transparent_1px)] bg-[size:4rem_4rem] opacity-50" />
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />

        <div className="container relative mx-auto px-4 lg:px-8 py-8 lg:py-12">
          <Button variant="ghost" size="sm" asChild className="mb-6">
            <Link href="/marketplace">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Marketplace
            </Link>
          </Button>

          <div className="grid lg:grid-cols-3 gap-8">
            <div className="space-y-6">
              <TraderCard trader={trader ?? undefined} highlight className="w-full" />
              <Card className="border-primary/30 bg-gradient-to-br from-primary/5 via-primary/0 to-background">
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Win Rate</div>
                      <div className="text-3xl font-bold text-success">{formatPercent(trader?.win_rate)}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Followers</div>
                      <div className="flex items-center gap-2">
                        <Users className="h-5 w-5 text-muted-foreground" />
                        <span className="text-2xl font-bold">{trader?.followers.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Total PnL</div>
                      <div className="text-3xl font-bold text-success">{formatCurrency(trader?.total_pnl)}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Performance Fee</div>
                      <div className="text-2xl font-bold">{trader?.performance_fee}%</div>
                    </div>
                  </div>
                  <Button className="w-full h-12 shadow-lg shadow-primary/25" size="lg" asChild>
                    <Link href={`/copy/${trader?.id}`}>
                      <Sparkles className="mr-2 h-5 w-5" />
                      Copy This Trader
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            </div>

            <div className="lg:col-span-2 space-y-6">
              <div className="flex flex-col gap-6">
                <div className="flex items-center justify-between gap-4 flex-wrap">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h1 className="text-4xl lg:text-5xl font-bold">{trader.display_name}</h1>
                      {trader.trust_tier >= 3 && (
                        <Badge className="bg-primary/10 text-primary border-primary/20">
                          <Award className="h-3 w-3 mr-1" />
                          Top Trader
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <code className="px-3 py-1.5 bg-muted/50 backdrop-blur-sm rounded-lg text-xs font-mono border border-border/50">
                        {shortenIdentifier(trader.address)}
                      </code>
                      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => navigator.clipboard.writeText(trader.address)}>
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>

                {heroLoading && (
                  <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/80">
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                    Syncing live performance data...
                  </div>
                )}

                {dataErrors.length > 0 && (
                  <div className="flex items-start gap-3 rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    <AlertCircle className="h-5 w-5" />
                    <div>
                      <p className="font-semibold">Some trader data failed to load</p>
                      <p className="text-destructive/80">Showing cached data where available. Try refreshing.</p>
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap gap-2">
                  {trader.verification_types?.map((type: string) => (
                    <VerificationBadge key={type} type={type} />
                  ))}
                  <Badge variant="outline" className="gap-1.5">
                    <Shield className="h-3 w-3" />
                    Trust Tier {trader.trust_tier}
                  </Badge>
                </div>

                <p className="text-base text-muted-foreground leading-relaxed">{trader.bio}</p>

                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span>Joined {new Date(trader.joined_date).toLocaleDateString()}</span>
                </div>

                <div className="space-y-3">
                  {trader.chains && trader.chains.length > 0 && (
                    <div className="flex flex-wrap gap-2 items-center">
                      <span className="text-sm font-medium text-muted-foreground">Chains:</span>
                      {trader.chains.map((chain: string) => (
                        <Badge key={chain} variant="secondary" className="text-xs">
                          {chain}
                        </Badge>
                      ))}
                    </div>
                  )}
                  {trader.exchanges && trader.exchanges.length > 0 && (
                    <div className="flex flex-wrap gap-2 items-center">
                      <span className="text-sm font-medium text-muted-foreground">Exchanges:</span>
                      {trader.exchanges.map((exchange: string) => (
                        <Badge key={exchange} variant="secondary" className="text-xs">
                          {exchange}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 lg:px-8 py-8 lg:py-12">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
          {[
            { label: "Total Trades", value: trader.total_trades, icon: Activity, color: "text-foreground" },
            {
              label: "Verified Trades",
              value: trader.verified_trades,
              icon: Shield,
              color: "text-primary",
            },
            { label: "Avg Win", value: performance ? `${performance.win_rate?.toFixed(1)}%` : "—", icon: TrendingUp, color: "text-success" },
            { label: "Max Drawdown", value: performance ? `${performance.max_drawdown?.toFixed(1)}%` : "—", icon: TrendingDown, color: "text-destructive" },
          ].map((stat, i) => (
            <Card key={i} className="border-border/50 hover:shadow-lg transition-all duration-300 group">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <div className="text-sm font-medium text-muted-foreground">{stat.label}</div>
                  <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center group-hover:scale-110 transition-transform">
                    <stat.icon className={`h-5 w-5 ${stat.color}`} />
                  </div>
                </div>
                <div className={`text-3xl font-bold ${stat.color}`}>{stat.value}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="mb-8 border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl">Performance Overview</CardTitle>
              <Badge variant="outline" className="text-xs">
                Last 30 days
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-[350px] lg:h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={performanceData}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                  <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2.5}
                    fill="url(#colorValue)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl">Recent Verified Trades</CardTitle>
              <Badge variant="outline">{trades.length} trades</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {trades.length > 0 ? (
                trades.map((trade) => (
                  <div
                    key={trade.id}
                    className="flex items-center justify-between p-5 border border-border/50 rounded-xl hover:border-primary/30 hover:shadow-md transition-all duration-300 group"
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={`h-12 w-12 rounded-xl flex items-center justify-center ${
                          trade.pnl > 0
                            ? "bg-success/10 group-hover:bg-success/20"
                            : "bg-destructive/10 group-hover:bg-destructive/20"
                        } transition-colors`}
                      >
                        {trade.pnl > 0 ? (
                          <TrendingUp className="h-6 w-6 text-success" />
                        ) : (
                          <TrendingDown className="h-6 w-6 text-destructive" />
                        )}
                      </div>
                      <div>
                        <div className="font-bold text-base mb-1">
                          {trade.asset_in} → {trade.asset_out}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span>{trade.exchange}</span>
                          {trade.chain && (
                            <>
                              <span>•</span>
                              <span>{trade.chain}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <div className={`font-bold text-lg ${trade.pnl > 0 ? "text-success" : "text-destructive"}`}>
                          {trade.pnl > 0 ? "+" : ""}${trade.pnl.toLocaleString()}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {trade.pnl_percentage > 0 ? "+" : ""}
                          {trade.pnl_percentage}%
                        </div>
                      </div>

                      <VerificationBadge type={trade.verification_type} showLabel={false} />

                      {trade.tx_hash && (
                        <Button variant="ghost" size="icon" className="h-9 w-9" asChild>
                          <a href={`https://arbiscan.io/tx/${trade.tx_hash}`} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-16 text-muted-foreground">
                  <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No recent trades available</p>
                </div>
              )}
              {tradesLoading && renderLoadingState("Loading recent trades...")}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function renderLoadingState(label: string) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border/50 px-4 py-3 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" />
      {label}
    </div>
  )
}
