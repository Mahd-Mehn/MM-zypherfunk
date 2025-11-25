"use client"

import Link from "next/link"
import { useMemo } from "react"
import { AlertCircle, Loader2 } from "lucide-react"
import TraderCard from "./TraderCard"
import { useTraders } from "@/hooks/use-traders"
import { useAuthContext } from "@/components/providers/auth-provider"

const FALLBACK_TRADERS = [
  {
    id: "fallback-1",
    display_name: "ZKMaster.eth",
    address: "0x8ba1...BA72",
    verification_types: ["ZK-VERIFIED", "TEE-ATTESTED"],
    chains: ["ARBITRUM", "BASE", "ETHEREUM"],
    win_rate: 92.3,
    total_pnl: 89000,
    bio: "DEX-only trader with proven ZK-verified performance. Focus on ETH and stablecoin pairs.",
  },
  {
    id: "fallback-2",
    display_name: "CryptoWhale",
    address: "0x742d...0bEb",
    verification_types: ["ZK-VERIFIED"],
    chains: ["ARBITRUM", "BASE", "ETHEREUM"],
    win_rate: 90.1,
    total_pnl: 125000,
    bio: "High-volume trader aggregating CEX + DEX performance with continuous attestations.",
  },
  {
    id: "fallback-3",
    display_name: "DeFiNinja",
    address: "0xdD87...2148",
    verification_types: ["TEE-ATTESTED"],
    chains: ["ARBITRUM", "BASE", "SOLANA"],
    win_rate: 88.4,
    total_pnl: 102000,
    bio: "Centralized exchange veteran. TEE-attested trades with consistent performance across majors.",
  },
]

