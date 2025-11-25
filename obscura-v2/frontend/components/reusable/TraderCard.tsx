"use client"

import Image from "next/image"
import { Plus, X } from "lucide-react"
import type { TraderProfile } from "@/lib/api/types"
import { cn, shortenIdentifier } from "@/lib/utils"

interface TraderCardProps {
  trader?: Partial<TraderProfile> & {
    description?: string
    name?: string
    winRate?: number
    totalPnL?: number
    verificationTypes?: string[]
  }
  highlight?: boolean
  className?: string
}

function formatWinRate(winRate?: number | string | null) {
  if (winRate === null || winRate === undefined) return "—"
  const numeric = typeof winRate === "string" ? Number.parseFloat(winRate) : winRate
  if (Number.isNaN(numeric)) return winRate
  return `${numeric.toFixed(1)}%`
}

function formatPnL(totalPnL?: number | string | null) {
  if (totalPnL === null || totalPnL === undefined) return "—"
  const numeric = typeof totalPnL === "string" ? Number.parseFloat(totalPnL.replace(/[$,k]/gi, "")) : totalPnL
  if (Number.isNaN(numeric)) return String(totalPnL)
  if (Math.abs(numeric) >= 1000) {
    return `${numeric >= 0 ? "" : "-"}$${Math.abs(numeric / 1000).toFixed(1)}k`
  }
  return `${numeric >= 0 ? "" : "-"}$${Math.abs(numeric).toLocaleString()}`
}

export default function TraderCard({ trader, highlight = false, className }: TraderCardProps) {
  const name = trader?.display_name || trader?.name || "Anonymous"
  const address = trader?.address || trader?.id
  const description =
    trader?.description ||
    trader?.bio ||
    "DEX-only trader with proven ZK-verified performance. Focus on ETH and stablecoin pairs."

  const chains = trader?.chains?.length ? trader.chains : trader?.exchanges || ["ARBITRUM", "BASE", "ETHEREUM"]
  const verificationTypes =
    trader?.verification_types?.length
      ? trader.verification_types
      : trader?.verificationTypes?.length
        ? trader.verificationTypes
        : ["ZK-VERIFIED", "TEE-ATTESTED"]
  const winRate = trader?.win_rate ?? trader?.winRate
  const totalPnL = trader?.total_pnl ?? trader?.totalPnL

  return (
    <div
      className={cn(
        "relative w-[360px] rounded-[32px] border border-white/10 bg-[#050E16] p-[1px] text-white shadow-[0_25px_80px_rgba(8,13,32,0.7)]",
        highlight && "scale-105 shadow-[0_35px_120px_rgba(62,213,185,0.35)]",
        className
      )}
    >
      <div className="relative z-10 rounded-[32px] bg-gradient-to-br from-[#041627] via-[#070f1d] to-[#041627] p-8">
        <div className="pointer-events-none absolute inset-0 z-[-1] rounded-[32px] bg-[radial-gradient(circle_at_20%_20%,rgba(46,243,227,0.15),transparent_45%),radial-gradient(circle_at_80%_0%,rgba(138,92,255,0.25),transparent_45%)]" />

        <div className="flex flex-col items-center gap-4 text-center">
          <div className="relative h-20 w-20 rounded-full border border-white/10 bg-white/5 shadow-[0_10px_30px_rgba(0,0,0,0.4)]">
            {trader?.avatar_url ? (
              <Image
                src={trader.avatar_url}
                alt={name}
                fill
                sizes="80px"
                className="rounded-full object-cover"
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-2xl font-bold text-white/70">
                {name.slice(0, 2).toUpperCase()}
              </div>
            )}
          </div>

          <div className="space-y-1">
            <h3 className="font-display text-2xl tracking-tight">{name}</h3>
            <p className="text-sm font-medium text-white/70">{shortenIdentifier(address)}</p>
          </div>
        </div>

        <div className="mt-6 flex flex-col items-center gap-3">
          <div className="flex flex-wrap justify-center gap-3">
            {(verificationTypes?.length ? verificationTypes : ["ZK-VERIFIED"]).map((type) => (
              <VerificationBadge key={type} text={type} />
            ))}
          </div>
          <div className="flex flex-wrap justify-center gap-2">
            {chains?.slice(0, 3).map((chain) => (
              <ChainBadge key={chain} name={chain} />
            ))}
          </div>
        </div>

        <p className="mt-6 text-sm text-white/80">{description}</p>

        <div className="mt-6 flex rounded-2xl border border-white/15 bg-white/5 text-center">
          <div className="flex-1 border-r border-white/10 p-4">
            <span className="block font-display text-3xl text-[#2EF3E3]">{formatWinRate(winRate)}</span>
            <span className="text-xs text-white/60">Win Rate</span>
          </div>
          <div className="flex-1 p-4">
            <span className="block font-display text-3xl text-[#2EF3E3]">{formatPnL(totalPnL)}</span>
            <span className="text-xs text-white/60">Total PnL</span>
          </div>
        </div>
      </div>
    </div>
  )
}




