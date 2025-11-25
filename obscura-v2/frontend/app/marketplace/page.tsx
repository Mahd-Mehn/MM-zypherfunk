"use client"

import { useMemo, useState } from "react"
import Link from "next/link"
import { Header } from "@/components/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Search, ArrowRight, Star, Filter, X, AlertTriangle } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import TraderCard from "@/components/reusable/TraderCard"
import { useTraders } from "@/hooks/use-traders"

export default function MarketplacePage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [verificationFilter, setVerificationFilter] = useState<string>("all")
  const [chainFilter, setChainFilter] = useState<string>("all")
  const [sortBy, setSortBy] = useState<string>("winRate")

  const traderFilters = useMemo(() => {
    return {
      search: searchQuery || undefined,
      verificationType: verificationFilter !== "all" ? verificationFilter : undefined,
      chain: chainFilter !== "all" ? chainFilter : undefined,
      sortBy: sortBy as "followers" | "winRate" | "pnl" | "trades",
      limit: 30,
    }
  }, [searchQuery, verificationFilter, chainFilter, sortBy])

  const { traders, total, loading, error } = useTraders(traderFilters)

  const hasActiveFilters = verificationFilter !== "all" || chainFilter !== "all" || searchQuery !== ""

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <div className="relative border-b bg-gradient-to-br from-purple-500/10 via-primary/5 to-background overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,hsl(var(--border))_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border))_1px,transparent_1px)] bg-[size:4rem_4rem] opacity-50" />
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />

        <div className="container relative mx-auto px-4 lg:px-8 py-12 lg:py-16">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 bg-gradient-to-r from-purple-500/20 to-primary/20 border border-purple-500/30 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Star className="h-4 w-4 text-purple-400 fill-purple-400" />
              <span className="font-bold">
                {loading ? "Loading" : `${total || traders.length}+`} Verified Traders
              </span>
            </div>
            <h1 className="text-4xl lg:text-5xl font-bold mb-4">Discover Top Traders</h1>
            <p className="text-lg lg:text-xl text-muted-foreground">
              Browse cryptographically verified traders and copy their strategies. All performance metrics are proven
              on-chain.
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 lg:px-8 py-8 lg:py-12">
        <Card className="mb-8 border-purple-500/30 bg-gradient-to-br from-purple-500/5 to-card shadow-lg">
          <CardContent className="p-6">
            <div className="space-y-4">
              {/* Search bar */}
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <Input
                  placeholder="Search by name or address..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-12 h-12 text-base"
                />
                {searchQuery && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8"
                    onClick={() => setSearchQuery("")}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>

              {/* Filters row */}
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <Filter className="h-4 w-4" />
                  <span>Filters:</span>
                </div>

                <div className="flex flex-wrap gap-3 flex-1">
                  <Select value={verificationFilter} onValueChange={setVerificationFilter}>
                    <SelectTrigger className="w-[180px] h-10">
                      <SelectValue placeholder="Verification" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="ZK">ZK-Verified</SelectItem>
                      <SelectItem value="TEE">TEE-Attested</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select value={chainFilter} onValueChange={setChainFilter}>
                    <SelectTrigger className="w-[180px] h-10">
                      <SelectValue placeholder="Chain" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Chains</SelectItem>
                      <SelectItem value="Arbitrum">Arbitrum</SelectItem>
                      <SelectItem value="Base">Base</SelectItem>
                      <SelectItem value="Aptos">Aptos</SelectItem>
                      <SelectItem value="Ethereum">Ethereum</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger className="w-[180px] h-10">
                      <SelectValue placeholder="Sort by" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="winRate">Win Rate</SelectItem>
                      <SelectItem value="totalPnL">Total PnL</SelectItem>
                      <SelectItem value="followers">Followers</SelectItem>
                      <SelectItem value="trades">Total Trades</SelectItem>
                    </SelectContent>
                  </Select>

                  {hasActiveFilters && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSearchQuery("")
                        setVerificationFilter("all")
                        setChainFilter("all")
                      }}
                      className="h-10"
                    >
                      <X className="h-4 w-4 mr-2" />
                      Clear All
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results count */}
        <div className="mb-6 flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            {loading ? (
              "Loading traders..."
            ) : (
              <>
                Showing <span className="font-bold text-foreground">{traders.length}</span>{" "}
                {traders.length === 1 ? "trader" : "traders"}
              </>
            )}
          </div>
        </div>

        {error && !loading && (
          <div className="mb-8 flex items-center gap-2 rounded-2xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            <AlertTriangle className="h-4 w-4" />
            Failed to load live traders. Please try again.
          </div>
        )}

        {loading ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-[420px] rounded-[32px] border border-white/10 bg-[#050E16]/60 animate-pulse" />
            ))}
          </div>
        ) : traders.length > 0 ? (
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {traders.map((trader) => (
              <div key={trader.id} className="flex flex-col items-center">
                <TraderCard trader={trader} className="w-full" />
                <div className="mt-4 flex w-full gap-2">
                  <Button
                    asChild
                    className="flex-1 h-11 bg-gradient-to-r from-purple-600 to-primary hover:from-purple-700 hover:to-primary/90"
                    size="sm"
                  >
                    <Link href={`/trader/${trader.id}`}>
                      View Profile
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-11 px-5 border-purple-500/40 text-purple-600"
                    asChild
                  >
                    <Link href={`/copy/${trader.id}`}>Copy</Link>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <Card className="border-border/50">
            <CardContent className="p-16 lg:p-24">
              <div className="text-center space-y-6 max-w-md mx-auto">
                <div className="h-20 w-20 rounded-full bg-muted/50 flex items-center justify-center mx-auto">
                  <Search className="h-10 w-10 text-muted-foreground" />
                </div>
                <div>
                  <h3 className="text-2xl prepare font-bold mb-2">No traders found</h3>
                  <p className="text-muted-foreground">
                    Try adjusting your filters or search query to discover traders.
                  </p>
                </div>
                <Button
                  variant="outline"
                  onClick={() => {
                    setSearchQuery("")
                    setVerificationFilter("all")
                    setChainFilter("all")
                  }}
                >
                  Clear All Filters
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
