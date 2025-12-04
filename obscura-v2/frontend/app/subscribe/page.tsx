"use client"

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { Header } from "@/components/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import {
  Shield,
  Lock,
  CheckCircle2,
  ArrowLeft,
  AlertCircle,
  Loader2,
  Wallet,
  Clock,
  ExternalLink,
} from "lucide-react"
import { QRCodeSVG } from "qrcode.react"
import { useAuthContext } from "@/components/providers/auth-provider"
import { useZcashPayment } from "@/hooks/use-zcash-payment"
import { SubscriptionTierCards } from "@/components/zcash/subscription-tier-cards"
import { WalletConnectModal } from "@/components/zcash/wallet-connect-modal"
import { SUBSCRIPTION_TIERS, formatZEC, generatePaymentURI } from "@/lib/zcash/payment"
import { useToast } from "@/hooks/use-toast"

type PaymentStep = "select-tier" | "payment" | "confirming" | "complete"

export default function SubscribePage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, isAuthenticated, loading: authLoading } = useAuthContext()
  const { toast } = useToast()

  const traderId = searchParams.get("trader")
  const preselectedTier = searchParams.get("tier") as keyof typeof SUBSCRIPTION_TIERS | null

  const [step, setStep] = useState<PaymentStep>("select-tier")
  const [selectedTier, setSelectedTier] = useState<keyof typeof SUBSCRIPTION_TIERS | null>(
    preselectedTier
  )
  const [showWalletModal, setShowWalletModal] = useState(false)
  const [pollProgress, setPollProgress] = useState(0)

  const {
    payment,
    paymentRequest,
    status,
    loading,
    error,
    isPolling,
    createPayment,
    checkStatus,
    startPolling,
    stopPolling,
    simulatePayment,
  } = useZcashPayment(user?.id || "", {
    pollInterval: 5000,
    maxPollTime: 30 * 60 * 1000,
    onPaymentConfirmed: () => {
      setStep("complete")
      toast({
        title: "Payment Confirmed! 🎉",
        description: "Your subscription is now active",
      })
    },
    onPaymentExpired: () => {
      toast({
        title: "Payment Expired",
        description: "The payment window has closed. Please try again.",
        variant: "destructive",
      })
    },
  })

  // Auth check
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/auth/login?redirect=/subscribe")
    }
  }, [authLoading, isAuthenticated, router])

  // Polling progress indicator
  useEffect(() => {
    if (!isPolling) {
      setPollProgress(0)
      return
    }

    const interval = setInterval(() => {
      setPollProgress((prev) => Math.min(prev + 1, 100))
    }, 300)

    return () => clearInterval(interval)
  }, [isPolling])

  const handleTierSelect = async (tier: keyof typeof SUBSCRIPTION_TIERS) => {
    setSelectedTier(tier)
  }

  const handleProceedToPayment = async () => {
    if (!selectedTier || !user?.id) return

    try {
      await createPayment(selectedTier, traderId || undefined)
      setStep("payment")
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to create payment. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handlePaymentSent = async () => {
    setStep("confirming")
    startPolling()
  }

  const handleSimulatePayment = async () => {
    await simulatePayment()
    toast({
      title: "Payment Simulated",
      description: "Demo payment has been simulated",
    })
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <div className="container mx-auto px-4 lg:px-8 py-12 max-w-6xl">
        {/* Back Button */}
        <Button variant="ghost" asChild className="mb-6">
          <Link href="/marketplace">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Marketplace
          </Link>
        </Button>

        {/* Step: Select Tier */}
        {step === "select-tier" && (
          <div className="space-y-8">
            <div className="text-center">
              <h1 className="text-4xl font-bold mb-4">Choose Your Subscription</h1>
              <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                {traderId ? (
                  <>Subscribe to start copying verified trades from this trader</>
                ) : (
                  <>Select a plan to access copy trading and analytics</>
                )}
              </p>
            </div>

            {traderId && (
              <Alert className="max-w-2xl mx-auto">
                <Shield className="h-4 w-4" />
                <AlertDescription>
                  You're subscribing to copy trade a verified trader. All payments are made with
                  Zcash for maximum privacy.
                </AlertDescription>
              </Alert>
            )}

            <SubscriptionTierCards
              onSelectTier={handleTierSelect}
              selectedTier={selectedTier || undefined}
            />

            {selectedTier && (
              <div className="flex justify-center">
                <Button
                  size="lg"
                  className="h-14 px-12 text-lg"
                  onClick={handleProceedToPayment}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      Creating Payment...
                    </>
                  ) : (
                    <>
                      <Wallet className="h-5 w-5 mr-2" />
                      Pay with Zcash ({formatZEC(SUBSCRIPTION_TIERS[selectedTier].price)} ZEC)
                    </>
                  )}
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Step: Payment */}
        {step === "payment" && payment && paymentRequest && (
          <div className="max-w-2xl mx-auto space-y-8">
            <div className="text-center">
              <h1 className="text-3xl font-bold mb-4">Complete Payment</h1>
              <p className="text-muted-foreground">
                Scan the QR code or copy the address to pay with your Zcash wallet
              </p>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Card className="border-2 border-primary/30">
              <CardHeader className="text-center pb-2">
                <div className="flex justify-center mb-4">
                  <Badge variant="outline" className="text-lg px-4 py-2">
                    {formatZEC(paymentRequest.amount)} ZEC
                  </Badge>
                </div>
                <CardTitle>{SUBSCRIPTION_TIERS[selectedTier!].name} Subscription</CardTitle>
                <CardDescription>
                  {SUBSCRIPTION_TIERS[selectedTier!].description}
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-6">
                {/* QR Code */}
                <div className="flex flex-col items-center gap-4">
                  <div className="bg-white p-4 rounded-xl shadow-lg">
                    <QRCodeSVG
                      value={generatePaymentURI(paymentRequest)}
                      size={200}
                      level="M"
                      includeMargin
                    />
                  </div>
                </div>

                {/* Address */}
                <div className="bg-muted rounded-lg p-4 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Payment Address</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        navigator.clipboard.writeText(paymentRequest.address)
                        toast({ title: "Copied!" })
                      }}
                    >
                      Copy
                    </Button>
                  </div>
                  <code className="text-xs break-all block">{paymentRequest.address}</code>
                </div>

                {/* Expiry */}
                <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  <span>
                    Payment expires at{" "}
                    {new Date(payment.expiresAt).toLocaleTimeString()}
                  </span>
                </div>

                {/* Actions */}
                <div className="space-y-3">
                  <Button className="w-full h-12" onClick={handlePaymentSent}>
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    I've Sent the Payment
                  </Button>

                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => setShowWalletModal(true)}
                  >
                    <Wallet className="h-4 w-4 mr-2" />
                    Open in Wallet App
                  </Button>

                  {/* Dev-only simulate */}
                  {process.env.NODE_ENV === "development" && (
                    <Button
                      variant="ghost"
                      className="w-full text-muted-foreground"
                      onClick={handleSimulatePayment}
                    >
                      [DEV] Simulate Payment
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Security Notice */}
            <div className="flex items-start gap-3 text-sm text-muted-foreground">
              <Lock className="h-5 w-5 shrink-0 mt-0.5" />
              <p>
                Your payment uses Zcash shielded transactions. Transaction details are encrypted
                and only visible to you and Obscura. No third party can see your payment amount or
                identity.
              </p>
            </div>
          </div>
        )}

        {/* Step: Confirming */}
        {step === "confirming" && (
          <div className="max-w-md mx-auto text-center space-y-8">
            <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
            </div>

            <div>
              <h1 className="text-2xl font-bold mb-2">Confirming Payment</h1>
              <p className="text-muted-foreground">
                Waiting for your Zcash transaction to confirm on the network
              </p>
            </div>

            <Progress value={pollProgress} className="w-full" />

            <div className="space-y-2 text-sm text-muted-foreground">
              <p>This usually takes 1-2 minutes</p>
              <p>
                Status: <span className="font-medium text-foreground">{status?.status}</span>
              </p>
              {status?.confirmations !== undefined && (
                <p>
                  Confirmations: <span className="font-medium">{status.confirmations}</span>
                </p>
              )}
            </div>

            <Button variant="outline" onClick={() => setStep("payment")}>
              Back to Payment Details
            </Button>
          </div>
        )}

        {/* Step: Complete */}
        {step === "complete" && (
          <Card className="max-w-lg mx-auto border-2 border-primary/50 bg-gradient-to-br from-primary/10 to-background">
            <CardContent className="p-12 text-center space-y-6">
              <div className="h-20 w-20 rounded-full bg-primary/20 flex items-center justify-center mx-auto ring-4 ring-primary/30">
                <CheckCircle2 className="h-10 w-10 text-primary" />
              </div>

              <div>
                <h1 className="text-3xl font-bold mb-2">Payment Complete!</h1>
                <p className="text-muted-foreground">
                  Your {SUBSCRIPTION_TIERS[selectedTier!].name} subscription is now active
                </p>
              </div>

              {status?.txid && (
                <div className="bg-muted rounded-lg p-4">
                  <div className="text-sm text-muted-foreground mb-1">Transaction ID</div>
                  <code className="text-xs break-all">{status.txid}</code>
                </div>
              )}

              <div className="flex flex-col gap-3">
                <Button asChild className="h-12">
                  <Link href="/dashboard">Go to Dashboard</Link>
                </Button>
                {traderId && (
                  <Button asChild variant="outline">
                    <Link href={`/trader/${traderId}`}>View Trader Profile</Link>
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Wallet Connect Modal */}
      <WalletConnectModal
        open={showWalletModal}
        onOpenChange={setShowWalletModal}
        paymentRequest={paymentRequest}
        onPaymentConfirmed={() => {
          setShowWalletModal(false)
          handlePaymentSent()
        }}
        checkPaymentStatus={checkStatus}
      />
    </div>
  )
}
