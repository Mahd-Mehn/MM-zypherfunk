import { Shield, Lock } from "lucide-react"
import { cn } from "@/lib/utils"

interface VerificationBadgeProps {
  type: string
  className?: string
  showLabel?: boolean
}

export function VerificationBadge({ type, className, showLabel = true }: VerificationBadgeProps) {
  const normalized = type?.toUpperCase?.() ?? ""
  const isZK = normalized.includes("ZK")

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium",
        isZK
          ? "bg-primary/10 text-primary border border-primary/20"
          : "bg-muted text-muted-foreground border border-border",
        className,
      )}
    >
      {isZK ? <Shield className="h-3 w-3" /> : <Lock className="h-3 w-3" />}
      {showLabel && <span>{isZK ? "ZK-Verified" : "TEE-Attested"}</span>}
    </div>
  )
}
