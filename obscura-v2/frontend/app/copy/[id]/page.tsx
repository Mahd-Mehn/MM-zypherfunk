"use client"

import { useState } from "react"
import Link from "next/link"
import { Header } from "@/components/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { VerificationBadge } from "@/components/verification-badge"
import TraderCard from "@/components/reusable/TraderCard"
import {
  ArrowLeft,
  CheckCircle2,
  Info,
  TrendingUp,
  Shield,
  Sparkles,
  AlertTriangle,
  DollarSign,
  Loader2,
  AlertCircle,
  TrendingDown,
} from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useTraderProfile, useTraderPerformance, useTraderTrades } from "@/hooks/use-traders"
import { Badge } from "@/components/ui/badge"
import { shortenIdentifier } from "@/lib/utils"
import { subscriptionsAPI } from "@/lib/api"
import type { Subscription } from "@/lib/api/types"
import { useToast } from "@/components/ui/use-toast"

const formatCurrency = (value?: number | string, fraction: number = 0) => {
  if (value === undefined || value === null) return "—"
  const numeric = typeof value === "string" ? Number.parseFloat(value) : value
  if (Number.isNaN(numeric)) return String(value)
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: fraction,
    maximumFractionDigits: fraction,
  }).format(numeric)
}

const formatPercent = (value?: number, digits: number = 1) => {
  if (value === undefined || value === null || Number.isNaN(value)) return "—"
  return `${value.toFixed(digits)}%`
}

const parseNumberOrUndefined = (value?: string | number | null) => {
  if (value === undefined || value === null) return undefined
  const numeric = typeof value === "string" ? Number.parseFloat(value) : value
  return Number.isFinite(numeric) ? numeric : undefined
}

