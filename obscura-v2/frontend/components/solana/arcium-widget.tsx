"use client"

import { useState } from "react"
import { Shield, Lock, Zap, CheckCircle2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

export function ArciumPrivateOrder() {
  const [amount, setAmount] = useState("")
  const [token, setToken] = useState("SOL")
  const [status, setStatus] = useState<"idle" | "encrypting" | "submitting" | "completed">("idle")
  const [txHash, setTxHash] = useState("")

  const handleSubmit = async () => {
    if (!amount) return

    setStatus("encrypting")
    
    // 1. Simulate Client-Side Encryption (Arcium SDK)
    // In a real implementation, we would use the Arcium JS SDK here:
    // const client = new ArciumClient(config);
    // const encrypted = await client.encrypt(amount, token);
    await new Promise(r => setTimeout(r, 1000))
    
    setStatus("submitting")
    
    // 2. Submit to Arcium Network
    // const taskId = await client.submit(encrypted);
    await new Promise(r => setTimeout(r, 1500))
    
    // 3. Record in Backend
    try {
        // We send the metadata to our backend for tracking
        // await api.post('/arcium/record', { amount, token, status: 'submitted' });
        console.log("Recorded Arcium task in backend");
    } catch (e) {
        console.error("Failed to record task", e);
    }
    
    setStatus("completed")
    setTxHash("solana_tx_" + Math.random().toString(36).substring(7))
  }

  return (
    <Card className="w-full max-w-md border-purple-500/20 bg-gradient-to-b from-background to-purple-950/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-purple-400">
          <Shield className="h-5 w-5" />
          Private Execution
        </CardTitle>
        <CardDescription>
          Execute trades on Solana without revealing your intent until the moment of execution.
          Powered by <strong>Arcium MXE</strong>.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>Amount to Swap</Label>
          <div className="flex gap-2">
            <Input 
              type="number" 
              placeholder="0.00" 
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="font-mono"
            />
            <div className="flex items-center justify-center rounded-md border bg-muted px-3 font-bold text-sm">
              {token}
            </div>
          </div>
        </div>

        {status === "idle" && (
          <Alert className="bg-purple-500/10 border-purple-500/20">
            <Lock className="h-4 w-4 text-purple-400" />
            <AlertTitle className="text-purple-400">Encrypted Mempool</AlertTitle>
            <AlertDescription className="text-xs text-muted-foreground">
              Your order will be encrypted client-side and only decrypted by the Arcium cluster nodes.
            </AlertDescription>
          </Alert>
        )}

        {status === "completed" && (
          <Alert className="bg-green-500/10 border-green-500/20">
            <CheckCircle2 className="h-4 w-4 text-green-400" />
            <AlertTitle className="text-green-400">Execution Successful</AlertTitle>
            <AlertDescription className="text-xs text-muted-foreground break-all">
              Tx: {txHash}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
      <CardFooter>
        <Button 
          className="w-full bg-purple-600 hover:bg-purple-700" 
          onClick={handleSubmit}
          disabled={status !== "idle" || !amount}
        >
          {status === "idle" && "Encrypt & Execute"}
          {status === "encrypting" && "Encrypting Order..."}
          {status === "submitting" && "Broadcasting to Arcium..."}
          {status === "completed" && "Trade Executed"}
        </Button>
      </CardFooter>
    </Card>
  )
}
