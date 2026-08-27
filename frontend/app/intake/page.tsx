"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { ProjectType, EducationStatus } from "@/lib/types";
import { INDIAN_STATES } from "@/lib/types";

export default function IntakePage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [projectType, setProjectType] = useState<ProjectType>("business_self_employment");
  const [estimatedCost, setEstimatedCost] = useState("");
  const [incomeLevel, setIncomeLevel] = useState("");
  const [educationStatus, setEducationStatus] = useState<EducationStatus | "">("");
  const [userState, setUserState] = useState("");
  const [casteScope] = useState<string[]>(["SC"]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cost = parseFloat(estimatedCost);
    const income = parseFloat(incomeLevel);

    if (isNaN(cost) || cost <= 0) {
      setError("Please enter a valid estimated project or education cost.");
      return;
    }
    if (isNaN(income) || income < 0) {
      setError("Please enter a valid annual family income.");
      return;
    }
    if (projectType === "education" && !educationStatus) {
      setError("Please select your current education admission status.");
      return;
    }

    setIsSubmitting(true);

    const intake = {
      estimated_cost: cost,
      income_level: income,
      project_type: projectType,
      education_status: projectType === "education" ? educationStatus : undefined,
      user_state: userState || undefined,
      caste_scope: casteScope.length > 0 ? casteScope : undefined,
    };

    sessionStorage.setItem("nidhipath_intake", JSON.stringify(intake));
    router.push("/recommendation");
  };

  const quickCostOptions = [
    { label: "₹50,000", val: "50000" },
    { label: "₹1,00,000", val: "100000" },
    { label: "₹2,50,000", val: "250000" },
    { label: "₹5,00,000", val: "500000" },
    { label: "₹10,00,000", val: "1000000" },
  ];

  const quickIncomeOptions = [
    { label: "₹1,50,000", val: "150000" },
    { label: "₹2,50,000", val: "250000" },
    { label: "₹3,00,000", val: "300000" },
    { label: "₹4,50,000", val: "450000" },
  ];

  return (
    <div className="w-full bg-[#F8FAF8] min-h-[calc(100vh-80px)] py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        
        {/* Back Link & Header */}
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#6B7280] hover:text-[#16A34A] transition-colors mb-4"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            <span>Back to Home</span>
          </Link>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0F1F0F] tracking-tight">
                Find Matching Schemes
              </h1>
              <p className="text-sm text-[#6B7280] mt-1">
                Answer 4 simple questions to check instant eligibility for NSFDC credit support.
              </p>
            </div>
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-xs font-bold text-[#16A34A] bg-[#DCFCE7] px-3 py-1 rounded-full">
                100% Deterministic Engine
              </span>
              <span className="text-[11px] text-[#9CA3AF] mt-1">Under 100ms response</span>
            </div>
          </div>
        </div>

        {/* Guided Form Card */}
        <div className="bg-white border border-[#E5EBE5] rounded-3xl p-6 sm:p-8 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-7">
            
            {/* Question 1: Purpose */}
            <div>
              <label className="block text-sm font-bold text-[#111827] mb-2">
                1. What is the purpose of your loan requirement?
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {/* Business Option */}
                <button
                  type="button"
                  onClick={() => { setProjectType("business_self_employment"); setEducationStatus(""); }}
                  className={`p-4 rounded-2xl border-2 text-left cursor-pointer transition-all flex items-start gap-3.5 ${
                    projectType === "business_self_employment"
                      ? "border-[#16A34A] bg-[#F0FDF4] shadow-xs"
                      : "border-[#E5E7EB] bg-white hover:border-[#D1D5DB] hover:bg-[#F9FAFB]"
                  }`}
                  id="type-business"
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                    projectType === "business_self_employment"
                      ? "bg-[#16A34A] text-white"
                      : "bg-[#F3F4F6] text-[#6B7280]"
                  }`}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                      <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[#111827]">Business / Enterprise</h4>
                    <p className="text-xs text-[#6B7280] mt-0.5 leading-relaxed">
                      Micro-finance, term loan, or working capital
                    </p>
                  </div>
                </button>

                {/* Education Option */}
                <button
                  type="button"
                  onClick={() => setProjectType("education")}
                  className={`p-4 rounded-2xl border-2 text-left cursor-pointer transition-all flex items-start gap-3.5 ${
                    projectType === "education"
                      ? "border-[#16A34A] bg-[#F0FDF4] shadow-xs"
                      : "border-[#E5E7EB] bg-white hover:border-[#D1D5DB] hover:bg-[#F9FAFB]"
                  }`}
                  id="type-education"
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                    projectType === "education"
                      ? "bg-[#16A34A] text-white"
                      : "bg-[#F3F4F6] text-[#6B7280]"
                  }`}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
                      <path d="M6 12v5c0 1.1.9 2 2 2h8a2 2 0 002-2v-5" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[#111827]">Higher Education</h4>
                    <p className="text-xs text-[#6B7280] mt-0.5 leading-relaxed">
                      Professional &amp; technical courses in India or abroad
                    </p>
                  </div>
                </button>
              </div>
            </div>

            {/* Conditional: Education Status */}
            {projectType === "education" && (
              <div className="p-4 rounded-2xl bg-[#F0FDF4] border border-[#BBF7D0]">
                <label className="block text-sm font-bold text-[#111827] mb-2" htmlFor="education-status">
                  Admission / Enrollment Status <span className="text-[#DC2626]">*</span>
                </label>
                <select
                  id="education-status"
                  className="w-full bg-white border border-[#D1D5DB] rounded-xl px-3.5 py-2.5 text-sm font-medium text-[#111827] focus:outline-none focus:border-[#16A34A] focus:ring-2 focus:ring-[#16A34A]/20 cursor-pointer"
                  value={educationStatus}
                  onChange={(e) => setEducationStatus(e.target.value as EducationStatus)}
                  required
                >
                  <option value="">Select your status...</option>
                  <option value="admission_secured">Admission Secured / Offer Letter in Hand</option>
                  <option value="currently_enrolled">Currently Enrolled in Recognized Course</option>
                </select>
                <p className="text-[11px] text-[#047857] mt-1.5 font-medium">
                  ✓ NSFDC Education loans require secured admission in recognized institutions.
                </p>
              </div>
            )}

            {/* Question 2: Estimated Cost */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-bold text-[#111827]" htmlFor="estimated-cost">
                  2. Estimated {projectType === "education" ? "Education / Course" : "Project"} Cost (₹)
                </label>
                <span className="text-[11px] text-[#6B7280]">Range: ₹0 to ₹50,00,000</span>
              </div>
              
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#6B7280] font-semibold text-base">₹</span>
                <input
                  type="number"
                  id="estimated-cost"
                  className="w-full pl-9 pr-4 py-3 bg-white border border-[#D1D5DB] rounded-xl text-base font-semibold text-[#111827] placeholder:text-[#9CA3AF] focus:outline-none focus:border-[#16A34A] focus:ring-2 focus:ring-[#16A34A]/20 transition-all"
                  placeholder="e.g. 100000"
                  value={estimatedCost}
                  onChange={(e) => setEstimatedCost(e.target.value)}
                  required
                  min="1"
                />
              </div>

              {/* Quick Select Pills */}
              <div className="flex flex-wrap gap-2 mt-2.5">
                <span className="text-xs text-[#9CA3AF] self-center mr-1">Quick pick:</span>
                {quickCostOptions.map((opt) => (
                  <button
                    key={opt.val}
                    type="button"
                    onClick={() => setEstimatedCost(opt.val)}
                    className="px-2.5 py-1 rounded-lg bg-[#F3F4F6] hover:bg-[#E5E7EB] text-xs font-semibold text-[#374151] transition-colors"
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Question 3: Income Level */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-bold text-[#111827]" htmlFor="income-level">
                  3. Annual Family Income (₹)
                </label>
                <span className="text-[11px] font-semibold text-[#16A34A]">Cap: Up to ₹5,00,000</span>
              </div>

              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#6B7280] font-semibold text-base">₹</span>
                <input
                  type="number"
                  id="income-level"
                  className="w-full pl-9 pr-4 py-3 bg-white border border-[#D1D5DB] rounded-xl text-base font-semibold text-[#111827] placeholder:text-[#9CA3AF] focus:outline-none focus:border-[#16A34A] focus:ring-2 focus:ring-[#16A34A]/20 transition-all"
                  placeholder="e.g. 250000"
                  value={incomeLevel}
                  onChange={(e) => setIncomeLevel(e.target.value)}
                  required
                  min="0"
                />
              </div>

              {/* Quick Income Pills */}
              <div className="flex flex-wrap gap-2 mt-2.5">
                <span className="text-xs text-[#9CA3AF] self-center mr-1">Quick pick:</span>
                {quickIncomeOptions.map((opt) => (
                  <button
                    key={opt.val}
                    type="button"
                    onClick={() => setIncomeLevel(opt.val)}
                    className="px-2.5 py-1 rounded-lg bg-[#F3F4F6] hover:bg-[#E5E7EB] text-xs font-semibold text-[#374151] transition-colors"
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Question 4: State */}
            <div>
              <label className="block text-sm font-bold text-[#111827] mb-1.5" htmlFor="user-state">
                4. Select Your State (for Channel Partner &amp; Welfare Schemes)
              </label>
              <select
                id="user-state"
                className="w-full bg-white border border-[#D1D5DB] rounded-xl px-4 py-3 text-sm font-medium text-[#111827] focus:outline-none focus:border-[#16A34A] focus:ring-2 focus:ring-[#16A34A]/20 cursor-pointer"
                value={userState}
                onChange={(e) => setUserState(e.target.value)}
              >
                <option value="">Select State (e.g. Karnataka, Tamil Nadu, Delhi)...</option>
                {INDIAN_STATES.map((state) => (
                  <option key={state} value={state}>{state}</option>
                ))}
              </select>
              <p className="text-[11px] text-[#6B7280] mt-1.5">
                Required to match state-chartered SCAs (State Channelising Agencies).
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-4 rounded-xl bg-[#FEF2F2] border border-[#FECACA] text-sm text-[#991B1B] flex items-center gap-2.5">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span>{error}</span>
              </div>
            )}

            {/* Submit CTA */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-4 rounded-2xl bg-[#16A34A] hover:bg-[#15803D] text-white text-base font-bold shadow-md hover:shadow-lg transition-all active:scale-[0.99] flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60"
              id="btn-find-schemes"
            >
              {isSubmitting ? (
                <>
                  <svg className="animate-spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <circle cx="12" cy="12" r="10" strokeDasharray="60" strokeDashoffset="15" />
                  </svg>
                  <span>Matching Schemes via Rule Engine...</span>
                </>
              ) : (
                <>
                  <span>Find Eligible Schemes</span>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Security & Eligibility Trust Footer */}
        <div className="mt-6 flex items-center justify-center gap-6 text-xs text-[#6B7280]">
          <div className="flex items-center gap-1.5">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#16A34A" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            <span>No data shared externally</span>
          </div>
          <div className="flex items-center gap-1.5">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#16A34A" strokeWidth="2">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>Zero AI Hallucinations</span>
          </div>
        </div>

      </div>
    </div>
  );
}
