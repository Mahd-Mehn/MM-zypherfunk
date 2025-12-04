"use client"

import { ReactNode } from "react"
import { sepolia, mainnet } from "@starknet-react/chains"
import {
  StarknetConfig,
  publicProvider,
  argent,
  braavos,
  useInjectedConnectors,
  voyager,
} from "@starknet-react/core"

// Custom Ztarknet chain configuration
const ztarknet = {
  id: BigInt("0x534e5f5a5441524b4e4554"), // SN_ZTARKNET in hex
  name: "Ztarknet",
  network: "ztarknet",
  nativeCurrency: {
    name: "STRK",
    symbol: "STRK",
    decimals: 18,
    address: "0x1ad102b4c4b3e40a51b6fb8a446275d600555bd63a95cdceed3e5cef8a6bc1d",
  },
  rpcUrls: {
    default: {
      http: ["https://ztarknet-madara.d.karnot.xyz"],
    },
    public: {
      http: ["https://ztarknet-madara.d.karnot.xyz"],
    },
  },
  testnet: true,
} as const

interface StarknetProviderProps {
  children: ReactNode
}

export function StarknetProvider({ children }: StarknetProviderProps) {
  const { connectors } = useInjectedConnectors({
    // Show recommended wallets
    recommended: [argent(), braavos()],
    // Include any other installed wallets
    includeRecommended: "onlyIfNoConnectors",
    // Sort by recommended first
    order: "random",
  })

  return (
    <StarknetConfig
      chains={[sepolia, ztarknet as any]}
      provider={publicProvider()}
      connectors={connectors}
      explorer={voyager}
    >
      {children}
    </StarknetConfig>
  )
}
