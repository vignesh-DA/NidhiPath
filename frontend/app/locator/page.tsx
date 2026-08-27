"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { locatePartners } from "@/lib/apiClient";
import type { MatchedScheme, LocateResponse, Partner } from "@/lib/types";

export default function LocatorPage() {
  const router = useRouter();
  const [scheme, setScheme] = useState<MatchedScheme | null>(null);
  const [result, setResult] = useState<LocateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem("nidhipath_selected_scheme");
    if (!stored) {
      router.push("/intake");
      return;
    }
    const parsed = JSON.parse(stored) as MatchedScheme;
    setScheme(parsed);

    const intake = sessionStorage.getItem("nidhipath_intake");
    const intakeData = intake ? JSON.parse(intake) : {};

    locatePartners({
      scheme_channel_partners: parsed.channel_partners,
      user_state: intakeData.user_state || undefined,
    })
      .then((res) => {
        setResult(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to locate partners. Is the backend running?");
        setLoading(false);
      });
  }, [router]);

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      SCA: "var(--color-accent)",
      PSB: "var(--color-info)",
      RRB: "#A855F7",
      "NBFC-MFI": "var(--color-warning)",
      Cooperative: "#EC4899",
      SFB: "#06B6D4",
    };
    return colors[type] || "var(--color-text-muted)";
  };

  if (loading) {
    return (
      <div className="page-container pt-16 text-center">
        <div className="animate-pulse-glow inline-block p-8 glass-card">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full border-2 border-[var(--color-accent)] border-t-transparent animate-spin" />
          <p className="text-[var(--color-text-secondary)]">Locating channel partners...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container pt-16 max-w-xl mx-auto">
        <div className="glass-card p-8 text-center">
          <h2 className="text-lg font-semibold mb-2">Connection Error</h2>
          <p className="text-sm text-[var(--color-text-secondary)] mb-4">{error}</p>
          <button onClick={() => window.location.reload()} className="btn-primary">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container pt-8 pb-16">
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

        <h1 className="section-title">Channel Partners</h1>
        {scheme && (
          <p className="text-sm text-[var(--color-accent)] font-medium">{scheme.scheme_name}</p>
        )}
        <p className="section-subtitle mt-1">
          {result?.total_results || 0} authorized partner{(result?.total_results || 0) !== 1 ? "s" : ""} found
        </p>
      </div>

      {/* Pipeline Summary */}
      {result?.pipeline_summary && (
        <div className="animate-fade-in glass-card p-4 mb-8">
          <p className="text-xs font-medium text-[var(--color-text-muted)] mb-3">Filter Pipeline</p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(result.pipeline_summary).map(([step, info]) => {
              const stepInfo = info as Record<string, unknown>;
              return (
                <div key={step} className="bg-[var(--color-surface-2)] rounded-lg px-3 py-2 text-xs">
                  <span className="text-[var(--color-text-muted)]">{step}: </span>
                  <span className="text-[var(--color-foreground)] font-medium">
                    {stepInfo.output !== undefined ? `${stepInfo.output} partners` : stepInfo.status as string}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Proximity Notice */}
      {result?.proximity_status === "unavailable" && (
        <div className="animate-fade-in bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-lg p-4 mb-6">
          <div className="flex items-start gap-2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-warning)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <div>
              <p className="text-xs font-medium text-[var(--color-warning)]">Proximity Not Available</p>
              <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{result.proximity_note}</p>
            </div>
          </div>
        </div>
      )}

      {/* Partners List */}
      <div className="space-y-3 stagger-children">
        {result?.partners.map((partner: Partner, idx: number) => (
          <div key={partner.partner_id || idx} className="glass-card p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-medium text-[var(--color-foreground)]">{partner.partner_name}</h3>
                  <span
                    className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                    style={{
                      background: `${getTypeColor(partner.partner_type)}15`,
                      color: getTypeColor(partner.partner_type),
                    }}
                  >
                    {partner.partner_type}
                  </span>
                </div>

                <p className="text-xs text-[var(--color-text-muted)] mb-2">
                  📍 {partner.state || "National"}
                  {partner.contact && ` • 📞 ${partner.contact}`}
                </p>

                {partner.address && (
                  <p className="text-xs text-[var(--color-text-secondary)]">{partner.address}</p>
                )}
              </div>

              {/* Health badge */}
              {partner.health && (
                <div className={`shrink-0 text-center px-3 py-1.5 rounded-lg text-xs ${
                  partner.health.is_healthy
                    ? "bg-[var(--color-accent)]/10 text-[var(--color-accent)]"
                    : "bg-[var(--color-warning)]/10 text-[var(--color-warning)]"
                }`}>
                  <p className="font-medium">{partner.health.is_healthy ? "Healthy" : "Deprioritized"}</p>
                  <p className="text-[10px] opacity-75">NPA: {partner.health.npa_ratio}%</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {result?.partners.length === 0 && (
        <div className="glass-card p-8 text-center">
          <p className="text-[var(--color-text-secondary)]">No partners found for this scheme and location.</p>
          <p className="text-sm text-[var(--color-text-muted)] mt-2">Try selecting a different state.</p>
        </div>
      )}

      {/* Known gaps */}
      {result?.known_gaps && result.known_gaps.length > 0 && (
        <div className="mt-8 bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-lg p-4 text-xs text-[var(--color-text-muted)]">
          <p className="font-medium text-[var(--color-text-secondary)] mb-2">Known Limitations</p>
          {result.known_gaps.map((gap, i) => (
            <p key={i} className="mb-1">• {gap}</p>
          ))}
        </div>
      )}

      {/* CTA to apply */}
      <div className="mt-8 text-center">
        <a
          href="https://pmsuraj.dosje.gov.in/"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary inline-flex"
          id="btn-apply"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
          </svg>
          Apply via PM-SURAJ Portal
        </a>
      </div>
    </div>
  );
}
