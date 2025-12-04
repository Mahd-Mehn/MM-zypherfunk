"use client"

import { useAccount, useConnect, useDisconnect, useNetwork } from "@starknet-react/core"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Wallet, ChevronDown, Copy, Check, ExternalLink, LogOut } from "lucide-react"
import { useState } from "react"

export function StarknetWalletConnect() {
  const { address, status, connector } = useAccount()
  const { connect, connectors, isPending } = useConnect()
  const { disconnect } = useDisconnect()
  const { chain } = useNetwork()

  const [showConnectModal, setShowConnectModal] = useState(false)
  const [copied, setCopied] = useState(false)

  const copyAddress = () => {
    if (address) {
      navigator.clipboard.writeText(address)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const formatAddress = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`
  }

  const getNetworkBadge = () => {
    if (!chain) return null
    
    const isZtarknet = chain.name === "Ztarknet"
    return (
      <Badge 
        variant="outline" 
        className={isZtarknet ? "border-yellow-500 text-yellow-500" : "border-blue-500 text-blue-500"}
      >
        {chain.name}
      </Badge>
    )
  }

  if (status === "connected" && address) {
    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="gap-2">
            <Wallet className="h-4 w-4" />
            {formatAddress(address)}
            {getNetworkBadge()}
            <ChevronDown className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel className="flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">Connected with {connector?.name}</span>
            <code className="text-xs font-mono">{formatAddress(address)}</code>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={copyAddress}>
            {copied ? (
              <Check className="h-4 w-4 mr-2 text-green-500" />
            ) : (
              <Copy className="h-4 w-4 mr-2" />
            )}
            Copy Address
          </DropdownMenuItem>
          {chain?.name !== "Ztarknet" && (
            <DropdownMenuItem
              onClick={() => window.open("https://ztarknet-explorer.d.karnot.xyz", "_blank")}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Ztarknet Explorer
            </DropdownMenuItem>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => disconnect()} className="text-destructive">
            <LogOut className="h-4 w-4 mr-2" />
            Disconnect
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    )
  }

  return (
    <>
      <Button 
        onClick={() => setShowConnectModal(true)} 
        variant="outline" 
        className="gap-2"
        disabled={isPending}
      >
        <Wallet className="h-4 w-4" />
        {isPending ? "Connecting..." : "Connect Wallet"}
      </Button>

      <Dialog open={showConnectModal} onOpenChange={setShowConnectModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Wallet className="h-5 w-5" />
              Connect Starknet Wallet
            </DialogTitle>
            <DialogDescription>
              Connect your Starknet wallet to verify your trading activity on-chain
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-3 py-4">
            {connectors.map((connector) => (
              <Button
                key={connector.id}
                variant="outline"
                className="w-full justify-start gap-3 h-14"
                onClick={() => {
                  connect({ connector })
                  setShowConnectModal(false)
                }}
                disabled={isPending}
              >
                {connector.icon && (
                  <img 
                    src={typeof connector.icon === 'string' ? connector.icon : connector.icon?.dark || connector.icon?.light} 
                    alt={connector.name} 
                    className="h-6 w-6"
                  />
                )}
                <div className="flex flex-col items-start">
                  <span className="font-medium">{connector.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {connector.id === "argentX" && "Most popular Starknet wallet"}
                    {connector.id === "braavos" && "Smart contract wallet"}
                  </span>
                </div>
              </Button>
            ))}
          </div>

          <div className="text-xs text-center text-muted-foreground">
            By connecting, you agree to our Terms of Service and Privacy Policy
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
