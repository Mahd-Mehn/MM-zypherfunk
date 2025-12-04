"use client"

import { MagicLinkForm } from "@/components/auth/magic-link-form"
import Link from "next/link"

export default function LoginPage() {
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
          <h1 className="text-3xl font-bold mb-2">Get Started</h1>
          <p className="text-sm text-muted-foreground mb-1">
            We'll send you a magic link to get started.
          </p>
          <p className="text-sm text-muted-foreground">
            No passwords, no KYC.
          </p>
        </div>

        {/* Form */}
        <MagicLinkForm />

        {/* Terms - suppressHydrationWarning due to browser extensions modifying links */}
        <p className="text-center text-xs text-muted-foreground mt-6" suppressHydrationWarning>
          By continuing you agree to our{" "}
          <Link href="/terms" className="text-primary hover:underline" suppressHydrationWarning>
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link href="/privacy" className="text-primary hover:underline" suppressHydrationWarning>
            Privacy Policy
          </Link>
          . We use a secure passwordless login.
        </p>
      </div>
    </div>
  )
}
