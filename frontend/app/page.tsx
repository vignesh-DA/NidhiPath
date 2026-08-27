"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LandingPage() {
  const router = useRouter();
  const [freeText, setFreeText] = useState("");

  return (
    <div className="relative overflow-hidden">
      {/* Background gradient orbs */}
      <div className="absolute top-[-200px] left-[-100px] w-[500px] h-[500px] rounded-full bg-[radial-gradient(circle,rgba(34,197,94,0.08),transparent_70%)] pointer-events-none" />
      <div className="absolute bottom-[-200px] right-[-100px] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle,rgba(59,130,246,0.06),transparent_70%)] pointer-events-none" />

      {/* Hero Section */}
      <section className="page-container pt-16 pb-20 text-center relative">
        {/* Badge */}
        <div className="animate-fade-in inline-flex items-center gap-2 bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-full px-4 py-1.5 text-sm text-[var(--color-text-secondary)] mb-8">
          <span className="w-2 h-2 rounded-full bg-[var(--color-accent)] animate-pulse" />
          Ministry of Social Justice &amp; Empowerment
        </div>

        {/* Headline */}
        <h1 className="animate-slide-up text-4xl md:text-5xl lg:text-6xl font-bold leading-tight max-w-3xl mx-auto mb-6">
          Your path to{" "}
          <span className="gradient-text">financial empowerment</span>{" "}
          starts here
        </h1>

        <p className="animate-slide-up text-lg md:text-xl text-[var(--color-text-secondary)] max-w-2xl mx-auto mb-12" style={{ animationDelay: "0.1s" }}>
          Find the right NSFDC concessional credit scheme, calculate your EMI,
          and locate the nearest authorized channel partner — all in one place.
        </p>

        {/* Two paths */}
        <div className="animate-slide-up max-w-3xl mx-auto grid md:grid-cols-2 gap-6" style={{ animationDelay: "0.2s" }}>
          {/* Path 1: Structured Form */}
          <button
            onClick={() => router.push("/intake")}
            className="glass-card p-8 text-left cursor-pointer group"
            id="path-form"
          >
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#22C55E]/20 to-[#22C55E]/5 flex items-center justify-center mb-5 group-hover:from-[#22C55E]/30 transition-all">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#22C55E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 11l3 3L22 4" />
                <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-[var(--color-foreground)] mb-2">
              Fill a form
            </h2>
            <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
              Answer 4 simple questions about your project type, cost, and income.
              Get an instant, exact match.
            </p>
            <div className="mt-5 flex items-center gap-2 text-[var(--color-accent)] text-sm font-medium">
              Start now
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </div>
          </button>

          {/* Path 2: Free Text (Module 4) */}
          <div className="glass-card p-8 text-left relative">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#3B82F6]/20 to-[#3B82F6]/5 flex items-center justify-center mb-5">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-[var(--color-foreground)] mb-2">
              Describe your need
            </h2>
            <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed mb-4">
              Tell us in your own words what you're looking for. Our AI will
              extract the details and find matching schemes.
            </p>
            <div className="relative">
              <textarea
                className="input-field resize-none h-20 text-sm"
                placeholder="e.g., I want to start a small tailoring business in Karnataka. My family income is ₹2 lakh per year..."
                value={freeText}
                onChange={(e) => setFreeText(e.target.value)}
                id="free-text-input"
              />
              <button
                className="btn-primary mt-3 w-full justify-center text-sm opacity-60 cursor-not-allowed"
                disabled
                title="AI intake coming soon — use the form path for now"
                id="btn-ai-intake"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                </svg>
                AI Intake (Coming Soon)
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="page-container pb-20">
        <div className="grid md:grid-cols-3 gap-6 stagger-children">
          {/* Feature 1 */}
          <div className="glass-card p-6">
            <div className="w-10 h-10 rounded-lg bg-[var(--color-accent)]/10 flex items-center justify-center mb-4">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22C55E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                <path d="M22 4L12 14.01l-3-3" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-[var(--color-foreground)] mb-2">Smart Scheme Match</h3>
            <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
              Deterministic rule engine matches you to NSFDC credit schemes in under 100ms.
              No AI guesswork — 100% reproducible results.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="glass-card p-6">
            <div className="w-10 h-10 rounded-lg bg-[var(--color-info)]/10 flex items-center justify-center mb-4">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="2" />
                <path d="M7 15h0M2 9.5h20" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-[var(--color-foreground)] mb-2">EMI Calculator</h3>
            <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
              Calculate projected EMIs with scheme-enforced caps. See moratorium
              periods, interest breakdowns, and repayment schedules.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="glass-card p-6">
            <div className="w-10 h-10 rounded-lg bg-[var(--color-warning)]/10 flex items-center justify-center mb-4">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
                <circle cx="12" cy="10" r="3" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-[var(--color-foreground)] mb-2">Partner Locator</h3>
            <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
              Find the nearest SCA, bank, or NBFC-MFI authorized to process your
              loan category, with health-based ranking.
            </p>
          </div>
        </div>
      </section>

      {/* Income cap transparency notice */}
      <section className="page-container pb-16">
        <div className="bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-xl p-5 text-sm text-[var(--color-text-secondary)] max-w-2xl mx-auto">
          <div className="flex items-start gap-3">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <div>
              <p className="font-medium text-[var(--color-foreground)] mb-1">Income Eligibility Cap</p>
              <p>
                This platform uses ₹5,00,000 as the annual income cap per the Problem Statement text.
                The live NSFDC figure is ₹3,00,000. Both figures are stored — this is a documented,
                deliberate choice for demo accuracy.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
