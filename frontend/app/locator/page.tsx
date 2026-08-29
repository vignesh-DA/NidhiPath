"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { locatePartners } from "@/lib/apiClient";
import type {
  MatchedScheme,
  LocateResponse,
  Partner,
  UserLocation,
  LocationSource,
} from "@/lib/types";
import { INDIAN_STATES } from "@/lib/types";

// ─── Reverse Geocode via Nominatim (free, no API key) ───────────────────────

async function reverseGeocode(
  lat: number,
  lon: number
): Promise<{ state: string; district?: string } | null> {
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10&addressdetails=1`,
      { headers: { "User-Agent": "NidhiPath/1.0" } }
    );
    if (!res.ok) return null;
    const data = await res.json();
    const addr = data.address || {};
    // Nominatim returns "state" for Indian states and "county" or "state_district" for districts
    const state = addr.state || null;
    const district =
      addr.state_district || addr.county || addr.city_district || null;
    if (!state) return null;
    return { state, district: district || undefined };
  } catch (e) {
    console.warn(
      `[locator] reverse geocode request failed for lat=${lat}, lon=${lon}:`,
      e
    );
    return null;
  }
}

// ─── Location Cache TTL (approved decision) ─────────────────────────────────
// Successful geolocation results are cached for 30 minutes. Manual overrides
// persist for the full session (no TTL). The intake fallback is always
// re-checkable — it never blocks a geolocation re-attempt.
// Why 30 min: a user's state doesn't change during a loan research session;
// sessionStorage dies on tab close (within-session freshness only); and ~2
// Nominatim calls/hour/user stays well inside its "max 1 request per second,
// no heavy use" usage policy.
const LOCATION_TTL_MS = 30 * 60 * 1000;

// GeolocationPositionError.code → human-readable failure reason
const GEO_ERROR_REASONS: Record<number, string> = {
  1: "permission denied",
  2: "position unavailable",
  3: "timed out",
};

function geoErrorReason(err: GeolocationPositionError): string {
  return GEO_ERROR_REASONS[err.code] ?? `unknown error (code ${err.code})`;
}

function useLocationResolution() {
  const [location, setLocation] = useState<UserLocation | null>(null);
  const [locationLoading, setLocationLoading] = useState(true);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [locationFallbackReason, setLocationFallbackReason] = useState<
    string | null
  >(null);

  useEffect(() => {
    // ── Step 1: cache check — only certain sources may short-circuit. ─────
    // Approved precedence: manual → use it, no TTL. Geolocation < 30 min old
    // → use it. Anything else (stale geolocation, intake fallback) is held
    // only as a failure fallback; geolocation is re-attempted either way.
    let staleFallback: UserLocation | null = null;
    let staleFallbackAgeMin: number | null = null;

    const cachedRaw = sessionStorage.getItem("nidhipath_location");
    if (cachedRaw) {
      try {
        const cached = JSON.parse(cachedRaw) as UserLocation;
        const ageMs =
          typeof cached.resolvedAt === "number"
            ? Date.now() - cached.resolvedAt
            : Infinity; // legacy entry without resolvedAt → treat as stale
        if (cached.source === "manual") {
          console.info(
            `[locator] cache hit (manual override, no TTL): ${cached.state}`
          );
          setLocation(cached);
          setLocationLoading(false);
          return;
        }
        if (cached.source === "geolocation" && ageMs < LOCATION_TTL_MS) {
          const ageMin = Math.max(0, Math.round(ageMs / 60000));
          console.info(
            `[locator] cache hit (geolocation, ${ageMin} min old < 30 min TTL): ${cached.state}`
          );
          setLocation(cached);
          setLocationLoading(false);
          return;
        }
        // Not authoritative — remember as fallback, but re-attempt geolocation.
        staleFallback = cached;
        if (Number.isFinite(ageMs)) {
          staleFallbackAgeMin = Math.max(0, Math.round(ageMs / 60000));
        }
        console.info(
          `[locator] cache not authoritative (source=${cached.source}, ` +
            `${
              staleFallbackAgeMin === null
                ? "no timestamp"
                : `${staleFallbackAgeMin} min old`
            }) — re-attempting geolocation`
        );
      } catch (e) {
        console.warn("[locator] corrupt location cache — discarding:", e);
        sessionStorage.removeItem("nidhipath_location");
      }
    }

    // ── Step 2: attempt browser geolocation (unless manual/TTL hit above) ──
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const { latitude, longitude } = pos.coords;
          console.info(
            `[locator] geolocation success: lat=${latitude.toFixed(5)}, lon=${longitude.toFixed(5)}`
          );
          const result = await reverseGeocode(latitude, longitude);
          if (result) {
            console.info(
              `[locator] reverse geocode OK: state=${result.state}${
                result.district ? `, district=${result.district}` : ""
              }`
            );
            const loc: UserLocation = {
              state: result.state,
              district: result.district,
              lat: latitude,
              lon: longitude,
              source: "geolocation",
              resolvedAt: Date.now(),
            };
            sessionStorage.setItem("nidhipath_location", JSON.stringify(loc));
            setLocation(loc);
            setLocationFallbackReason(null);
          } else {
            console.warn(
              `[locator] reverse geocode returned null for lat=${latitude}, lon=${longitude}`
            );
            fallbackOnFailure("Could not map your coordinates to a state");
          }
          setLocationLoading(false);
        },
        (err: GeolocationPositionError) => {
          const reason = geoErrorReason(err);
          console.error(
            `[locator] geolocation failed: ${reason} — ${err.message}`
          );
          fallbackOnFailure(`Location detection failed (${reason})`);
          setLocationLoading(false);
        },
        { timeout: 5000, maximumAge: 300000 }
      );
    } else {
      console.warn(
        "[locator] browser does not support geolocation — falling back"
      );
      fallbackOnFailure("Your browser does not support location detection");
      setLocationLoading(false);
    }

    // ── Step 3: fallback chain on geolocation failure ─────────────────────
    // Priority: last known geolocation reading → intake state → manual picker.
    // DECIDED explicitly in post-approval review (recorded as AD-12): stale
    // GPS deliberately outranks the intake form. The TTL policy already ranks
    // fresh GPS above the declared state, and letting a form value supersede
    // a good reading on any transient failure (5 s timeouts are routine on
    // desktops) would resurrect the original bug in reverse. A wrong guess is
    // visible here (fallback reason with reading age) and one tap from
    // correction. FLIP this precedence if user_state ever means "project
    // location" rather than "applicant location" — the declared state then
    // becomes the eligibility-relevant fact and must outrank GPS.
    // Intake values are cached as source "intake", which never short-circuits
    // a geolocation attempt on the next page load.
    function fallbackOnFailure(detail: string) {
      if (staleFallback?.source === "geolocation") {
        const age =
          staleFallbackAgeMin !== null ? ` (${staleFallbackAgeMin} min ago)` : "";
        setLocation(staleFallback);
        setLocationFallbackReason(
          `${detail} — showing your last detected location: ${staleFallback.state}${age}`
        );
        return;
      }
      if (staleFallback?.source === "intake") {
        setLocation(staleFallback);
        setLocationFallbackReason(
          `${detail} — using ${staleFallback.state} from your intake form`
        );
        return;
      }
      const intakeRaw = sessionStorage.getItem("nidhipath_intake");
      if (intakeRaw) {
        try {
          const parsed = JSON.parse(intakeRaw);
          if (parsed.user_state) {
            const loc: UserLocation = {
              state: parsed.user_state,
              source: "intake",
            };
            sessionStorage.setItem("nidhipath_location", JSON.stringify(loc));
            setLocation(loc);
            setLocationFallbackReason(
              `${detail} — using ${loc.state} from your intake form`
            );
            return;
          }
        } catch (e) {
          console.warn("[locator] corrupt intake cache:", e);
        }
      }
      // Nothing usable — surface the manual state picker.
      setLocationError("no_location");
    }
  }, []);

  const setManualLocation = useCallback(
    (state: string, district?: string) => {
      const loc: UserLocation = {
        state,
        district: district || undefined,
        source: "manual" as LocationSource,
        resolvedAt: Date.now(),
      };
      sessionStorage.setItem("nidhipath_location", JSON.stringify(loc));
      setLocation(loc);
      setLocationError(null);
      setLocationFallbackReason(null);
    },
    []
  );

  return {
    location,
    locationLoading,
    locationError,
    locationFallbackReason,
    setManualLocation,
  };
}

// ─── Main Component ─────────────────────────────────────────────────────────

export default function LocatorPage() {
  const router = useRouter();
  const [scheme, setScheme] = useState<MatchedScheme | null>(null);
  const [result, setResult] = useState<LocateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPartner, setSelectedPartner] = useState<Partner | null>(null);

  // Manual override state
  const [showOverride, setShowOverride] = useState(false);
  const [overrideState, setOverrideState] = useState("");

  const {
    location,
    locationLoading,
    locationError,
    locationFallbackReason,
    setManualLocation,
  } = useLocationResolution();

  // Load scheme from session
  useEffect(() => {
    const stored = sessionStorage.getItem("nidhipath_selected_scheme");
    if (!stored) {
      router.push("/intake");
      return;
    }
    setScheme(JSON.parse(stored) as MatchedScheme);
  }, [router]);

  // Fetch partners once location and scheme are ready
  useEffect(() => {
    if (!scheme) return;
    if (locationLoading) return;

    // If no location and no error yet, wait for manual input
    if (!location && locationError) {
      setLoading(false);
      return;
    }
    if (!location) return;

    setLoading(true);
    locatePartners({
      scheme_channel_partners: scheme.channel_partners,
      user_state: location.state || undefined,
      user_district: location.district || undefined,
      user_lat: location.lat,
      user_lon: location.lon,
    })
      .then((res) => {
        setResult(res);
        if (res.partners && res.partners.length > 0) {
          setSelectedPartner(res.partners[0]);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(
          err.message || "Failed to locate channel partners. Is the backend running?"
        );
        setLoading(false);
      });
  }, [scheme, location, locationLoading, locationError]);

  // Handle manual location override
  const handleOverrideSubmit = () => {
    if (overrideState) {
      setManualLocation(overrideState);
      setShowOverride(false);
      // Clear cached results so new ones load
      setResult(null);
      setSelectedPartner(null);
    }
  };

  const getPartnerBadge = (type: string) => {
    switch (type) {
      case "SCA":
        return {
          bg: "bg-[#DCFCE7]",
          text: "text-[#16A34A]",
          label: "State Channelising Agency (SCA)",
        };
      case "PSB":
        return {
          bg: "bg-[#DBEAFE]",
          text: "text-[#1D4ED8]",
          label: "Public Sector Bank",
        };
      case "RRB":
        return {
          bg: "bg-[#F3E8FF]",
          text: "text-[#7E22CE]",
          label: "Regional Rural Bank",
        };
      case "NBFC-MFI":
        return {
          bg: "bg-[#FEF3C7]",
          text: "text-[#92400E]",
          label: "Micro-Finance Institution",
        };
      default:
        return { bg: "bg-[#F3F4F6]", text: "text-[#374151]", label: type };
    }
  };

  const getTierBadge = (tier?: number) => {
    switch (tier) {
      case 1:
        return {
          bg: "bg-[#DCFCE7]",
          text: "text-[#16A34A]",
          icon: "📍",
          label: "District Match",
        };
      case 2:
        return {
          bg: "bg-[#DBEAFE]",
          text: "text-[#1D4ED8]",
          icon: "🏛️",
          label: "State Match",
        };
      case 3:
        return {
          bg: "bg-[#F3F4F6]",
          text: "text-[#6B7280]",
          icon: "🌐",
          label: "National",
        };
      default:
        return { bg: "bg-[#F3F4F6]", text: "text-[#6B7280]", icon: "", label: "" };
    }
  };

  const getLocationSourceLabel = () => {
    if (!location) return null;
    switch (location.source) {
      case "geolocation":
        return {
          icon: "📡",
          text: `Auto-detected: ${location.state}${location.district ? `, ${location.district}` : ""}`,
          color: "text-[#16A34A]",
          bg: "bg-[#F0FDF4]",
          border: "border-[#BBF7D0]",
        };
      case "intake":
        return {
          icon: "📋",
          text: locationFallbackReason
            ? `Fallback — from your intake: ${location.state}`
            : `From your intake: ${location.state}`,
          color: "text-[#1D4ED8]",
          bg: "bg-[#EFF6FF]",
          border: "border-[#BFDBFE]",
        };
      case "manual":
        return {
          icon: "✏️",
          text: `Manually selected: ${location.state}`,
          color: "text-[#7E22CE]",
          bg: "bg-[#FAF5FF]",
          border: "border-[#E9D5FF]",
        };
    }
  };

  // ─── No location: show location picker ──────────────────────────────────

  if (!locationLoading && locationError && !location) {
    return (
      <div className="w-full bg-[#F8FAF8] min-h-[calc(100vh-80px)] py-20 px-4 flex items-center justify-center">
        <div className="bg-white border border-[#E5EBE5] rounded-3xl p-8 text-center shadow-md max-w-md w-full">
          <div className="w-14 h-14 mx-auto mb-5 rounded-2xl bg-[#DBEAFE] flex items-center justify-center text-[#1D4ED8]">
            <svg
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-[#0F1F0F] mb-1">
            Select Your Location
          </h3>
          <p className="text-xs text-[#6B7280] mb-5 leading-relaxed">
            We need your state to filter partners to your region. National banks
            (PSBs) are shown regardless.
          </p>

          {locationFallbackReason && (
            <p className="text-xs text-[#92400E] bg-[#FFFBEB] border border-[#FDE68A] rounded-xl p-3 mb-4 leading-relaxed text-left flex items-start gap-1.5">
              <span aria-hidden>⚠️</span>
              <span>{locationFallbackReason}</span>
            </p>
          )}

          <select
            id="location-state-picker"
            className="w-full bg-white border border-[#D1D5DB] rounded-xl px-4 py-3 text-sm font-medium text-[#111827] focus:outline-none focus:border-[#16A34A] focus:ring-2 focus:ring-[#16A34A]/20 cursor-pointer mb-4"
            value={overrideState}
            onChange={(e) => setOverrideState(e.target.value)}
          >
            <option value="">Select your state...</option>
            {INDIAN_STATES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>

          <button
            onClick={() => {
              if (overrideState) {
                setManualLocation(overrideState);
              }
            }}
            disabled={!overrideState}
            className="w-full py-3 rounded-xl bg-[#16A34A] hover:bg-[#15803D] text-white text-sm font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            id="btn-set-location"
          >
            Show Partners for {overrideState || "..."}
          </button>
        </div>
      </div>
    );
  }

  // ─── Loading ────────────────────────────────────────────────────────────

  if (loading || locationLoading) {
    return (
      <div className="w-full bg-[#F8FAF8] min-h-[calc(100vh-80px)] py-20 px-4 flex items-center justify-center">
        <div className="bg-white border border-[#E5EBE5] rounded-3xl p-10 text-center shadow-md max-w-sm w-full">
          <div className="w-14 h-14 mx-auto mb-5 rounded-2xl bg-[#DCFCE7] flex items-center justify-center text-[#16A34A]">
            <svg
              className="animate-spin"
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <circle
                cx="12"
                cy="12"
                r="10"
                strokeDasharray="60"
                strokeDashoffset="15"
              />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-[#0F1F0F]">
            {locationLoading
              ? "Detecting Your Location..."
              : "Locating Channel Partners..."}
          </h3>
          <p className="text-xs text-[#6B7280] mt-1.5 leading-relaxed">
            {locationLoading
              ? "Using browser geolocation. You may see a permission prompt."
              : "Applying 4-step pipeline: Capability → Eligibility → Health → Location ranking."}
          </p>
        </div>
      </div>
    );
  }

  // ─── Error ──────────────────────────────────────────────────────────────

  if (error) {
    return (
      <div className="w-full bg-[#F8FAF8] min-h-[calc(100vh-80px)] py-16 px-4">
        <div className="bg-white border border-[#E5EBE5] rounded-3xl p-8 text-center shadow-md max-w-lg mx-auto">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-[#FEF2F2] flex items-center justify-center text-[#DC2626]">
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
            </svg>
          </div>
          <h2 className="text-lg font-bold text-[#111827] mb-2">
            Partner Query Error
          </h2>
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

  // ─── Main Result View ──────────────────────────────────────────────────

  const locationLabel = getLocationSourceLabel();

  // Group partners by tier for section rendering
  const tier2Partners = result?.partners.filter((p) => p.rank_tier === 2) || [];
  const tier3Partners = result?.partners.filter((p) => p.rank_tier === 3) || [];
  const tier1Partners = result?.partners.filter((p) => p.rank_tier === 1) || [];

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
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="19" y1="12" x2="5" y2="12" />
                <polyline points="12 19 5 12 12 5" />
              </svg>
              <span>Back to Recommendations</span>
            </Link>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0F1F0F] tracking-tight">
              Authorized Channel Partners
            </h1>
            <p className="text-sm text-[#6B7280] mt-0.5">
              Found{" "}
              <strong>{result?.total_results || 0}</strong> verified lending
              agencies authorized for{" "}
              <span className="text-[#16A34A] font-bold">
                {scheme?.scheme_name}
              </span>
              .
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
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="7" y1="17" x2="17" y2="7" />
              <polyline points="7 7 17 7 17 17" />
            </svg>
          </a>
        </div>

        {/* Location Bar */}
        {locationLabel && (
          <div
            className={`${locationLabel.bg} border ${locationLabel.border} rounded-2xl p-3.5 mb-4 flex flex-wrap items-center justify-between gap-3`}
          >
            <div className="flex items-center gap-2">
              <span className="text-base">{locationLabel.icon}</span>
              <span
                className={`text-sm font-semibold ${locationLabel.color}`}
              >
                {locationLabel.text}
              </span>
            </div>
            <button
              onClick={() => {
                setShowOverride(!showOverride);
                if (location) setOverrideState(location.state);
              }}
              className="text-xs font-semibold text-[#6B7280] hover:text-[#16A34A] transition-colors flex items-center gap-1"
              id="btn-change-location"
            >
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
              >
                <path d="M17 3a2.85 2.85 0 114 4L7.5 20.5 2 22l1.5-5.5z" />
              </svg>
              Change Location
            </button>
            {locationFallbackReason && (
              <p className="basis-full flex items-start gap-1.5 text-xs font-medium text-[#92400E] leading-relaxed">
                <span aria-hidden>⚠️</span>
                <span>{locationFallbackReason}</span>
              </p>
            )}
          </div>
        )}

        {/* Location Override Dropdown */}
        {showOverride && (
          <div className="bg-white border border-[#E5EBE5] rounded-2xl p-4 mb-4 shadow-xs flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[200px]">
              <label
                className="block text-xs font-bold text-[#374151] mb-1"
                htmlFor="override-state"
              >
                Select State
              </label>
              <select
                id="override-state"
                className="w-full bg-white border border-[#D1D5DB] rounded-xl px-3 py-2 text-sm font-medium text-[#111827] focus:outline-none focus:border-[#16A34A] focus:ring-2 focus:ring-[#16A34A]/20 cursor-pointer"
                value={overrideState}
                onChange={(e) => setOverrideState(e.target.value)}
              >
                <option value="">Select state...</option>
                {INDIAN_STATES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={handleOverrideSubmit}
              disabled={!overrideState}
              className="px-5 py-2 rounded-xl bg-[#16A34A] hover:bg-[#15803D] text-white text-xs font-bold transition-all disabled:opacity-50"
              id="btn-apply-override"
            >
              Update Results
            </button>
            <button
              onClick={() => setShowOverride(false)}
              className="px-4 py-2 rounded-xl border border-[#D1D5DB] text-xs font-semibold text-[#6B7280] hover:bg-[#F3F4F6] transition-all"
            >
              Cancel
            </button>
          </div>
        )}

        {/* 4-Step Pipeline Summary Pill */}
        {result?.pipeline_summary && (
          <div className="bg-white border border-[#E5EBE5] rounded-2xl p-4 mb-6 shadow-xs flex flex-wrap items-center gap-3 text-xs">
            <span className="font-bold text-[#111827] flex items-center gap-1.5">
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#16A34A"
                strokeWidth="2.5"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Verified Pipeline:
            </span>
            <span className="bg-[#F0FDF4] text-[#16A34A] px-2.5 py-1 rounded-lg font-medium">
              1. Capability Filter:{" "}
              {((
                result.pipeline_summary as Record<
                  string,
                  Record<string, unknown>
                >
              )?.step1_capability?.output as number) ?? 0}
            </span>
            <span className="text-[#D1D5DB]">→</span>
            <span className="bg-[#F0FDF4] text-[#16A34A] px-2.5 py-1 rounded-lg font-medium">
              2. State Eligibility:{" "}
              {((
                result.pipeline_summary as Record<
                  string,
                  Record<string, unknown>
                >
              )?.step2_eligibility?.output as number) ?? 0}
            </span>
            <span className="text-[#D1D5DB]">→</span>
            <span className="bg-[#F0FDF4] text-[#16A34A] px-2.5 py-1 rounded-lg font-medium">
              3. Health Prioritization:{" "}
              {((
                result.pipeline_summary as Record<
                  string,
                  Record<string, unknown>
                >
              )?.step3_health?.output as number) ?? 0}
            </span>
            <span className="text-[#D1D5DB]">→</span>
            <span className="bg-[#EFF6FF] text-[#1D4ED8] px-2.5 py-1 rounded-lg font-medium">
              4. Location Ranked
            </span>
          </div>
        )}

        {/* 2-Column Split: Partner List + Detail */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left: Interactive Partner List (lg:col-span-7) */}
          <div className="lg:col-span-7 space-y-5">
            {/* Tier 1: District Matches */}
            {tier1Partners.length > 0 && (
              <div>
                <h3 className="text-xs font-bold text-[#16A34A] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <span>📍</span> District Match ({tier1Partners.length})
                </h3>
                <div className="space-y-3">
                  {tier1Partners.map((partner, idx) =>
                    renderPartnerCard(partner, idx, selectedPartner, setSelectedPartner, getPartnerBadge, getTierBadge)
                  )}
                </div>
              </div>
            )}

            {/* Tier 2: State Matches */}
            {tier2Partners.length > 0 && (
              <div>
                <h3 className="text-xs font-bold text-[#1D4ED8] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <span>🏛️</span> Your State — {location?.state} (
                  {tier2Partners.length})
                </h3>
                <div className="space-y-3">
                  {tier2Partners.map((partner, idx) =>
                    renderPartnerCard(partner, idx, selectedPartner, setSelectedPartner, getPartnerBadge, getTierBadge)
                  )}
                </div>
              </div>
            )}

            {/* Tier 3: National */}
            {tier3Partners.length > 0 && (
              <div>
                <h3 className="text-xs font-bold text-[#6B7280] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <span>🌐</span> National — Not Location-Specific (
                  {tier3Partners.length})
                </h3>
                <div className="space-y-3">
                  {tier3Partners.map((partner, idx) =>
                    renderPartnerCard(partner, idx, selectedPartner, setSelectedPartner, getPartnerBadge, getTierBadge)
                  )}
                </div>
              </div>
            )}

            {result?.partners.length === 0 && (
              <div className="bg-white border border-[#E5EBE5] rounded-3xl p-10 text-center shadow-xs">
                <p className="text-base font-bold text-[#111827]">
                  No channel partners found for selected location.
                </p>
                <p className="text-xs text-[#6B7280] mt-1">
                  Try choosing a different state or check national partners.
                </p>
              </div>
            )}
          </div>

          {/* Right: Partner Card & Geographic Map Representation (lg:col-span-5) */}
          <div className="lg:col-span-5 space-y-5">
            {/* Map Representation Box */}
            <div className="bg-white border border-[#E5EBE5] rounded-3xl p-6 shadow-xs relative overflow-hidden">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-bold text-[#0F1F0F]">
                  Geographic Representation
                </h4>
                {result?.proximity_status === "tier_ranking" ? (
                  <span className="text-[11px] font-semibold text-[#16A34A] bg-[#DCFCE7] px-2.5 py-0.5 rounded-full">
                    ✓ Location Ranked
                  </span>
                ) : (
                  <span className="text-[11px] font-semibold text-[#92400E] bg-[#FEF3C7] px-2.5 py-0.5 rounded-full">
                    ⏳ Proximity: Pending
                  </span>
                )}
              </div>

              {/* Map Canvas Graphic */}
              <div className="w-full h-48 rounded-2xl bg-gradient-to-br from-[#ECFDF5] via-[#EFF6FF] to-[#F8FAF8] border border-[#D1E8D4] flex flex-col items-center justify-center p-4 text-center relative">
                <div className="w-12 h-12 rounded-full bg-white shadow-md flex items-center justify-center text-[#16A34A] mb-2 animate-bounce">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                  </svg>
                </div>
                <span className="text-xs font-bold text-[#0F1F0F]">
                  {selectedPartner
                    ? selectedPartner.partner_name
                    : "Select a partner"}
                </span>
                <span className="text-[11px] text-[#6B7280] mt-0.5">
                  {selectedPartner?.location_label ||
                    (selectedPartner?.state
                      ? `State: ${selectedPartner.state}`
                      : "National Coverage")}
                </span>
                {selectedPartner?.rank_tier && (
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full mt-1.5 ${
                      getTierBadge(selectedPartner.rank_tier).bg
                    } ${getTierBadge(selectedPartner.rank_tier).text}`}
                  >
                    {getTierBadge(selectedPartner.rank_tier).label}
                  </span>
                )}
              </div>

              {/* Proximity / Geocoding Notice */}
              <div className="mt-4 p-3 rounded-xl bg-[#F0FDF4] border border-[#BBF7D0] text-xs text-[#047857]">
                <p className="font-semibold">Proximity Notice:</p>
                <p className="text-[11px] text-[#4B5563] mt-0.5">
                  NBFC-MFIs are referenced via registered corporate offices.
                  SCAs and RRBs operate within their designated state. PSBs have
                  nationwide branch networks.
                </p>
              </div>
            </div>

            {/* Quick Next Step Guide */}
            <div className="bg-[#F0FDF4] border border-[#BBF7D0] rounded-3xl p-6 shadow-xs">
              <h4 className="text-sm font-bold text-[#0F1F0F] mb-2">
                How to Apply with this Partner
              </h4>
              <ol className="text-xs text-[#4B5563] space-y-2 list-decimal list-inside leading-relaxed">
                <li>
                  Note the partner agency name and scheme:{" "}
                  <strong>{scheme?.scheme_name}</strong>
                </li>
                <li>
                  Submit your application on the <strong>PM-SURAJ</strong>{" "}
                  portal selecting this channel agency.
                </li>
                <li>
                  Visit the nearest branch with Caste Certificate, Aadhaar, and
                  Project Report.
                </li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Partner Card Renderer ──────────────────────────────────────────────────

