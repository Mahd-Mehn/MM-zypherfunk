import { BadgeCheck, ExternalLink, HelpCircle, Layers, LinkIcon, Lock, TrendingUp } from "lucide-react";
import { SecurityFeature } from "./TraderCard";

export default function Privacy() {
    return (
        <section className="py-[60px] px-[120px] bg-white">
        <div className="max-w-[1200px] mx-auto">
          <h2 className="font-display text-[36px] leading-[120%] tracking-[-1.44px] text-[#484848] max-w-[594px] mb-10">
            The strongest privacy, security, and verifiability in trading reputation.
          </h2>

          <div className="space-y-10">
            <div className="grid grid-cols-2 gap-10">
              <SecurityFeature 
                icon={<Lock className="w-12 h-12 text-[#A3A3A3]" />}
                title="Privacy First."
                description="Your data stays sealed inside secure enclaves. Only proofs are ever published."
              />
              <SecurityFeature 
                icon={<BadgeCheck className="w-12 h-12 text-[#A3A3A3]" />}
                title="Truth Over Trust."
                description="Every metric is cryptographically verified.  No cherry-picking. No unverifiable claim"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-10">
              <SecurityFeature 
                icon={<Layers className="w-12 h-12 text-[#A3A3A3]" />}
                title="Tamper-Proof Reputation."
                description="Your on-chain profile cannot be faked or manipulated—ever."
              />
              <SecurityFeature 
                icon={<TrendingUp className="w-12 h-12 text-[#A3A3A3]" />}
                title="Built for Real Markets."
                description="Supports CEX and DEX environments with advanced performance metrics."
              />
            </div>

            <div className="grid grid-cols-2 gap-10">
              <SecurityFeature 
                icon={<LinkIcon className="w-12 h-12 text-[#A3A3A3]" />}
                title="Fully Composable."
                description="Integrates across the entire DeFi ecosystem lending, copy-trading, asset-management...etc"
              />
              <div className="flex flex-col gap-2 p-6 rounded-[20px] bg-[#F8F8F8]">
                <div className="flex items-center justify-between">
                  <HelpCircle className="w-12 h-12 text-[#A3A3A3]" />
                  <div className="w-6 h-6 bg-[#E8E8E8] rounded-full flex items-center justify-center">
                    <ExternalLink className="w-4 h-4 text-[#484848]" />
                  </div>
                </div>
                <p className="text-[18px] leading-[145%] font-medium">
                  <span className="text-[#1A1A1A]">Get Started Now.</span>
                  <span className="text-[#A3A3A3]"> Easy connect your wallet and start profiting and connecting</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    )
}