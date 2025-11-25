"use client"

import { useState } from "react"
import Link from "next/link"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Search, CheckCircle, Copy, List, LayoutGrid } from "lucide-react"

const traders = [
  {
    id: "1",
    name: "OB-Williams",
    verified: true,
    roi: "9871.9%",
    pnl: "1648.28%",
    followingPnl: "305.27%",
    winRate: "87.58%",
    followers: 669,
  },
  {
    id: "2",
    name: "OB-Jones",
    verified: true,
    roi: "449.89%",
    pnl: "2495.62%",
    followingPnl: "2317.63%",
    winRate: "43.19%",
    followers: 275,
  },
  {
    id: "3",
    name: "OB-Wilson",
    verified: true,
    roi: "2467.30%",
    pnl: "374.38%",
    followingPnl: "2153.39%",
    winRate: "31.92%",
    followers: 715,
  },
  {
    id: "4",
    name: "OB-Wilson",
    verified: true,
    roi: "2280.16%",
    pnl: "1285.27%",
    followingPnl: "1238.60%",
    winRate: "22.91%",
    followers: 616,
  },
  {
    id: "5",
    name: "OB-White",
    verified: true,
    roi: "762.60%",
    pnl: "719.88%",
    followingPnl: "613.91%",
    winRate: "79.48%",
    followers: 111,
  },
  {
    id: "6",
    name: "OB-Johnson",
    verified: true,
    roi: "1760.12%",
    pnl: "1953.15%",
    followingPnl: "2781.28%",
    winRate: "47.14%",
    followers: 33,
  },
]

export default function ExplorePage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [timeFilter, setTimeFilter] = useState("7d")
  const [categoryFilter, setCategoryFilter] = useState("all")
  const [platformFilter, setPlatformFilter] = useState("all")
  const [verifiedOnly, setVerifiedOnly] = useState(false)
  const [viewMode, setViewMode] = useState<"list" | "grid">("list")

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Explore Traders</h1>
          <p className="text-muted-foreground">
            Find traders with verified performance and choose who fits your strategy.
          </p>
          <p className="text-sm text-muted-foreground">
            ROI and performance shown only as percentages.
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

            {/* Time Filter */}
            <Select value={timeFilter} onValueChange={setTimeFilter}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="7d" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">7d</SelectItem>
                <SelectItem value="30d">30d</SelectItem>
                <SelectItem value="90d">90d</SelectItem>
                <SelectItem value="all">All time</SelectItem>
              </SelectContent>
            </Select>

            {/* Category Filter */}
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="balanced">Balanced</SelectItem>
                <SelectItem value="aggressive">Aggressive</SelectItem>
                <SelectItem value="conservative">Conservative</SelectItem>
              </SelectContent>
            </Select>

            {/* Platform Filter */}
            <Select value={platformFilter} onValueChange={setPlatformFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Platform" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Platforms</SelectItem>
                <SelectItem value="binance">Binance</SelectItem>
                <SelectItem value="bybit">Bybit</SelectItem>
                <SelectItem value="okx">OKX</SelectItem>
              </SelectContent>
            </Select>

            {/* Verified Only Toggle */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="verified"
                checked={verifiedOnly}
                onChange={(e) => setVerifiedOnly(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300"
              />
              <label htmlFor="verified" className="text-sm whitespace-nowrap">
                Verified Only
              </label>
            </div>

            {/* View Mode Toggle */}
            <div className="flex gap-1 border rounded-md p-1">
              <button
                onClick={() => setViewMode("list")}
                className={`p-2 rounded ${viewMode === "list" ? "bg-gray-100" : ""}`}
              >
                <List className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode("grid")}
                className={`p-2 rounded ${viewMode === "grid" ? "bg-gray-100" : ""}`}
              >
                <LayoutGrid className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Trader Count */}
        <div className="mb-4">
          <h2 className="text-xl font-semibold">
            Trader <span className="text-muted-foreground">10,267</span>
          </h2>
        </div>

        {/* Traders Table */}
        <div className="bg-card rounded-lg shadow-sm overflow-hidden border">
          <table className="w-full">
            <thead className="bg-muted border-b">
              <tr>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                  Trader ↕
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                  ROI ↕
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                  PnL ↕
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                  Following PnL ↕
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                  Win Rate ↕
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                  Followers ↕
                </th>
                <th className="text-right py-3 px-4"></th>
              </tr>
            </thead>
            <tbody>
              {traders.map((trader, index) => (
                <tr key={trader.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-3">
                      <Avatar className="w-10 h-10">
                        <AvatarFallback className="bg-pink-200">
                          {trader.name.slice(0, 2)}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{trader.name}</span>
                        {trader.verified && (
                          <CheckCircle className="w-4 h-4 text-primary" />
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <span className="text-green-600 font-medium">{trader.roi}</span>
                  </td>
                  <td className="py-4 px-4">
                    <span className="font-medium">{trader.pnl}</span>
                  </td>
                  <td className="py-4 px-4">
                    <span className="font-medium">{trader.followingPnl}</span>
                  </td>
                  <td className="py-4 px-4">
                    <span className="font-medium">{trader.winRate}</span>
                  </td>
                  <td className="py-4 px-4">
                    <span className="font-medium">{trader.followers}</span>
                  </td>
                  <td className="py-4 px-4 text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-2"
                    >
                      <Copy className="h-3 w-3" />
                      Copy
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
