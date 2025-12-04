"use client"

import { useState, useEffect } from "react"
import { QRCodeSVG } from "qrcode.react"
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle 
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { 
  Copy, 
  Check, 
  AlertCircle, 
  Shield, 
  Clock, 
  Wallet,
  ExternalLink,
  RefreshCw,
  Smartphone
} from "lucide-react"
import { useZcashPayment } from "@/components/providers/zcash-payment-provider"
import { formatZEC, SUBSCRIPTION_TIERS } from "@/lib/zcash/payment"

interface ZcashPaymentModalProps {
  isOpen: boolean
  onClose: () => void
  tier: 'basic' | 'pro' | 'premium'
  traderId?: string
  onSuccess?: () => void
}

export function ZcashPaymentModal({
  isOpen,
  onClose,
  tier,
  traderId,
  onSuccess,
}: ZcashPaymentModalProps) {
  const {
    currentPayment,
    paymentStatus,
    isLoading,
    error,
    createPayment,
    checkPayment,
    clearPayment,
    simulatePayment,
    getPaymentQRData,
  } = useZcashPayment()

  const [copied, setCopied] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState<number>(0)

  const tierInfo = SUBSCRIPTION_TIERS[tier]

  // Create payment on mount
  useEffect(() => {
    if (isOpen && !currentPayment) {
      createPayment(tier, traderId)
    }
  }, [isOpen, currentPayment, tier, traderId, createPayment])

  // Countdown timer
  useEffect(() => {
    if (currentPayment?.expiresAt) {
      const updateTimer = () => {
        const expires = new Date(currentPayment.expiresAt).getTime()
        const now = Date.now()
        const remaining = Math.max(0, Math.floor((expires - now) / 1000))
        setTimeRemaining(remaining)
      }

      updateTimer()
      const interval = setInterval(updateTimer, 1000)
      return () => clearInterval(interval)
    }
  }, [currentPayment])

  // Handle success
  useEffect(() => {
    if (paymentStatus?.status === 'confirmed') {
      onSuccess?.()
    }
  }, [paymentStatus, onSuccess])

  const handleClose = () => {
    clearPayment()
    onClose()
  }

  const copyAddress = () => {
    if (currentPayment?.paymentAddress) {
      navigator.clipboard.writeText(currentPayment.paymentAddress)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const qrData = getPaymentQRData()

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-yellow-500" />
            Pay with Zcash
          </DialogTitle>
          <DialogDescription>
            Complete your {tierInfo.name} subscription with a shielded ZEC payment
          </DialogDescription>
        </DialogHeader>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {paymentStatus?.status === 'confirmed' ? (
          // Success State
          <div className="flex flex-col items-center gap-4 py-6">
            <div className="h-16 w-16 rounded-full bg-green-500/10 flex items-center justify-center">
              <Check className="h-8 w-8 text-green-500" />
            </div>
            <div className="text-center">
              <h3 className="text-lg font-semibold text-green-500">Payment Confirmed!</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Your {tierInfo.name} subscription is now active
              </p>
              {paymentStatus.txid && (
                <p className="text-xs font-mono text-muted-foreground mt-2">
                  TX: {paymentStatus.txid.slice(0, 16)}...
                </p>
              )}
            </div>
            <Button onClick={handleClose} className="mt-2">
              Done
            </Button>
          </div>
        ) : paymentStatus?.status === 'expired' ? (
          // Expired State
          <div className="flex flex-col items-center gap-4 py-6">
            <div className="h-16 w-16 rounded-full bg-destructive/10 flex items-center justify-center">
              <Clock className="h-8 w-8 text-destructive" />
            </div>
            <div className="text-center">
              <h3 className="text-lg font-semibold text-destructive">Payment Expired</h3>
              <p className="text-sm text-muted-foreground mt-1">
                The payment window has closed
              </p>
            </div>
            <Button 
              onClick={() => createPayment(tier, traderId)}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Try Again'
              )}
            </Button>
          </div>
        ) : isLoading && !currentPayment ? (
          // Loading State
          <div className="flex flex-col items-center gap-4 py-8">
            <RefreshCw className="h-8 w-8 animate-spin text-primary" />
            <p className="text-muted-foreground">Generating payment address...</p>
          </div>
        ) : currentPayment ? (
          // Payment State
          <div className="space-y-4">
            {/* Tier Info */}
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div>
                <div className="font-medium">{tierInfo.name} Subscription</div>
                <div className="text-sm text-muted-foreground">{tierInfo.description}</div>
              </div>
              <Badge variant="secondary" className="text-lg font-mono">
                {formatZEC(tierInfo.price)} ZEC
              </Badge>
            </div>

            {/* Timer */}
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-1 text-muted-foreground">
                <Clock className="h-4 w-4" />
                Time remaining
              </span>
              <span className={`font-mono ${timeRemaining < 60 ? 'text-destructive' : ''}`}>
                {formatTime(timeRemaining)}
              </span>
            </div>
            <Progress value={(timeRemaining / 900) * 100} className="h-1" />

            <Tabs defaultValue="qr" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="qr">
                  <Smartphone className="h-4 w-4 mr-2" />
                  Scan QR
                </TabsTrigger>
                <TabsTrigger value="address">
                  <Wallet className="h-4 w-4 mr-2" />
                  Copy Address
                </TabsTrigger>
              </TabsList>

              <TabsContent value="qr" className="mt-4">
                <div className="flex flex-col items-center gap-4">
                  {qrData && (
                    <div className="p-4 bg-white rounded-lg">
                      <QRCodeSVG 
                        value={qrData} 
                        size={200}
                        level="H"
                        includeMargin
                      />
                    </div>
                  )}
                  <p className="text-xs text-center text-muted-foreground max-w-xs">
                    Scan with Zashi, Nighthawk, or any ZIP-321 compatible Zcash wallet
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open('https://electriccoin.co/zashi/', '_blank')}
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Get Zashi Wallet
                  </Button>
                </div>
              </TabsContent>

              <TabsContent value="address" className="mt-4">
                <div className="space-y-3">
                  <div className="p-3 bg-muted rounded-lg">
                    <label className="text-xs text-muted-foreground block mb-1">
                      Payment Address (Unified)
                    </label>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 text-xs font-mono break-all">
                        {currentPayment.paymentAddress}
                      </code>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={copyAddress}
                        className="shrink-0"
                      >
                        {copied ? (
                          <Check className="h-4 w-4 text-green-500" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>

                  <div className="p-3 bg-muted rounded-lg">
                    <label className="text-xs text-muted-foreground block mb-1">
                      Amount
                    </label>
                    <div className="font-mono font-medium">
                      {formatZEC(currentPayment.amountZec)} ZEC
                    </div>
                  </div>

                  <Alert className="bg-muted/50 border-primary/20">
                    <Shield className="h-4 w-4 text-primary" />
                    <AlertTitle className="text-sm">Shielded Payment</AlertTitle>
                    <AlertDescription className="text-xs text-muted-foreground">
                      Send exactly {formatZEC(currentPayment.amountZec)} ZEC to complete your subscription. 
                      Your transaction will be fully private.
                    </AlertDescription>
                  </Alert>
                </div>
              </TabsContent>
            </Tabs>

            {/* Status */}
            <div className="flex items-center justify-between pt-2 border-t">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-yellow-500 animate-pulse" />
                <span className="text-sm text-muted-foreground">Waiting for payment...</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={checkPayment}
                disabled={isLoading}
              >
                {isLoading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
              </Button>
            </div>

            {/* Dev Mode: Simulate Payment */}
            {process.env.NODE_ENV !== 'production' && (
              <Button
                variant="outline"
                className="w-full"
                onClick={simulatePayment}
                disabled={isLoading}
              >
                [DEV] Simulate Payment
              </Button>
            )}
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}
