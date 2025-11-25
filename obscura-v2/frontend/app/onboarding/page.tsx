"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Header } from "@/components/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import {
  Shield,
  Lock,
  CheckCircle2,
  ArrowRight,
  Eye,
  EyeOff,
  AlertCircle,
  Users,
  TrendingUp,
  Loader2,
  ExternalLink,
  Sparkles,
} from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useAuthContext } from "@/components/providers/auth-provider"
import { useExchanges } from "@/hooks/use-exchanges"
import { exchangesAPI, authAPI } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

type OnboardingStep = "role" | "binance" | "complete"

export default function OnboardingPage() {
  const router = useRouter()
  const { user, isAuthenticated, loading: authLoading, refetch } = useAuthContext()
  const { connections, loading: exchangesLoading, refetch: refetchExchanges } = useExchanges()
  const { toast } = useToast()
  const [checking, setChecking] = useState(true)
  const [currentStep, setCurrentStep] = useState<OnboardingStep>("role")
  const [selectedRole, setSelectedRole] = useState<"trader" | "follower" | null>(null)
  const [roleSaving, setRoleSaving] = useState(false)
  const [roleError, setRoleError] = useState<string | null>(null)
  const [showApiKey, setShowApiKey] = useState(false)
  const [showApiSecret, setShowApiSecret] = useState(false)
  const [apiKey, setApiKey] = useState("")
  const [apiSecret, setApiSecret] = useState("")
  const [showGuide, setShowGuide] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)

  // Check if user needs onboarding
  useEffect(() => {
    // Wait for auth to finish loading
    if (authLoading || exchangesLoading) {
      return
    }

    // Small delay to ensure state is fully updated after redirect
    const timer = setTimeout(() => {
      if (!isAuthenticated) {
        console.log('Not authenticated, redirecting to login')
        router.push("/auth/login")
        return
      }

      // Check if user has completed onboarding (has exchange connections OR localStorage flag)
      const hasOnboardingFlag = typeof window !== 'undefined' && localStorage.getItem('onboarding_complete') === 'true'
      
      if ((connections && connections.length > 0) || hasOnboardingFlag) {
        // User has already completed onboarding, redirect to dashboard
        console.log('Onboarding complete, redirecting to dashboard')
        router.push("/dashboard")
      } else {
        // User needs onboarding
        console.log('User needs onboarding')
        setChecking(false)
      }
    }, 100)

    return () => clearTimeout(timer)
  }, [isAuthenticated, authLoading, connections, exchangesLoading, router])

    useEffect(() => {
      if (
        !selectedRole &&
        user?.user_type &&
        (user.user_type === "trader" || user.user_type === "follower")
      ) {
        setSelectedRole(user.user_type)
      }
    }, [user, selectedRole])

  if (checking || authLoading || exchangesLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  const handleRoleSelect = async (role: "trader" | "follower") => {
    if (roleSaving) return

    if (!user) {
      toast({
        title: "Please sign in",
        description: "Log in again to continue onboarding.",
        variant: "destructive",
      })
      return
    }

    setRoleSaving(true)
    setRoleError(null)

    try {
      await authAPI.updateUserType(user.id, role)
      await refetch()
      setSelectedRole(role)
      toast({
        title: role === "trader" ? "Signal provider activated" : "Follower mode activated",
        description: "Your profile has been updated",
      })
      setCurrentStep("binance")
    } catch (error: any) {
      console.error("Failed to update user role", error)
      const message = error?.message || "Could not update your role. Please try again."
      setRoleError(message)
      toast({
        title: "Role update failed",
        description: message,
        variant: "destructive",
      })
    } finally {
      setRoleSaving(false)
    }
  }

  const handleConnectBinance = async () => {
    if (!apiKey || !apiSecret) {
      return
    }

    setConnecting(true)
    setConnectionError(null)
    
    try {
      // Call API to connect Binance
      const connection = await exchangesAPI.createConnection({
        exchange: 'binance',
        api_key: apiKey,
        api_secret: apiSecret,
        is_signal_provider: selectedRole === 'trader',
      })
      
      // Mark onboarding as complete in localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('onboarding_complete', 'true')
      }
      
      // Refresh exchange connections
      await refetchExchanges()
      
      toast({
        title: "Success!",
        description: "Binance account connected successfully.",
      })
      
      setCurrentStep("complete")
    } catch (error: any) {
      console.error('Failed to connect Binance:', error)
      const errorMessage = error.message || 'Failed to connect Binance. Please check your API credentials.'
      setConnectionError(errorMessage)
      
      toast({
        title: "Connection Failed",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setConnecting(false)
    }
  }

  const handleSkipBinance = () => {
    // Mark onboarding as complete even if skipped
    if (typeof window !== 'undefined') {
      localStorage.setItem('onboarding_complete', 'true')
    }
    setCurrentStep("complete")
  }

  const steps = [
    { step: "role", label: "Choose Role", completed: !!selectedRole },
    { step: "binance", label: "Connect Binance", completed: currentStep === "complete" },
    { step: "complete", label: "Done", completed: currentStep === "complete" },
  ]

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <div className="container mx-auto px-4 lg:px-8 py-12 lg:py-16 max-w-6xl">
        {/* Progress indicator */}
        <div className="mb-16">
          <div className="flex items-center justify-between max-w-4xl mx-auto">
            {steps.map((item, index, array) => (
              <div key={item.step} className="flex items-center flex-1">
                <div className="flex flex-col items-center gap-3 flex-1">
                  <div
                    className={`h-12 w-12 rounded-full flex items-center justify-center transition-all duration-300 ${
                      item.completed || currentStep === item.step
                        ? "bg-primary text-primary-foreground ring-4 ring-primary/20 scale-110"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {item.completed ? (
                      <CheckCircle2 className="h-6 w-6" />
                    ) : (
                      <span className="text-lg font-bold">{index + 1}</span>
                    )}
                  </div>
                  <span
                    className={`text-sm font-medium ${item.completed || currentStep === item.step ? "text-foreground" : "text-muted-foreground"}`}
                  >
                    {item.label}
                  </span>
                </div>
                {index < array.length - 1 && (
                  <div
                    className={`flex-1 h-1 rounded-full mx-4 transition-colors ${item.completed ? "bg-primary" : "bg-border"}`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>



        {/* Role selection */}
        {currentStep === "role" && (
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">Choose Your Role</h2>
              <p className="text-muted-foreground text-lg">You can change this later in settings</p>
            </div>

            <div className="grid md:grid-cols-2 gap-8">
              {[
                {
                  role: "trader" as const,
                  icon: Shield,
                  title: "Signal Provider",
                  description: "Share your verified trading performance and earn fees from followers",
                  features: [
                    "Verify trades with ZK proofs or TEE",
                    "Build on-chain reputation",
                    "Earn performance fees in ZEN",
                    "Gain followers and credibility",
                  ],
                  badge: "Earn Fees",
                  badgeColor: "bg-success/10 text-success border-success/20",
                },
                {
                  role: "follower" as const,
                  icon: Users,
                  title: "Follower",
                  description: "Copy verified traders and benefit from their expertise",
                  features: [
                    "Browse verified traders",
                    "One-click copy trading",
                    "Pay fees only on profits",
                    "Automated risk management",
                  ],
                  badge: "Start Copying",
                  badgeColor: "bg-primary/10 text-primary border-primary/20",
                },
              ].map((option) => (
                <Card
                  key={option.role}
                  className={`cursor-pointer transition-all duration-300 hover:shadow-2xl ${
                    roleSaving ? "pointer-events-none opacity-60" : ""
                  } ${
                    selectedRole === option.role
                      ? "border-2 border-primary bg-gradient-to-br from-primary/10 to-primary/5 scale-105"
                      : "border-border/50 hover:border-primary/50"
                  }`}
                  onClick={() => handleRoleSelect(option.role)}
                >
                  <CardContent className="p-10 text-center space-y-6">
                    <Badge className={`${option.badgeColor} mb-2`}>{option.badge}</Badge>
                    <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto ring-4 ring-primary/20">
                      <option.icon className="h-10 w-10 text-primary" />
                    </div>
                    <div>
                      <h3 className="text-3xl font-bold mb-3">{option.title}</h3>
                      <p className="text-base text-muted-foreground leading-relaxed">{option.description}</p>
                    </div>
                    <ul className="space-y-3 text-left">
                      {option.features.map((feature) => (
                        <li key={feature} className="flex items-start gap-3">
                          <CheckCircle2 className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                          <span className="text-sm">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              ))}
            </div>
            {roleError && (
              <Alert variant="destructive" className="mt-8">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{roleError}</AlertDescription>
              </Alert>
            )}
          </div>
        )}

        {/* Binance Connection */}
        {currentStep === "binance" && (
          <div className="max-w-3xl mx-auto space-y-8">
            <div className="text-center">
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">Connect Binance</h2>
              <p className="text-muted-foreground text-lg">
                {selectedRole === "trader" 
                  ? "Connect your Binance account to verify and share your trading performance"
                  : "Connect your Binance account to start copying verified traders"}
              </p>
            </div>

            <Card className="border-2 border-purple-500/40 bg-gradient-to-br from-purple-500/10 to-card shadow-xl">
              <CardContent className="p-8 space-y-6">
                <div className="flex items-start gap-4">
                  <div className="h-12 w-12 rounded-xl bg-purple-500/20 flex items-center justify-center shrink-0">
                    <Lock className="h-6 w-6 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg mb-2">Secure API Connection</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      Your API keys are encrypted with AES-256 and stored in AWS Nitro Enclave. They never leave the secure environment and are only used to {selectedRole === "trader" ? "verify your trades" : "execute copy trades"}.
                    </p>
                  </div>
                </div>

                <div className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="api-key">API Key</Label>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowGuide(!showGuide)}
                        className="h-auto p-0 text-primary hover:text-primary/80"
                      >
                        <AlertCircle className="h-4 w-4 mr-1" />
                        How to get API keys?
                      </Button>
                    </div>
                    <div className="relative">
                      <Input
                        id="api-key"
                        type={showApiKey ? "text" : "password"}
                        placeholder="Enter your Binance API key"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        className="h-12 pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="api-secret">API Secret</Label>
                    <div className="relative">
                      <Input
                        id="api-secret"
                        type={showApiSecret ? "text" : "password"}
                        placeholder="Enter your Binance API secret"
                        value={apiSecret}
                        onChange={(e) => setApiSecret(e.target.value)}
                        className="h-12 pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiSecret(!showApiSecret)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showApiSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                </div>

                {showGuide && (
                  <Alert className="border-primary/30 bg-primary/5">
                    <Shield className="h-5 w-5 text-primary" />
                    <AlertDescription className="space-y-3">
                      <p className="font-semibold">How to create Binance API keys:</p>
                      <ol className="list-decimal list-inside space-y-2 text-sm">
                        <li>Log in to your Binance account</li>
                        <li>Go to Profile → API Management</li>
                        <li>Click "Create API" and choose "System generated"</li>
                        <li>Label it "Obscura" and complete verification</li>
                        <li>
                          <strong>Important:</strong> Enable only these permissions:
                          <ul className="list-disc list-inside ml-4 mt-1">
                            <li>✓ Enable Reading (required)</li>
                            <li>✓ Enable Spot & Margin Trading (for copy trading)</li>
                            <li>✗ Do NOT enable withdrawals</li>
                          </ul>
                        </li>
                        <li>Copy your API Key and Secret Key</li>
                      </ol>
                      <a
                        href="https://www.binance.com/en/support/faq/how-to-create-api-keys-on-binance-360002502072"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-primary hover:underline text-sm font-medium"
                      >
                        View detailed guide on Binance
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {connectionError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{connectionError}</AlertDescription>
              </Alert>
            )}

            <div className="flex gap-4">
              <Button variant="outline" onClick={() => setCurrentStep("role")} className="h-12 px-8">
                Back
              </Button>
              <Button
                variant="ghost"
                onClick={handleSkipBinance}
                className="h-12 px-8"
              >
                Skip for Now
              </Button>
              <Button
                className="flex-1 h-12 shadow-lg shadow-primary/25"
                onClick={handleConnectBinance}
                disabled={!apiKey || !apiSecret || connecting}
              >
                {connecting ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    Connect Binance
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {/* Complete */}
        {currentStep === "complete" && (
          <Card className="max-w-3xl mx-auto border-2 border-primary/50 bg-gradient-to-br from-primary/10 via-primary/5 to-background shadow-2xl">
            <CardContent className="p-12 lg:p-20 text-center space-y-8">
              <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center mx-auto ring-8 ring-primary/20">
                <Sparkles className="h-12 w-12 text-primary" />
              </div>
              <div>
                <h2 className="text-4xl lg:text-5xl font-bold mb-4">Welcome to Obscura!</h2>
                <p className="text-muted-foreground text-xl leading-relaxed">
                  Your account is set up and ready. Start {selectedRole === "trader" ? "sharing" : "copying"} verified
                  trades today.
                </p>
              </div>

              <div className="bg-card border border-border/50 rounded-xl p-8 space-y-4 text-left max-w-lg mx-auto">
                <h3 className="font-bold text-lg mb-4">Setup Complete</h3>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="h-6 w-6 text-primary shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold">Role Selected</div>
                    <div className="text-sm text-muted-foreground">
                      {selectedRole === "trader" ? "Signal Provider" : "Follower"}
                    </div>
                  </div>
                </div>
                {apiKey && apiSecret && (
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-6 w-6 text-primary shrink-0 mt-0.5" />
                    <div>
                      <div className="font-semibold">Binance Connected</div>
                      <div className="text-sm text-muted-foreground">API keys securely stored</div>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex flex-col sm:flex-row gap-4 max-w-lg mx-auto">
                {selectedRole === "trader" ? (
                  <>
                    <Button className="flex-1 h-12" asChild>
                      <Link href="/dashboard">
                        <TrendingUp className="mr-2 h-5 w-5" />
                        Go to Dashboard
                      </Link>
                    </Button>
                    <Button variant="outline" className="flex-1 h-12 bg-transparent" asChild>
                      <Link href="/docs">View Documentation</Link>
                    </Button>
                  </>
                ) : (
                  <>
                    <Button className="flex-1 h-12" asChild>
                      <Link href="/marketplace">
                        <Users className="mr-2 h-5 w-5" />
                        Browse Traders
                      </Link>
                    </Button>
                    <Button variant="outline" className="flex-1 h-12 bg-transparent" asChild>
                      <Link href="/dashboard">Go to Dashboard</Link>
                    </Button>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
