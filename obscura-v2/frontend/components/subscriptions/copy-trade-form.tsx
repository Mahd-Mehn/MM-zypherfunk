"use client"

import { useState } from "react"
import { useSubscriptions } from "@/hooks/use-subscriptions"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, TrendingUp } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"

interface CopyTradeFormProps {
  traderId: string
  traderName: string
}

export function CopyTradeForm({ traderId, traderName }: CopyTradeFormProps) {
  const [maxCapitalPct, setMaxCapitalPct] = useState(10)
  const [maxPositionSize, setMaxPositionSize] = useState("")
  const [stopLossPct, setStopLossPct] = useState("")
  const [takeProfitPct, setTakeProfitPct] = useState("")
  const [loading, setLoading] = useState(false)

  const { createSubscription, error } = useSubscriptions()
  const { toast } = useToast()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      await createSubscription({
        trader_id: traderId,
        // Map to new backend fields
        proportion_percent: maxCapitalPct,
        max_position_usd: maxPositionSize ? parseFloat(maxPositionSize) : undefined,
        copy_mode: "proportional",
        // Keep legacy fields for now just in case
        max_capital_pct: maxCapitalPct,
        max_position_size: maxPositionSize ? parseFloat(maxPositionSize) : undefined,
        stop_loss_pct: stopLossPct ? parseFloat(stopLossPct) : undefined,
        take_profit_pct: takeProfitPct ? parseFloat(takeProfitPct) : undefined,
      })

      toast({
        title: "Copy Trading Activated",
        description: `You are now copying ${traderName}'s trades`,
      })

      router.push("/dashboard")
    } catch (err: any) {
      toast({
        title: "Failed to Activate",
        description: err.message,
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <div className="space-y-2">
          <Label>Max Capital Per Trade: {maxCapitalPct}%</Label>
          <Slider
            value={[maxCapitalPct]}
            onValueChange={(value) => setMaxCapitalPct(value[0])}
            min={1}
            max={100}
            step={1}
            className="w-full"
          />
          <p className="text-sm text-muted-foreground">
            Maximum percentage of your capital to allocate per trade
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="maxPosition">Max Position Size (USD) - Optional</Label>
          <Input
            id="maxPosition"
            type="number"
            placeholder="e.g., 10000"
            value={maxPositionSize}
            onChange={(e) => setMaxPositionSize(e.target.value)}
            min="0"
            step="0.01"
          />
          <p className="text-sm text-muted-foreground">
            Maximum position size in USD (leave empty for no limit)
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="stopLoss">Stop Loss % - Optional</Label>
            <Input
              id="stopLoss"
              type="number"
              placeholder="e.g., 5"
              value={stopLossPct}
              onChange={(e) => setStopLossPct(e.target.value)}
              min="0"
              max="100"
              step="0.1"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="takeProfit">Take Profit % - Optional</Label>
            <Input
              id="takeProfit"
              type="number"
              placeholder="e.g., 15"
              value={takeProfitPct}
              onChange={(e) => setTakeProfitPct(e.target.value)}
              min="0"
              max="1000"
              step="0.1"
            />
          </div>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Button type="submit" className="w-full" size="lg" disabled={loading}>
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Activating...
          </>
        ) : (
          <>
            <TrendingUp className="mr-2 h-4 w-4" />
            Start Copy Trading
          </>
        )}
      </Button>

      <p className="text-xs text-center text-muted-foreground">
        You can pause or cancel this subscription at any time from your dashboard
      </p>
    </form>
  )
}
