"use client"

import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { Card, CardContent } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

const verifiedTrades = [
  { pair: "ACH/USDT", type: "LONG", platform: "Binance", roi: "+2,679.46%" },
  { pair: "ACH/USDT", type: "LONG", platform: "Binance", roi: "+2,679.46%" },
  { pair: "ACH/USDT", type: "LONG", platform: "Binance", roi: "+2,679.46%" },
  { pair: "ACH/USDT", type: "LONG", platform: "Binance", roi: "+2,679.46%" },
  { pair: "ACH/USDT", type: "LONG", platform: "Binance", roi: "+2,679.46%" },
]

const copiedTrades = [
  { pair: "ACH/USDT", type: "LONG", platform: "Binance", roi: "+2,679.46%" },
  { pair: "ACH/USDT", type: "LONG", platform: "Binance", roi: "+2,679.46%" },
  { pair: "ACH/USDT", type: "LONG", platform: "Binance", roi: "+2,679.46%" },
  { pair: "ACH/USDT", type: "LONG", platform: "Binance", roi: "+2,679.46%" },
  { pair: "ACH/USDT", type: "LONG", platform: "Binance", roi: "+2,679.46%" },
]

export default function MyProfilePage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Profile Header */}
        <div className="flex items-center gap-4 mb-8">
          <Avatar className="w-24 h-24">
            <AvatarFallback className="bg-gray-300 text-3xl">O</AvatarFallback>
          </Avatar>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <h1 className="text-3xl font-bold">Octavianmx</h1>
              <Badge variant="secondary" className="text-xs">VERIFIED</Badge>
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span><span className="font-semibold text-foreground">23</span> Following</span>
              <span><span className="font-semibold text-foreground">324</span> Followers</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="overview" className="mb-8">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="trades">Trades</TabsTrigger>
            <TabsTrigger value="followings">Followings</TabsTrigger>
            <TabsTrigger value="wallets">Wallets/Accounts</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Performance Card */}
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold">Performance</h3>
                    <select className="text-sm border rounded px-2 py-1">
                      <option>7d</option>
                      <option>30d</option>
                      <option>90d</option>
                    </select>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">ROI</div>
                      <div className="text-3xl font-bold text-green-600">+48,008.33%</div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-muted-foreground mb-1">Trades Verified</div>
                        <div className="font-semibold">243</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground mb-1">Win rate</div>
                        <div className="font-semibold">72%</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground mb-1">Loss rate</div>
                        <div className="font-semibold">28%</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground mb-1">Consistency Score</div>
                        <Badge variant="default" className="bg-green-100 text-green-700">High</Badge>
                      </div>
                    </div>

                    <div className="pt-4 border-t">
                      <div className="text-sm space-y-2">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Total Copiers</span>
                          <span className="font-semibold">2345</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Last Trade</span>
                          <span className="font-semibold">2025/11/19 15:48:04</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Profit share ratio</span>
                          <span className="font-semibold">10%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Trading frequency</span>
                          <span className="font-semibold">164</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Watchers</span>
                          <span className="font-semibold">12694</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* ROI Chart */}
              <Card className="lg:col-span-2">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold">ROI</h3>
                    <select className="text-sm border rounded px-2 py-1">
                      <option>7d</option>
                      <option>30d</option>
                      <option>90d</option>
                    </select>
                  </div>

                  <div className="h-64 flex items-end justify-center bg-gradient-to-br from-cyan-50 to-transparent rounded-lg p-4">
                    <svg viewBox="0 0 400 200" className="w-full h-full">
                      <defs>
                        <linearGradient id="roiGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                          <stop offset="0%" stopColor="rgb(46, 243, 227)" stopOpacity="0.3" />
                          <stop offset="100%" stopColor="rgb(46, 243, 227)" stopOpacity="0" />
                        </linearGradient>
                      </defs>
                      <polyline
                        points="0,180 50,160 100,140 150,120 200,100 250,90 300,70 350,40 400,20"
                        fill="url(#roiGradient)"
                        stroke="none"
                      />
                      <polyline
                        points="0,180 50,160 100,140 150,120 200,100 250,90 300,70 350,40 400,20"
                        fill="none"
                        stroke="rgb(46, 243, 227)"
                        strokeWidth="3"
                      />
                      <circle cx="300" cy="70" r="4" fill="rgb(46, 243, 227)" />
                      <text x="300" y="60" textAnchor="middle" className="text-xs" fill="rgb(46, 243, 227)">
                        12th November
                      </text>
                      <text x="300" y="90" textAnchor="middle" className="text-xs font-bold" fill="rgb(46, 243, 227)">
                        ROI +48,008.33%
                      </text>
                    </svg>
                  </div>

                  <div className="flex justify-between text-xs text-muted-foreground mt-4">
                    <span>10-20</span>
                    <span>10-22</span>
                    <span>10-24</span>
                    <span>10-26</span>
                    <span>10-28</span>
                    <span>10-30</span>
                    <span>11-01</span>
                    <span>11-03</span>
                    <span>11-05</span>
                    <span>11-07</span>
                    <span>11-09</span>
                    <span>11-11</span>
                    <span>11-13</span>
                    <span>11-15</span>
                    <span>11-17</span>
                    <span>11-19</span>
                  </div>
                </CardContent>
              </Card>

              {/* Trading Pairs */}
              <Card className="lg:col-span-3">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold">Trading Pairs</h3>
                    <select className="text-sm border rounded px-2 py-1">
                      <option>7d</option>
                      <option>30d</option>
                      <option>90d</option>
                    </select>
                  </div>

                  <div className="flex items-center gap-8">
                    {/* Donut Chart */}
                    <div className="relative w-48 h-48">
                      <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                        <circle cx="50" cy="50" r="40" fill="none" stroke="#2EF3E3" strokeWidth="20" strokeDasharray="157 251" />
                        <circle cx="50" cy="50" r="40" fill="none" stroke="#FF6B6B" strokeWidth="20" strokeDasharray="45 251" strokeDashoffset="-157" />
                        <circle cx="50" cy="50" r="40" fill="none" stroke="#FFA500" strokeWidth="20" strokeDasharray="45 251" strokeDashoffset="-202" />
                        <circle cx="50" cy="50" r="40" fill="none" stroke="#9B59B6" strokeWidth="20" strokeDasharray="45 251" strokeDashoffset="-247" />
                        <circle cx="50" cy="50" r="40" fill="none" stroke="#3498DB" strokeWidth="20" strokeDasharray="45 251" strokeDashoffset="-292" />
                        <circle cx="50" cy="50" r="40" fill="none" stroke="#E91E63" strokeWidth="20" strokeDasharray="45 251" strokeDashoffset="-337" />
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <div className="text-3xl font-bold">64%</div>
                        <div className="text-sm text-muted-foreground">ALT/USDT</div>
                      </div>
                    </div>

                    {/* Legend */}
                    <div className="flex-1 grid grid-cols-2 gap-3 text-sm">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-[#2EF3E3]"></div>
                          <span>ALT/USDT</span>
                        </div>
                        <span className="font-semibold">64.3%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-[#FF6B6B]"></div>
                          <span>XRP/USDT</span>
                        </div>
                        <span className="font-semibold">7.14%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-[#FFA500]"></div>
                          <span>BTC/USDT</span>
                        </div>
                        <span className="font-semibold">7.14%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-[#9B59B6]"></div>
                          <span>PARTCOIN/USDT</span>
                        </div>
                        <span className="font-semibold">7.14%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-[#3498DB]"></div>
                          <span>THE/USDT</span>
                        </div>
                        <span className="font-semibold">7.14%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-[#E91E63]"></div>
                          <span>Others</span>
                        </div>
                        <span className="font-semibold">7.14%</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* My Verified Trades */}
              <Card className="lg:col-span-3">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold">My Verified Trades</h3>
                    <a href="#" className="text-sm text-primary hover:underline">See all →</a>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="border-b">
                        <tr className="text-sm text-muted-foreground">
                          <th className="text-left py-2">Trading Pairs</th>
                          <th className="text-left py-2">Platform</th>
                          <th className="text-right py-2">ROI</th>
                        </tr>
                      </thead>
                      <tbody>
                        {verifiedTrades.map((trade, index) => (
                          <tr key={index} className="border-b">
                            <td className="py-3">
                              <div className="flex items-center gap-2">
                                <div className="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center text-white text-xs">A</div>
                                <span className="font-medium">{trade.pair}</span>
                                <Badge variant="default" className="bg-green-100 text-green-700 text-xs">{trade.type}</Badge>
                              </div>
                            </td>
                            <td className="py-3">
                              <div className="flex items-center gap-2">
                                <div className="w-5 h-5 rounded bg-yellow-400"></div>
                                <span className="text-sm">{trade.platform}</span>
                              </div>
                            </td>
                            <td className="py-3 text-right">
                              <span className="text-green-600 font-semibold">{trade.roi}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* Copied Trades */}
              <Card className="lg:col-span-3">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold">Copied Trades</h3>
                    <a href="#" className="text-sm text-primary hover:underline">See all →</a>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="border-b">
                        <tr className="text-sm text-muted-foreground">
                          <th className="text-left py-2">Trading Pairs</th>
                          <th className="text-left py-2">Platform</th>
                          <th className="text-right py-2">ROI</th>
                        </tr>
                      </thead>
                      <tbody>
                        {copiedTrades.map((trade, index) => (
                          <tr key={index} className="border-b">
                            <td className="py-3">
                              <div className="flex items-center gap-2">
                                <div className="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center text-white text-xs">A</div>
                                <span className="font-medium">{trade.pair}</span>
                                <Badge variant="default" className="bg-green-100 text-green-700 text-xs">{trade.type}</Badge>
                              </div>
                            </td>
                            <td className="py-3">
                              <div className="flex items-center gap-2">
                                <div className="w-5 h-5 rounded bg-yellow-400"></div>
                                <span className="text-sm">{trade.platform}</span>
                              </div>
                            </td>
                            <td className="py-3 text-right">
                              <span className="text-green-600 font-semibold">{trade.roi}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>

      <Footer />
    </div>
  )
}