export function VerificationBadge({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-1.5 rounded-full border border-[#21FFAF] bg-[#21FFAF]/10 px-3 py-1.5 text-xs font-semibold tracking-[1px] text-white shadow-[0_10px_25px_rgba(33,255,175,0.2)]">
      <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="none">
        <path fillRule="evenodd" clipRule="evenodd" d="M12.9966 2.08868C13.1444 1.99982 13.3208 1.97164 13.4888 2.01005C13.6569 2.04846 13.8035 2.15047 13.898 2.29468L14.558 3.30135C14.644 3.43285 14.6808 3.59053 14.6619 3.74654C14.643 3.90255 14.5696 4.04686 14.4546 4.15401L14.4526 4.15668L14.4433 4.16535L14.4053 4.20068L14.2553 4.34401C13.4253 5.14908 12.6205 5.9797 11.842 6.83468C10.3773 8.44535 8.63798 10.5533 7.46732 12.5987C7.14065 13.1693 6.34265 13.292 5.86932 12.7993L1.54598 8.30735C1.48403 8.24295 1.43565 8.16675 1.40373 8.08328C1.3718 7.99982 1.35699 7.91078 1.36016 7.82148C1.36333 7.73217 1.38443 7.64441 1.42219 7.56342C1.45995 7.48243 1.51361 7.40985 1.57998 7.35001L2.88665 6.17135C3.00148 6.06782 3.14872 6.00742 3.30317 6.00049C3.45762 5.99356 3.60968 6.04052 3.73332 6.13335L5.93932 7.78735C9.38532 4.38935 11.3393 3.08535 12.9966 2.08868Z" fill="#00D743"/>
      </svg>
      <span className="text-[10px] uppercase text-white">{text}</span>
    </div>
  )
}

export function ChainBadge({ name }: { name: string }) {
  return (
    <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] font-semibold tracking-[1.2px] text-white/80">
      {name.toUpperCase()}
    </div>
  )
}

