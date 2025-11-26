import { Metadata } from "next"
import { ZcashExplorer } from "@/components/wallet/zcash-explorer"

export const metadata: Metadata = {
  title: "Zcash Private Explorer | Obscura",
  description: "Client-side Zcash block explorer for shielded transactions.",
}

export default function ZcashExplorerPage() {
  return (
    <div className="container max-w-6xl py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-primary">Private Zcash Explorer</h1>
        <p className="text-muted-foreground mt-2">
          Decrypt your shielded transactions entirely client-side. Your viewing keys never leave your browser.
        </p>
      </div>
      <ZcashExplorer />
    </div>
  )
}
