"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ArrowRight, Pencil, CheckCircle } from "lucide-react"

export default function SetupIdentityPage() {
  const [username, setUsername] = useState("")
  const [isAvailable, setIsAvailable] = useState<boolean | null>(null)
  const [profileImage, setProfileImage] = useState<string | null>(null)

  const handleUsernameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setUsername(value)
    // Simulate username availability check
    if (value.length > 3) {
      setIsAvailable(true)
    } else {
      setIsAvailable(null)
    }
  }

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
          <h1 className="text-3xl font-bold mb-2">Set up your Obscura identity</h1>
          <p className="text-sm text-muted-foreground mb-1">
            Choose a profile picture and username.
          </p>
          <p className="text-sm text-muted-foreground">
            No personal details required.
          </p>
        </div>

        {/* Profile Picture */}
        <div className="flex justify-center mb-6">
          <div className="relative">
            <Avatar className="w-24 h-24">
              <AvatarImage src={profileImage || undefined} />
              <AvatarFallback className="bg-muted text-muted-foreground text-2xl">
                <svg viewBox="0 0 24 24" fill="none" className="w-12 h-12">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" fill="currentColor"/>
                </svg>
              </AvatarFallback>
            </Avatar>
            <button 
              className="absolute bottom-0 right-0 w-8 h-8 bg-card rounded-full shadow-md flex items-center justify-center border hover:bg-accent"
              aria-label="Edit profile picture"
            >
              <Pencil className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Username Input */}
        <div className="space-y-4 mb-6">
          <div className="relative">
            <Input
              type="text"
              placeholder="Choose Username"
              value={username}
              onChange={handleUsernameChange}
              className="h-12 px-4 pr-10 border-cyan-200 focus:border-primary focus:ring-primary"
            />
            {isAvailable && (
              <CheckCircle className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-success" />
            )}
          </div>
        </div>

        {/* Continue Button */}
        <Button 
          className="w-full h-12 bg-primary hover:bg-primary/90 text-black font-medium rounded-full mb-6"
          disabled={!username || !isAvailable}
        >
          Continue
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>

        {/* Terms */}
        <p className="text-center text-xs text-muted-foreground">
          By continuing you agree to our{" "}
          <Link href="/terms" className="text-primary hover:underline">
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link href="/privacy" className="text-primary hover:underline">
            Privacy Policy
          </Link>
          . We use a secure passwordless login.
        </p>
      </div>
    </div>
  )
}
