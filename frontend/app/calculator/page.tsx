"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
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
    setRequestedAmount(Math.min(maxLoan, parsed.project_cost_max));
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

  const formatCurrency = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

  if (!scheme) return null;

  const maxLoan = scheme.max_loan_amount || scheme.project_cost_max * (scheme.project_cost_coverage_pct / 100);
  const maxMonths = scheme.tenure_years ? scheme.tenure_years * 12 : 120;

  return (
    <div className="page-container pt-8 pb-16 max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-8 animate-fade-in">
        <button
          onClick={() => router.push("/recommendation")}
          className="flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors mb-6 cursor-pointer"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Back to recommendations
        </button>

        <h1 className="section-title">EMI Calculator</h1>
        <p className="text-sm text-[var(--color-accent)] font-medium">{scheme.scheme_name}</p>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">
          {scheme.interest_rate_beneficiary}% p.a. • Coverage: {scheme.project_cost_coverage_pct}%
        </p>
      </div>

      <div className="grid md:grid-cols-[1fr,1.2fr] gap-8">
        {/* Sliders */}
        <div className="space-y-6 animate-slide-up">
          {/* Loan Amount */}
          <div>
            <label className="label">
              Loan Amount: <span className="text-[var(--color-foreground)] font-semibold">{formatCurrency(requestedAmount)}</span>
            </label>
            <input
              type="range"
              min={10000}
              max={maxLoan}
              step={5000}
              value={requestedAmount}
              onChange={(e) => setRequestedAmount(Number(e.target.value))}
              className="w-full h-2 rounded-full bg-[var(--color-surface-3)] appearance-none cursor-pointer accent-[var(--color-accent)]"
              id="slider-amount"
            />
            <div className="flex justify-between text-xs text-[var(--color-text-muted)] mt-1">
              <span>₹10,000</span>
              <span>{formatCurrency(maxLoan)}</span>
            </div>
          </div>

          {/* Tenure */}
          <div>
            <label className="label">
              Tenure: <span className="text-[var(--color-foreground)] font-semibold">{requestedMonths} months ({(requestedMonths / 12).toFixed(1)} yrs)</span>
            </label>
            <input
              type="range"
              min={6}
              max={maxMonths}
              step={6}
              value={requestedMonths}
              onChange={(e) => setRequestedMonths(Number(e.target.value))}
              className="w-full h-2 rounded-full bg-[var(--color-surface-3)] appearance-none cursor-pointer accent-[var(--color-accent)]"
              id="slider-tenure"
            />
            <div className="flex justify-between text-xs text-[var(--color-text-muted)] mt-1">
              <span>6 months</span>
              <span>{maxMonths} months</span>
            </div>
          </div>

          {/* Moratorium Info */}
          {scheme.moratorium_months && scheme.moratorium_months > 0 && (
            <div className="bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-lg p-4">
              <p className="text-xs font-medium text-[var(--color-text-secondary)] mb-1">Moratorium Period</p>
              <p className="text-sm text-[var(--color-foreground)]">{scheme.moratorium_months} months</p>
              <p className="text-xs text-[var(--color-text-muted)] mt-1">
                EMI starts from month {scheme.moratorium_months + 1}
              </p>
            </div>
          )}
        </div>

        {/* Results */}
        <div className="animate-slide-up" style={{ animationDelay: "0.1s" }}>
          {error && (
            <div className="bg-[var(--color-destructive)]/10 border border-[var(--color-destructive)]/30 rounded-lg p-3 text-sm text-[var(--color-destructive)] mb-4">
              {error}
            </div>
          )}

          {result && (
            <div className="space-y-4">
              {/* EMI Hero */}
              <div className="glass-card p-6 text-center glow-border">
                <p className="text-sm text-[var(--color-text-muted)] mb-1">Monthly EMI</p>
                <p className="text-4xl font-bold text-[var(--color-accent)] glow-text">
                  {formatCurrency(result.emi_amount)}
                </p>
                <p className="text-xs text-[var(--color-text-muted)] mt-2">
                  Starting from month {result.first_emi_month}
                </p>
              </div>

              {/* Breakdown */}
              <div className="grid grid-cols-2 gap-3">
                <div className="glass-card p-4">
                  <p className="text-xs text-[var(--color-text-muted)]">Effective Loan</p>
                  <p className="text-lg font-semibold">{formatCurrency(result.effective_loan_amount)}</p>
                </div>
                <div className="glass-card p-4">
                  <p className="text-xs text-[var(--color-text-muted)]">Total Interest</p>
                  <p className="text-lg font-semibold text-[var(--color-warning)]">{formatCurrency(result.total_interest)}</p>
                </div>
                <div className="glass-card p-4">
                  <p className="text-xs text-[var(--color-text-muted)]">Total Payment</p>
                  <p className="text-lg font-semibold">{formatCurrency(result.total_payment)}</p>
                </div>
                <div className="glass-card p-4">
                  <p className="text-xs text-[var(--color-text-muted)]">Total Duration</p>
                  <p className="text-lg font-semibold">{result.total_duration_months} months</p>
                </div>
              </div>

              {/* Caps Applied */}
              {result.caps_applied.length > 0 && (
                <div className="bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-lg p-4">
                  <p className="text-xs font-medium text-[var(--color-warning)] mb-2">⚠ Caps Applied</p>
                  {result.caps_applied.map((cap, i) => (
                    <p key={i} className="text-xs text-[var(--color-text-secondary)] mb-1">• {cap}</p>
                  ))}
                </div>
              )}

              {/* Assumption */}
              <div className="bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-lg p-3">
                <p className="text-xs text-[var(--color-text-muted)]">
                  ⓘ {result.assumption_note}
                </p>
              </div>

              {/* Schedule toggle */}
              <button
                onClick={() => { setShowSchedule(!showSchedule); }}
                className="btn-secondary w-full justify-center text-sm"
                id="btn-toggle-schedule"
              >
                {showSchedule ? "Hide" : "Show"} Amortization Schedule
              </button>

              {/* Schedule Table */}
              {showSchedule && result.schedule.length > 0 && (
                <div className="overflow-x-auto glass-card p-4 max-h-64 overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead className="sticky top-0 bg-[var(--color-card)]">
                      <tr className="text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                        <th className="py-2 text-left">Month</th>
                        <th className="py-2 text-left">Type</th>
                        <th className="py-2 text-right">EMI</th>
                        <th className="py-2 text-right">Principal</th>
                        <th className="py-2 text-right">Interest</th>
                        <th className="py-2 text-right">Balance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.schedule.map((row) => (
                        <tr key={row.month} className="border-b border-[var(--color-border)]/30 text-[var(--color-text-secondary)]">
                          <td className="py-1.5">{row.month}</td>
                          <td className="py-1.5">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                              row.type === "moratorium"
                                ? "bg-[var(--color-warning)]/10 text-[var(--color-warning)]"
                                : "bg-[var(--color-accent)]/10 text-[var(--color-accent)]"
                            }`}>
                              {row.type}
                            </span>
                          </td>
                          <td className="py-1.5 text-right">{formatCurrency(row.emi)}</td>
                          <td className="py-1.5 text-right">{formatCurrency(row.principal)}</td>
                          <td className="py-1.5 text-right">{formatCurrency(row.interest)}</td>
                          <td className="py-1.5 text-right font-medium">{formatCurrency(row.balance)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => router.push("/locator")}
                  className="btn-primary flex-1 justify-center"
                  id="btn-find-partners"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" /><circle cx="12" cy="10" r="3" />
                  </svg>
                  Find Partners
                </button>
              </div>
            </div>
          )}

          {loading && !result && (
            <div className="glass-card p-8 text-center">
              <div className="w-8 h-8 mx-auto mb-3 rounded-full border-2 border-[var(--color-accent)] border-t-transparent animate-spin" />
              <p className="text-sm text-[var(--color-text-secondary)]">Calculating...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
