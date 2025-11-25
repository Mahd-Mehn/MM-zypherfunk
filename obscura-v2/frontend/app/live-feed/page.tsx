"use client"

import { useState } from "react"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Search, CheckCircle, Copy, TrendingUp } from "lucide-react"
import { Input } from "@/components/ui/input"

const MiniChart = ({ data }: { data: number[] }) => {
  const max = Math.max(...data)
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 100
    const y = 100 - (value / max) * 100
    return `${x},${y}`
  }).join(' ')

  return (
    <svg viewBox="0 0 100 30" className="w-full h-8" preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        stroke="rgb(46, 243, 227)"
        strokeWidth="2"
      />
    </svg>
  )
}

const trades = [
  {
    id: "1",
    pair: "BTC/USDT",
    pairIcon: "₿",
    pairIconBg: "bg-yellow-400",
    type: "SHORT",
    verified: true,
    followers: 265,
    roi: "4678.45%",
    chartData: [20, 40, 35, 50, 49, 60, 70, 91, 100],
    runTime: "12h 55m",
    maxDrawdown: "1,672.35%",
    profitShareRatio: "28%",
    creator: "Octavian.mc",
  },
  {
    id: "2",
    pair: "ETH/USDT",
    pairIcon: "Ξ",
    pairIconBg: "bg-blue-500",
    type: "LONG",
    verified: true,
    followers: 217,
    roi: "6658.97%",
    chartData: [15, 25, 35, 45, 55, 65, 75, 85, 95],
    runTime: "12h 55m",
    maxDrawdown: "1,672.35%",
    profitShareRatio: "28%",
    creator: "Octavian.mc",
  },
  {
    id: "3",
    pair: "ETH/WBTC",
    pairIcon: "Ξ",
    pairIconBg: "bg-purple-500",
    type: "LONG",
    verified: true,
    followers: 62,
    roi: "1426.15%",
    chartData: [10, 30, 25, 40, 50, 55, 65, 75, 80],
    runTime: "12h 55m",
    maxDrawdown: "1,672.35%",
    profitShareRatio: "28%",
    creator: "Octavian.mc",
  },
  {
    id: "4",
    pair: "SOL/USDT",
    pairIcon: "◎",
    pairIconBg: "bg-purple-600",
    type: "LONG",
    verified: true,
    followers: 81,
    roi: "1221.83%",
    chartData: [25, 35, 30, 45, 55, 60, 70, 80, 90],
    runTime: "12h 55m",
    maxDrawdown: "1,672.35%",
    profitShareRatio: "28%",
    creator: "Octavian.mc",
  },
  {
    id: "5",
    pair: "BNB/USDT",
    pairIcon: "B",
    pairIconBg: "bg-yellow-500",
    type: "LONG",
    verified: true,
    followers: 232,
    roi: "1334.60%",
    chartData: [20, 30, 40, 50, 60, 70, 80, 90, 85],
    runTime: "12h 55m",
    maxDrawdown: "1,672.35%",
    profitShareRatio: "28%",
    creator: "Octavian.mc",
  },
  {
    id: "6",
    pair: "XRP/USDT",
    pairIcon: "X",
    pairIconBg: "bg-gray-700",
    type: "LONG",
    verified: true,
    followers: 58,
    roi: "813.72%",
    chartData: [15, 20, 25, 35, 45, 50, 55, 60, 65],
    runTime: "12h 55m",
    maxDrawdown: "1,672.35%",
    profitShareRatio: "28%",
    creator: "Octavian.mc",
  },
  {
    id: "7",
    pair: "ETH/USDC",
    pairIcon: "Ξ",
    pairIconBg: "bg-blue-600",
    type: "LONG",
    verified: true,
    followers: 133,
    roi: "7.82%",
    chartData: [50, 48, 52, 49, 51, 50, 52, 51, 50],
    runTime: "12h 55m",
    maxDrawdown: "1,672.35%",
    profitShareRatio: "28%",
    creator: "Octavian.mc",
  },
  {
    id: "8",
    pair: "AAVE/ETH",
    pairIcon: "A",
    pairIconBg: "bg-purple-400",
    type: "LONG",
    verified: true,
    followers: 226,
    roi: "759.40%",
    chartData: [30, 40, 35, 50, 55, 60, 65, 70, 75],
    runTime: "12h 55m",
    maxDrawdown: "1,672.35%",
    profitShareRatio: "28%",
    creator: "Octavian.mc",
  },
]

