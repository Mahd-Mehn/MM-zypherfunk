"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { useAuthContext } from "@/components/providers/auth-provider"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, CheckCircle2, XCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export default function VerifyPage() {
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading")
  const [errorMessage, setErrorMessage] = useState("")
  const [hasVerified, setHasVerified] = useState(false)
  const searchParams = useSearchParams()
  const router = useRouter()
  const { verifyMagicLink } = useAuthContext()

  useEffect(() => {
    // Prevent double verification
    if (hasVerified) return
    
    const token = searchParams.get("token")
    
    if (!token) {
      setStatus("error")
      setErrorMessage("No verification token provided")
      return
    }

    verifyToken(token)
  }, [searchParams, hasVerified])

  const verifyToken = async (token: string) => {
    try {
      setHasVerified(true)
      const response = await verifyMagicLink(token)
      setStatus("success")
      
      // Wait a bit longer to ensure state is updated
      setTimeout(() => {
        router.push("/onboarding")
      }, 2000)
    } catch (error: any) {
      setStatus("error")
      setErrorMessage(error.message || "Failed to verify magic link")
      setHasVerified(false)
    }
  }

  return (
    <div className="container flex items-center justify-center min-h-screen py-12">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Verifying Your Login</CardTitle>
          <CardDescription>
            Please wait while we verify your magic link
          </CardDescription>
        </CardHeader>
        <CardContent>
          {status === "loading" && (
            <div className="flex flex-col items-center justify-center py-8 space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">Verifying...</p>
            </div>
          )}

          {status === "success" && (
            <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800 dark:text-green-200">
                Successfully verified! Redirecting to onboarding...
              </AlertDescription>
            </Alert>
          )}

          {status === "error" && (
            <div className="space-y-4">
              <Alert variant="destructive">
                <XCircle className="h-4 w-4" />
                <AlertDescription>{errorMessage}</AlertDescription>
              </Alert>
              <Link href="/auth/login">
                <Button className="w-full">Back to Login</Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
