"use client";

import Link from "next/link";
import Image from "next/image";

export default function LandingPage() {
  return (
    <div className="w-full bg-white">
      {/* ─── Hero Section ──────────────────────────────────────────────────────── */}
      <section className="max-w-[1340px] mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-12 lg:pt-14 lg:pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-8 items-center">
          
          {/* Left Column: Hero Content */}
          <div className="lg:col-span-6 flex flex-col items-start z-10">
            {/* Ministry Badge */}
            <div className="inline-flex items-center gap-2.5 bg-[#ECFDF5] border border-[#A7F3D0] rounded-full px-4 py-1.5 text-xs font-semibold text-[#047857] mb-6 shadow-xs">
              <span className="w-2 h-2 rounded-full bg-[#16A34A]" />
              Ministry of Social Justice &amp; Empowerment
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-[54px] font-extrabold tracking-tight text-[#0F1F0F] leading-[1.15] mb-5">
              Find the right scheme.<br />
              Fuel your <span className="text-[#16A34A]">dreams.</span>
            </h1>

            {/* Subtitle */}
            <p className="text-base sm:text-lg text-[#4B5563] leading-relaxed max-w-xl mb-8 font-normal">
              Discover NSFDC concessional credit schemes, calculate your EMI,
              and connect with authorized channel partners near you.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-4 w-full sm:w-auto">
              {/* Primary CTA */}
              <Link
                href="/intake"
                className="inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-[#16A34A] hover:bg-[#15803D] text-white text-base font-semibold shadow-md hover:shadow-lg transition-all active:scale-[0.99] group"
                id="hero-find-scheme"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <polyline points="10 9 9 9 8 9" />
                </svg>
                <span>Find Your Scheme Now</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="group-hover:translate-x-1 transition-transform">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </Link>

              {/* Secondary CTA */}
              <Link
                href="/qa"
                className="inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-white hover:bg-[#F9FAFB] border border-[#D1D5DB] text-[#374151] hover:text-[#111827] text-base font-semibold shadow-xs hover:shadow-sm transition-all"
                id="hero-ask-ai"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4B5563" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                <span>Ask AI Assistant</span>
              </Link>
            </div>
          </div>

          {/* Right Column: Hero Visual + Floating Stats Card */}
          <div className="lg:col-span-6 relative flex flex-col items-center">
            {/* Visual Container */}
            <div className="relative w-full h-[320px] sm:h-[400px] lg:h-[420px] rounded-3xl overflow-hidden bg-gradient-to-b from-[#F0FDF4] via-[#F8FAF8] to-white border border-[#E5EBE5] flex items-center justify-center shadow-xs">
              <Image
                src="/images/hero-beneficiaries.jpg"
                alt="Diverse Indian beneficiaries and entrepreneurs"
                fill
                priority
                className="object-contain object-bottom scale-105"
                sizes="(max-width: 768px) 100vw, 50vw"
              />
            </div>

            {/* Floating Trust / Stats Card */}
            <div className="w-full mt-4 sm:-mt-10 sm:max-w-[94%] bg-white border border-[#E5EBE5] rounded-2xl shadow-lg p-4 sm:p-5 z-20">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 divide-y sm:divide-y-0 sm:divide-x divide-[#F3F4F6]">
                
                {/* Stat 1 */}
                <div className="flex flex-col items-center text-center px-2 pt-2 sm:pt-0">
                  <div className="w-7 h-7 rounded-lg bg-[#DCFCE7] text-[#16A34A] flex items-center justify-center mb-1.5">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                      <circle cx="9" cy="7" r="4" />
                      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                    </svg>
                  </div>
                  <span className="text-xl font-bold text-[#0F1F0F]">5+</span>
                  <span className="text-[11px] text-[#6B7280] font-medium leading-tight">NSFDC Credit Schemes</span>
                </div>

                {/* Stat 2 */}
                <div className="flex flex-col items-center text-center px-2 pt-2 sm:pt-0">
                  <div className="w-7 h-7 rounded-lg bg-[#DCFCE7] text-[#16A34A] flex items-center justify-center mb-1.5">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                      <polyline points="10 9 9 9 8 9" />
                    </svg>
                  </div>
                  <span className="text-xl font-bold text-[#0F1F0F]">377+</span>
                  <span className="text-[11px] text-[#6B7280] font-medium leading-tight">Welfare Schemes Covered</span>
                </div>

                {/* Stat 3 */}
                <div className="flex flex-col items-center text-center px-2 pt-2 sm:pt-0">
                  <div className="w-7 h-7 rounded-lg bg-[#DCFCE7] text-[#16A34A] flex items-center justify-center mb-1.5">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="3" width="18" height="18" rx="2" />
                      <path d="M3 9h18" />
                      <path d="M9 21V9" />
                    </svg>
                  </div>
                  <span className="text-xl font-bold text-[#0F1F0F]">100+</span>
                  <span className="text-[11px] text-[#6B7280] font-medium leading-tight">Authorized Partners</span>
                </div>

                {/* Stat 4 */}
                <div className="flex flex-col items-center text-center px-2 pt-2 sm:pt-0">
                  <div className="w-7 h-7 rounded-lg bg-[#DCFCE7] text-[#16A34A] flex items-center justify-center mb-1.5">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                  </div>
                  <span className="text-xl font-bold text-[#0F1F0F]">10L+</span>
                  <span className="text-[11px] text-[#6B7280] font-medium leading-tight">Beneficiaries Empowered</span>
                </div>

              </div>
            </div>
          </div>

        </div>
      </section>

      {/* ─── 4 Feature Cards Section ─────────────────────────────────────────── */}
      <section className="max-w-[1340px] mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12" id="about">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          
          {/* Card 1: Smart Scheme Match */}
          <div className="bg-white border border-[#E5EBE5] hover:border-[#86EFAC] rounded-2xl p-6 shadow-xs hover:shadow-md transition-all flex flex-col justify-between group">
            <div>
              <div className="w-12 h-12 rounded-xl bg-[#DCFCE7] flex items-center justify-center text-[#16A34A] mb-4">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 11l3 3L22 4" />
                  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                </svg>
              </div>
              <h3 className="text-base font-bold text-[#0F1F0F] mb-2">Smart Scheme Match</h3>
              <p className="text-xs sm:text-sm text-[#6B7280] leading-relaxed">
                Our rule engine matches you to the most suitable NSFDC credit or education schemes.
              </p>
            </div>
            <Link
              href="/intake"
              className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-[#16A34A] hover:text-[#15803D] mt-5 group-hover:underline"
            >
              <span>Find Scheme</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </Link>
          </div>

          {/* Card 2: EMI Calculator */}
          <div className="bg-white border border-[#E5EBE5] hover:border-[#93C5FD] rounded-2xl p-6 shadow-xs hover:shadow-md transition-all flex flex-col justify-between group">
            <div>
              <div className="w-12 h-12 rounded-xl bg-[#DBEAFE] flex items-center justify-center text-[#2563EB] mb-4">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="4" y="2" width="16" height="20" rx="2" />
                  <line x1="8" y1="6" x2="16" y2="6" />
                  <line x1="8" y1="10" x2="16" y2="10" />
                  <line x1="8" y1="14" x2="16" y2="14" />
                  <line x1="8" y1="18" x2="12" y2="18" />
                </svg>
              </div>
              <h3 className="text-base font-bold text-[#0F1F0F] mb-2">EMI Calculator</h3>
              <p className="text-xs sm:text-sm text-[#6B7280] leading-relaxed">
                Calculate your loan EMI with scheme guidelines, moratorium periods, interest, and repayment schedules.
              </p>
            </div>
            <Link
              href="/calculator"
              className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-[#2563EB] hover:text-[#1D4ED8] mt-5 group-hover:underline"
            >
              <span>Calculate Now</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </Link>
          </div>

          {/* Card 3: Partner Locator */}
          <div className="bg-white border border-[#E5EBE5] hover:border-[#D8B4FE] rounded-2xl p-6 shadow-xs hover:shadow-md transition-all flex flex-col justify-between group">
            <div>
              <div className="w-12 h-12 rounded-xl bg-[#F3E8FF] flex items-center justify-center text-[#9333EA] mb-4">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
              </div>
              <h3 className="text-base font-bold text-[#0F1F0F] mb-2">Partner Locator</h3>
              <p className="text-xs sm:text-sm text-[#6B7280] leading-relaxed">
                Find the nearest authorized SCA, bank, NBFC-MFI or RRB partner using our interactive map.
              </p>
            </div>
            <Link
              href="/locator"
              className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-[#9333EA] hover:text-[#7E22CE] mt-5 group-hover:underline"
            >
              <span>Find Partners</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </Link>
          </div>

          {/* Card 4: Ask Questions */}
          <div className="bg-white border border-[#E5EBE5] hover:border-[#FDBA74] rounded-2xl p-6 shadow-xs hover:shadow-md transition-all flex flex-col justify-between group">
            <div>
              <div className="w-12 h-12 rounded-xl bg-[#FFEDD5] flex items-center justify-center text-[#EA580C] mb-4">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <h3 className="text-base font-bold text-[#0F1F0F] mb-2">Ask Questions</h3>
              <p className="text-xs sm:text-sm text-[#6B7280] leading-relaxed">
                Get answers to your scheme-related questions in simple language using our AI assistant.
              </p>
            </div>
            <Link
              href="/qa"
              className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-[#EA580C] hover:text-[#C2410C] mt-5 group-hover:underline"
            >
              <span>Ask Now</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </Link>
          </div>

        </div>
      </section>

      {/* ─── Bottom Highlight Banner ─────────────────────────────────────────── */}
      <section className="max-w-[1340px] mx-auto px-4 sm:px-6 lg:px-8 pb-14">
        <div className="bg-[#F0FDF4] border border-[#BBF7D0] rounded-2xl p-6 sm:p-7 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-xs">
          
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-white border border-[#A7F3D0] flex items-center justify-center text-[#16A34A] shrink-0 shadow-xs">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="m9 12 2 2 4-4" />
              </svg>
            </div>
            <div>
              <h3 className="text-base sm:text-lg font-bold text-[#0F1F0F]">
                Concessional loans. Lower interest rates. Bigger dreams.
              </h3>
              <p className="text-xs sm:text-sm text-[#4B5563] mt-0.5">
                For SC individuals &amp; entrepreneurs with family income up to ₹5.00 Lakhs.
              </p>
            </div>
          </div>

          <Link
            href="/intake"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white hover:bg-[#F9FAFB] border border-[#86EFAC] hover:border-[#16A34A] text-[#16A34A] text-sm font-semibold shadow-xs hover:shadow-sm transition-all whitespace-nowrap"
          >
            <span>Learn More About NSFDC Schemes</span>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </Link>

        </div>
      </section>
    </div>
  );
}