export function FeatureCard({ icon, title, description }: any) {
  return (
    <div className="relative flex flex-col items-center justify-between gap-6 p-5 h-[300px] rounded-[20px] border border-[#F5F5F5] overflow-hidden">
      {/* Gradient background */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute w-[146px] h-[172px] bg-brand-cyan rounded-full blur-[51px] -top-5 right-0"></div>
        <div className="absolute w-[146px] h-[172px] bg-brand-purple rounded-full blur-[51px] top-12 -right-8"></div>
        <div className="absolute w-[146px] h-[172px] bg-brand-blue rounded-full blur-[51px] bottom-0 left-0"></div>
      </div>

      <div className="relative z-10 w-32 h-[120px] flex items-center justify-center">
        {/* 5-sided shape with flat bottom and rounded corners */}
        <div className="absolute w-[112px] h-[104px]">
          <svg width="112" height="104" viewBox="0 0 112 104" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M56.2637 0.504883C59.9857 0.597859 63.5173 1.76626 67.8281 4.08008C72.1494 6.3995 77.2136 9.84784 84.0078 14.4756L85.8105 15.7031C92.509 20.2657 97.5021 23.6671 101.199 26.7705C104.889 29.8673 107.251 32.6388 108.712 35.9229C109.395 37.4595 109.925 39.0602 110.293 40.7012C111.08 44.2081 110.837 47.842 109.724 52.5283C108.608 57.2245 106.63 62.933 103.976 70.5908C101.496 77.7465 99.6468 83.0803 97.7598 87.1973C95.8769 91.3052 93.9728 94.1634 91.4033 96.3818C90.1979 97.4226 88.8976 98.3483 87.5195 99.1465C84.582 100.848 81.2578 101.711 76.7598 102.145C72.2519 102.579 66.6072 102.58 59.0342 102.58H52.2197C44.6467 102.58 39.002 102.579 34.4941 102.145C29.9961 101.711 26.6719 100.848 23.7344 99.1465C22.3563 98.3483 21.056 97.4226 19.8506 96.3818C17.2811 94.1634 15.377 91.3052 13.4941 87.1973C11.6071 83.0803 9.75835 77.7465 7.27832 70.5908C4.62428 62.933 2.64603 57.2245 1.53027 52.5283C0.416867 47.842 0.173969 44.2081 0.960938 40.7012C1.32921 39.0602 1.85858 37.4595 2.54199 35.9229C4.00254 32.6388 6.3654 29.8673 10.0547 26.7705C13.7518 23.6671 18.7449 20.2657 25.4434 15.7031L27.2461 14.4756C34.0403 9.84784 39.1045 6.3995 43.4258 4.08008C47.7366 1.76626 51.2683 0.597859 54.9902 0.504883C55.4144 0.494292 55.8395 0.494292 56.2637 0.504883Z" fill="white" stroke="#E8E8E8"/>
          </svg>
        </div>
        {/* Icon on top of shape */}
        <div className="relative z-10">
          {icon}
        </div>
      </div>
      
      <div className="relative z-10 flex flex-col items-center gap-4 text-center">
        <h3 className="font-display text-[20px] leading-[120%] tracking-[-0.4px] text-[#1A1A1A]">
          {title}
        </h3>
        <p className="text-sm text-[#484848] max-w-[302px]">
          {description}
        </p>
      </div>
    </div>
  );
}

export function SecurityFeature({ icon, title, description }: any) {
  return (
    <div className="flex flex-col gap-2 p-6 rounded-[20px]">
      <div className="w-12 h-12 mb-2">
        {icon}
      </div>
      <p className="text-[18px] leading-[145%] font-medium">
        <span className="text-[#1A1A1A]">{title}</span>
        <span className="text-[#A3A3A3]"> {description}</span>
      </p>
    </div>
  );
}

export function ExchangeLogo({ name, color, gradient }: any) {
  return (
    <div className="flex flex-col items-center gap-2 w-[100px]">
      <div 
        className="w-16 h-16 rounded-full flex items-center justify-center font-bold text-white text-xl"
        style={{ 
          backgroundColor: gradient ? '#6966FF' : color,
          background: gradient ? 'linear-gradient(135deg, #F50DB4 0%, #2C6BFF 100%)' : undefined
        }}
      >
        {name.slice(0, 2).toUpperCase()}
      </div>
      <span className="text-[18px] text-black">{name}</span>
    </div>
  );
}

export function FaqItem({ question, answer, isOpen, onToggle }: any) {
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onToggle();
  };

  return (
    <div className={`p-6 rounded-[20px] transition-colors ${isOpen ? 'bg-brand-cyan/[0.03]' : ''}`}>
      <button 
        className="w-full flex items-start justify-between cursor-pointer text-left" 
        onClick={handleClick}
        type="button"
      >
        <h3 className="font-display text-[20px] leading-[120%] tracking-[-0.4px] text-[#1A1A1A] flex-1 pr-4">
          {question}
        </h3>
        <div className="w-6 h-6 text-[#484848] flex-shrink-0">
          {isOpen ? <X className="w-6 h-6" /> : <Plus className="w-6 h-6" />}
        </div>
      </button>
      {isOpen && answer && (
        <p className="mt-4 text-[16px] leading-[145%] text-[#484848]">
          {answer}
        </p>
      )}
    </div>
  );
}



export function FooterColumn({ title, links }: { title: string; links: string[] }) {
  return (
    <div className="flex flex-col gap-2.5 w-[160px]">
      <h4 className="text-[16px] font-medium text-[#767676] mb-1">{title}</h4>
      {links.map((link) => (
        <a key={link} href="#" className="text-[16px] font-medium text-white hover:text-brand-cyan transition-colors">
          {link}
        </a>
      ))}
    </div>
  );
}