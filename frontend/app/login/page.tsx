"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();

  return (
    <div className="w-full bg-[#F8FAF8] min-h-[calc(100vh-80px)] py-16 px-4 flex items-center justify-center">
      <div className="bg-white border border-[#E5EBE5] rounded-3xl p-8 sm:p-10 shadow-sm max-w-md w-full">
        
        {/* Logo Icon & Title */}
        <div className="text-center mb-7">
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-[#16A34A] to-[#15803D] flex items-center justify-center shadow-xs">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-[#0F1F0F] tracking-tight">
            Sign in to Nidhi<span className="text-[#16A34A]">Path</span>
          </h1>
          <p className="text-xs text-[#6B7280] mt-1.5 leading-relaxed">
            Access your saved scheme eligibility matches and tracked channel partners.
          </p>
        </div>

        {/* Optional Guest Notice */}
        <div className="bg-[#F0FDF4] border border-[#BBF7D0] rounded-2xl p-4 mb-6 text-xs text-[#047857] flex items-start gap-2.5">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mt-0.5 shrink-0">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
          <div>
            <span className="font-bold block">Login is Optional:</span>
            <span>You can explore schemes, calculate EMIs, and find partners 100% free without logging in.</span>
          </div>
        </div>

        {/* Form */}
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-[#111827] mb-1.5" htmlFor="login-phone">
              Mobile Phone Number
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-[#6B7280]">+91</span>
              <input
                type="tel"
                id="login-phone"
                className="w-full pl-12 pr-4 py-3 bg-[#F9FAFB] border border-[#D1D5DB] rounded-xl text-sm font-medium text-[#111827] focus:outline-none focus:border-[#16A34A] focus:ring-2 focus:ring-[#16A34A]/20"
                placeholder="Enter 10-digit mobile number"
              />
            </div>
          </div>

          <button
            type="button"
            className="w-full py-3.5 rounded-xl bg-[#16A34A] hover:bg-[#15803D] text-white text-sm font-bold shadow-xs hover:shadow-md transition-all cursor-pointer"
            onClick={() => router.push("/intake")}
          >
            Send Verification OTP
          </button>
        </div>

        {/* Guest Action */}
        <div className="mt-6 pt-5 border-t border-[#F3F4F6] text-center">
          <Link
            href="/intake"
            className="text-xs font-bold text-[#16A34A] hover:underline"
          >
            Continue as Guest without signing in →
          </Link>
        </div>

      </div>
    </div>
  );
}