function renderPartnerCard(
  partner: Partner,
  idx: number,
  selectedPartner: Partner | null,
  setSelectedPartner: (p: Partner) => void,
  getPartnerBadge: (type: string) => { bg: string; text: string; label: string },
  getTierBadge: (tier?: number) => { bg: string; text: string; icon: string; label: string }
) {
  const badge = getPartnerBadge(partner.partner_type);
  const tierBadge = getTierBadge(partner.rank_tier);
  const isSelected =
    selectedPartner?.partner_id === partner.partner_id;

  return (
    <div
      key={`${partner.partner_id}-${idx}`}
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
            <span
              className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider ${badge.bg} ${badge.text}`}
            >
              {badge.label}
            </span>
            {partner.rank_tier && partner.rank_tier <= 2 && (
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${tierBadge.bg} ${tierBadge.text}`}
              >
                {tierBadge.icon} {tierBadge.label}
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
            {partner.pincode && <span>PIN: {partner.pincode}</span>}
            {partner.contact && <span>📞 {partner.contact}</span>}
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
            <span
              className={`text-[11px] font-bold px-2.5 py-1 rounded-xl block ${
                partner.health.is_healthy
                  ? "bg-[#DCFCE7] text-[#16A34A]"
                  : "bg-[#FEF3C7] text-[#92400E]"
              }`}
            >
              {partner.health.is_healthy ? "✓ Operational" : "Deprioritized"}
            </span>
            <span className="text-[10px] text-[#9CA3AF] mt-1 block">
              NPA: {partner.health.npa_ratio}%{" "}
              <span className="text-[#D1D5DB]">(sim.)</span>
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
