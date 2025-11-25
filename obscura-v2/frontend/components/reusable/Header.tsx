import Link from "next/link"
import { ExternalLink } from "lucide-react";

export default function Header() {
    return (
        <header className="bg-black">
        <div className="flex items-center justify-between px-[120px] py-5">
          <div className="flex items-center gap-6">
            <img 
              src="/asets/obscuralogo.svg" 
              alt="Obscura" 
              className="h-10"
            />
            <nav className="flex items-center gap-2">
              <a href="#features" className="px-3 py-2 text-sm text-[#767676] hover:text-white transition-colors">Features</a>
              <a href="#faqs" className="px-3 py-2 text-sm text-[#767676] hover:text-white transition-colors">FAQs</a>
              <a href="#community" className="px-3 py-2 text-sm text-[#767676] hover:text-white transition-colors">Community</a>
            </nav>
          </div>
          
          <div className="flex items-center gap-6">
            <a href="#developers" className="flex items-center gap-2 px-4 py-2 text-sm text-[#767676] hover:text-white transition-colors">
              Developers
              <div className="flex items-center justify-center w-[18px] h-[18px] rounded-full bg-[#F5F5F5]">
                <ExternalLink className="w-2.5 h-2.5 text-[#484848]" />
              </div>
            </a>
            <Link
              href="/auth/login"
              className="px-[18px] py-2.5 bg-brand-cyan rounded-full text-sm font-medium text-black hover:opacity-90 transition-opacity"
            >
              Launch App
            </Link>
          </div>
        </div>
      </header>
    )
}