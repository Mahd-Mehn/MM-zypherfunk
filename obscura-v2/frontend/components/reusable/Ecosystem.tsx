import binanceLogo from "@/public/asets/logo/binance.svg";
import coinbaseLogo from "@/public/asets/logo/coinbase.svg";
import kucoinLogo from "@/public/asets/logo/kucoin.svg";
import bybitLogo from "@/public/asets/logo/bybit.svg";
import okxLogo from "@/public/asets/logo/okx.svg";
import krakenLogo from "@/public/asets/logo/kraken.svg";
import uniswapLogo from "@/public/asets/logo/uniswap.svg";
import sushiswapLogo from "@/public/asets/logo/sushiswap.svg";
import balanceLogo from "@/public/asets/logo/balance.svg";
import dydxLogo from "@/public/asets/logo/dydx.svg";
import gmxLogo from "@/public/asets/logo/gmx.svg";
import pancakeLogo from "@/public/asets/logo/pancake.svg";
import Image from "next/image";

function ExchangeLogo({ logo, name }: { logo: string; name: string }) {
  return (
    <div className="flex flex-col items-center gap-2 w-[100px]">
      <div className="w-16 h-16 flex items-center justify-center">
        <Image src={logo} alt={name} className="w-full h-full object-contain" />
      </div>
      <span className="text-[18px] text-black">{name}</span>
    </div>
  );
}

export default function Ecosystem() {
    return (
        <section className="py-[60px] bg-background">
        <div className="max-w-[1200px] mx-auto flex flex-col items-center gap-10">
          <div className="flex flex-col items-center gap-4">
            <h2 className="font-display text-[36px] leading-[120%] tracking-[-1.44px] text-[#1A1A1A] text-center">
              Our Ecosystem
            </h2>
            <p className="text-sm text-[#484848] text-center">
              The platforms that power your verified performance.  Trade anywhere — prove everywhere.
            </p>
          </div>

          <div className="flex gap-16">
            <div className="flex flex-col gap-12">
              <div className="flex gap-16">
                <ExchangeLogo logo={binanceLogo} name="Binance" />
                <ExchangeLogo logo={coinbaseLogo} name="Coinbase" />
              </div>
              <div className="flex gap-16">
                <ExchangeLogo logo={kucoinLogo} name="Kucoin" />
                <ExchangeLogo logo={bybitLogo} name="Bybit" />
              </div>
              <div className="flex gap-16">
                <ExchangeLogo logo={okxLogo} name="OKX" />
                <ExchangeLogo logo={krakenLogo} name="Kraken" />
              </div>
            </div>

            <div className="w-px bg-[#E8E8E8]"></div>

            <div className="flex flex-col gap-12">
              <div className="flex gap-16">
                <ExchangeLogo logo={uniswapLogo} name="Uniswap" />
                <ExchangeLogo logo={sushiswapLogo} name="SushiSwap" />
              </div>
              <div className="flex gap-16">
                <ExchangeLogo logo={balanceLogo} name="Balance" />
                <ExchangeLogo logo={dydxLogo} name="DyDx" />
              </div>
              <div className="flex gap-16">
                <ExchangeLogo logo={gmxLogo} name="GMX" />
                <ExchangeLogo logo={pancakeLogo} name="Pancake" />
              </div>
            </div>
          </div>
        </div>
      </section>
    )
}