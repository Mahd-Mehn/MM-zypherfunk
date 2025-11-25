"use client"

import { useTraders } from "@/hooks/use-traders"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { shortenIdentifier } from "@/lib/utils"
import { Skeleton } from "@/components/ui/skeleton"
import { TrendingUp, Users, Award } from "lucide-react"

export function TraderList() {
  const { traders, loading, error } = useTraders({ limit: 10 })

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-3/4" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-20 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-destructive">Failed to load traders: {error}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {traders.map((trader) => (
        <Card key={trader.id} className="hover:border-primary transition-colors">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-lg">{trader.display_name}</CardTitle>
                <p className="text-sm text-muted-foreground truncate">
                  {shortenIdentifier(trader.address)}
                </p>
              </div>
              <Badge variant={trader.trust_tier === 1 ? "default" : "secondary"}>
                Tier {trader.trust_tier}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {trader.win_rate.toFixed(1)}%
                </div>
                <div className="text-xs text-muted-foreground">Win Rate</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  ${(trader.total_pnl / 1000).toFixed(0)}k
                </div>
                <div className="text-xs text-muted-foreground">Total PnL</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{trader.followers}</div>
                <div className="text-xs text-muted-foreground">Followers</div>
              </div>
            </div>

            <div className="flex flex-wrap gap-1">
              {trader.verification_types?.map((type) => (
                <Badge key={type} variant="outline" className="text-xs">
                  {type}
                </Badge>
              ))}
            </div>

            <Link href={`/trader/${trader.id}`}>
              <Button className="w-full" variant="outline">
                View Profile
              </Button>
            </Link>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