export default function Hero() {
  const { isAuthenticated, loading: authLoading } = useAuthContext()
  const { traders, loading, error } = useTraders({ limit: 3, sortBy: "winRate" }, { enabled: isAuthenticated })
  const heroTraders = useMemo(() => {
    if (!isAuthenticated || traders.length === 0) {
      return FALLBACK_TRADERS
    }
    return traders.slice(0, 3)
  }, [traders, isAuthenticated])

  return (
    <section className="relative h-[1000px] overflow-hidden bg-black pt-20">
        {/* Gradient Background */}
        <div className="absolute inset-0">
          <svg className="absolute top-[276px] h-[1000px] w-full" viewBox="0 0 1440 627" fill="none" xmlns="http://www.w3.org/2000/svg">
            <g clipPath="url(#clip0)">
              <g filter="url(#filter0_f)" style={{ animation: 'wave-float 8s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite' }}>
                <path d="M-40.2083 1002.64V736.046C-40.2083 720.036 -35.6152 704.25 -26.2475 691.267C246.955 312.628 948.848 295.787 1329.26 340.856C1369.36 345.606 1398.72 380.078 1398.72 420.459V1002.64C1398.72 1047.84 1362.07 1084.48 1316.87 1084.48H41.6332C-3.56664 1084.48 -40.2083 1047.84 -40.2083 1002.64Z" fill="#2EF3E3"/>
              </g>
              <g style={{ mixBlendMode: 'lighten', animation: 'wave-float-alt 10s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite' }} opacity="0.8" filter="url(#filter1_f)">
                <path d="M191.052 442.756C45.9902 367.871 -76.553 397.506 -160.476 449.813C-236.327 497.089 -260.729 590.327 -260.729 679.704C-260.729 913.383 -75.9294 1105.22 157.586 1113.95L1095.21 1149.02C1442.47 1162 1799.55 951.809 1775.37 605.154C1767.81 496.719 1738.4 395.536 1673.71 320.82C1531.07 156.08 1252.25 262.383 1043.81 390.349C927.088 462.004 802.985 527.513 666.064 530.702C517.124 534.172 333.819 516.455 191.052 442.756Z" fill="#8A5CFF"/>
              </g>
            </g>
            <defs>
              <filter id="filter0_f" x="-205.545" y="157.893" width="1769.6" height="1091.92" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
                <feFlood floodOpacity="0" result="BackgroundImageFix"/>
                <feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape"/>
                <feGaussianBlur stdDeviation="82.6682" result="effect1_foregroundBlur"/>
              </filter>
              <filter id="filter1_f" x="-392.998" y="104.363" width="2301.8" height="1177.49" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
                <feFlood floodOpacity="0" result="BackgroundImageFix"/>
                <feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape"/>
                <feGaussianBlur stdDeviation="66.1346" result="effect1_foregroundBlur"/>
              </filter>
              <clipPath id="clip0">
                <rect width="1450" height="999.896" fill="white" transform="translate(-10)"/>
              </clipPath>
            </defs>
          </svg>
        </div>

        {/* Hero Content */}
        <div className="relative z-10 flex flex-col items-center gap-8 px-[120px] pt-[139px]">
          <div className="flex flex-col items-center gap-4 max-w-[684px]">
            <h1 className="font-display text-[56px] leading-[100%] tracking-[-2.24px] text-white text-center">
              Trade With Proof, Not Trust.
            </h1>
            <p className="text-[18px] leading-[27px] font-medium text-[#767676] text-center max-w-[492px]">
              The first privacy-preserving social trading protocol. Copy verified traders or prove your performance using zero-knowledge cryptography.
            </p>
          </div>

          <div className="flex items-center gap-4">
            <Link
              href={isAuthenticated ? "/dashboard" : "/auth/login"}
              className="px-[18px] py-2.5 bg-brand-cyan rounded-full text-sm font-medium text-black hover:opacity-90 transition-opacity"
            >
              {isAuthenticated ? "Launch App" : "Sign In"}
            </Link>
            <Link
              href="/whitepaper"
              className="px-[18px] py-2.5 bg-[#F5F5F5] rounded-full text-sm font-medium text-[#767676] hover:bg-gray-200 transition-colors"
            >
              Read Whitepaper
            </Link>
          </div>
        </div>

        {/* Trader Cards */}
        <div className="relative z-10 mt-[80px] flex justify-center">
          <div className="relative flex h-[520px] items-center justify-center">
            {isAuthenticated && loading && (
              <div className="absolute inset-0 z-30 flex flex-col items-center justify-center gap-3 rounded-[40px] bg-black/60 text-white">
                <Loader2 className="h-8 w-8 animate-spin text-brand-cyan" />
                <span className="text-sm uppercase tracking-[2px] text-white/80">Fetching live traders…</span>
              </div>
            )}
            {isAuthenticated && error && !loading && (
              <div className="absolute inset-0 z-30 flex flex-col items-center justify-center gap-2 rounded-[40px] bg-black/60 text-white">
                <AlertCircle className="h-6 w-6 text-destructive" />
                <span className="text-sm font-medium text-white">Failed to load traders</span>
                <p className="text-xs text-white/70">Showing featured profiles instead.</p>
              </div>
            )}
            {[ -210, 0, 210 ].map((offset, index) => {
              const trader = heroTraders[index] || FALLBACK_TRADERS[index]
              const rotation = index === 1 ? 0 : index === 0 ? -10 : 10
              const highlight = index === 1

              if (!trader) return null

              return (
                <div
                  key={trader.id ?? `hero-card-${index}`}
                  className={index === 1 ? "relative z-20" : "absolute z-0"}
                  style={{
                    transform: `translateX(${offset}px) rotate(${rotation}deg)` + (index === 1 ? "" : ""),
                    transformOrigin: 'center center',
                    bottom: index === 1 ? undefined : index === 0 ? "-84px" : "-88px",
                    top: index === 1 ? "-8px" : undefined,
                  }}
                >
                  <TraderCard trader={trader} highlight={highlight} />
                </div>
              )
            })}
          </div>
        </div>
      </section>
  )
}