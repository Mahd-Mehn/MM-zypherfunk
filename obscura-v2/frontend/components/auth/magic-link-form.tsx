"use client"

import { useState } from "react"
import { useAuthContext } from "@/components/providers/auth-provider"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Loader2, Mail, CheckCircle2, AlertCircle, ExternalLink, ArrowRight } from "lucide-react"
import { APIError } from "@/lib/api"
import Link from "next/link"

export function MagicLinkForm() {
  const [email, setEmail] = useState("")
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)
  const { requestMagicLink } = useAuthContext()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setSent(false)
    setLocalError(null)

    try {
      await requestMagicLink(email)
      setSent(true)
    } catch (err) {
      console.error("Failed to send magic link:", err)
      
      if (err instanceof APIError) {
        if (err.code === 'NETWORK_ERROR' || err.code === 'TIMEOUT') {
          setLocalError('api_offline')
        } else {
          setLocalError(err.message)
        }
      } else {
        setLocalError('An unexpected error occurred')
      }
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
    return (
      <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
        <CheckCircle2 className="h-4 w-4 text-green-600" />
        <AlertDescription className="text-green-800 dark:text-green-200">
          Magic link sent to <strong>{email}</strong>. Check your inbox and click the link to sign in.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Input
          id="email"
          type="email"
          placeholder="Enter email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          disabled={loading}
          className="h-12 px-4 border-cyan-200 focus:border-primary focus:ring-primary"
        />
      </div>

      {localError === 'api_offline' ? (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>API Gateway Not Running</AlertTitle>
          <AlertDescription className="space-y-2">
            <p>The backend API is not available. Please start the API Gateway:</p>
            <div className="bg-destructive/10 p-2 rounded text-xs font-mono mt-2">
              cd api-gateway && make dev
            </div>
            <Link 
              href="https://github.com/yourusername/obscura/blob/main/SETUP.md" 
              target="_blank"
              className="inline-flex items-center gap-1 text-xs underline mt-2"
            >
              View Setup Guide <ExternalLink className="h-3 w-3" />
            </Link>
          </AlertDescription>
        </Alert>
      ) : localError ? (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{localError}</AlertDescription>
        </Alert>
      ) : null}

      <Button 
        type="submit" 
        className="w-full h-12 bg-primary hover:bg-primary/90 text-black font-medium rounded-full"
        disabled={loading}
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Sending...
          </>
        ) : (
          <>
            Send Magic Link
            <ArrowRight className="ml-2 h-4 w-4" />
          </>
        )}
      </Button>
    </form>
  )
}
