import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "NidhiPath — Concessional Scheme Matching for Marginalized Entrepreneurs",
  description:
    "Discover NSFDC concessional credit schemes, calculate your loan EMI, " +
    "and connect with authorized channel partners near you. Built for SC " +
    "beneficiaries under the Ministry of Social Justice and Empowerment.",
  keywords: [
    "NSFDC", "scheme matching", "SC beneficiaries", "concessional loan",
    "MoSJE", "financial inclusion", "EMI calculator", "channel partner",
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} h-full`}>
      <body className="min-h-full flex flex-col bg-white text-[#111827] font-sans antialiased">
        {/* Top Navbar */}
        <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-[#E5EBE5] transition-shadow">
          <div className="max-w-[1340px] mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-3 no-underline group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#16A34A] to-[#15803D] flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                  <path d="M2 12l10 5 10-5" />
                </svg>
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold tracking-tight text-[#0F1F0F]">
                  Nidhi<span className="text-[#16A34A]">Path</span>
                </span>
                <span className="text-[11px] font-medium text-[#6B7280] tracking-normal -mt-0.5">
                  Your Path. Your Growth.
                </span>
              </div>
            </Link>

            {/* Navigation Links */}
            <nav className="hidden md:flex items-center gap-8 text-[15px] font-medium text-[#374151]" aria-label="Main Navigation">
              <Link href="/" className="text-[#16A34A] font-semibold transition-colors hover:text-[#15803D] relative py-2">
                Home
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#16A34A] rounded-full"></span>
              </Link>
              <Link href="/intake" className="hover:text-[#16A34A] transition-colors py-2">
                Find Scheme
              </Link>
              <Link href="/calculator" className="hover:text-[#16A34A] transition-colors py-2">
                Calculator
              </Link>
              <Link href="/locator" className="hover:text-[#16A34A] transition-colors py-2">
                Partners
              </Link>
              <Link href="/#about" className="hover:text-[#16A34A] transition-colors py-2">
                About Us
              </Link>
              <Link href="/qa" className="hover:text-[#16A34A] transition-colors py-2">
                Help
              </Link>
            </nav>

            {/* Right actions */}
            <div className="flex items-center gap-3.5">
              {/* Language Selector */}
              <div className="relative inline-flex items-center">
                <div className="flex items-center gap-1.5 px-3 py-2 bg-[#F9FAFB] hover:bg-[#F3F4F6] border border-[#E5E7EB] rounded-xl text-sm font-medium text-[#374151] cursor-pointer transition-colors">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4B5563" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="2" y1="12" x2="22" y2="12" />
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                  </svg>
                  <select
                    className="bg-transparent text-sm font-medium text-[#374151] cursor-pointer focus:outline-none appearance-none pr-4"
                    defaultValue="en"
                    aria-label="Select language"
                  >
                    <option value="en">English</option>
                    <option value="hi">हिन्दी (Hindi)</option>
                    <option value="ta">தமிழ் (Tamil)</option>
                    <option value="te">తెలుగు (Telugu)</option>
                    <option value="kn">ಕನ್ನಡ (Kannada)</option>
                    <option value="ml">മലയാളം (Malayalam)</option>
                  </select>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="pointer-events-none -ml-3">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </div>
              </div>

              {/* Login / Sign Up CTA */}
              <Link
                href="/login"
                className="hidden sm:inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#16A34A] hover:bg-[#15803D] text-white text-sm font-semibold shadow-sm hover:shadow-md transition-all active:scale-[0.98]"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                <span>Login / Sign Up</span>
              </Link>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 w-full">{children}</main>

        {/* Footer */}
        <footer className="bg-white border-t border-[#E5EBE5] mt-16 pt-12 pb-8">
          <div className="max-w-[1340px] mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 pb-10 border-b border-[#F0FDF4]">
              {/* Brand Col */}
              <div className="md:col-span-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-lg bg-[#16A34A] flex items-center justify-center text-white">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 2L2 7l10 5 10-5-10-5z" />
                      <path d="M2 17l10 5 10-5" />
                      <path d="M2 12l10 5 10-5" />
                    </svg>
                  </div>
                  <div>
                    <span className="text-lg font-bold text-[#0F1F0F]">Nidhi<span className="text-[#16A34A]">Path</span></span>
                    <p className="text-[11px] text-[#6B7280]">Your Path. Your Growth.</p>
                  </div>
                </div>
                <p className="text-xs text-[#6B7280] mt-3 leading-relaxed">
                  Concessional credit discovery and financial empowerment platform for Scheduled Caste beneficiaries.
                </p>
              </div>

              {/* Quick Links */}
              <div>
                <h4 className="text-xs font-bold text-[#111827] uppercase tracking-wider mb-3">Quick Links</h4>
                <div className="flex flex-col gap-2 text-sm text-[#4B5563]">
                  <Link href="/intake" className="hover:text-[#16A34A] transition-colors">Find Scheme</Link>
                  <Link href="/calculator" className="hover:text-[#16A34A] transition-colors">EMI Calculator</Link>
                  <Link href="/locator" className="hover:text-[#16A34A] transition-colors">Partner Locator</Link>
                  <Link href="/qa" className="hover:text-[#16A34A] transition-colors">Scheme Q&A</Link>
                </div>
              </div>

              {/* Contact */}
              <div>
                <h4 className="text-xs font-bold text-[#111827] uppercase tracking-wider mb-3">Contact & Support</h4>
                <div className="flex flex-col gap-2.5 text-sm text-[#4B5563]">
                  <div className="flex items-center gap-2">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#16A34A" strokeWidth="2">
                      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                    </svg>
                    <span>1800-11-0033 / 1800-xxx-xxxx</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#16A34A" strokeWidth="2">
                      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                      <polyline points="22,6 12,13 2,6" />
                    </svg>
                    <span>support@nsfdc.gov.in</span>
                  </div>
                  <div className="text-xs text-[#6B7280] mt-1">
                    National Scheduled Castes Finance &amp; Development Corporation
                  </div>
                </div>
              </div>

              {/* Social / Info */}
              <div>
                <h4 className="text-xs font-bold text-[#111827] uppercase tracking-wider mb-3">Follow Us</h4>
                <div className="flex items-center gap-3">
                  <a href="#" className="w-9 h-9 rounded-lg bg-[#F3F4F6] hover:bg-[#E5E7EB] flex items-center justify-center text-[#4B5563] transition-colors" aria-label="Twitter">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                  </a>
                  <a href="#" className="w-9 h-9 rounded-lg bg-[#F3F4F6] hover:bg-[#E5E7EB] flex items-center justify-center text-[#4B5563] transition-colors" aria-label="Facebook">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M9 8H6v4h3v12h5V12h3.642L18 8h-4V6.333C14 5.374 14.5 5 15.688 5H18V0h-3.808C10.595 0 9 1.582 9 4.615V8z"/>
                    </svg>
                  </a>
                  <a href="#" className="w-9 h-9 rounded-lg bg-[#F3F4F6] hover:bg-[#E5E7EB] flex items-center justify-center text-[#4B5563] transition-colors" aria-label="YouTube">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                    </svg>
                  </a>
                  <a href="#" className="w-9 h-9 rounded-lg bg-[#F3F4F6] hover:bg-[#E5E7EB] flex items-center justify-center text-[#4B5563] transition-colors" aria-label="WhatsApp">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21 5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.816 9.816 0 0 0 12.04 2m.01 1.67c2.2 0 4.26.86 5.82 2.42a8.225 8.225 0 0 1 2.41 5.83c0 4.54-3.7 8.24-8.24 8.24-1.48 0-2.93-.4-4.2-1.15l-.3-.18-3.12.82.83-3.04-.2-.31a8.196 8.196 0 0 1-1.26-4.38c0-4.54 3.7-8.24 8.24-8.24m4.52 11.66c-.25.7-.99 1.28-1.74 1.44-.52.11-1.2.2-3.48-.75-1.95-.81-3.21-2.79-3.3-2.92-.1-.13-.79-1.05-.79-2 0-.95.5-1.42.68-1.61.18-.19.4-.24.53-.24.13 0 .27 0 .38.01.12.01.29-.05.45.34.17.39.57 1.4.62 1.5.05.1.09.22.02.35-.07.13-.1.21-.2.33-.1.12-.22.27-.31.36-.1.1-.21.21-.09.42.12.21.54.89 1.16 1.44.8.71 1.47.93 1.68 1.03.21.1.33.09.46-.05.12-.14.53-.62.67-.83.14-.21.28-.18.47-.11.19.07 1.2.57 1.41.67.21.1.35.15.4.24.05.09.05.53-.2 1.23"/>
                    </svg>
                  </a>
                </div>
              </div>
            </div>

            {/* Bottom Disclaimer */}
            <div className="pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-[#6B7280] gap-4">
              <p>© 2025 NidhiPath. All rights reserved.</p>
              <p className="text-center sm:text-right">
                Built for the <strong className="text-[#374151]">Ministry of Social Justice &amp; Empowerment (MoSJE)</strong>
              </p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
