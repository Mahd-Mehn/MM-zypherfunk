"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { QRCodeSVG } from "qrcode.react"
import { Smartphone, Monitor, Copy, CheckCircle2, ExternalLink, Loader2, AlertCircle } from "lucide-react"
import { generatePaymentURI, formatZEC, type PaymentRequest } from "@/lib/zcash/payment"
import { useToast } from "@/hooks/use-toast"

interface WalletOption {
  id: string
  name: string
  icon: string
  description: string
  platforms: string[]
  deepLink?: (uri: string) => string
  storeLinks: {
    ios?: string
    android?: string
    desktop?: string
  }
}

const WALLET_OPTIONS: WalletOption[] = [
  {
    id: "zashi",
    name: "Zashi",
    icon: "⚡",
    description: "Official ECC wallet with full Orchard support",
    platforms: ["iOS", "Android"],
    deepLink: (uri: string) => uri, // Zashi handles zcash: URIs natively
    storeLinks: {
      ios: "https://apps.apple.com/app/zashi-zcash-wallet/id1672392439",
      android: "https://play.google.com/store/apps/details?id=co.electriccoin.zcash",
    },
  },
  {
    id: "ywallet",
    name: "Ywallet",
    icon: "💎",
    description: "Fast, feature-rich wallet with sync optimization",
    platforms: ["iOS", "Android", "Desktop"],
    deepLink: (uri: string) => uri,
    storeLinks: {
      ios: "https://apps.apple.com/app/ywallet/id1583353077",
      android: "https://play.google.com/store/apps/details?id=me.hanh.ywallet",
      desktop: "https://github.com/hhanh00/zwallet/releases",
    },
  },
  {
    id: "zecwallet-lite",
    name: "Zecwallet Lite",
    icon: "🔒",
    description: "Lightweight desktop wallet with full privacy",
    platforms: ["Windows", "macOS", "Linux"],
    storeLinks: {
      desktop: "https://github.com/adityapk00/zecwallet-lite/releases",
    },
  },
  {
    id: "edge",
    name: "Edge Wallet",
    icon: "🌐",
    description: "Multi-currency wallet with Zcash support",
    platforms: ["iOS", "Android"],
    deepLink: (uri: string) => `edge://x-callback-url/request?uri=${encodeURIComponent(uri)}`,
    storeLinks: {
      ios: "https://apps.apple.com/app/edge-crypto-bitcoin-wallet/id1344400091",
      android: "https://play.google.com/store/apps/details?id=co.edgesecure.app",
    },
  },
]

interface WalletConnectModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  paymentRequest: PaymentRequest | null
  onPaymentConfirmed?: () => void
  checkPaymentStatus?: () => Promise<boolean>
}

