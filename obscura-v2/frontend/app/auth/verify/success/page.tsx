"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"

export default function MagicLinkSentPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-blue-50 to-cyan-50">
      <div className="w-full max-w-md px-6">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 relative">
              <svg viewBox="0 0 100 100" className="w-full h-full">
                <path d="M50 10 L90 30 L90 70 L50 90 L10 70 L10 30 Z" fill="none" stroke="#000" strokeWidth="2"/>
                <circle cx="50" cy="50" r="15" fill="none" stroke="#000" strokeWidth="2"/>
                <path d="M50 35 L50 25 M50 65 L50 75 M35 50 L25 50 M65 50 L75 50" stroke="#000" strokeWidth="2"/>
              </svg>
            </div>
            <div>
              <div className="text-xl font-bold">Obscura</div>
              <div className="text-xs text-muted-foreground">VERIFIABLE REPUTATION</div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">Magic Link Sent</h1>
          <p className="text-sm text-muted-foreground mb-1">
            Check your inbox.
          </p>
          <p className="text-sm text-muted-foreground">
            The link expires in <span className="text-primary font-medium">15</span> minutes.
          </p>
        </div>

        {/* Resend Button */}
        <Button 
          className="w-full h-12 bg-primary hover:bg-primary/90 text-black font-medium rounded-full mb-6"
        >
          Resend Link
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>

        {/* Help Text */}
        <p className="text-center text-sm text-muted-foreground">
          Haven't received it? Check spam or try again.
        </p>
      </div>
    </div>
  )
}
