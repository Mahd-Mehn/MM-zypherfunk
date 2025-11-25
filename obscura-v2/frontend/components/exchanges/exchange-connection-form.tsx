"use client"

import { useState } from "react"
import { useExchanges } from "@/hooks/use-exchanges"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, Plus } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

export function ExchangeConnectionForm() {
  const [exchange, setExchange] = useState("")
  const [apiKey, setApiKey] = useState("")
  const [apiSecret, setApiSecret] = useState("")
  const [loading, setLoading] = useState(false)
  
  const { supportedExchanges, createConnection, error } = useExchanges()
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      await createConnection({
        exchange,
        api_key: apiKey,
        api_secret: apiSecret,
      })

      toast({
        title: "Connection Created",
        description: "Your exchange connection is being tested...",
      })

      // Reset form
      setExchange("")
      setApiKey("")
      setApiSecret("")
    } catch (err: any) {
      toast({
        title: "Connection Failed",
        description: err.message,
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="exchange">Exchange</Label>
        <Select value={exchange} onValueChange={setExchange} required>
          <SelectTrigger>
            <SelectValue placeholder="Select exchange" />
          </SelectTrigger>
          <SelectContent>
            {supportedExchanges.map((ex) => (
              <SelectItem key={ex.name} value={ex.name}>
                {ex.display_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="apiKey">API Key</Label>
        <Input
          id="apiKey"
          type="text"
          placeholder="Enter your API key"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          required
          disabled={loading}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="apiSecret">API Secret</Label>
        <Input
          id="apiSecret"
          type="password"
          placeholder="Enter your API secret"
          value={apiSecret}
          onChange={(e) => setApiSecret(e.target.value)}
          required
          disabled={loading}
        />
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Button type="submit" className="w-full" disabled={loading || !exchange}>
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Connecting...
          </>
        ) : (
          <>
            <Plus className="mr-2 h-4 w-4" />
            Add Connection
          </>
        )}
      </Button>
    </form>
  )
}
