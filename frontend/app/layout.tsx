import type { Metadata } from "next";
import { IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const ibmPlexSans = IBM_Plex_Sans({
  variable: "--font-ibm-plex",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "NidhiPath — AI-Driven Scheme Matching for Marginalized Entrepreneurs",
  description:
    "Find the right NSFDC concessional credit scheme, calculate EMIs, " +
    "and locate your nearest authorized channel partner. Built for SC " +
    "beneficiaries under the Ministry of Social Justice and Empowerment.",
  keywords: [
    "NSFDC", "scheme matching", "SC beneficiaries", "concessional loan",
    "MoSJE", "financial inclusion", "EMI calculator", "channel partner",
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${ibmPlexSans.variable} h-full`}>
      <body className="min-h-full flex flex-col antialiased">
        {/* Top navigation bar */}
        <nav className="glass sticky top-0 z-50 border-b border-[var(--color-border)]">
          <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between">
            {/* Logo */}
            <a href="/" className="flex items-center gap-2.5 no-underline">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#22C55E] to-[#16A34A] flex items-center justify-center">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0F172A" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                  <path d="M2 12l10 5 10-5" />
                </svg>
              </div>
              <span className="text-lg font-semibold text-[var(--color-foreground)] tracking-tight">
                Nidhi<span className="text-[var(--color-accent)]">Path</span>
              </span>
            </a>

            {/* Nav links */}
            <div className="hidden md:flex items-center gap-6 text-sm text-[var(--color-text-secondary)]">
              <a href="/" className="hover:text-[var(--color-foreground)] transition-colors cursor-pointer">Home</a>
              <a href="/intake" className="hover:text-[var(--color-foreground)] transition-colors cursor-pointer">Find Scheme</a>
              <a href="/calculator" className="hover:text-[var(--color-foreground)] transition-colors cursor-pointer">Calculator</a>
              <a href="/locator" className="hover:text-[var(--color-foreground)] transition-colors cursor-pointer">Partners</a>
            </div>

            {/* Language + action */}
            <div className="flex items-center gap-3">
              <select
                className="bg-[var(--color-surface-2)] text-[var(--color-text-secondary)] text-sm border border-[var(--color-border)] rounded-lg px-3 py-1.5 cursor-pointer focus:border-[var(--color-accent)] focus:outline-none"
                defaultValue="en"
                aria-label="Select language"
              >
                <option value="en">English</option>
                <option value="hi">हिन्दी</option>
                <option value="ta">தமிழ்</option>
                <option value="te">తెలుగు</option>
                <option value="kn">ಕನ್ನಡ</option>
                <option value="mr">मराठी</option>
              </select>
            </div>
          </div>
        </nav>

        {/* Page content */}
        <main className="flex-1">{children}</main>

        {/* Footer */}
        <footer className="border-t border-[var(--color-border)] py-8 mt-auto">
          <div className="max-w-[1200px] mx-auto px-6 text-center text-sm text-[var(--color-text-muted)]">
            <p>
              NidhiPath — Built for the{" "}
              <span className="text-[var(--color-text-secondary)]">
                Ministry of Social Justice and Empowerment (MoSJE)
              </span>
            </p>
            <p className="mt-1 text-xs">
              This platform does NOT process loan applications. It routes you to the
              official PM-SURAJ Portal for application submission.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