export default function LiveFeedPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [assetFilter, setAssetFilter] = useState("all")
  const [typeFilter, setTypeFilter] = useState("all")

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Live Feed</h1>
          <p className="text-muted-foreground">
            Real-time verified trades from verified traders
          </p>
          <p className="text-sm text-muted-foreground">
            and also traders you follow
          </p>
        </div>

        {/* Filters */}
        <div className="bg-card rounded-lg shadow-sm p-4 mb-6 border">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="search trader"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Asset Pairs Filter */}
            <Select value={assetFilter} onValueChange={setAssetFilter}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Asset Pairs" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="btc">BTC Pairs</SelectItem>
                <SelectItem value="eth">ETH Pairs</SelectItem>
                <SelectItem value="sol">SOL Pairs</SelectItem>
              </SelectContent>
            </Select>

            {/* Type Filter */}
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="long">Long</SelectItem>
                <SelectItem value="short">Short</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Trade Count */}
        <div className="mb-4">
          <h2 className="text-xl font-semibold">
            Trades <span className="text-muted-foreground">10,267</span>
          </h2>
        </div>

        {/* Trades Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {trades.map((trade) => (
            <Card key={trade.id} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-4">
                {/* Trade Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-full ${trade.pairIconBg} flex items-center justify-center text-white font-bold`}>
                      {trade.pairIcon}
                    </div>
                    <div className={`w-6 h-6 rounded-full ${trade.pairIconBg} flex items-center justify-center text-white text-xs -ml-3`}>
                      $
                    </div>
                  </div>
                  <Badge
                    variant={trade.type === "LONG" ? "default" : "secondary"}
                    className={trade.type === "LONG" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}
                  >
                    {trade.type}
                  </Badge>
                </div>

                <div className="flex items-center gap-2 mb-3">
                  <span className="font-bold">{trade.pair}</span>
                  {trade.verified && (
                    <CheckCircle className="w-4 h-4 text-primary" />
                  )}
                  <span className="text-xs text-muted-foreground ml-auto">
                    👥 {trade.followers}
                  </span>
                </div>

                {/* ROI */}
                <div className="mb-2">
                  <div className="text-xs text-muted-foreground">ROI</div>
                  <div className="text-xl font-bold text-green-600">{trade.roi}</div>
                </div>

                {/* Chart */}
                <div className="mb-3">
                  <MiniChart data={trade.chartData} />
                </div>

                {/* Stats */}
                <div className="space-y-1 text-xs mb-3">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Run Time</span>
                    <span className="font-medium">{trade.runTime}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Max Drawdown</span>
                    <span className="font-medium">{trade.maxDrawdown}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Profit Share Ratio</span>
                    <span className="font-medium">{trade.profitShareRatio}</span>
                  </div>
                </div>

                {/* Creator */}
                <div className="flex items-center gap-2 mb-3 text-xs">
                  <span className="text-muted-foreground">Creator</span>
                  <Avatar className="w-4 h-4">
                    <AvatarFallback className="bg-pink-200 text-xs">
                      O
                    </AvatarFallback>
                  </Avatar>
                  <span className="text-red-500">{trade.creator}</span>
                </div>

                {/* Copy Button */}
                <Button className="w-full bg-primary hover:bg-primary/90 text-black font-medium rounded-full text-sm h-9">
                  Copy
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Pagination */}
        <div className="flex justify-center items-center gap-2 mt-6">
          <Button variant="ghost" size="sm">←</Button>
          <Button variant="ghost" size="sm">1</Button>
          <Button variant="ghost" size="sm">2</Button>
          <Button variant="default" size="sm" className="bg-primary text-black">3</Button>
          <Button variant="ghost" size="sm">4</Button>
          <Button variant="ghost" size="sm">5</Button>
          <Button variant="ghost" size="sm">6</Button>
          <span className="text-muted-foreground">...</span>
          <Button variant="ghost" size="sm">567</Button>
          <Button variant="ghost" size="sm">→</Button>
        </div>
      </main>

      <Footer />
    </div>
  )
}
