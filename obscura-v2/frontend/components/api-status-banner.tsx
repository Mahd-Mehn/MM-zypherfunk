"use client"

import { useEffect, useState } from "react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export function APIStatusBanner() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking")
  const [showBanner, setShowBanner] = useState(false)

  useEffect(() => {
    checkAPIStatus()
  }, [])

  const checkAPIStatus = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      const response = await fetch(`${apiUrl}/health`, {
        method: "GET",
        signal: AbortSignal.timeout(5000),
      })

      if (response.ok) {
        setStatus("online")
        setShowBanner(false)
      } else {
        setStatus("offline")
        setShowBanner(true)
      }
    } catch (error) {
      setStatus("offline")
      setShowBanner(true)
    }
  }

  if (!showBanner) return null

  return (
    <Alert variant="destructive" className="rounded-none border-x-0 border-t-0">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>API Gateway Not Available</AlertTitle>
      <AlertDescription className="flex items-center justify-between">
        <span>
          The backend API is not running. Please start the API Gateway to use authentication and
          real-time features.
        </span>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={checkAPIStatus}>
            Retry
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href="/docs/setup" target="_blank">
              Setup Guide
            </Link>
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  )
}

export function APIStatusIndicator() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking")

  useEffect(() => {
    checkAPIStatus()
    const interval = setInterval(checkAPIStatus, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const checkAPIStatus = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      const response = await fetch(`${apiUrl}/health`, {
        method: "GET",
        signal: AbortSignal.timeout(5000),
      })

      if (response.ok) {
        setStatus("online")
      } else {
        setStatus("offline")
      }
    } catch (error) {
      setStatus("offline")
    }
  }

  return (
    <div className="flex items-center gap-2 text-xs">
      {status === "checking" && (
        <>
          <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
          <span className="text-muted-foreground">Checking API...</span>
        </>
      )}
      {status === "online" && (
        <>
          <CheckCircle2 className="h-3 w-3 text-green-500" />
          <span className="text-green-500">API Online</span>
        </>
      )}
      {status === "offline" && (
        <>
          <AlertCircle className="h-3 w-3 text-destructive" />
          <span className="text-destructive">API Offline</span>
        </>
      )}
    </div>
  )
}
