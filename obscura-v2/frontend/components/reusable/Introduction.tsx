export default function Introduction() {
    return (
        <section className="py-[60px] px-[120px] bg-white">
                <div className="max-w-[1200px] mx-auto flex flex-col items-center gap-16">
                  <h2 className="font-display text-[36px] leading-[120%] tracking-[-1.44px] text-[#1A1A1A] text-center">
                    Introducing Obscura
                  </h2>
                  <p className="font-display text-[20px] leading-[120%] tracking-[-0.4px] text-[#767676] text-center max-w-[1200px]">
                    Obscura transforms your real trading history into cryptographic proofs—without exposing a single trade.
                    <br /><br />
                    Using secure enclaves, decentralized oracle verification, and zero-knowledge computation, Obscura converts performance into an on-chain reputation you can take anywhere.
                    <br /><br />
                    Your data never leaves the enclave. Your results are mathematically verified. Your reputation becomes universal.
                  </p>
                </div>
              </section>
    )
}