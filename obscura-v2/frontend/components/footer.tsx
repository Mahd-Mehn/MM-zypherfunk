import Link from "next/link"
import { Shield, Twitter, Github, MessageCircle, Linkedin, Mail } from "lucide-react"

export function Footer() {
  return (
    <footer className="bg-card border-t text-foreground relative overflow-hidden">
      <div className="container mx-auto px-4 lg:px-8 py-12 lg:py-16 relative">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
          <div>
            <Link href="/" className="flex items-center gap-2.5 font-semibold text-xl mb-6 group">
              <div className="w-12 h-12 relative">
                <svg viewBox="0 0 100 100" className="w-full h-full">
                  <path d="M50 10 L90 30 L90 70 L50 90 L10 70 L10 30 Z" fill="none" stroke="#2EF3E3" strokeWidth="2"/>
                  <circle cx="50" cy="50" r="15" fill="none" stroke="#2EF3E3" strokeWidth="2"/>
                  <path d="M50 35 L50 25 M50 65 L50 75 M35 50 L25 50 M65 50 L75 50" stroke="#2EF3E3" strokeWidth="2"/>
                </svg>
              </div>
              <div>
                <div className="text-xl font-bold">Obscura</div>
                <div className="text-xs text-muted-foreground">VERIFIABLE REPUTATION</div>
              </div>
            </Link>
            <div className="flex items-center gap-3 mt-6">
              <Link
                href="https://telegram.org"
                target="_blank"
                rel="noopener noreferrer"
                className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 hover:bg-primary transition-all"
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.941z"/>
                </svg>
                <span className="sr-only">Telegram</span>
              </Link>
              <Link
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 hover:bg-primary transition-all"
              >
                <Twitter className="h-5 w-5" />
                <span className="sr-only">Twitter</span>
              </Link>
              <Link
                href="https://discord.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 hover:bg-primary transition-all"
              >
                <MessageCircle className="h-5 w-5" />
                <span className="sr-only">Discord</span>
              </Link>
              <Link
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 hover:bg-primary transition-all"
              >
                <Twitter className="h-5 w-5" />
                <span className="sr-only">Twitter</span>
              </Link>
              <Link
                href="https://linkedin.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 hover:bg-primary transition-all"
              >
                <Linkedin className="h-5 w-5" />
                <span className="sr-only">LinkedIn</span>
              </Link>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-sm mb-4">Product</h3>
            <ul className="space-y-3">
              <li>
                <Link href="/app" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  App
                </Link>
              </li>
              <li>
                <Link href="/dev-docs" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Dev Docs
                </Link>
              </li>
              <li>
                <Link href="/governance" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Governance
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-sm mb-4">Company</h3>
            <ul className="space-y-3">
              <li>
                <Link href="/about" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  About
                </Link>
              </li>
              <li>
                <Link href="/career" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Career
                </Link>
              </li>
              <li>
                <Link href="/blog" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Blog
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-sm mb-4">Legal</h3>
            <ul className="space-y-3">
              <li>
                <Link href="/terms" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Terms and Condition
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Privacy
                </Link>
              </li>
              <li>
                <Link href="/compliance" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Compliance
                </Link>
              </li>
            </ul>
          </div>
        </div>

      </div>
    </footer>
  )
}
