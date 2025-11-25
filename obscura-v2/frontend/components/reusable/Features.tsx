import { FeatureCard } from "./TraderCard";
import Image from "next/image";
import gif1 from "@/public/asets/1.gif";
import gif2 from "@/public/asets/2.gif";
import gif3 from "@/public/asets/3.gif";
import gif4 from "@/public/asets/4.gif";
import gif5 from "@/public/asets/5.gif";
import gif6 from "@/public/asets/6.gif";

export default function Features() {
    return(
        <section id="features" className="py-[60px] bg-background">
                <div className="max-w-[1200px] mx-auto flex flex-col items-center gap-16">
                  <div className="flex flex-col items-center gap-4">
                    <div className="px-2.5 py-2 bg-brand-cyan/10 rounded-full">
                      <span className="text-[10px] font-semibold tracking-[1.6px] uppercase text-[#1A1A1A]">Features</span>
                    </div>
                    <h2 className="font-display text-[36px] leading-[120%] tracking-[-1.44px] text-[#1A1A1A] text-center max-w-[756px]">
                      Everything you need to prove performance, protect privacy, and build reputation.
                    </h2>
                  </div>
        
                  <div className="grid grid-cols-3 gap-10 w-full">
                    <FeatureCard
                      icon={<Image src={gif1} alt="Private Performance Proofs" width={64} height={64} />}
                      title="Private Performance Proofs"
                      description="Zero-knowledge proofs for real trading metrics. Your strategy stays fully private."
                    />
                    <FeatureCard 
                      icon={<Image src={gif2} alt="Zero Data Exposure" width={64} height={64} />}
                      title="Zero Data Exposure"
                      description="API keys and trade logs never leave secure enclaves. Obscura cannot access your data."
                    />
                    <FeatureCard 
                      icon={<Image src={gif3} alt="On-Chain Reputation Credentials" width={64} height={64} />}
                      title="On-Chain Reputation Credentials"
                      description="Publish tamper-proof performance records that any protocol can trust."
                    />
                    <FeatureCard 
                      icon={<Image src={gif4} alt="Verified Trader Marketplace" width={64} height={64} />}
                      title="Verified Trader Marketplace"
                      description="A curated ecosystem of traders with mathematically proven performance."
                    />
                    <FeatureCard 
                      icon={<Image src={gif5} alt="One-Click Copy" width={64} height={64} />}
                      title="One-Click Copy"
                      description="Mirror verified traders with a single click. Allocate capital, set limits, and grow"
                    />
                    <FeatureCard 
                      icon={<Image src={gif6} alt="Protocol-Ready Integrations" width={64} height={64} />}
                      title="Protocol-Ready Integrations"
                      description="A reputation API for lending markets, copy-trading platforms and asset managers"
                    />
                  </div>
                </div>
              </section>
    )
}