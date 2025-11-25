// Mock data for the Obscura MVP

export type VerificationType = "ZK" | "TEE"
export type Chain = "Arbitrum" | "Base" | "Aptos" | "Ethereum"
export type Exchange = "Binance" | "Coinbase" | "Uniswap" | "Liquidswap" | "Thala"

export interface Trade {
  id: string
  traderId: string
  timestamp: Date
  assetIn: string
  assetOut: string
  amountIn: number
  amountOut: number
  pnl: number
  pnlPercentage: number
  verificationType: VerificationType
  chain?: Chain
  exchange: Exchange
  txHash?: string
}

export interface Trader {
  id: string
  address: string
  displayName: string
  avatar: string
  verificationType: VerificationType[]
  winRate: number
  totalTrades: number
  verifiedTrades: number
  totalPnL: number
  followers: number
  performanceFee: number
  chains: Chain[]
  exchanges: Exchange[]
  trustTier: 1 | 2
  bio: string
  joinedDate: Date
}

export const mockTraders: Trader[] = [
  {
    id: "1",
    address: "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    displayName: "CryptoWhale",
    avatar: "/crypto-trader-avatar.png",
    verificationType: ["ZK", "TEE"],
    winRate: 87.5,
    totalTrades: 342,
    verifiedTrades: 342,
    totalPnL: 125000,
    followers: 1247,
    performanceFee: 15,
    chains: ["Arbitrum", "Base", "Ethereum"],
    exchanges: ["Uniswap", "Binance"],
    trustTier: 1,
    bio: "Professional DeFi trader specializing in high-frequency strategies across multiple chains.",
    joinedDate: new Date("2024-01-15"),
  },
  {
    id: "2",
    address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
    displayName: "ZKMaster",
    avatar: "/professional-trader.png",
    verificationType: ["ZK"],
    winRate: 92.3,
    totalTrades: 156,
    verifiedTrades: 156,
    totalPnL: 89000,
    followers: 892,
    performanceFee: 20,
    chains: ["Arbitrum", "Base"],
    exchanges: ["Uniswap"],
    trustTier: 1,
    bio: "DEX-only trader with proven ZK-verified performance. Focus on ETH and stablecoin pairs.",
    joinedDate: new Date("2024-02-20"),
  },
  {
    id: "3",
    address: "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
    displayName: "AptosAlpha",
    avatar: "/crypto-expert.png",
    verificationType: ["ZK"],
    winRate: 78.9,
    totalTrades: 234,
    verifiedTrades: 234,
    totalPnL: 67000,
    followers: 543,
    performanceFee: 12,
    chains: ["Aptos"],
    exchanges: ["Liquidswap", "Thala"],
    trustTier: 1,
    bio: "Aptos ecosystem specialist. Early adopter with deep knowledge of Move-based DEXs.",
    joinedDate: new Date("2024-03-10"),
  },
  {
    id: "4",
    address: "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
    displayName: "CEXPro",
    avatar: "/trading-professional.jpg",
    verificationType: ["TEE"],
    winRate: 84.2,
    totalTrades: 567,
    verifiedTrades: 567,
    totalPnL: 156000,
    followers: 2103,
    performanceFee: 18,
    chains: ["Ethereum"],
    exchanges: ["Binance", "Coinbase"],
    trustTier: 2,
    bio: "Centralized exchange veteran. TEE-attested trades with consistent performance across major pairs.",
    joinedDate: new Date("2023-12-05"),
  },
  {
    id: "5",
    address: "0xdD870fA1b7C4700F2BD7f44238821C26f7392148",
    displayName: "DeFiNinja",
    avatar: "/defi-trader.png",
    verificationType: ["ZK"],
    winRate: 81.7,
    totalTrades: 289,
    verifiedTrades: 289,
    totalPnL: 94000,
    followers: 756,
    performanceFee: 15,
    chains: ["Arbitrum", "Ethereum"],
    exchanges: ["Uniswap"],
    trustTier: 1,
    bio: "Arbitrage and liquidity provision strategies. All trades verified on-chain with ZK proofs.",
    joinedDate: new Date("2024-01-28"),
  },
  {
    id: "6",
    address: "0x583031D1113aD414F02576BD6afaBfb302140225",
    displayName: "MultiChainMax",
    avatar: "/blockchain-trader.jpg",
    verificationType: ["ZK", "TEE"],
    winRate: 76.4,
    totalTrades: 412,
    verifiedTrades: 412,
    totalPnL: 78000,
    followers: 634,
    performanceFee: 14,
    chains: ["Arbitrum", "Base", "Aptos"],
    exchanges: ["Uniswap", "Liquidswap", "Binance"],
    trustTier: 1,
    bio: "Cross-chain opportunities hunter. Leveraging price discrepancies across multiple ecosystems.",
    joinedDate: new Date("2024-02-14"),
  },
]

export const mockTrades: Trade[] = [
  {
    id: "t1",
    traderId: "1",
    timestamp: new Date("2024-05-08T14:23:00"),
    assetIn: "USDC",
    assetOut: "ETH",
    amountIn: 5000,
    amountOut: 1.67,
    pnl: 450,
    pnlPercentage: 9.0,
    verificationType: "ZK",
    chain: "Arbitrum",
    exchange: "Uniswap",
    txHash: "0x1234...5678",
  },
  {
    id: "t2",
    traderId: "1",
    timestamp: new Date("2024-05-08T10:15:00"),
    assetIn: "ETH",
    assetOut: "USDC",
    amountIn: 2.5,
    amountOut: 7650,
    pnl: 150,
    pnlPercentage: 2.0,
    verificationType: "TEE",
    exchange: "Binance",
  },
  {
    id: "t3",
    traderId: "2",
    timestamp: new Date("2024-05-08T16:45:00"),
    assetIn: "USDC",
    assetOut: "ARB",
    amountIn: 3000,
    amountOut: 2500,
    pnl: 320,
    pnlPercentage: 10.7,
    verificationType: "ZK",
    chain: "Arbitrum",
    exchange: "Uniswap",
    txHash: "0xabcd...efgh",
  },
  {
    id: "t4",
    traderId: "3",
    timestamp: new Date("2024-05-08T12:30:00"),
    assetIn: "APT",
    assetOut: "USDC",
    amountIn: 500,
    amountOut: 4200,
    pnl: 200,
    pnlPercentage: 5.0,
    verificationType: "ZK",
    chain: "Aptos",
    exchange: "Liquidswap",
    txHash: "0x9876...5432",
  },
]

export function getTraderById(id: string): Trader | undefined {
  return mockTraders.find((trader) => trader.id === id)
}

export function getTradesByTraderId(traderId: string): Trade[] {
  return mockTrades.filter((trade) => trade.traderId === traderId)
}

export function generatePerformanceData(days = 30) {
  const data = []
  const now = new Date()

  for (let i = days; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)

    // Generate realistic performance curve
    const baseValue = 10000
    const trend = (days - i) * 50
    const volatility = Math.sin(i / 3) * 500 + Math.random() * 300

    data.push({
      date: date.toISOString().split("T")[0],
      value: Math.round(baseValue + trend + volatility),
    })
  }

  return data
}
