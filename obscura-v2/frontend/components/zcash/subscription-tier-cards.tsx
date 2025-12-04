"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, Zap, Shield, Users, Crown, ArrowRight } from "lucide-react"
import { SUBSCRIPTION_TIERS } from "@/lib/zcash/payment"
import { formatZEC } from "@/lib/zcash/payment"

interface SubscriptionTier {
  id: keyof typeof SUBSCRIPTION_TIERS
  icon: React.ReactNode
  popular?: boolean
}

const TIER_ICONS: SubscriptionTier[] = [
  { id: "basic", icon: <Users className="h-6 w-6" /> },
  { id: "pro", icon: <Zap className="h-6 w-6" />, popular: true },
  { id: "premium", icon: <Crown className="h-6 w-6" /> },
]

interface SubscriptionTierCardProps {
  onSelectTier: (tier: keyof typeof SUBSCRIPTION_TIERS) => void
  selectedTier?: keyof typeof SUBSCRIPTION_TIERS
  loading?: boolean
}

export function SubscriptionTierCards({
  onSelectTier,
  selectedTier,
  loading,
}: SubscriptionTierCardProps) {
  return (
    <div className="grid md:grid-cols-3 gap-6">
      {TIER_ICONS.map(({ id, icon, popular }) => {
        const tier = SUBSCRIPTION_TIERS[id]
        const isSelected = selectedTier === id

        return (
          <Card
            key={id}
            className={`relative transition-all duration-300 ${
              isSelected
                ? "border-2 border-primary scale-105 shadow-xl"
                : "hover:border-primary/50 hover:shadow-lg"
            } ${popular ? "ring-2 ring-primary/20" : ""}`}
          >
            {popular && (
              <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary">
                Most Popular
              </Badge>
            )}

            <CardHeader className="text-center pb-2">
              <div
                className={`h-14 w-14 rounded-full mx-auto flex items-center justify-center mb-2 ${
                  isSelected
                    ? "bg-primary text-primary-foreground"
                    : "bg-primary/10 text-primary"
                }`}
              >
                {icon}
              </div>
              <CardTitle className="text-xl">{tier.name}</CardTitle>
              <CardDescription>{tier.description}</CardDescription>
            </CardHeader>

            <CardContent className="text-center space-y-4">
              <div className="space-y-1">
                <div className="text-4xl font-bold">{formatZEC(tier.price)} ZEC</div>
                <div className="text-sm text-muted-foreground">per month</div>
              </div>

              <ul className="space-y-2 text-left">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>

            <CardFooter>
              <Button
                className="w-full"
                variant={isSelected ? "default" : "outline"}
                onClick={() => onSelectTier(id)}
                disabled={loading}
              >
                {isSelected ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Selected
                  </>
                ) : (
                  <>
                    Choose {tier.name}
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>
        )
      })}
    </div>
  )
}

interface SubscriptionStatusProps {
  subscription: {
    tier: keyof typeof SUBSCRIPTION_TIERS
    status: "active" | "pending" | "expired"
    expiresAt?: Date
    renewalAddress?: string
  } | null
}

export function SubscriptionStatus({ subscription }: SubscriptionStatusProps) {
  if (!subscription) {
    return (
      <Card className="bg-muted/50">
        <CardContent className="p-6 text-center">
          <Shield className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="font-semibold text-lg mb-2">No Active Subscription</h3>
          <p className="text-muted-foreground">
            Subscribe to start copy trading verified traders
          </p>
        </CardContent>
      </Card>
    )
  }

  const tier = SUBSCRIPTION_TIERS[subscription.tier]
  const statusColors = {
    active: "bg-success/10 text-success border-success/20",
    pending: "bg-warning/10 text-warning border-warning/20",
    expired: "bg-destructive/10 text-destructive border-destructive/20",
  }

  return (
    <Card className="border-primary/20">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
              <Shield className="h-6 w-6 text-primary" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-lg">{tier.name} Plan</h3>
                <Badge className={statusColors[subscription.status]}>
                  {subscription.status}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                {formatZEC(tier.price)} ZEC/month
              </p>
            </div>
          </div>

          {subscription.expiresAt && (
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Expires</div>
              <div className="font-medium">
                {new Date(subscription.expiresAt).toLocaleDateString()}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
