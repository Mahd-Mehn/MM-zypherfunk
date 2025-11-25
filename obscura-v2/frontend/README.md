# Obscura - Privacy-Preserving Social Trading Protocol

## 🌟 Project Overview

Obscura is a cutting-edge Web3 social trading platform that enables traders to prove their performance using zero-knowledge proofs (ZK) and trusted execution environments (TEE), while allowing followers to copy their trades with complete privacy preservation. Built on modern blockchain infrastructure, Obscura revolutionizes social trading by eliminating the need to expose sensitive trading data while maintaining verifiable proof of performance.

## 🎯 Core Concept

Traditional social trading platforms require traders to expose their complete trading history and strategies, creating privacy concerns and competitive disadvantages. Obscura solves this by:

- **Zero-Knowledge Proofs (ZK)**: For DEX trades, traders generate cryptographic proofs that verify their performance without revealing actual trade details
- **Trusted Execution Environments (TEE)**: For CEX trades, secure enclaves attest to trading performance while keeping data encrypted
- **Privacy-First Architecture**: No raw trade data is ever exposed to the public
- **Multi-Chain Support**: Works across Arbitrum, Base, Aptos, and other major chains
- **Exchange Integration**: Supports both centralized (Binance, Coinbase) and decentralized (Uniswap, PancakeSwap) exchanges

## ✨ Key Features

### 1. **Landing Page**
- **Hero Section**: Asymmetric layout with animated gradient backgrounds and floating stat cards
- **Trust Indicators**: Real-time platform statistics (total traders, verified trades, total volume)
- **Verification Methods**: Detailed explanation of ZK and TEE verification with visual comparisons
- **Features Grid**: Bento-style layout showcasing privacy, performance, and multi-chain support
- **Featured Traders**: Horizontal scrolling showcase of top-performing verified traders
- **How It Works**: Step-by-step visual guide for both signal providers and followers
- **Technology Stack**: Display of cryptographic and blockchain technologies used
- **Testimonials**: Social proof from verified traders
- **FAQ Section**: Common questions and answers
- **CTA Sections**: Multiple conversion points throughout the page

### 2. **Trader Marketplace**
- **Advanced Search**: Real-time search across trader names and descriptions
- **Multi-Filter System**:
  - Verification type (ZK-Verified, TEE-Attested, All)
  - Chain selection (Arbitrum, Base, Aptos, All Chains)
  - Sort options (Win Rate, PnL, Followers, Total Trades)
- **Trader Cards**: Rich cards displaying:
  - Trader avatar and name
  - Verification badges
  - Key metrics (Win Rate, Total PnL, Followers, Trades)
  - Supported chains and exchanges
  - Hover effects with gradient backgrounds
- **Responsive Grid**: Adapts from 1 to 3 columns based on screen size
- **Loading States**: Skeleton loaders for better UX
- **Empty States**: Helpful messages when no traders match filters

### 3. **Trader Profile Page**
- **Hero Section**: Large trader showcase with verification status
- **Performance Metrics**: 
  - Total PnL with percentage change
  - Win rate with visual indicator
  - Total trades count
  - Follower count
  - Average trade size
  - Sharpe ratio
- **Performance Chart**: Interactive 30-day performance visualization using Recharts
- **Trade History**: Detailed list of recent verified trades with:
  - Trade pair and type (Long/Short)
  - Entry and exit prices
  - PnL with color coding
  - Timestamp
  - Verification badge
- **Chain & Exchange Info**: Visual display of supported platforms
- **Copy Trading CTA**: Prominent button to start copying the trader

### 4. **User Dashboard**
- **Split Hero Layout**: User info on left, bento-style stats on right
- **Key Metrics**:
  - Total portfolio value
  - Total PnL (24h change)
  - Active copies
  - Win rate
- **Tab Navigation**: 
  - Overview: Performance chart and activity feed
  - My Trades: Personal trading history
  - Copied Trades: Trades executed via copy trading
  - Following: List of traders being copied
- **Performance Chart**: 30-day portfolio performance visualization
- **Activity Feed**: Recent trades with detailed information
- **Quick Actions Sidebar**: 
  - Find new traders
  - Manage copies
  - View analytics
- **Following Section**: Cards for each trader being copied with quick actions

