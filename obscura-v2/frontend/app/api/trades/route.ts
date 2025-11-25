import { NextResponse } from "next/server"
import { mockTrades } from "@/lib/mock-data"

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const traderId = searchParams.get("traderId")
  const limit = Number.parseInt(searchParams.get("limit") || "50")

  let filtered = [...mockTrades]

  if (traderId) {
    filtered = filtered.filter((trade) => trade.traderId === traderId)
  }

  // Sort by timestamp descending
  filtered.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())

  // Apply limit
  filtered = filtered.slice(0, limit)

  return NextResponse.json({ trades: filtered, total: filtered.length })
}
