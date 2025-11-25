"use client"
import { useState } from "react";
import { FaqItem } from "./TraderCard";

export default function FAQ() {
    const [openFaq, setOpenFaq] = useState<number | null>(null);
    
    return(
        <section id="faqs" className="py-[60px] px-[120px] bg-background">
        <div className="max-w-[894px] mx-auto">
          <div className="flex flex-col items-center gap-4 mb-10">
            <div className="px-2.5 py-2 bg-brand-cyan/10 rounded-full">
              <span className="text-[10px] font-semibold tracking-[1.6px] uppercase text-black">FAQs</span>
            </div>
            <h2 className="font-display text-[36px] leading-[120%] tracking-[-1.44px] text-[#1A1A1A] text-center">
              Frequently Asked Questions
            </h2>
          </div>

          <div className="space-y-5">
            <FaqItem 
              question="How does Obscura protect my data?"
              answer="Your API keys and trading history are processed inside secure hardware enclaves (TEEs) and never leave that environment. Only zero-knowledge proofs are generated and shared. Obscura has no access to your raw trading data or credentials."
              isOpen={openFaq === 0}
              onToggle={() => setOpenFaq(openFaq === 0 ? null : 0)}
            />
            <FaqItem 
              question="Does Obscura see my trades?"
              answer="No. All computation happens inside trusted execution environments that are cryptographically isolated. Obscura cannot access your trading data, strategies, or API keys. We only see the final zero-knowledge proofs that verify your performance metrics."
              isOpen={openFaq === 1}
              onToggle={() => setOpenFaq(openFaq === 1 ? null : 1)}
            />
            <FaqItem 
              question="Which exchanges and chains do you support?"
              answer="Obscura supports major centralized exchanges including Binance, Coinbase, Bybit, OKX, Kraken, and KuCoin. For DeFi, we support Uniswap, SushiSwap, GMX, dYdX, PancakeSwap, and Balancer across multiple chains. More integrations are added regularly."
              isOpen={openFaq === 2}
              onToggle={() => setOpenFaq(openFaq === 2 ? null : 2)}
            />
            <FaqItem 
              question="What metrics can I prove?"
              answer="You can prove key performance metrics including total PnL, win rate, Sharpe ratio, maximum drawdown, trading volume, and consistency over time. All proofs are mathematically verifiable without revealing your actual trades or strategies."
              isOpen={openFaq === 3}
              onToggle={() => setOpenFaq(openFaq === 3 ? null : 3)}
            />
            <FaqItem 
              question="Why should I publish an on-chain reputation?"
              answer="An on-chain reputation credential allows you to prove your trading performance to lending protocols, copy-trading platforms, and asset managers without revealing your strategy. It unlocks access to capital allocation, better terms, and partnership opportunities based on verified performance."
              isOpen={openFaq === 4}
              onToggle={() => setOpenFaq(openFaq === 4 ? null : 4)}
            />
          </div>
        </div>
      </section>
    )
}