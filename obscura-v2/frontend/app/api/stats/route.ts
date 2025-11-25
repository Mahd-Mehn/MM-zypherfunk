import { NextResponse } from "next/server"
import { mockTraders, mockTrades } from "@/lib/mock-data"

export async function GET() {
  const totalTraders = mockTraders.length
  const totalTrades = mockTrades.reduce((sum, trade) => sum + 1, 0)
  const totalVolume = mockTrades.reduce((sum, trade) => sum + trade.amountIn, 0)
  const totalPnL = mockTraders.reduce((sum, trader) => sum + trader.totalPnL, 0)
  const avgWinRate = mockTraders.reduce((sum, trader) => sum + trader.winRate, 0) / totalTraders

  return NextResponse.json({
    totalTraders,
    totalTrades,
    totalVolume: Math.round(totalVolume),
    totalPnL: Math.round(totalPnL),
    avgWinRate: Math.round(avgWinRate * 10) / 10,
    zkVerified: mockTraders.filter((t) => t.verificationType.includes("ZK")).length,
    teeVerified: mockTraders.filter((t) => t.verificationType.includes("TEE")).length,
  })
}
