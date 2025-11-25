import Link from "next/link"

export default function CTA() {
    return(
<section className="py-16 px-[120px]">
        <div className="bg-[#F8F8F8] rounded-[40px] py-[120px] px-20 flex flex-col items-center gap-8">
          <div className="flex flex-col items-center gap-4 max-w-[800px]">
            <h2 className="font-display text-[48px] leading-[100%] tracking-[-1.92px] text-black text-center">
              Start Trading With Proof.  Build Reputation That Compounds.
            </h2>
            <p className="text-[18px] leading-[27px] font-medium text-[#767676] text-center max-w-[600px]">
              Your performance is an asset.  Now you can prove it — privately and universally.
            </p>
          </div>
          <Link
            href="/auth/login"
            className="px-[18px] py-2.5 bg-brand-cyan rounded-full text-sm font-medium text-black hover:opacity-90 transition-opacity"
          >
            Launch App
          </Link>
        </div>
      </section>
    )
}