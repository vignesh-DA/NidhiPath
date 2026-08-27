"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { locatePartners } from "@/lib/apiClient";
import type { MatchedScheme, LocateResponse, Partner } from "@/lib/types";

export default function LocatorPage() {
  const router = useRouter();
  const [scheme, setScheme] = useState<MatchedScheme | null>(null);
  const [result, setResult] = useState<LocateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPartner, setSelectedPartner] = useState<Partner | null>(null);

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
        if (res.partners && res.partners.length > 0) {
          setSelectedPartner(res.partners[0]);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to locate channel partners. Is the backend running?");
        setLoading(false);
      });
  }, [router]);

  const getPartnerBadge = (type: string) => {
    switch (type) {
      case "SCA":
        return { bg: "bg-[#DCFCE7]", text: "text-[#16A34A]", label: "State Channelising Agency (SCA)" };
      case "PSB":
        return { bg: "bg-[#DBEAFE]", text: "text-[#1D4ED8]", label: "Public Sector Bank" };
      case "RRB":
        return { bg: "bg-[#F3E8FF]", text: "text-[#7E22CE]", label: "Regional Rural Bank" };
      case "NBFC-MFI":
        return { bg: "bg-[#FEF3C7]", text: "text-[#92400E]", label: "Micro-Finance Institution" };
      default:
        return { bg: "bg-[#F3F4F6]", text: "text-[#374151]", label: type };
    }
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
          <h3 className="text-lg font-bold text-[#0F1F0F]">Locating Channel Partners...</h3>
          <p className="text-xs text-[#6B7280] mt-1.5 leading-relaxed">
            Applying 4-step pipeline: Capability → Eligibility → Health ranking.
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
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" />
            </svg>
          </div>
          <h2 className="text-lg font-bold text-[#111827] mb-2">Partner Query Error</h2>
          <p className="text-sm text-[#4B5563] mb-5">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-5 py-2.5 rounded-xl bg-[#16A34A] text-sm font-semibold text-white hover:bg-[#15803D]"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-[#F8FAF8] min-h-[calc(100vh-80px)] py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1280px] mx-auto">
        
        {/* Navigation & Header */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <Link
              href="/recommendation"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#6B7280] hover:text-[#16A34A] transition-colors mb-2"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="19" y1="12" x2="5" y2="12" />
                <polyline points="12 19 5 12 12 5" />
              </svg>
              <span>Back to Recommendations</span>
            </Link>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0F1F0F] tracking-tight">
              Authorized Channel Partners
            </h1>
            <p className="text-sm text-[#6B7280] mt-0.5">
              Found <strong>{result?.total_results || 0}</strong> verified lending agencies authorized for <span className="text-[#16A34A] font-bold">{scheme?.scheme_name}</span>.
            </p>
          </div>

          <a
            href="https://pmsuraj.dosje.gov.in/"
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2.5 rounded-xl bg-[#16A34A] hover:bg-[#15803D] text-white text-xs font-bold shadow-xs hover:shadow-md transition-all self-start sm:self-auto flex items-center gap-2"
            id="btn-apply-portal"
          >
            <span>Submit on PM-SURAJ</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="7" y1="17" x2="17" y2="7" />
              <polyline points="7 7 17 7 17 17" />
            </svg>
          </a>
        </div>

        {/* 4-Step Pipeline Summary Pill */}
        {result?.pipeline_summary && (
          <div className="bg-white border border-[#E5EBE5] rounded-2xl p-4 mb-6 shadow-xs flex flex-wrap items-center gap-3 text-xs">
            <span className="font-bold text-[#111827] flex items-center gap-1.5">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#16A34A" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Verified Pipeline:
            </span>
            <span className="bg-[#F0FDF4] text-[#16A34A] px-2.5 py-1 rounded-lg font-medium">
              1. Capability Filter: {((result.pipeline_summary as Record<string, Record<string, unknown>>)?.step1_capability?.output as number) ?? 0}
            </span>
            <span className="text-[#D1D5DB]">→</span>
            <span className="bg-[#F0FDF4] text-[#16A34A] px-2.5 py-1 rounded-lg font-medium">
              2. State Eligibility: {((result.pipeline_summary as Record<string, Record<string, unknown>>)?.step2_eligibility?.output as number) ?? 0}
            </span>
            <span className="text-[#D1D5DB]">→</span>
            <span className="bg-[#F0FDF4] text-[#16A34A] px-2.5 py-1 rounded-lg font-medium">
              3. Health Prioritization: {((result.pipeline_summary as Record<string, Record<string, unknown>>)?.step3_health?.output as number) ?? 0}
            </span>
          </div>
        )}

        {/* 2-Column Split: Map Representation + List */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left: Interactive Partner List (lg:col-span-7) */}
          <div className="lg:col-span-7 space-y-3.5">
            {result?.partners.map((partner: Partner, idx: number) => {
              const badge = getPartnerBadge(partner.partner_type);
              const isSelected = selectedPartner?.partner_id === partner.partner_id || (!selectedPartner && idx === 0);

              return (
                <div
                  key={partner.partner_id || idx}
                  onClick={() => setSelectedPartner(partner)}
                  className={`bg-white rounded-2xl p-5 border-2 cursor-pointer transition-all ${
                    isSelected
                      ? "border-[#16A34A] shadow-md bg-[#FAFDF9]"
                      : "border-[#E5EBE5] hover:border-[#BBF7D0] shadow-xs"
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2 mb-1.5">
                        <span className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider ${badge.bg} ${badge.text}`}>
                          {badge.label}
                        </span>
                        {idx === 0 && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#DCFCE7] text-[#16A34A]">
                            PRIMARY CHANNEL
                          </span>
                        )}
                      </div>

                      <h3 className="text-base font-bold text-[#0F1F0F] leading-snug">
                        {partner.partner_name}
                      </h3>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-[#6B7280] mt-2">
                        <span className="flex items-center gap-1 font-medium text-[#374151]">
                          📍 {partner.state || "National Jurisdiction"}
                        </span>
                        {partner.pincode && (
                          <span>PIN: {partner.pincode}</span>
                        )}
                        {partner.contact && (
                          <span>📞 {partner.contact}</span>
                        )}
                      </div>

                      {partner.address_raw && (
                        <p className="text-xs text-[#6B7280] mt-2 line-clamp-2 leading-relaxed bg-[#F8FAF8] p-2.5 rounded-xl border border-[#F3F4F6]">
                          {partner.address_raw}
                        </p>
                      )}
                    </div>

                    {/* Health Status Metric */}
                    {partner.health && (
                      <div className="shrink-0 text-right">
                        <span className={`text-[11px] font-bold px-2.5 py-1 rounded-xl block ${
                          partner.health.is_healthy
                            ? "bg-[#DCFCE7] text-[#16A34A]"
                            : "bg-[#FEF3C7] text-[#92400E]"
                        }`}>
                          {partner.health.is_healthy ? "✓ Operational" : "Deprioritized"}
                        </span>
                        <span className="text-[10px] text-[#9CA3AF] mt-1 block">
                          NPA: {partner.health.npa_ratio}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {result?.partners.length === 0 && (
              <div className="bg-white border border-[#E5EBE5] rounded-3xl p-10 text-center shadow-xs">
                <p className="text-base font-bold text-[#111827]">No channel partners found for selected location.</p>
                <p className="text-xs text-[#6B7280] mt-1">Try choosing a state or check national partners.</p>
              </div>
            )}
          </div>

          {/* Right: Partner Card & Geographic Map Representation (lg:col-span-5) */}
          <div className="lg:col-span-5 space-y-5">
            {/* Map Representation Box */}
            <div className="bg-white border border-[#E5EBE5] rounded-3xl p-6 shadow-xs relative overflow-hidden">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-bold text-[#0F1F0F]">Geographic Representation</h4>
                <span className="text-[11px] font-semibold text-[#16A34A] bg-[#DCFCE7] px-2.5 py-0.5 rounded-full">
                  PostGIS Enabled
                </span>
              </div>

              {/* Map Canvas Graphic */}
              <div className="w-full h-48 rounded-2xl bg-gradient-to-br from-[#ECFDF5] via-[#EFF6FF] to-[#F8FAF8] border border-[#D1E8D4] flex flex-col items-center justify-center p-4 text-center relative">
                {/* SVG Map grid dots */}
                <div className="w-12 h-12 rounded-full bg-white shadow-md flex items-center justify-center text-[#16A34A] mb-2 animate-bounce">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                  </svg>
                </div>
                <span className="text-xs font-bold text-[#0F1F0F]">
                  {selectedPartner ? selectedPartner.partner_name : "Select a partner"}
                </span>
                <span className="text-[11px] text-[#6B7280] mt-0.5">
                  {selectedPartner?.state ? `State: ${selectedPartner.state}` : "National Coverage"}
                </span>
              </div>

              {/* Proximity / Geocoding Notice */}
              <div className="mt-4 p-3 rounded-xl bg-[#F0FDF4] border border-[#BBF7D0] text-xs text-[#047857]">
                <p className="font-semibold">Proximity Notice:</p>
                <p className="text-[11px] text-[#4B5563] mt-0.5">
                  NBFC-MFIs are referenced via registered corporate offices. SCAs operate state-wide through district branches.
                </p>
              </div>
            </div>

            {/* Quick Next Step Guide */}
            <div className="bg-[#F0FDF4] border border-[#BBF7D0] rounded-3xl p-6 shadow-xs">
              <h4 className="text-sm font-bold text-[#0F1F0F] mb-2">How to Apply with this Partner</h4>
              <ol className="text-xs text-[#4B5563] space-y-2 list-decimal list-inside leading-relaxed">
                <li>Note the partner agency name and scheme ID: <strong>{scheme?.scheme_id}</strong></li>
                <li>Submit your application on the <strong>PM-SURAJ</strong> portal selecting this channel agency.</li>
                <li>Visit the nearest branch with Caste Certificate, Aadhaar, and Project Report.</li>
              </ol>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
