"use client";

import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();

  return (
    <div className="page-container pt-16 pb-16 max-w-md mx-auto">
      <div className="glass-card p-8 animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-[#22C55E] to-[#16A34A] flex items-center justify-center">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0F172A" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-[var(--color-foreground)]">Sign in to NidhiPath</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-2">
            Save your matched schemes and track application status
          </p>
        </div>

        {/* Info */}
        <div className="bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-lg p-4 mb-6">
          <div className="flex items-start gap-2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
            <p className="text-xs text-[var(--color-text-secondary)]">
              Login is <strong>optional</strong>. The entire scheme-matching flow works
              fully as a guest. Sign in only if you want to save your results.
            </p>
          </div>
        </div>

        {/* Placeholder auth */}
        <div className="space-y-4 opacity-50">
          <div>
            <label className="label" htmlFor="login-phone">Phone number</label>
            <input type="tel" id="login-phone" className="input-field" placeholder="+91 XXXXX XXXXX" disabled />
          </div>
          <button className="btn-primary w-full justify-center cursor-not-allowed" disabled>
            Send OTP (Coming Soon)
          </button>
        </div>

        <div className="mt-6 text-center">
          <button
            onClick={() => router.push("/")}
            className="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors cursor-pointer"
          >
            Continue as guest →
          </button>
        </div>
      </div>
    </div>
  );
}