### 5. **Copy Trading Interface**
- **Trader Overview**: Summary of the trader being copied
- **Configuration Form**:
  - Copy amount (USD)
  - Position size percentage (slider)
  - Stop-loss percentage (slider)
  - Take-profit percentage (slider)
  - Auto-renew toggle
- **Risk Management**: Visual indicators for risk levels
- **Summary Sidebar**: 
  - All configuration parameters
  - Estimated fees
  - Risk assessment
  - Verification information
- **Activation Flow**: 
  - Review configuration
  - Confirm copy trading
  - Success state with next steps
- **Real-time Validation**: Form validation with helpful error messages

### 6. **Onboarding Flow**
- **Multi-Step Wizard**: 
  - Step 1: Wallet Connection
  - Step 2: Role Selection (Trader vs Follower)
  - Step 3: DEX Account Linking (ZK Verification)
  - Step 4: CEX Account Linking (TEE Attestation)
- **Progress Indicator**: Visual progress bar showing current step
- **Role Selection**: Large cards for choosing between Signal Provider and Follower
- **DEX Integration**: 
  - Wallet connection simulation
  - Chain selection (Arbitrum, Base, Aptos)
  - ZK proof generation status
- **CEX Integration**: 
  - Exchange selection (Binance, Coinbase, Kraken)
  - API key input (secure)
  - TEE attestation process
- **Completion Screen**: 
  - Setup summary
  - Next steps
  - Quick action buttons

### 7. **Professional Header**
- **Logo**: Obscura branding with shield icon
- **Navigation Links**: 
  - Marketplace
  - Dashboard
  - How It Works
  - Docs
- **Theme Toggle**: Switch between dark and light modes
- **Wallet Connection**: Prominent CTA button
- **Mobile Menu**: Responsive hamburger menu for mobile devices
- **Gradient Background**: Purple-to-primary gradient with blur effects

### 8. **Professional Footer**
- **Multi-Column Layout**:
  - Product links (Marketplace, Dashboard, Copy Trading, Analytics)
  - Resources (Documentation, API, Blog, Support)
  - Company (About, Careers, Privacy, Terms)
- **Social Media Links**: Twitter, Discord, GitHub, LinkedIn
- **Newsletter Signup**: Email subscription form
- **Legal Links**: Privacy Policy and Terms of Service
- **Copyright Notice**: Current year with Obscura branding

## 🎨 Design System

### Color Palette
- **Primary**: Cyan/Teal (`#06b6d4`) - Trust and technology
- **Purple**: Vibrant purple (`#a855f7`) - Premium and innovation
- **Success**: Green (`#10b981`) - Positive metrics
- **Destructive**: Red (`#ef4444`) - Negative metrics and warnings
- **Background**: Dark (`#0a0a0a`) / Light (`#ffffff`)
- **Foreground**: Light (`#fafafa`) / Dark (`#0a0a0a`)
- **Muted**: Gray tones for secondary content
- **Accent**: Purple highlights for interactive elements

### Typography
- **Font Family**: Inter (sans-serif) - Modern, clean, highly readable
- **Heading Sizes**: 
  - H1: 3.75rem (60px) - Hero titles
  - H2: 3rem (48px) - Section titles
  - H3: 2.25rem (36px) - Subsection titles
  - H4: 1.875rem (30px) - Card titles
- **Body Text**: 1rem (16px) with 1.5 line height
- **Font Weights**: 400 (regular), 500 (medium), 600 (semibold), 700 (bold)

### Components
- **Buttons**: 
  - Primary: Purple gradient background with shadow
  - Secondary: Border with transparent background
  - Hover: Scale transform with enhanced shadow
- **Cards**: 
  - Border with subtle background
  - Hover: Border color change and shadow enhancement
  - Gradient overlays for premium feel
- **Badges**: 
  - Verification: Green with checkmark icon
  - Status: Color-coded based on state
- **Forms**: 
  - Labeled inputs with focus states
  - Sliders with purple accent
  - Toggles with smooth animations

### Layout Patterns
- **Bento Grid**: Asymmetric card layouts for visual interest
- **Split Sections**: Two-column layouts with content and visuals
- **Horizontal Scroll**: For showcasing multiple items
- **Sticky Elements**: Navigation and sidebars
- **Responsive Breakpoints**: Mobile-first with sm, md, lg, xl breakpoints

## 🏗️ Architecture

### Frontend Stack
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **Charts**: Recharts
- **Icons**: Lucide React
- **Theme**: next-themes (dark/light mode)
- **State Management**: React hooks and SWR for data fetching

