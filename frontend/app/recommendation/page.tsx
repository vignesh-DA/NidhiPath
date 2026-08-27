"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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

  const handleSelectScheme = (scheme: MatchedScheme) => {
    sessionStorage.setItem("nidhipath_selected_scheme", JSON.stringify(scheme));
    router.push("/calculator");
  };

  const handleLocatePartners = (scheme: MatchedScheme) => {
    sessionStorage.setItem("nidhipath_selected_scheme", JSON.stringify(scheme));
    router.push("/locator");
  };

  const formatCurrency = (n: number | undefined | null) => {
    if (n == null) return "N/A";
    return `₹${n.toLocaleString("en-IN")}`;
  };

  if (loading) {
    return (
      <div className="page-container pt-16 text-center">
        <div className="animate-pulse-glow inline-block p-8 glass-card">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full border-2 border-[var(--color-accent)] border-t-transparent animate-spin" />
          <p className="text-[var(--color-text-secondary)]">Matching schemes...</p>
          <p className="text-xs text-[var(--color-text-muted)] mt-1">&lt;100ms, zero LLM calls</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container pt-16 max-w-xl mx-auto">
        <div className="glass-card p-8 text-center">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-[var(--color-destructive)]/10 flex items-center justify-center">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-destructive)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold mb-2">Connection Error</h2>
          <p className="text-sm text-[var(--color-text-secondary)] mb-4">{error}</p>
          <p className="text-xs text-[var(--color-text-muted)] mb-6">
            Make sure the backend is running: <code className="text-[var(--color-accent)]">uvicorn app.main:app --reload</code>
          </p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => router.push("/intake")} className="btn-secondary">
              ← Edit intake
            </button>
            <button onClick={() => window.location.reload()} className="btn-primary">
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
    <div className="page-container pt-8 pb-16">
      {/* Back + Header */}
      <div className="mb-8 animate-fade-in">
        <button
          onClick={() => router.push("/intake")}
          className="flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors mb-6 cursor-pointer"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Edit intake
        </button>

        <h1 className="section-title">Your Scheme Recommendations</h1>
        <p className="section-subtitle">
          Found {primary?.total_matches || 0} NSFDC credit scheme{(primary?.total_matches || 0) !== 1 ? "s" : ""} matching your profile
        </p>
      </div>

      {/* Input Summary */}
      {intake && (
        <div className="animate-fade-in glass-card p-4 mb-8 flex flex-wrap gap-3 text-sm">
          <span className="bg-[var(--color-surface-3)] px-3 py-1 rounded-full text-[var(--color-text-secondary)]">
            💼 {intake.project_type === "education" ? "Education" : "Business"}
          </span>
          <span className="bg-[var(--color-surface-3)] px-3 py-1 rounded-full text-[var(--color-text-secondary)]">
            💰 Cost: {formatCurrency(intake.estimated_cost)}
          </span>
          <span className="bg-[var(--color-surface-3)] px-3 py-1 rounded-full text-[var(--color-text-secondary)]">
            📊 Income: {formatCurrency(intake.income_level)}
          </span>
          {intake.user_state && (
            <span className="bg-[var(--color-surface-3)] px-3 py-1 rounded-full text-[var(--color-text-secondary)]">
              📍 {intake.user_state}
            </span>
          )}
        </div>
      )}

      {/* ═══ PRIMARY: NSFDC Credit Schemes ═══ */}
      <section className="mb-12 animate-slide-up">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-6 rounded-full bg-[var(--color-accent)]" />
          <h2 className="text-lg font-semibold">NSFDC Credit Schemes</h2>
          <span className="text-xs bg-[var(--color-accent)]/10 text-[var(--color-accent)] px-2 py-0.5 rounded-full font-medium">
            Exact Match
          </span>
        </div>

        {!primary?.top_pick ? (
          <div className="glass-card p-8 text-center">
            <p className="text-[var(--color-text-secondary)]">No NSFDC credit schemes match your criteria.</p>
            <p className="text-sm text-[var(--color-text-muted)] mt-2">
              Try adjusting your project cost or income level.
            </p>
          </div>
        ) : (
          <div className="space-y-4 stagger-children">
            {/* Top Pick */}
            <div className="glass-card p-6 border-[var(--color-accent)]/30 glow-border">
              <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium bg-[var(--color-accent)] text-[var(--color-on-accent)] px-2 py-0.5 rounded-full">
                      TOP PICK
                    </span>
                  </div>
                  <h3 className="text-xl font-semibold text-[var(--color-foreground)]">
                    {primary.top_pick.scheme_name}
                  </h3>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-[var(--color-accent)]">
                    {primary.top_pick.interest_rate_beneficiary}%
                  </p>
                  <p className="text-xs text-[var(--color-text-muted)]">p.a. beneficiary rate</p>
                </div>
              </div>

              <p className="text-sm text-[var(--color-text-secondary)] mb-4 leading-relaxed">
                {primary.top_pick.match_reason}
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
                <div className="bg-[var(--color-surface-2)] rounded-lg p-3">
                  <p className="text-xs text-[var(--color-text-muted)]">Max Loan</p>
                  <p className="text-sm font-semibold">{formatCurrency(primary.top_pick.max_loan_amount)}</p>
                </div>
                <div className="bg-[var(--color-surface-2)] rounded-lg p-3">
                  <p className="text-xs text-[var(--color-text-muted)]">Tenure</p>
                  <p className="text-sm font-semibold">{primary.top_pick.tenure_years ? `${primary.top_pick.tenure_years} years` : "N/A"}</p>
                </div>
                <div className="bg-[var(--color-surface-2)] rounded-lg p-3">
                  <p className="text-xs text-[var(--color-text-muted)]">Moratorium</p>
                  <p className="text-sm font-semibold">{primary.top_pick.moratorium_months ? `${primary.top_pick.moratorium_months} months` : "None"}</p>
                </div>
                <div className="bg-[var(--color-surface-2)] rounded-lg p-3">
                  <p className="text-xs text-[var(--color-text-muted)]">Coverage</p>
                  <p className="text-sm font-semibold">{primary.top_pick.project_cost_coverage_pct}%</p>
                </div>
              </div>

              <div className="flex gap-3 flex-wrap">
                <button onClick={() => handleSelectScheme(primary.top_pick!)} className="btn-primary" id="btn-calc-top">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="4" y="2" width="16" height="20" rx="2" /><line x1="8" y1="10" x2="16" y2="10" /><line x1="8" y1="14" x2="16" y2="14" /><line x1="8" y1="18" x2="12" y2="18" />
                  </svg>
                  Calculate EMI
                </button>
                <button onClick={() => handleLocatePartners(primary.top_pick!)} className="btn-secondary" id="btn-locate-top">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" /><circle cx="12" cy="10" r="3" />
                  </svg>
                  Find Partners
                </button>
              </div>
            </div>

            {/* Alternatives */}
            {primary.alternatives.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-[var(--color-text-muted)] mb-3 mt-6">
                  {primary.alternatives.length} Alternative{primary.alternatives.length > 1 ? "s" : ""}
                </h4>
                <div className="grid md:grid-cols-2 gap-3">
                  {primary.alternatives.map((alt) => (
                    <div key={alt.scheme_id} className="glass-card p-5">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-medium text-[var(--color-foreground)] text-sm">{alt.scheme_name}</h4>
                        <span className="text-sm font-semibold text-[var(--color-accent)]">{alt.interest_rate_beneficiary}%</span>
                      </div>
                      <p className="text-xs text-[var(--color-text-muted)] mb-3 line-clamp-2">{alt.match_reason}</p>
                      {alt.max_loan_amount && (
                        <p className="text-xs text-[var(--color-text-secondary)]">Max: {formatCurrency(alt.max_loan_amount)}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* ═══ SECONDARY: Welfare Schemes ═══ */}
      {secondary && secondary.total_matches > 0 && (
        <section className="animate-slide-up" style={{ animationDelay: "0.2s" }}>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-1 h-6 rounded-full bg-[var(--color-info)]" />
            <h2 className="text-lg font-semibold">Related Welfare Schemes</h2>
            <span className="text-xs bg-[var(--color-info)]/10 text-[var(--color-info)] px-2 py-0.5 rounded-full font-medium">
              Approximate Match
            </span>
          </div>
          <p className="text-xs text-[var(--color-text-muted)] mb-4 ml-3">{secondary.disclaimer}</p>

          <div className="grid md:grid-cols-2 gap-3 stagger-children">
            {secondary.matches.slice(0, 8).map((scheme) => (
              <div key={scheme.scheme_id} className="glass-card p-4">
                <h4 className="font-medium text-sm text-[var(--color-foreground)] mb-1">{scheme.scheme_name}</h4>
                <p className="text-xs text-[var(--color-text-muted)] mb-2">{scheme.issuing_state}</p>
                {scheme.benefits && (
                  <p className="text-xs text-[var(--color-text-secondary)] line-clamp-2">{scheme.benefits}</p>
                )}
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {scheme.match_reasons.map((reason, i) => (
                    <span key={i} className="text-[10px] bg-[var(--color-surface-3)] px-2 py-0.5 rounded-full text-[var(--color-text-muted)]">
                      {reason}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {secondary.total_matches > 8 && (
            <p className="text-sm text-[var(--color-text-muted)] mt-4 text-center">
              +{secondary.total_matches - 8} more schemes available
            </p>
          )}
        </section>
      )}

      {/* Handoff notice */}
      <div className="mt-12 bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-xl p-5 text-sm text-[var(--color-text-secondary)] animate-fade-in" style={{ animationDelay: "0.3s" }}>
        <div className="flex items-start gap-3">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0">
            <circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
          <div>
            <p className="font-medium text-[var(--color-foreground)] mb-1">Application Process</p>
            <p>
              This platform helps you find the right scheme — it does NOT process loan applications.
              To apply, visit the{" "}
              <a href="https://pmsuraj.dosje.gov.in/" target="_blank" rel="noopener noreferrer" className="text-[var(--color-accent)] underline">
                PM-SURAJ Portal
              </a>{" "}
              with your matched scheme details.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