export default function CopyTradingPage({ params }: { params: { id: string } }) {
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
  } = useTraderTrades(traderId, 5)

  const [copyAmount, setCopyAmount] = useState("1000")
  const [copyPercentage, setCopyPercentage] = useState([50])
  const [autoRenew, setAutoRenew] = useState(true)
  const [stopLoss, setStopLoss] = useState("10")
  const [takeProfit, setTakeProfit] = useState("20")
  const [isProcessing, setIsProcessing] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const { toast } = useToast()

  const heroLoading = traderLoading || performanceLoading
  const dataErrors = [traderError, performanceError, tradesError].filter(Boolean) as string[]

  if (!trader && traderLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto px-4 py-20 text-center">
          <Loader2 className="mx-auto mb-4 h-10 w-10 animate-spin text-primary" />
          <div className="text-lg text-muted-foreground">Loading trader...</div>
        </div>
      </div>
    )
  }

  if (!trader) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto px-4 py-20 text-center space-y-4">
          <h1 className="text-2xl SAN font-bold">Trader Not Found</h1>
          {traderError && <p className="text-muted-foreground">{traderError}</p>}
          <Button asChild>
            <Link href="/marketplace">Back to Marketplace</Link>
          </Button>
        </div>
      </div>
    )
  }

  const handleCopyTrade = async () => {
    const rawTraderId = trader?.id ?? (trader as any)?.trader_id ?? traderId
    const resolvedTraderId = rawTraderId ? String(rawTraderId) : undefined

    if (!resolvedTraderId) {
      toast({
        title: "Missing trader information",
        description: "We couldn't determine which trader to copy. Please refresh and try again.",
        variant: "destructive",
      })
      return
    }

    setIsProcessing(true)
    try {
      const payload = {
        trader_id: resolvedTraderId,
        max_capital_pct: copyPercentage[0],
        max_position_size: parseNumberOrUndefined(copyAmount),
        stop_loss_pct: parseNumberOrUndefined(stopLoss),
        take_profit_pct: parseNumberOrUndefined(takeProfit),
      }

      const result = await subscriptionsAPI.createSubscription(payload)
      setSubscription(result)
      setIsSuccess(true)
      toast({
        title: "Copy trading activated",
        description: `${trader.display_name} is now being copied.`,
      })
    } catch (error: any) {
      console.error("Failed to create subscription", error)
      toast({
        title: "Unable to start copying",
        description: error?.message || "Please try again later.",
        variant: "destructive",
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const performanceFee = trader?.performance_fee ?? 0
  const estimatedFee = (Number.parseFloat(copyAmount || "0") * (performanceFee / 100)).toFixed(2)
  const maxLoss = (Number.parseFloat(copyAmount) * (Number.parseFloat(stopLoss) / 100)).toFixed(2)
  const maxProfit = (Number.parseFloat(copyAmount) * (Number.parseFloat(takeProfit) / 100)).toFixed(2)

  const recentTrade = trades?.[0]
  const winRate = performance?.win_rate ?? trader?.win_rate
  const verificationTypes = trader?.verification_types?.length ? trader.verification_types : ["Verification pending"]
  const traderChains = trader?.chains ?? []
  const traderExchanges = trader?.exchanges ?? []

  return (
    <div className="min-h-screen bg-background">
      <Header />

      {isSuccess ? (
        <div className="container mx-auto px-4 lg:px-8 py-20 max-w-3xl">
          <Card className="border-2 border-success/50 bg-gradient-to-br from-success/10 to-success/5">
            <CardContent className="p-12 lg:p-20 text-center space-y-8">
              <div className="h-24 w-24 rounded-full bg-success/10 flex items-center justify-center mx-auto ring-8 ring-success/20">
                <CheckCircle2 className="h-12 w-12 text-success" />
              </div>
              <div>
                <h2 className="text-3xl lg:text-4xl font-bold mb-4">Copy Trading Activated!</h2>
                <p className="text-muted-foreground text-lg max-w-md mx-auto leading-relaxed">
                  You're now copying trades from{" "}
                  <span className="font-semibold text-foreground">{trader.display_name}</span>. You'll receive
                  notifications for each trade execution.
                </p>
              </div>
              <div className="bg-card border border-border/50 rounded-xl p-6 space-y-3 text-left max-w-md mx-auto">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Allocated Amount</span>
                  <span className="font-bold">${Number.parseFloat(copyAmount).toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Copy Percentage</span>
                  <span className="font-bold text-primary">{copyPercentage[0]}%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Risk Management</span>
                  <span className="font-bold">
                    -{stopLoss}% / +{takeProfit}%
                  </span>
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
                <Button asChild className="flex-1 h-12">
                  <Link href="/dashboard">
                    <Sparkles className="mr-2 h-5 w-5" />
                    Go to Dashboard
                  </Link>
                </Button>
                <Button variant="outline" asChild className="flex-1 h-12 bg-transparent">
                  <Link href="/marketplace">Browse More Traders</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <>
          <div className="relative border-b bg-gradient-to-br from-primary/5 via-background to-background overflow-hidden">
            <div className="absolute inset-0 bg-[linear-gradient(to_right,hsl(var(--border))_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border))_1px,transparent_1px)] bg-[size:4rem_4rem] opacity-50" />

            <div className="container relative mx-auto px-4 lg:px-8 py-8 lg:py-12">
              <Button variant="ghost" size="sm" asChild className="mb-6">
                <Link href={`/trader/${trader.id}`}>
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to Profile
                </Link>
              </Button>

              <div className="grid gap-8 lg:grid-cols-[1.1fr_360px] items-start">
                <div className="space-y-5">
                  <div>
                    <h1 className="text-4xl lg:text-5xl font-bold mb-4">Copy Trading Setup</h1>
                    <p className="text-lg text-muted-foreground">
                      Configure your parameters to start copying{" "}
                      <span className="font-semibold text-foreground">{trader.display_name}</span>
                    </p>
                  </div>

                  {heroLoading && (
                    <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/80">
                      <Loader2 className="h-4 w-4 animate-spin text-primary" />
                      Syncing latest performance data...
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

                  <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
                    <span className="font-semibold text-foreground">{shortenIdentifier(trader.address)}</span>
                    <span>• Joined {new Date(trader.joined_date).toLocaleDateString()}</span>
                    <span>• {trader.followers?.toLocaleString() ?? "0"} followers</span>
                    {verificationTypes.map((type, index) => (
                      <span key={`verification-${index}`}>• {type}</span>
                    ))}
                    {traderChains.map((chain, index) => (
                      <span key={`chain-${index}`}>• {chain}</span>
                    ))}
                    {traderExchanges.map((exchange, index) => (
                      <span key={`exchange-${index}`}>• {exchange}</span>
                    ))}
                  </div>
                </div>

                <div className="flex justify-center lg:justify-end">
                  <TraderCard trader={trader} highlight className="w-full max-w-xs lg:max-w-sm" />
                </div>
              </div>
            </div>
          </div>

          <div className="container mx-auto px-4 lg:px-8 py-8 lg:py-12 max-w-7xl">
            <div className="grid lg:grid-cols-3 gap-8">
              {/* Main configuration */}
              <div className="lg:col-span-2 space-y-6">
                {/* Trader stats strip */}
                <Card className="border-primary/30 bg-gradient-to-br from-primary/5 to-background">
                  <CardContent className="p-6 lg:p-8">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                      <div>
                        <p className="text-sm text-muted-foreground">Win Rate</p>
                        <p className="text-2xl font-bold text-success">{formatPercent(winRate)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Total PnL</p>
                        <p className="text-2xl font-bold text-success">{formatCurrency(trader.total_pnl)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Followers</p>
                        <p className="text-2xl font-bold">{trader.followers.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Performance Fee</p>
                        <p className="text-2xl font-bold">{trader.performance_fee}%</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Copy amount */}
                <Card className="border-border/50">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <DollarSign className="h-5 w-5 text-primary" />
                      Copy Amount
                    </CardTitle>
                    <CardDescription>Set the total amount you want to allocate for copying trades</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="space-y-3">
                      <Label htmlFor="amount" className="text-base">
                        Amount (USDC)
                      </Label>
                      <Input
                        id="amount"
                        type="number"
                        placeholder="1000"
                        value={copyAmount}
                        onChange={(e) => setCopyAmount(e.target.value)}
                        className="h-12 text-lg"
                      />
                      <p className="text-sm text-muted-foreground">Minimum: $100 USDC</p>
                    </div>

                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <Label className="text-base">Position Size</Label>
                        <span className="text-2xl font-bold text-primary">{copyPercentage[0]}%</span>
                      </div>
                      <Slider
                        value={copyPercentage}
                        onValueChange={setCopyPercentage}
                        max={100}
                        step={5}
                        className="py-4"
                      />
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        Copy {copyPercentage[0]}% of the trader's position size relative to your allocated amount. Lower
                        percentages reduce risk but also potential returns.
                      </p>
                    </div>
                  </CardContent>
                </Card>

                {/* Risk management */}
                <Card className="border-border/50">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="h-5 w-5 text-primary" />
                      Risk Management
                    </CardTitle>
                    <CardDescription>
                      Protect your capital with automated stop-loss and take-profit levels
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-3">
                        <Label htmlFor="stopLoss" className="text-base">
                          Stop Loss (%)
                        </Label>
                        <Input
                          id="stopLoss"
                          type="number"
                          placeholder="10"
                          value={stopLoss}
                          onChange={(e) => setStopLoss(e.target.value)}
                          className="h-12 text-lg"
                        />
                        <p className="text-sm text-muted-foreground">Max loss: ${maxLoss}</p>
                      </div>

                      <div className="space-y-3">
                        <Label htmlFor="takeProfit" className="text-base">
                          Take Profit (%)
                        </Label>
                        <Input
                          id="takeProfit"
                          type="number"
                          placeholder="20"
                          value={takeProfit}
                          onChange={(e) => setTakeProfit(e.target.value)}
                          className="h-12 text-lg"
                        />
                        <p className="text-sm text-muted-foreground">Max profit: ${maxProfit}</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                      <div className="space-y-1">
                        <Label htmlFor="autoRenew" className="text-base font-semibold">
                          Auto-Renew Positions
                        </Label>
                        <p className="text-sm text-muted-foreground">
                          Continue copying after reaching profit/loss limits
                        </p>
                      </div>
                      <Switch id="autoRenew" checked={autoRenew} onCheckedChange={setAutoRenew} />
                    </div>
                  </CardContent>
                </Card>

                <Alert className="border-primary/30 bg-primary/5">
                  <Info className="h-5 w-5 text-primary" />
                  <AlertDescription className="leading-relaxed">
                    <strong>Privacy Notice:</strong> Your copy trading activity is completely private. The trader will
                    only see aggregate follower counts, not individual positions, amounts, or identities.
                  </AlertDescription>
                </Alert>
              </div>

              {/* Sidebar summary */}
              <div className="space-y-6">
                <Card className="sticky top-24 border-border/50 space-y-6 p-6">
                  <TraderCard trader={trader} className="w-full" />
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Allocated Amount</span>
                      <span className="font-bold">{formatCurrency(Number.parseFloat(copyAmount || "0"), 0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Position Size</span>
                      <span className="font-bold text-primary">{copyPercentage[0]}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Stop Loss</span>
                      <span className="font-bold text-destructive">-{stopLoss}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Take Profit</span>
                      <span className="font-bold text-success">+{takeProfit}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Auto-Renew</span>
                      <span className="font-bold">{autoRenew ? "Enabled" : "Disabled"}</span>
                    </div>
                  </div>

                  <div className="pt-4 border-t space-y-4">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Performance Fee</span>
                      <span className="font-bold">{performanceFee}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Est. Fee (on profit)</span>
                      <span className="font-bold">${estimatedFee}</span>
                    </div>
                  </div>

                  <div className="space-y-3 rounded-xl border border-border/60 bg-muted/30 p-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Recent Trade</span>
                      {recentTrade ? (
                        <span className="font-semibold">
                          {recentTrade.asset_in} → {recentTrade.asset_out}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">No executions yet</span>
                      )}
                    </div>
                    {recentTrade && (
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{new Date(recentTrade.timestamp).toLocaleString()}</span>
                        <span className={recentTrade.pnl >= 0 ? "text-success font-semibold" : "text-destructive font-semibold"}>
                          {recentTrade.pnl >= 0 ? "+" : ""}${recentTrade.pnl.toFixed(2)}
                        </span>
                      </div>
                    )}
                    {tradesLoading && <LoadingStrip label="Loading trade feed..." />}
                  </div>

                  <Alert className="bg-success/5 border-success/20">
                    <TrendingUp className="h-4 w-4 text-success" />
                    <AlertDescription className="text-xs leading-relaxed">
                      Fees are only charged on profitable trades and settled in ZEN on Horizen L3
                    </AlertDescription>
                  </Alert>

                  <Button
                    className="w-full h-12 shadow-lg shadow-primary/25"
                    size="lg"
                    onClick={handleCopyTrade}
                    disabled={isProcessing}
                  >
                    {isProcessing ? (
                      "Processing..."
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-5 w-5" />
                        Start Copying
                      </>
                    )}
                  </Button>

                  <p className="text-xs text-muted-foreground text-center leading-relaxed">
                    By continuing, you agree to the copy trading terms and conditions
                  </p>
                </Card>

                <Card className="border-border/50">
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Shield className="h-4 w-4" />
                      Verification Details
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {verificationTypes.map((type: string) => (
                      <div key={type} className="flex items-start gap-3">
                        <CheckCircle2 className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                        <span className="text-sm text-muted-foreground leading-relaxed">
                          {type === "ZK"
                            ? "All DEX trades verified with zero-knowledge proofs"
                            : "CEX trades attested in secure hardware enclaves (AWS Nitro)"}
                        </span>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Alert className="border-warning/30 bg-warning/5">
                  <AlertTriangle className="h-4 w-4 text-warning" />
                  <AlertDescription className="text-xs leading-relaxed">
                    <strong>Risk Warning:</strong> Copy trading involves risk. Past performance does not guarantee
                    future results. Only invest what you can afford to lose.
                  </AlertDescription>
                </Alert>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function LoadingStrip({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border/50 px-4 py-3 text-xs text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" />
      {label}
    </div>
  )
}
