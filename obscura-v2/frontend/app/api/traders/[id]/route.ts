import { NextResponse } from "next/server"
import { getTraderById } from "@/lib/mock-data"

export async function GET(request: Request, { params }: { params: { id: string } }) {
  const trader = getTraderById(params.id)

  if (!trader) {
    return NextResponse.json({ error: "Trader not found" }, { status: 404 })
  }

  return NextResponse.json({ trader })
}
