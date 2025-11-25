import { NextResponse } from "next/server"
import { mockTraders } from "@/lib/mock-data"

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const search = searchParams.get("search")
  const verificationType = searchParams.get("verificationType")
  const chain = searchParams.get("chain")
  const sortBy = searchParams.get("sortBy") || "followers"

  let filtered = [...mockTraders]

  // Apply filters
  if (search) {
    filtered = filtered.filter(
      (trader) =>
        trader.displayName.toLowerCase().includes(search.toLowerCase()) ||
        trader.address.toLowerCase().includes(search.toLowerCase()),
    )
  }

  if (verificationType && verificationType !== "all") {
    filtered = filtered.filter((trader) => trader.verificationType.includes(verificationType as any))
  }

  if (chain && chain !== "all") {
    filtered = filtered.filter((trader) => trader.chains.includes(chain as any))
  }

  // Apply sorting
  filtered.sort((a, b) => {
    switch (sortBy) {
      case "winRate":
        return b.winRate - a.winRate
      case "pnl":
        return b.totalPnL - a.totalPnL
      case "trades":
        return b.totalTrades - a.totalTrades
      case "followers":
      default:
        return b.followers - a.followers
    }
  })

  return NextResponse.json({ traders: filtered, total: filtered.length })
}