export function WalletConnectModal({
  open,
  onOpenChange,
  paymentRequest,
  onPaymentConfirmed,
  checkPaymentStatus,
}: WalletConnectModalProps) {
  const { toast } = useToast()
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null)
  const [checking, setChecking] = useState(false)
  const [copied, setCopied] = useState(false)

  const paymentURI = paymentRequest ? generatePaymentURI(paymentRequest) : ""

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      toast({
        title: "Copied!",
        description: `${label} copied to clipboard`,
      })
      setTimeout(() => setCopied(false), 2000)
    } catch {
      toast({
        title: "Copy failed",
        description: "Please manually select and copy",
        variant: "destructive",
      })
    }
  }

  const handleCheckPayment = async () => {
    if (!checkPaymentStatus) return

    setChecking(true)
    try {
      const confirmed = await checkPaymentStatus()
      if (confirmed) {
        toast({
          title: "Payment Confirmed! 🎉",
          description: "Your subscription is now active",
        })
        onPaymentConfirmed?.()
        onOpenChange(false)
      } else {
        toast({
          title: "Payment not yet detected",
          description: "Please wait for the transaction to confirm",
        })
      }
    } catch {
      toast({
        title: "Error checking payment",
        description: "Please try again",
        variant: "destructive",
      })
    } finally {
      setChecking(false)
    }
  }

  const openWalletLink = (wallet: WalletOption) => {
    // Try deep link first on mobile
    if (wallet.deepLink && /iPhone|iPad|Android/i.test(navigator.userAgent)) {
      window.location.href = wallet.deepLink(paymentURI)
      return
    }

    // Otherwise open store/download page
    const link = wallet.storeLinks.desktop || wallet.storeLinks.ios || wallet.storeLinks.android
    if (link) {
      window.open(link, "_blank")
    }
  }

  if (!paymentRequest) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">Pay with Zcash</DialogTitle>
          <DialogDescription>
            Scan the QR code with your Zcash wallet or choose a wallet app below
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Payment Details */}
          <Card className="bg-primary/5 border-primary/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-muted-foreground">Amount</div>
                  <div className="text-2xl font-bold">{formatZEC(paymentRequest.amount)} ZEC</div>
                </div>
                <Badge variant="outline" className="bg-primary/10">
                  Shielded
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* QR Code Section */}
          <div className="flex flex-col items-center gap-4 py-4">
            <div className="bg-white p-4 rounded-xl shadow-lg">
              <QRCodeSVG
                value={paymentURI}
                size={200}
                level="M"
                includeMargin
                imageSettings={{
                  src: "/zcash-logo.svg",
                  x: undefined,
                  y: undefined,
                  height: 32,
                  width: 32,
                  excavate: true,
                }}
              />
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(paymentRequest.address, "Address")}
              >
                {copied ? <CheckCircle2 className="h-4 w-4 mr-2" /> : <Copy className="h-4 w-4 mr-2" />}
                Copy Address
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(paymentURI, "Payment URI")}
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy URI
              </Button>
            </div>

            <p className="text-xs text-muted-foreground text-center max-w-sm">
              Scan with any ZIP-321 compatible wallet. Payment will be detected automatically.
            </p>
          </div>

          {/* Address Display */}
          <div className="bg-muted rounded-lg p-4">
            <div className="text-xs text-muted-foreground mb-1">Payment Address (Unified)</div>
            <code className="text-xs break-all">{paymentRequest.address}</code>
          </div>

          {/* Wallet Options */}
          <div className="space-y-3">
            <h4 className="font-semibold flex items-center gap-2">
              <Smartphone className="h-4 w-4" />
              Choose a Wallet
            </h4>

            <div className="grid grid-cols-2 gap-3">
              {WALLET_OPTIONS.map((wallet) => (
                <Card
                  key={wallet.id}
                  className={`cursor-pointer transition-all hover:shadow-md ${
                    selectedWallet === wallet.id
                      ? "border-primary bg-primary/5"
                      : "hover:border-primary/50"
                  }`}
                  onClick={() => {
                    setSelectedWallet(wallet.id)
                    openWalletLink(wallet)
                  }}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="text-2xl">{wallet.icon}</div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium">{wallet.name}</div>
                        <div className="text-xs text-muted-foreground truncate">
                          {wallet.description}
                        </div>
                        <div className="flex gap-1 mt-1 flex-wrap">
                          {wallet.platforms.map((p) => (
                            <Badge key={p} variant="secondary" className="text-[10px] px-1 py-0">
                              {p}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <ExternalLink className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Check Payment Button */}
          {checkPaymentStatus && (
            <div className="pt-4 border-t space-y-3">
              <Button
                className="w-full h-12"
                onClick={handleCheckPayment}
                disabled={checking}
              >
                {checking ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Checking for payment...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    I've sent the payment
                  </>
                )}
              </Button>

              <div className="flex items-center gap-2 text-sm text-muted-foreground justify-center">
                <AlertCircle className="h-4 w-4" />
                <span>Payment usually confirms within 1-2 minutes</span>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
