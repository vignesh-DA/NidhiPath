"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { calculateEmi } from "@/lib/apiClient";
import type { MatchedScheme, EmiBreakdown } from "@/lib/types";

export default function CalculatorPage() {
  const router = useRouter();
  const [scheme, setScheme] = useState<MatchedScheme | null>(null);
  const [result, setResult] = useState<EmiBreakdown | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSchedule, setShowSchedule] = useState(false);

  // User-adjustable inputs
  const [requestedAmount, setRequestedAmount] = useState(0);
  const [requestedMonths, setRequestedMonths] = useState(36);

  useEffect(() => {
    const stored = sessionStorage.getItem("nidhipath_selected_scheme");
    if (!stored) {
      router.push("/intake");
      return;
    }
    const parsed = JSON.parse(stored) as MatchedScheme;
    setScheme(parsed);

    // Set default requested amount to scheme's max or a reasonable default
    const maxLoan = parsed.max_loan_amount || parsed.project_cost_max * (parsed.project_cost_coverage_pct / 100);
    setRequestedAmount(Math.min(maxLoan, parsed.project_cost_max || 100000));
    setRequestedMonths(parsed.tenure_years ? parsed.tenure_years * 12 : 36);
  }, [router]);

  const handleCalculate = useCallback(async () => {
    if (!scheme) return;
    setLoading(true);
    setError(null);

    try {
      const res = await calculateEmi({
        scheme_id: scheme.scheme_id,
        requested_amount: requestedAmount,
        requested_months: requestedMonths,
        interest_rate_pct: scheme.interest_rate_beneficiary,
        max_loan_amount: scheme.max_loan_amount ?? undefined,
        project_cost: scheme.project_cost_max,
        project_cost_coverage_pct: scheme.project_cost_coverage_pct,
        tenure_years: scheme.tenure_years ?? undefined,
        moratorium_months: scheme.moratorium_months ?? undefined,
        include_schedule: showSchedule,
      });
      setResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to calculate. Is the backend running?";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [scheme, requestedAmount, requestedMonths, showSchedule]);

  useEffect(() => {
    if (scheme && requestedAmount > 0 && requestedMonths > 0) {
      const debounce = setTimeout(handleCalculate, 300);
      return () => clearTimeout(debounce);
    }
  }, [scheme, requestedAmount, requestedMonths, handleCalculate]);

  const formatCurrency = (n: number | undefined | null) => {
    if (n == null) return "₹0";
    return `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
  };

  if (!scheme) return null;

  const maxLoan = scheme.max_loan_amount || scheme.project_cost_max * (scheme.project_cost_coverage_pct / 100);
  const maxMonths = scheme.tenure_years ? scheme.tenure_years * 12 : 120;

  return (
    <div className="w-full bg-[#F8FAF8] min-h-[calc(100vh-80px)] py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        
        {/* Navigation & Header */}
        <div className="mb-6">
          <Link
            href="/recommendation"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#6B7280] hover:text-[#16A34A] transition-colors mb-3"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            <span>Back to Recommendations</span>
          </Link>

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0F1F0F] tracking-tight">
                Financial EMI Calculator
              </h1>
              <p className="text-sm text-[#6B7280] mt-0.5">
                Scheme-enforced calculations for <strong className="text-[#16A34A]">{scheme.scheme_name}</strong>
              </p>
            </div>

            <div className="inline-flex items-center gap-2 bg-white border border-[#E5EBE5] rounded-xl px-3.5 py-2 shadow-xs">
              <span className="text-xs text-[#6B7280]">Fixed Scheme Rate:</span>
              <span className="text-sm font-bold text-[#16A34A]">{scheme.interest_rate_beneficiary}% p.a.</span>
            </div>
          </div>
        </div>

        {/* 2-Column Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Sliders & Scheme Controls (lg:col-span-7) */}
          <div className="lg:col-span-7 space-y-6">
            <div className="bg-white border border-[#E5EBE5] rounded-3xl p-6 sm:p-7 shadow-xs space-y-6">
              
              {/* Slider 1: Loan Amount */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-bold text-[#111827]">
                    Requested Loan Amount (P)
                  </label>
                  <span className="text-lg font-extrabold text-[#16A34A] bg-[#DCFCE7] px-3 py-1 rounded-xl">
                    {formatCurrency(requestedAmount)}
                  </span>
                </div>

                <input
                  type="range"
                  min={10000}
                  max={maxLoan}
                  step={5000}
                  value={requestedAmount}
                  onChange={(e) => setRequestedAmount(Number(e.target.value))}
                  className="w-full h-2.5 rounded-full bg-[#E5E7EB] appearance-none cursor-pointer accent-[#16A34A]"
                  id="slider-amount"
                />

                <div className="flex justify-between text-xs text-[#6B7280] mt-2 font-medium">
                  <span>Min: ₹10,000</span>
                  <span>Scheme Cap: {formatCurrency(maxLoan)}</span>
                </div>
              </div>

              {/* Slider 2: Repayment Tenure */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-bold text-[#111827]">
                    Repayment Tenure (n)
                  </label>
                  <span className="text-lg font-extrabold text-[#111827] bg-[#F3F4F6] px-3 py-1 rounded-xl">
                    {requestedMonths} Months <span className="text-xs font-normal text-[#6B7280]">({(requestedMonths / 12).toFixed(1)} yrs)</span>
                  </span>
                </div>

                <input
                  type="range"
                  min={6}
                  max={maxMonths}
                  step={6}
                  value={requestedMonths}
                  onChange={(e) => setRequestedMonths(Number(e.target.value))}
                  className="w-full h-2.5 rounded-full bg-[#E5E7EB] appearance-none cursor-pointer accent-[#16A34A]"
                  id="slider-tenure"
                />

                <div className="flex justify-between text-xs text-[#6B7280] mt-2 font-medium">
                  <span>Min: 6 Months</span>
                  <span>Scheme Max: {maxMonths} Months</span>
                </div>
              </div>

              {/* Moratorium Feature Callout */}
              {scheme.moratorium_months && scheme.moratorium_months > 0 ? (
                <div className="bg-[#F0FDF4] border border-[#BBF7D0] rounded-2xl p-4 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#DCFCE7] text-[#16A34A] flex items-center justify-center shrink-0">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                      <polyline points="12 6 12 12 16 14" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-[#047857] uppercase tracking-wider">
                      Moratorium Period: {scheme.moratorium_months} Months
                    </h4>
                    <p className="text-xs text-[#374151] mt-0.5 leading-relaxed">
                      First EMI payment starts at <strong>Month {scheme.moratorium_months + 1}</strong>. Interest does not accrue during this period per documented standard.
                    </p>
                  </div>
                </div>
              ) : null}

              {/* Scheme Limits Information */}
              <div className="pt-2 border-t border-[#F3F4F6] text-xs text-[#6B7280] space-y-1">
                <p>• Cost Coverage: <strong>{scheme.project_cost_coverage_pct}%</strong> of project cost</p>
                <p>• Interest Rate: <strong>{scheme.interest_rate_beneficiary}% p.a.</strong> (NSFDC concessional rate)</p>
              </div>

            </div>
          </div>

          {/* Right Column: EMI Calculation Result Card (lg:col-span-5) */}
          <div className="lg:col-span-5 space-y-5">
            {error && (
              <div className="p-4 rounded-2xl bg-[#FEF2F2] border border-[#FECACA] text-xs text-[#991B1B]">
                {error}
              </div>
            )}

            {result && (
              <div className="bg-white border border-[#E5EBE5] rounded-3xl p-6 sm:p-7 shadow-sm space-y-5">
                
                {/* Hero EMI Display */}
                <div className="bg-[#F0FDF4] border border-[#86EFAC] rounded-2xl p-5 text-center shadow-xs">
                  <span className="text-xs font-bold text-[#047857] uppercase tracking-wider block">
                    Calculated Monthly EMI
                  </span>
                  <span className="text-4xl sm:text-5xl font-extrabold text-[#16A34A] tracking-tight block my-2">
                    {formatCurrency(result.emi_amount)}
                  </span>
                  <span className="text-xs text-[#6B7280]">
                    Payment starts at Month {result.first_emi_month}
                  </span>
                </div>

                {/* Breakdown Tiles */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-[#F8FAF8] border border-[#E5EBE5] rounded-2xl p-3.5">
                    <span className="text-[11px] font-semibold text-[#6B7280] block">Effective Principal (P)</span>
                    <span className="text-base font-bold text-[#111827] mt-0.5 block">
                      {formatCurrency(result.effective_loan_amount)}
                    </span>
                  </div>

                  <div className="bg-[#F8FAF8] border border-[#E5EBE5] rounded-2xl p-3.5">
                    <span className="text-[11px] font-semibold text-[#6B7280] block">Total Interest</span>
                    <span className="text-base font-bold text-[#D97706] mt-0.5 block">
                      {formatCurrency(result.total_interest)}
                    </span>
                  </div>

                  <div className="bg-[#F8FAF8] border border-[#E5EBE5] rounded-2xl p-3.5">
                    <span className="text-[11px] font-semibold text-[#6B7280] block">Total Repayment</span>
                    <span className="text-base font-bold text-[#111827] mt-0.5 block">
                      {formatCurrency(result.total_payment)}
                    </span>
                  </div>

                  <div className="bg-[#F8FAF8] border border-[#E5EBE5] rounded-2xl p-3.5">
                    <span className="text-[11px] font-semibold text-[#6B7280] block">Total Duration</span>
                    <span className="text-base font-bold text-[#111827] mt-0.5 block">
                      {result.total_duration_months} Months
                    </span>
                  </div>
                </div>

                {/* Caps Warning if any */}
                {result.caps_applied.length > 0 && (
                  <div className="bg-[#FFFBEB] border border-[#FDE68A] rounded-xl p-3 text-xs text-[#92400E]">
                    <span className="font-bold block mb-1">Notice on Scheme Limits:</span>
                    {result.caps_applied.map((cap, i) => (
                      <p key={i}>• {cap}</p>
                    ))}
                  </div>
                )}

                {/* Action: Next step Locator */}
                <button
                  onClick={() => router.push("/locator")}
                  className="w-full py-3.5 rounded-xl bg-[#16A34A] hover:bg-[#15803D] text-white text-sm font-bold shadow-xs hover:shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
                  id="btn-find-partners"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                  <span>Find Authorized Partners for this Scheme</span>
                </button>

                {/* Amortization Schedule Toggle */}
                <button
                  onClick={() => setShowSchedule(!showSchedule)}
                  className="w-full py-2 text-xs font-bold text-[#6B7280] hover:text-[#111827] transition-colors"
                  id="btn-toggle-schedule"
                >
                  {showSchedule ? "▲ Hide Monthly Schedule" : "▼ Show Month-by-Month Schedule"}
                </button>

              </div>
            )}

            {/* Schedule View */}
            {showSchedule && result && result.schedule.length > 0 && (
              <div className="bg-white border border-[#E5EBE5] rounded-3xl p-4 shadow-sm max-h-72 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-white border-b border-[#E5EBE5]">
                    <tr className="text-[#6B7280] text-left">
                      <th className="py-2">Mth</th>
                      <th className="py-2">Type</th>
                      <th className="py-2 text-right">EMI</th>
                      <th className="py-2 text-right">Interest</th>
                      <th className="py-2 text-right">Balance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#F3F4F6]">
                    {result.schedule.map((row) => (
                      <tr key={row.month} className="text-[#374151]">
                        <td className="py-2 font-medium">{row.month}</td>
                        <td className="py-2">
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            row.type === "moratorium" ? "bg-[#FEF3C7] text-[#92400E]" : "bg-[#DCFCE7] text-[#16A34A]"
                          }`}>
                            {row.type}
                          </span>
                        </td>
                        <td className="py-2 text-right font-semibold">{formatCurrency(row.emi)}</td>
                        <td className="py-2 text-right text-[#D97706]">{formatCurrency(row.interest)}</td>
                        <td className="py-2 text-right font-medium">{formatCurrency(row.balance)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

          </div>

        </div>

      </div>
    </div>
  );
}
