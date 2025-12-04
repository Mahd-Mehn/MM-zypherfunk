"use client"

import { useState } from "react"
import Link from "next/link"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ArrowRight, TrendingUp, Users, CheckCircle, Shield } from "lucide-react"

// Mock data for traders
const topBalancedTraders = [
  {
    id: "1",
    name: "OB-Anderson",
    avatar: "/avatars/1.jpg",
    verified: true,
    teeAttested: true,
    roi: "9834.25%",
    roiValue: 9834.25,
    winRate: 72,
    lossRate: 28,
    badges: ["2K-VERIFIED", "TEE-ATTESTED"],
    chartData: [20, 40, 35, 50, 49, 60, 70, 91, 100],
  },
  {
    id: "2",
    name: "OB-Harris",
    avatar: "/avatars/2.jpg",
    verified: true,
    teeAttested: true,
    roi: "7978.46%",
    roiValue: 7978.46,
    winRate: 72,
    lossRate: 28,
    badges: ["2K-VERIFIED", "TEE-ATTESTED"],
    chartData: [15, 25, 35, 45, 55, 65, 75, 85, 95],
  },
  {
    id: "3",
    name: "OB-White",
    avatar: "/avatars/3.jpg",
    verified: true,
    teeAttested: true,
    roi: "5641.04%",
    roiValue: 5641.04,
    winRate: 72,
    lossRate: 28,
    badges: ["2K-VERIFIED", "TEE-ATTESTED"],
    chartData: [10, 30, 25, 40, 50, 55, 65, 75, 80],
  },
  {
    id: "4",
    name: "OB-Davis",
    avatar: "/avatars/4.jpg",
    verified: true,
    teeAttested: true,
    roi: "5884.63%",
    roiValue: 5884.63,
    winRate: 72,
    lossRate: 28,
    badges: ["2K-VERIFIED", "TEE-ATTESTED"],
    chartData: [25, 35, 30, 45, 55, 60, 70, 80, 90],
  },
]

const MiniChart = ({ data }: { data: number[] }) => {
  const max = Math.max(...data)
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 100
    const y = 100 - (value / max) * 100
    return `${x},${y}`
  }).join(' ')

  return (
    <svg viewBox="0 0 100 40" className="w-full h-12" preserveAspectRatio="none">
      <defs>
        <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="rgb(46, 243, 227)" stopOpacity="0.3" />
          <stop offset="100%" stopColor="rgb(46, 243, 227)" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline
        points={`0,100 ${points} 100,100`}
        fill="url(#chartGradient)"
      />
      <polyline
        points={points}
        fill="none"
        stroke="rgb(46, 243, 227)"
        strokeWidth="2"
      />
    </svg>
  )
}

const highROITraders = [
  {
    id: "5",
    name: "OB-Miller",
    avatar: "/avatars/5.jpg",
    verified: true,
    teeAttested: true,
    roi: "2191.31%",
    roiValue: 2191.31,
    winRate: 72,
    lossRate: 28,
    badges: ["2K-VERIFIED", "TEE-ATTESTED"],
    chartData: [20, 35, 30, 45, 50, 55, 60, 70, 75],
  },
  {
    id: "6",
    name: "OB-Brown",
    avatar: "/avatars/6.jpg",
    verified: true,
    teeAttested: true,
    roi: "3065.43%",
    roiValue: 3065.43,
    winRate: 72,
    lossRate: 28,
    badges: ["2K-VERIFIED", "TEE-ATTESTED"],
    chartData: [15, 30, 35, 50, 60, 70, 80, 90, 95],
  },
  {
    id: "7",
    name: "OB-Anderson",
    avatar: "/avatars/7.jpg",
    verified: true,
    teeAttested: true,
    roi: "771.09%",
    roiValue: 771.09,
    winRate: 72,
    lossRate: 28,
    badges: ["2K-VERIFIED", "TEE-ATTESTED"],
    chartData: [10, 20, 25, 30, 35, 40, 45, 50, 55],
  },
  {
    id: "8",
    name: "OB-Miller",
    avatar: "/avatars/8.jpg",
    verified: true,
    teeAttested: true,
    roi: "6640.85%",
    roiValue: 6640.85,
    winRate: 72,
    lossRate: 28,
    badges: ["2K-VERIFIED", "TEE-ATTESTED"],
    chartData: [25, 40, 45, 60, 70, 80, 85, 95, 100],
  },
]

