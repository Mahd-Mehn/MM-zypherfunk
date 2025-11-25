import { FooterColumn } from "./TraderCard";
import telegramIcon from "@/public/asets/social/telegram.svg";
import xIcon from "@/public/asets/social/x.svg";
import discordIcon from "@/public/asets/social/discord.svg";
import githubIcon from "@/public/asets/social/github.svg";
import linkedinIcon from "@/public/asets/social/linkedin.svg";
import Image from "next/image";

function SocialIcon({ icon, name }: { icon: string; name: string }) {
  return (
    <a 
      href="#" 
      className="w-10 h-10 bg-white rounded-full flex items-center justify-center hover:opacity-80 transition-opacity"
      aria-label={name}
    >
      <Image src={icon} alt={name} className="w-5 h-5" />
    </a>
  );
}

export default function Footer() {
    return(
        <footer className="bg-black py-[83px] px-[120px]">
        <div className="flex flex-col gap-16">
          <div className="flex items-center justify-between">
            <img 
              src="https://api.builder.io/api/v1/image/assets/TEMP/d252e081bc7984f85f7163d8e9ee75fd788911c8?width=724" 
              alt="Obscura" 
              className="h-[142px]"
            />
            <div className="flex items-center gap-2.5">
              <SocialIcon icon={telegramIcon} name="Telegram" />
              <SocialIcon icon={xIcon} name="X (Twitter)" />
              <SocialIcon icon={discordIcon} name="Discord" />
              <SocialIcon icon={githubIcon} name="GitHub" />
              <SocialIcon icon={linkedinIcon} name="LinkedIn" />
            </div>
          </div>

          <div className="flex justify-between">
            <FooterColumn 
              title="Product"
              links={["App", "Dev Docs", "Governance"]}
            />
            <FooterColumn 
              title="Company"
              links={["About", "Career", "Blog"]}
            />
            <FooterColumn 
              title="Legal"
              links={["Terms and Condition", "Privacy", "Compliance"]}
            />
          </div>
        </div>
      </footer>
    )
}