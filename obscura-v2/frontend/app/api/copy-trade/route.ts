import { NextResponse } from "next/server"

export async function POST(request: Request) {
  const body = await request.json()

  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 1000))

  // Mock successful copy trade activation
  return NextResponse.json({
    success: true,
    copyTradeId: `ct_${Date.now()}`,
    traderId: body.traderId,
    amount: body.amount,
    settings: body.settings,
    activatedAt: new Date().toISOString(),
  })
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const userId = searchParams.get("userId")

  // Mock active copy trades
  return NextResponse.json({
    copyTrades: [
      {
        id: "ct_1",
        traderId: "1",
        traderName: "CryptoWhale",
        amount: 5000,
        activeSince: new Date("2024-05-01").toISOString(),
        totalPnL: 450,
        status: "active",
      },
      {
        id: "ct_2",
        traderId: "2",
        traderName: "ZKMaster",
        amount: 3000,
        activeSince: new Date("2024-05-05").toISOString(),
        totalPnL: 280,
        status: "active",
      },
    ],
  })
}
