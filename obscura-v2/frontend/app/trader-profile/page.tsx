"use client"

import { useState } from "react"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Share2, Bookmark, CheckCircle } from "lucide-react"

export default function TraderProfilePage() {
  const [showCopyModal, setShowCopyModal] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Profile Header */}
        <div className="flex items-start justify-between mb-8">
          <div className="flex items-center gap-4">
            <Avatar className="w-20 h-20">
              <AvatarFallback className="bg-gray-300 text-2xl">X</AvatarFallback>
            </Avatar>
            <div>
              <div className="flex items-center gap-2 mb-2">
                <h1 className="text-3xl font-bold">Xeum.eth</h1>
                <CheckCircle className="w-6 h-6 text-primary" />
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>👥 98/1000</span>
                <Badge variant="secondary" className="text-xs">2K-VERIFIED</Badge>
                <Badge variant="secondary" className="text-xs">TEE-ATTESTED</Badge>
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" size="icon">
              <Share2 className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon">
              <Bookmark className="h-4 w-4" />
            </Button>
            <Button variant="outline" className="gap-2">
              Compare
            </Button>
            <Button 
              className="bg-primary hover:bg-primary/90 text-black font-medium gap-2"
              onClick={() => setShowCopyModal(true)}
            >
              Copy
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="overview" className="mb-8">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="trades">Trades</TabsTrigger>
            <TabsTrigger value="copiers">Copiers</TabsTrigger>
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

              {/* Asset Allocation */}
              <Card className="lg:col-span-3">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold">Asset allocation</h3>
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
            </div>
          </TabsContent>
        </Tabs>
      </main>

      <Footer />

      {/* Copy Trading Modal */}
      {showCopyModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowCopyModal(false)}>
          <Card className="w-full max-w-2xl mx-4" onClick={(e) => e.stopPropagation()}>
            <CardContent className="p-6">
              <div className="grid grid-cols-2 gap-6">
                {/* Left Column - Trader Info */}
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <Avatar className="w-16 h-16">
                      <AvatarFallback className="bg-gray-300">X</AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-lg">xeum.eth</span>
                        <CheckCircle className="w-5 h-5 text-primary" />
                      </div>
                      <div className="text-sm text-muted-foreground">👥 98/1000</div>
                    </div>
                  </div>

                  <div className="space-y-4 text-sm">
                    <div>
                      <div className="text-muted-foreground mb-1">ROI</div>
                      <div className="text-2xl font-bold text-green-600">+48,008.33%</div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
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

                    <div className="space-y-2 pt-4 border-t">
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

                {/* Right Column - Copy Settings */}
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-4">Trading Pairs</h3>
                    <div className="bg-gray-50 rounded p-3 text-sm mb-2">
                      <div className="flex justify-between items-center">
                        <span>BTC/USDT, ETH/USDT, SOL/USDT... (All) 25/25</span>
                        <Button variant="ghost" size="sm">Edit →</Button>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-4">Copy Mode</h3>
                    <div className="flex gap-2 mb-3">
                      <Button variant="outline" className="flex-1">Fixed Amound</Button>
                      <Button variant="default" className="flex-1 bg-primary text-black">Multiplier</Button>
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        value="10"
                        className="flex-1 border rounded px-3 py-2"
                      />
                      <span className="text-muted-foreground">USD</span>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-4">Account</h3>
                    <p className="text-sm text-muted-foreground mb-2">Select the platform for this trade</p>
                    <select className="w-full border rounded px-3 py-2">
                      <option>Binance</option>
                      <option>Bybit</option>
                      <option>OKX</option>
                    </select>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-4">Risk Management</h3>
                    <div className="space-y-3 text-sm">
                      <div>
                        <label className="block text-muted-foreground mb-1">Stop-Loss Ratio</label>
                        <div className="flex items-center gap-2">
                          <input type="number" value="10" className="flex-1 border rounded px-3 py-2" />
                          <span className="text-muted-foreground">%</span>
                        </div>
                      </div>
                      <div>
                        <label className="block text-muted-foreground mb-1">Take-Profit Ratio</label>
                        <div className="flex items-center gap-2">
                          <input type="number" value="10" className="flex-1 border rounded px-3 py-2" />
                          <span className="text-muted-foreground">%</span>
                        </div>
                      </div>
                      <div>
                        <label className="block text-muted-foreground mb-1">Maximum Exposure</label>
                        <div className="flex items-center gap-2">
                          <input type="number" value="10000" className="flex-1 border rounded px-3 py-2" />
                          <span className="text-muted-foreground">USD</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <Button className="w-full bg-primary hover:bg-primary/90 text-black font-medium h-12 rounded-full">
                    Continue
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
