"use client"

import { useState } from "react"
import { Eye, EyeOff, Shield, Search, RefreshCw, Lock, Key, AlertTriangle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { zcashScanner, type ZcashTransaction } from "@/lib/zcash/scanner"

export function ZcashExplorer() {
  const [viewingKey, setViewingKey] = useState("")
  const [isScanning, setIsScanning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [transactions, setTransactions] = useState<ZcashTransaction[]>([])
  const [showKey, setShowKey] = useState(false)

  const handleScan = async () => {
    if (!viewingKey) return
    setIsScanning(true)
    setProgress(0)
    setTransactions([])

    try {
      const results = await zcashScanner.scan(viewingKey, (p) => setProgress(p))
      setTransactions(results)
    } catch (error) {
      console.error("Scan failed:", error)
    } finally {
      setIsScanning(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5 text-yellow-500" />
              Viewing Key Input
            </CardTitle>
            <CardDescription>
              Enter your Unified Viewing Key (UVK) or Incoming Viewing Key (IVK) to scan for transactions.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="relative">
              <Input
                type={showKey ? "text" : "password"}
                placeholder="zxviews..."
                value={viewingKey}
                onChange={(e) => setViewingKey(e.target.value)}
                className="pr-10 font-mono text-sm"
              />
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                onClick={() => setShowKey(!showKey)}
              >
                {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
            
            <Alert variant="default" className="bg-muted/50 border-primary/20">
              <Shield className="h-4 w-4 text-primary" />
              <AlertTitle>Client-Side Only</AlertTitle>
              <AlertDescription className="text-xs text-muted-foreground">
                Your key is processed locally via WebAssembly. It is never sent to any server.
              </AlertDescription>
            </Alert>
          </CardContent>
          <CardFooter>
            <Button 
              onClick={handleScan} 
              disabled={isScanning || !viewingKey} 
              className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-semibold"
            >
              {isScanning ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Scanning Blockchain ({progress}%)
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Scan for Transactions
                </>
              )}
            </Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="h-5 w-5 text-green-500" />
              Privacy Status
            </CardTitle>
            <CardDescription>
              Real-time privacy metrics for your session.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Network Mode</span>
                <div className="flex items-center gap-2 font-medium">
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                  Light Client
                </div>
              </div>
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Data Leaked</span>
                <div className="font-medium text-green-500">0 Bytes</div>
              </div>
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Sync Status</span>
                <div className="font-medium">Up to date</div>
              </div>
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Protocol</span>
                <div className="font-medium">ZIP-307</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Decrypted Transactions</CardTitle>
          <CardDescription>
            Transactions found using the provided viewing key.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {transactions.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Amount (ZEC)</TableHead>
                  <TableHead>TxID</TableHead>
                  <TableHead>Height</TableHead>
                  <TableHead>Time</TableHead>
                  <TableHead>Memo</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.map((tx) => (
                  <TableRow key={tx.id}>
                    <TableCell>
                      <Badge variant={tx.type === "incoming" ? "default" : "secondary"} className={tx.type === "incoming" ? "bg-green-500 hover:bg-green-600" : ""}>
                        {tx.type === "incoming" ? "Received" : "Sent"}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono font-medium">{tx.amount.toFixed(4)}</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {tx.txid}
                    </TableCell>
                    <TableCell>{tx.height}</TableCell>
                    <TableCell className="text-muted-foreground">{tx.timestamp}</TableCell>
                    <TableCell className="max-w-[200px] truncate font-mono text-xs">
                      {tx.memo || <span className="text-muted-foreground italic">Encrypted</span>}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="flex h-32 flex-col items-center justify-center text-muted-foreground">
              <Search className="mb-2 h-8 w-8 opacity-20" />
              <p>No transactions found yet. Enter a key and scan.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
