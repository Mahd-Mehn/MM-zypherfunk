import { NextResponse } from "next/server"
import { generatePerformanceData } from "@/lib/mock-data"

export async function GET(request: Request, { params }: { params: { id: string } }) {
  const { searchParams } = new URL(request.url)
  const days = Number.parseInt(searchParams.get("days") || "30")

  const data = generatePerformanceData(days)

  return NextResponse.json({ data, traderId: params.id })
}