const mostCopiedTraders = [
  {
    id: "9",
    name: "OB-Davis",
    avatar: "/avatars/9.jpg",
    verified: true,
    teeAttested: true,
    roi: "5460.82%",
    roiValue: 5460.82,
    winRate: 72,
    lossRate: 28,
    badges: ["2K-VERIFIED", "TEE-ATTESTED"],
    chartData: [20, 30, 40, 50, 60, 65, 70, 75, 80],
  },
  {
    id: "10",
    name: "OB-Moore",
    avatar: "/avatars/10.jpg",
    verified: true,
    teeAttested: true,
    roi: "9946.63%",
    roiValue: 9946.63,
    winRate: 72,
    lossRate: 28,
    badges: ["2K-VERIFIED", "TEE-ATTESTED"],
    chartData: [30, 45, 55, 70, 80, 85, 90, 95, 98],
  },
  {
    id: "11",
    name: "OB-Brown",
    avatar: "/avatars/11.jpg",
    verified: true,
    teeAttested: true,
    roi: "8226.66%",
    roiValue: 8226.66,
    winRate: 72,
    lossRate: 28,
    badges: ["2K-VERIFIED", "TEE-ATTESTED"],
    chartData: [25, 35, 50, 60, 70, 75, 80, 85, 88],
  },
  {
    id: "12",
    name: "OB-Moore",
    avatar: "/avatars/12.jpg",
    verified: true,
    teeAttested: true,
    roi: "4435.11%",
    roiValue: 4435.11,
    winRate: 72,
    lossRate: 28,
    badges: ["2K-VERIFIED", "TEE-ATTESTED"],
    chartData: [15, 25, 35, 45, 55, 60, 65, 70, 72],
  },
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-8">
        {/* Welcome Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12">
          <div className="lg:col-span-2">
            <h1 className="text-4xl font-bold mb-2">
              Welcome to Obscura,{" "}
              <span className="text-primary">Octavian.mx</span>
            </h1>
            <p className="text-muted-foreground">
              Start by exploring verified traders and see who fits your style.
            </p>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground mb-1">Realized PnL</div>
                  <div className="text-sm text-muted-foreground mb-1">Last 7days</div>
                  <div className="text-2xl font-bold text-success">+4,200%</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground mb-1">Verified Traders</div>
                  <div className="text-sm text-muted-foreground mb-1">Last 7days</div>
                  <div className="text-2xl font-bold">10,204</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground mb-1">Trades Verified</div>
                  <div className="text-sm text-muted-foreground mb-1">Last 7days</div>
                  <div className="text-2xl font-bold">32,000,000+</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground mb-1">Active Followers</div>
                  <div className="text-2xl font-bold">800,000+</div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* CTA Card */}
          <Card className="bg-gradient-to-br from-cyan-60 to-cyan-100 border-cyan-200">
            <CardContent className="p-6">
              <h3 className="text-xl font-bold mb-2">
                Join expert traders and start sending verified signals
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                Become part of an elite network of real traders. Share your trades privately, get verified instantly, and build a public reputation.
              </p>
              <Button className="w-full bg-primary hover:bg-primary/90 text-black font-medium rounded-full">
                Get Started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Top Balanced Traders */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold">Top Balanced Traders</h2>
              <p className="text-sm text-muted-foreground">
                Traders with steady ROI, controlled risk, and consistent performance.
              </p>
            </div>
            <Link href="/explore">
              <Button variant="ghost" className="gap-2">
                See all <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {topBalancedTraders.map((trader) => (
              <Card key={trader.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-4">
                  {/* Trader Header */}
                  <div className="flex items-center gap-3 mb-4">
                    <Avatar className="w-12 h-12">
                      <AvatarFallback className="bg-muted text-muted-foreground">
                        {trader.name.slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="flex items-center gap-1">
                        <span className="font-semibold">{trader.name}</span>
                        {trader.verified && (
                          <CheckCircle className="w-4 h-4 text-primary" />
                        )}
                      </div>
                      <div className="flex gap-1 mt-1">
                        {trader.badges.map((badge) => (
                          <Badge
                            key={badge}
                            variant="secondary"
                            className="text-xs px-1.5 py-0"
                          >
                            {badge}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* ROI */}
                  <div className="mb-2">
                    <div className="text-xs text-muted-foreground mb-1">ROI 7D</div>
                    <div className="text-xl font-bold text-success">{trader.roi}</div>
                  </div>

                  {/* Chart */}
                  <div className="mb-3">
                    <MiniChart data={trader.chartData} />
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div>
                      <div className="text-muted-foreground">Win rate</div>
                      <div className="font-semibold">{trader.winRate}%</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Loss rate</div>
                      <div className="font-semibold">{trader.lossRate}%</div>
                    </div>
                  </div>

                  {/* Platform Icons */}
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-5 h-5 rounded-full bg-yellow-400 flex items-center justify-center text-xs">₿</div>
                    <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center text-xs text-white">◎</div>
                    <div className="w-5 h-5 rounded-full bg-gray-800 flex items-center justify-center text-xs text-white">≡</div>
                    <span className="text-xs text-muted-foreground ml-auto">2</span>
                    <TrendingUp className="w-4 h-4" />
                    <span className="text-xs">10%</span>
                  </div>

                  {/* Copy Button */}
                  <Button className="w-full bg-primary hover:bg-primary/90 text-black font-medium rounded-full text-sm h-9">
                    Copy
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* High ROI Traders */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold">High ROI Traders</h2>
              <p className="text-sm text-muted-foreground">
                Traders delivering the highest percentage returns over the selected timeframe.
              </p>
            </div>
            <Link href="/explore">
              <Button variant="ghost" className="gap-2">
                See all <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {highROITraders.map((trader) => (
              <Card key={trader.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-4">
                  {/* Trader Header */}
                  <div className="flex items-center gap-3 mb-4">
                    <Avatar className="w-12 h-12">
                      <AvatarFallback className="bg-muted text-muted-foreground">
                        {trader.name.slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="flex items-center gap-1">
                        <span className="font-semibold">{trader.name}</span>
                        {trader.verified && (
                          <CheckCircle className="w-4 h-4 text-primary" />
                        )}
                      </div>
                      <div className="flex gap-1 mt-1">
                        {trader.badges.map((badge) => (
                          <Badge
                            key={badge}
                            variant="secondary"
                            className="text-xs px-1.5 py-0"
                          >
                            {badge}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* ROI */}
                  <div className="mb-2">
                    <div className="text-xs text-muted-foreground mb-1">ROI 7D</div>
                    <div className="text-xl font-bold text-success">{trader.roi}</div>
                  </div>

                  {/* Chart */}
                  <div className="mb-3">
                    <MiniChart data={trader.chartData} />
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div>
                      <div className="text-muted-foreground">Win rate</div>
                      <div className="font-semibold">{trader.winRate}%</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Loss rate</div>
                      <div className="font-semibold">{trader.lossRate}%</div>
                    </div>
                  </div>

                  {/* Platform Icons */}
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-5 h-5 rounded-full bg-yellow-400 flex items-center justify-center text-xs">₿</div>
                    <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center text-xs text-white">◎</div>
                    <div className="w-5 h-5 rounded-full bg-gray-800 flex items-center justify-center text-xs text-white">≡</div>
                    <span className="text-xs text-muted-foreground ml-auto">2</span>
                    <TrendingUp className="w-4 h-4" />
                    <span className="text-xs">10%</span>
                  </div>

                  {/* Copy Button */}
                  <Button className="w-full bg-primary hover:bg-primary/90 text-black font-medium rounded-full text-sm h-9">
                    Copy
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Most Copied Traders */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold">Most Copied Traders</h2>
              <p className="text-sm text-muted-foreground">
                The traders currently followed the most by Obscura's community.
              </p>
            </div>
            <Link href="/explore">
              <Button variant="ghost" className="gap-2">
                See all <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {mostCopiedTraders.map((trader) => (
              <Card key={trader.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-4">
                  {/* Trader Header */}
                  <div className="flex items-center gap-3 mb-4">
                    <Avatar className="w-12 h-12">
                      <AvatarFallback className="bg-muted text-muted-foreground">
                        {trader.name.slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="flex items-center gap-1">
                        <span className="font-semibold">{trader.name}</span>
                        {trader.verified && (
                          <CheckCircle className="w-4 h-4 text-primary" />
                        )}
                      </div>
                      <div className="flex gap-1 mt-1">
                        {trader.badges.map((badge) => (
                          <Badge
                            key={badge}
                            variant="secondary"
                            className="text-xs px-1.5 py-0"
                          >
                            {badge}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* ROI */}
                  <div className="mb-2">
                    <div className="text-xs text-muted-foreground mb-1">ROI 7D</div>
                    <div className="text-xl font-bold text-success">{trader.roi}</div>
                  </div>

                  {/* Chart */}
                  <div className="mb-3">
                    <MiniChart data={trader.chartData} />
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div>
                      <div className="text-muted-foreground">Win rate</div>
                      <div className="font-semibold">{trader.winRate}%</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Loss rate</div>
                      <div className="font-semibold">{trader.lossRate}%</div>
                    </div>
                  </div>

                  {/* Platform Icons */}
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-5 h-5 rounded-full bg-yellow-400 flex items-center justify-center text-xs">₿</div>
                    <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center text-xs text-white">◎</div>
                    <div className="w-5 h-5 rounded-full bg-gray-800 flex items-center justify-center text-xs text-white">≡</div>
                    <span className="text-xs text-muted-foreground ml-auto">2</span>
                    <TrendingUp className="w-4 w-4" />
                    <span className="text-xs">10%</span>
                  </div>

                  {/* Copy Button */}
                  <Button className="w-full bg-primary hover:bg-primary/90 text-black font-medium rounded-full text-sm h-9">
                    Copy
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  )
}
