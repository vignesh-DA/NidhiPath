"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { recommendSchemes } from "@/lib/apiClient";
import type { RecommendResponse, RecommendRequest, MatchedScheme } from "@/lib/types";

export default function RecommendationPage() {
  const router = useRouter();
  const [result, setResult] = useState<RecommendResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [intake, setIntake] = useState<RecommendRequest | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem("nidhipath_intake");
    if (!stored) {
      router.push("/intake");
      return;
    }

    const parsed = JSON.parse(stored) as RecommendRequest;
    setIntake(parsed);

    recommendSchemes(parsed)
      .then((res) => {
        setResult(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to fetch recommendations. Is the backend running?");
        setLoading(false);
      });
  }, [router]);

  const handleSelectScheme = (scheme: MatchedScheme | { scheme_id: string; scheme_name: string; interest_rate_beneficiary: number; max_loan_amount?: number; match_reason: string; channel_partners?: string[] }) => {
    const fullScheme: MatchedScheme = "project_cost_coverage_pct" in scheme
      ? (scheme as MatchedScheme)
      : {
          scheme_id: scheme.scheme_id,
          scheme_name: scheme.scheme_name,
          purpose: intake?.project_type || "business_self_employment",
          match_reason: scheme.match_reason,
          interest_rate_beneficiary: scheme.interest_rate_beneficiary,
          max_loan_amount: scheme.max_loan_amount,
          project_cost_min: 0,
          project_cost_max: intake?.estimated_cost || 500000,
          project_cost_coverage_pct: 90,
          tenure_years: 5,
          moratorium_months: 3,
          channel_partners: scheme.channel_partners ?? [],  // Use real data; [] is safe — never wrong hardcode
          max_annual_income: 500000,
          raw: {},
        };
    sessionStorage.setItem("nidhipath_selected_scheme", JSON.stringify(fullScheme));
    router.push("/calculator");
  };

  const handleLocatePartners = (scheme: MatchedScheme | { scheme_id: string; scheme_name: string; interest_rate_beneficiary: number; max_loan_amount?: number; match_reason: string; channel_partners?: string[] }) => {
    const fullScheme: MatchedScheme = "channel_partners" in scheme
      ? (scheme as MatchedScheme)
      : {
          scheme_id: scheme.scheme_id,
          scheme_name: scheme.scheme_name,
          purpose: intake?.project_type || "business_self_employment",
          match_reason: scheme.match_reason,
          interest_rate_beneficiary: scheme.interest_rate_beneficiary,
          max_loan_amount: scheme.max_loan_amount,
          project_cost_min: 0,
          project_cost_max: intake?.estimated_cost || 500000,
          project_cost_coverage_pct: 90,
          tenure_years: 5,
          moratorium_months: 3,
          channel_partners: scheme.channel_partners ?? [],  // Use real data; [] is safe — never wrong hardcode
          max_annual_income: 500000,
          raw: {},
        };
    sessionStorage.setItem("nidhipath_selected_scheme", JSON.stringify(fullScheme));
    router.push("/locator");
  };

  const formatCurrency = (n: number | undefined | null) => {
    if (n == null) return "N/A";
    return `₹${n.toLocaleString("en-IN")}`;
  };

  if (loading) {
    return (
      <div className="w-full bg-[#F8FAF8] min-h-[calc(100vh-80px)] py-20 px-4 flex items-center justify-center">
        <div className="bg-white border border-[#E5EBE5] rounded-3xl p-10 text-center shadow-md max-w-sm w-full">
          <div className="w-14 h-14 mx-auto mb-5 rounded-2xl bg-[#DCFCE7] flex items-center justify-center text-[#16A34A]">
            <svg className="animate-spin" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" strokeDasharray="60" strokeDashoffset="15" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-[#0F1F0F]">Matching Schemes...</h3>
          <p className="text-xs text-[#6B7280] mt-1.5 leading-relaxed">
            Executing deterministic rule filters on NSFDC and Welfare datasets.
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full bg-[#F8FAF8] min-h-[calc(100vh-80px)] py-16 px-4">
        <div className="bg-white border border-[#E5EBE5] rounded-3xl p-8 text-center shadow-md max-w-lg mx-auto">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-[#FEF2F2] flex items-center justify-center text-[#DC2626]">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <h2 className="text-lg font-bold text-[#111827] mb-2">Connection Issue</h2>
          <p className="text-sm text-[#4B5563] mb-5">{error}</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => router.push("/intake")}
              className="px-4 py-2 rounded-xl bg-white border border-[#D1D5DB] text-sm font-semibold text-[#374151] hover:bg-[#F9FAFB]"
            >
              ← Edit Intake
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-xl bg-[#16A34A] text-sm font-semibold text-white hover:bg-[#15803D]"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const primary = result?.primary;
  const secondary = result?.secondary;

  return (
    <div className="w-full bg-[#F8FAF8] min-h-[calc(100vh-80px)] py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1200px] mx-auto">
        
        {/* Top Breadcrumb & Title */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <Link
              href="/intake"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#6B7280] hover:text-[#16A34A] transition-colors mb-2"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="19" y1="12" x2="5" y2="12" />
                <polyline points="12 19 5 12 12 5" />
              </svg>
              <span>Modify Inputs</span>
            </Link>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0F1F0F] tracking-tight">
              Recommended Schemes for You
            </h1>
            <p className="text-sm text-[#6B7280] mt-0.5">
              Identified {primary?.total_matches || 0} direct NSFDC credit scheme{(primary?.total_matches || 0) !== 1 ? "s" : ""} matching your profile criteria.
            </p>
          </div>

          {/* User Profile Summary Pills */}
          {intake && (
            <div className="flex flex-wrap items-center gap-2 bg-white border border-[#E5EBE5] rounded-2xl p-2.5 shadow-xs">
              <span className="text-xs font-semibold bg-[#F3F4F6] text-[#374151] px-3 py-1.5 rounded-xl">
                {intake.project_type === "education" ? "🎓 Education" : "💼 Business / Enterprise"}
              </span>
              <span className="text-xs font-semibold bg-[#DCFCE7] text-[#16A34A] px-3 py-1.5 rounded-xl">
                Cost: {formatCurrency(intake.estimated_cost)}
              </span>
              <span className="text-xs font-semibold bg-[#F3F4F6] text-[#374151] px-3 py-1.5 rounded-xl">
                Income: {formatCurrency(intake.income_level)}
              </span>
              {intake.user_state && (
                <span className="text-xs font-semibold bg-[#EFF6FF] text-[#1D4ED8] px-3 py-1.5 rounded-xl">
                  📍 {intake.user_state}
                </span>
              )}
            </div>
          )}
        </div>

        {/* ══════════════════════════════════════════════════════════════════════ */}
        {/* PRIMARY NSFDC CREDIT SCHEMES                                           */}
        {/* ══════════════════════════════════════════════════════════════════════ */}
        <section className="mb-12">
          <div className="flex items-center gap-2.5 mb-4">
            <div className="w-1.5 h-6 rounded-full bg-[#16A34A]" />
            <h2 className="text-lg sm:text-xl font-bold text-[#0F1F0F]">
              Primary NSFDC Credit Schemes
            </h2>
            <span className="text-xs bg-[#DCFCE7] text-[#16A34A] border border-[#86EFAC] px-2.5 py-0.5 rounded-full font-bold">
              Exact Concessional Match
            </span>
          </div>

          {!primary?.top_pick ? (
            <div className="bg-white border border-[#E5EBE5] rounded-3xl p-10 text-center shadow-xs">
              <p className="text-base font-semibold text-[#111827]">No NSFDC credit schemes matched your current input.</p>
              <p className="text-xs text-[#6B7280] mt-1.5 max-w-md mx-auto">
                Check if your income is within ₹5,00,000 or project cost within the supported NSFDC scheme limits (₹0 to ₹50,00,000).
              </p>
              <button
                onClick={() => router.push("/intake")}
                className="mt-5 px-5 py-2.5 rounded-xl bg-[#16A34A] text-white text-sm font-semibold hover:bg-[#15803D]"
              >
                Adjust Intake Values
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              
              {/* Top Pick Featured Card */}
              <div className="bg-white border-2 border-[#16A34A] rounded-3xl p-6 sm:p-8 shadow-md relative overflow-hidden">
                <div className="absolute top-0 right-0 bg-[#16A34A] text-white text-xs font-extrabold tracking-wider uppercase px-4 py-1.5 rounded-bl-2xl shadow-xs">
                  ★ TOP RECOMMENDED
                </div>

                <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-6 border-b border-[#F0FDF4]">
                  <div>
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-xs font-bold text-[#16A34A] bg-[#DCFCE7] px-3 py-1 rounded-full">
                        NSFDC Scheme
                      </span>
                      <span className="text-xs text-[#6B7280]">
                        ID: {primary.top_pick.scheme_id}
                      </span>
                    </div>
                    <h3 className="text-2xl sm:text-3xl font-extrabold text-[#0F1F0F]">
                      {primary.top_pick.scheme_name}
                    </h3>
                    <p className="text-sm text-[#4B5563] mt-2 max-w-2xl leading-relaxed">
                      {primary.top_pick.match_reason}
                    </p>
                  </div>

                  {/* Interest rate badge */}
                  <div className="bg-[#F0FDF4] border border-[#BBF7D0] rounded-2xl p-4 text-center sm:text-right shrink-0 min-w-[150px]">
                    <span className="text-3xl sm:text-4xl font-extrabold text-[#16A34A] block">
                      {primary.top_pick.interest_rate_beneficiary}%
                    </span>
                    <span className="text-xs font-semibold text-[#047857]">Annual Beneficiary Rate</span>
                  </div>
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-6">
                  <div className="bg-[#F8FAF8] border border-[#E5EBE5] rounded-2xl p-4">
                    <span className="text-xs font-semibold text-[#6B7280] block">Max Loan Limit</span>
                    <span className="text-base sm:text-lg font-bold text-[#0F1F0F] mt-0.5 block">
                      {formatCurrency(primary.top_pick.max_loan_amount)}
                    </span>
                  </div>

                  <div className="bg-[#F8FAF8] border border-[#E5EBE5] rounded-2xl p-4">
                    <span className="text-xs font-semibold text-[#6B7280] block">Repayment Tenure</span>
                    <span className="text-base sm:text-lg font-bold text-[#0F1F0F] mt-0.5 block">
                      {primary.top_pick.tenure_years ? `${primary.top_pick.tenure_years} Years` : "Flexible"}
                    </span>
                  </div>

                  <div className="bg-[#F8FAF8] border border-[#E5EBE5] rounded-2xl p-4">
                    <span className="text-xs font-semibold text-[#6B7280] block">Moratorium Period</span>
                    <span className="text-base sm:text-lg font-bold text-[#0F1F0F] mt-0.5 block">
                      {primary.top_pick.moratorium_months ? `${primary.top_pick.moratorium_months} Months` : "None"}
                    </span>
                  </div>

                  <div className="bg-[#F8FAF8] border border-[#E5EBE5] rounded-2xl p-4">
                    <span className="text-xs font-semibold text-[#6B7280] block">Cost Coverage</span>
                    <span className="text-base sm:text-lg font-bold text-[#0F1F0F] mt-0.5 block">
                      {primary.top_pick.project_cost_coverage_pct}% of Cost
                    </span>
                  </div>
                </div>

                {/* Card Action Buttons */}
                <div className="flex flex-wrap items-center gap-3.5 pt-2">
                  <button
                    onClick={() => handleSelectScheme(primary.top_pick!)}
                    className="px-6 py-3 rounded-xl bg-[#16A34A] hover:bg-[#15803D] text-white text-sm font-bold shadow-sm hover:shadow-md transition-all flex items-center gap-2 cursor-pointer"
                    id="btn-calc-top"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="4" y="2" width="16" height="20" rx="2" />
                      <line x1="8" y1="6" x2="16" y2="6" />
                      <line x1="8" y1="10" x2="16" y2="10" />
                      <line x1="8" y1="14" x2="16" y2="14" />
                      <line x1="8" y1="18" x2="12" y2="18" />
                    </svg>
                    <span>Calculate Monthly EMI</span>
                  </button>

                  <button
                    onClick={() => handleLocatePartners(primary.top_pick!)}
                    className="px-6 py-3 rounded-xl bg-white hover:bg-[#F9FAFB] border border-[#D1D5DB] text-[#374151] hover:text-[#111827] text-sm font-bold shadow-xs transition-all flex items-center gap-2 cursor-pointer"
                    id="btn-locate-top"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#16A34A" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                      <circle cx="12" cy="10" r="3" />
                    </svg>
                    <span>Find Authorized Partners</span>
                  </button>
                </div>
              </div>

              {/* Alternative Scheme Cards */}
              {primary.alternatives.length > 0 && (
                <div>
                  <h4 className="text-sm font-bold text-[#374151] mb-3">
                    Alternative Matching Schemes ({primary.alternatives.length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {primary.alternatives.map((alt) => (
                      <div
                        key={alt.scheme_id}
                        className="bg-white border border-[#E5EBE5] hover:border-[#86EFAC] rounded-2xl p-5 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex justify-between items-start gap-2 mb-2">
                            <h4 className="font-bold text-base text-[#0F1F0F]">{alt.scheme_name}</h4>
                            <span className="text-base font-extrabold text-[#16A34A] bg-[#DCFCE7] px-2.5 py-0.5 rounded-lg shrink-0">
                              {alt.interest_rate_beneficiary}%
                            </span>
                          </div>
                          <p className="text-xs text-[#6B7280] leading-relaxed mb-3">
                            {alt.match_reason}
                          </p>
                          <div className="flex flex-wrap gap-2 text-xs text-[#374151] mb-4">
                            {alt.max_loan_amount && (
                              <span className="bg-[#F3F4F6] px-2.5 py-1 rounded-lg">
                                Max: {formatCurrency(alt.max_loan_amount)}
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2.5 pt-2 border-t border-[#F3F4F6]">
                          <button
                            onClick={() => handleSelectScheme(alt)}
                            className="text-xs font-bold text-[#16A34A] hover:underline"
                          >
                            Calculate EMI →
                          </button>
                          <span className="text-[#D1D5DB]">•</span>
                          <button
                            onClick={() => handleLocatePartners(alt)}
                            className="text-xs font-semibold text-[#4B5563] hover:text-[#111827]"
                          >
                            Locate Partners →
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>
          )}
        </section>

        {/* ══════════════════════════════════════════════════════════════════════ */}
        {/* SECONDARY WELFARE SCHEMES                                              */}
        {/* ══════════════════════════════════════════════════════════════════════ */}
        {secondary && secondary.total_matches > 0 && (
          <section className="mb-12">
            <div className="flex items-center gap-2.5 mb-2">
              <div className="w-1.5 h-6 rounded-full bg-[#0369A1]" />
              <h2 className="text-lg sm:text-xl font-bold text-[#0F1F0F]">
                Related Welfare Schemes You May Qualify For
              </h2>
              <span className="text-xs bg-[#E0F2FE] text-[#0369A1] border border-[#BAE6FD] px-2.5 py-0.5 rounded-full font-bold">
                Secondary / Approximate Match
              </span>
            </div>
            <p className="text-xs text-[#6B7280] mb-4">
              {secondary.disclaimer}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {secondary.matches.slice(0, 9).map((scheme) => (
                <div
                  key={scheme.scheme_id}
                  className="bg-white border border-[#E5EBE5] rounded-2xl p-4 shadow-xs flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#0369A1] bg-[#F0F9FF] px-2 py-0.5 rounded-md">
                        {scheme.issuing_state || "Central"}
                      </span>
                    </div>
                    <h4 className="font-bold text-sm text-[#111827] leading-snug mb-1.5">
                      {scheme.scheme_name}
                    </h4>
                    {scheme.benefits && (
                      <p className="text-xs text-[#6B7280] line-clamp-2 leading-relaxed mb-3">
                        {scheme.benefits}
                      </p>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-1 mt-2">
                    {scheme.match_reasons.map((reason, i) => (
                      <span key={i} className="text-[10px] bg-[#F3F4F6] text-[#4B5563] px-2 py-0.5 rounded-md">
                        ✓ {reason}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {secondary.total_matches > 9 && (
              <p className="text-xs text-[#6B7280] text-center mt-4 font-medium">
                +{secondary.total_matches - 9} additional state/central welfare schemes matched your target criteria.
              </p>
            )}
          </section>
        )}

        {/* ══════════════════════════════════════════════════════════════════════ */}
        {/* PM-SURAJ PORTAL APPLICATION NOTICE                                     */}
        {/* ══════════════════════════════════════════════════════════════════════ */}
        <div className="bg-[#F0FDF4] border border-[#BBF7D0] rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-white border border-[#A7F3D0] flex items-center justify-center text-[#16A34A] shrink-0">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-bold text-[#0F1F0F]">Official Application Submission</h4>
              <p className="text-xs text-[#4B5563] mt-0.5 leading-relaxed">
                NidhiPath is an eligibility discovery engine. To submit your formal loan application, proceed to the official Ministry PM-SURAJ portal.
              </p>
            </div>
          </div>

          <a
            href="https://pmsuraj.dosje.gov.in/"
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2.5 rounded-xl bg-[#16A34A] hover:bg-[#15803D] text-white text-xs font-bold whitespace-nowrap shadow-xs hover:shadow-sm transition-all"
          >
            Apply on PM-SURAJ →
          </a>
        </div>

      </div>
    </div>
  );
}