### Backend Stack (Simulated)
- **API Routes**: Next.js API routes
- **Data**: Mock data with realistic trading information
- **Authentication**: Simulated wallet connection
- **Database**: In-memory data structures (production would use PostgreSQL/Supabase)

### Blockchain Integration (Simulated)
- **Chains**: Arbitrum, Base, Aptos
- **DEX**: Uniswap, PancakeSwap, SushiSwap
- **CEX**: Binance, Coinbase, Kraken
- **ZK Proofs**: Simulated proof generation
- **TEE**: Simulated attestation process

## 📁 Project Structure

\`\`\`
obscura/
├── app/
│   ├── api/                    # API routes
│   │   ├── traders/           # Trader data endpoints
│   │   ├── trades/            # Trade history endpoints
│   │   ├── stats/             # Platform statistics
│   │   ├── performance/       # Performance data
│   │   └── copy-trade/        # Copy trading actions
│   ├── dashboard/             # User dashboard page
│   ├── marketplace/           # Trader marketplace page
│   ├── trader/[id]/          # Individual trader profile
│   ├── copy/[id]/            # Copy trading interface
│   ├── onboarding/           # Onboarding flow
│   ├── layout.tsx            # Root layout with theme
│   ├── page.tsx              # Landing page
│   └── globals.css           # Global styles and theme
├── components/
│   ├── ui/                   # shadcn/ui components
│   ├── header.tsx            # Site header
│   ├── footer.tsx            # Site footer
│   ├── theme-provider.tsx    # Theme context
│   ├── theme-toggle.tsx      # Dark/light mode toggle
│   ├── verification-badge.tsx # Verification badges
│   └── decorative-svg.tsx    # SVG patterns
├── lib/
│   ├── mock-data.ts          # Mock trading data
│   └── utils.ts              # Utility functions
└── public/                   # Static assets
\`\`\`

## 🔌 API Endpoints

### GET /api/traders
Fetch all traders with filtering and sorting
- Query params: `search`, `verification`, `chain`, `sort`
- Returns: Array of trader objects

### GET /api/traders/[id]
Fetch individual trader details
- Params: `id` (trader ID)
- Returns: Trader object with full details

### GET /api/trades
Fetch trade history
- Query params: `traderId`, `limit`
- Returns: Array of trade objects

### GET /api/stats
Fetch platform statistics
- Returns: Object with platform-wide metrics

### GET /api/performance/[id]
Fetch trader performance data
- Params: `id` (trader ID)
- Returns: Array of performance data points

### POST /api/copy-trade
Activate copy trading
- Body: `traderId`, `amount`, `stopLoss`, `takeProfit`, `autoRenew`
- Returns: Success confirmation

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

1. Clone the repository
\`\`\`bash
git clone https://github.com/yourusername/obscura.git
cd obscura
\`\`\`

2. Install dependencies
\`\`\`bash
npm install
\`\`\`

3. Run the development server
\`\`\`bash
npm run dev
\`\`\`

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Building for Production

\`\`\`bash
npm run build
npm start
\`\`\`

## 🎯 Usage Guide

### For Traders (Signal Providers)
1. **Connect Wallet**: Click "Connect Wallet" in the header
2. **Complete Onboarding**: 
   - Select "Signal Provider" role
   - Link DEX wallets for ZK verification
   - Link CEX accounts for TEE attestation
3. **Start Trading**: Your verified trades will automatically appear in your profile
4. **Build Reputation**: Consistent performance attracts followers
5. **Earn Fees**: Receive a percentage of follower profits

### For Followers
1. **Connect Wallet**: Click "Connect Wallet" in the header
2. **Complete Onboarding**: 
   - Select "Follower" role
   - Link trading accounts
3. **Browse Marketplace**: 
   - Use filters to find traders matching your criteria
   - Sort by performance metrics
4. **Review Trader Profiles**: 
   - Check performance history
   - Review verification status
   - Analyze trade patterns
5. **Configure Copy Trading**: 
   - Set copy amount
   - Configure risk parameters (stop-loss, take-profit)
   - Enable auto-renew if desired
6. **Activate Copying**: Confirm and start copying trades
7. **Monitor Performance**: Track copied trades in your dashboard

## 🔐 Security Features

- **Zero-Knowledge Proofs**: Trade data never leaves the trader's control
- **Trusted Execution Environments**: CEX data processed in secure enclaves
- **No Raw Data Exposure**: Only performance metrics are public
- **Wallet Security**: Non-custodial, users maintain full control
- **API Key Encryption**: CEX credentials encrypted at rest
- **Smart Contract Audits**: (Production would include audit reports)

## 📊 Performance Metrics

### Trader Metrics
- **Win Rate**: Percentage of profitable trades
- **Total PnL**: Cumulative profit/loss
- **Sharpe Ratio**: Risk-adjusted returns
- **Average Trade Size**: Mean position size
- **Total Trades**: Number of verified trades
- **Followers**: Number of active copiers

### Platform Metrics
- **Total Traders**: Number of verified signal providers
- **Verified Trades**: Total trades with ZK/TEE proof
- **Total Volume**: Cumulative trading volume
- **Active Copies**: Current copy trading relationships

## 🛠️ Technical Implementation

### Zero-Knowledge Proofs (Simulated)
In production, this would use:
- **Noir**: ZK circuit language for proof generation
- **Proof Generation**: Traders generate proofs locally
- **Verification**: Smart contracts verify proofs on-chain
- **Privacy**: Only proof validity is public, not trade details

### Trusted Execution Environments (Simulated)
In production, this would use:
- **AWS Nitro Enclaves**: Secure computation environment
- **Attestation**: Cryptographic proof of secure execution
- **Data Isolation**: CEX credentials never leave the enclave
- **Verification**: Public can verify attestation signatures

### Smart Contracts (Simulated)
In production, this would include:
- **Trader Registry**: On-chain trader profiles
- **Proof Verification**: Verify ZK proofs and TEE attestations
- **Copy Trading Logic**: Automated trade execution
- **Fee Distribution**: Transparent fee splitting
- **Reputation System**: On-chain reputation scores

## 🎨 Design Philosophy

### Principles
1. **Privacy First**: Never compromise user privacy
2. **Trust Through Verification**: Cryptographic proof over trust
3. **User Experience**: Complex crypto made simple
4. **Performance**: Fast, responsive, optimized
5. **Accessibility**: Usable by all traders
6. **Modern Aesthetics**: Professional, not "AI-ish"

### Visual Design
- **Purple Highlights**: Premium, innovative feel
- **Gradient Backgrounds**: Depth and visual interest
- **Hover Effects**: Interactive feedback
- **Smooth Animations**: Polished user experience
- **Consistent Spacing**: Clean, organized layouts
- **Icon Usage**: Visual communication
- **Dark/Light Modes**: User preference support

## 📈 Future Enhancements

### Planned Features
- [ ] Real blockchain integration
- [ ] Actual ZK proof generation
- [ ] Live TEE attestation
- [ ] Multi-signature wallets
- [ ] Advanced analytics dashboard
- [ ] Social features (comments, ratings)
- [ ] Mobile app (React Native)
- [ ] API for third-party integrations
- [ ] Automated strategy backtesting
- [ ] Risk management tools
- [ ] Portfolio optimization
- [ ] Tax reporting integration

### Scalability
- [ ] Database optimization
- [ ] Caching layer (Redis)
- [ ] CDN for static assets
- [ ] Load balancing
- [ ] Microservices architecture
- [ ] Real-time WebSocket updates
- [ ] GraphQL API

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Horizen**: L3 blockchain infrastructure
- **Noir**: Zero-knowledge proof framework
- **AWS Nitro**: Trusted execution environment
- **Next.js**: React framework
- **Tailwind CSS**: Utility-first CSS
- **shadcn/ui**: Beautiful component library
- **Recharts**: Charting library

## 📞 Support

- **Documentation**: [docs.obscura.io](https://docs.obscura.io)
- **Discord**: [discord.gg/obscura](https://discord.gg/obscura)
- **Twitter**: [@ObscuraProtocol](https://twitter.com/ObscuraProtocol)
- **Email**: support@obscura.io

## 🌐 Links

- **Website**: [obscura.io](https://obscura.io)
- **GitHub**: [github.com/obscura-protocol](https://github.com/obscura-protocol)
- **Blog**: [blog.obscura.io](https://blog.obscura.io)
- **Whitepaper**: [obscura.io/whitepaper](https://obscura.io/whitepaper)

---

Built with ❤️ by the Obscura team
