import { useState } from "react";
import { 
  ExternalLink, 
  Lock, 
  FileCheck, 
  Shield, 
  Users, 
  Copy, 
  Plug,
  BadgeCheck,
  Layers,
  TrendingUp,
  Link as LinkIcon,
  HelpCircle,
  X,
  Plus
} from "lucide-react";
import Header from "@/components/reusable/Header";
import TraderCard from "@/components/reusable/TraderCard";
import Hero from "@/components/reusable/Hero";
import Features from "@/components/reusable/Features";
import Privacy from "@/components/reusable/Privacy";
import Ecosystem from "@/components/reusable/Ecosystem";
import FAQ from "@/components/reusable/FAQ";
import Footer from "@/components/reusable/Footer";
import Introduction from "@/components/reusable/Introduction";
import CTA from "@/components/reusable/CTA";

export default function Index() {
  

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <Header />

      {/* Hero Section */}
      <Hero />

      {/* Introducing Obscura */}
      <Introduction />

      {/* Features Section */}
     <Features />

      {/* Privacy & Security Features */}
      <Privacy />

      {/* Ecosystem Section */}
      <Ecosystem />

      {/* FAQ Section */}
      <FAQ />

      {/* CTA Section */}
      <CTA />

      {/* Footer */}
      <Footer />

    </div>
  );
}

// Component definitions



