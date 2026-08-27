"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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
  const [casteScope, setCasteScope] = useState<string[]>(["SC"]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cost = parseFloat(estimatedCost);
    const income = parseFloat(incomeLevel);

    if (isNaN(cost) || cost <= 0) {
      setError("Please enter a valid estimated cost.");
      return;
    }
    if (isNaN(income) || income < 0) {
      setError("Please enter a valid annual income.");
      return;
    }
    if (projectType === "education" && !educationStatus) {
      setError("Please select your education status.");
      return;
    }

    // Store intake in sessionStorage and navigate to recommendation
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

  return (
    <div className="page-container pt-8 pb-16 max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-8 animate-fade-in">
        <button
          onClick={() => router.push("/")}
          className="flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors mb-6 cursor-pointer"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Back
        </button>
        <h1 className="section-title">Tell us about your project</h1>
        <p className="section-subtitle">
          Answer 4 questions to find matching NSFDC credit schemes instantly.
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6 animate-slide-up" style={{ animationDelay: "0.1s" }}>

        {/* Project Type */}
        <div>
          <label className="label" htmlFor="project-type">What is your project purpose?</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => { setProjectType("business_self_employment"); setEducationStatus(""); }}
              className={`glass-card p-4 text-left cursor-pointer transition-all ${
                projectType === "business_self_employment"
                  ? "border-[var(--color-accent)] glow-border"
                  : ""
              }`}
              id="type-business"
            >
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  projectType === "business_self_employment"
                    ? "bg-[var(--color-accent)]/20"
                    : "bg-[var(--color-surface-3)]"
                }`}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={projectType === "business_self_employment" ? "#22C55E" : "#94A3B8"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                    <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-[var(--color-foreground)]">Business / Self Employment</p>
                  <p className="text-xs text-[var(--color-text-muted)]">Start or grow your enterprise</p>
                </div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setProjectType("education")}
              className={`glass-card p-4 text-left cursor-pointer transition-all ${
                projectType === "education"
                  ? "border-[var(--color-accent)] glow-border"
                  : ""
              }`}
              id="type-education"
            >
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  projectType === "education"
                    ? "bg-[var(--color-accent)]/20"
                    : "bg-[var(--color-surface-3)]"
                }`}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={projectType === "education" ? "#22C55E" : "#94A3B8"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
                    <path d="M6 12v5c0 1.1.9 2 2 2h8a2 2 0 002-2v-5" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-[var(--color-foreground)]">Education</p>
                  <p className="text-xs text-[var(--color-text-muted)]">Fund your studies</p>
                </div>
              </div>
            </button>
          </div>
        </div>

        {/* Education Status (conditional) */}
        {projectType === "education" && (
          <div className="animate-fade-in">
            <label className="label" htmlFor="education-status">Education status</label>
            <select
              id="education-status"
              className="input-field cursor-pointer"
              value={educationStatus}
              onChange={(e) => setEducationStatus(e.target.value as EducationStatus)}
              required
            >
              <option value="">Select status...</option>
              <option value="admission_secured">Admission Secured</option>
              <option value="currently_enrolled">Currently Enrolled</option>
            </select>
          </div>
        )}

        {/* Estimated Cost */}
        <div>
          <label className="label" htmlFor="estimated-cost">
            Estimated {projectType === "education" ? "education" : "project"} cost (₹)
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] text-sm">₹</span>
            <input
              type="number"
              id="estimated-cost"
              className="input-field pl-7"
              placeholder="e.g., 100000"
              value={estimatedCost}
              onChange={(e) => setEstimatedCost(e.target.value)}
              required
              min="1"
            />
          </div>
          <p className="text-xs text-[var(--color-text-muted)] mt-1.5">
            NSFDC schemes cover projects from ₹0 to ₹50,00,000
          </p>
        </div>

        {/* Annual Family Income */}
        <div>
          <label className="label" htmlFor="income-level">Annual family income (₹)</label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] text-sm">₹</span>
            <input
              type="number"
              id="income-level"
              className="input-field pl-7"
              placeholder="e.g., 250000"
              value={incomeLevel}
              onChange={(e) => setIncomeLevel(e.target.value)}
              required
              min="0"
            />
          </div>
          <p className="text-xs text-[var(--color-text-muted)] mt-1.5">
            Eligibility cap: ₹5,00,000 per annum
          </p>
        </div>

        {/* State */}
        <div>
          <label className="label" htmlFor="user-state">Your state (for welfare schemes &amp; SCA matching)</label>
          <select
            id="user-state"
            className="input-field cursor-pointer"
            value={userState}
            onChange={(e) => setUserState(e.target.value)}
          >
            <option value="">Select state (optional)...</option>
            {INDIAN_STATES.map((state) => (
              <option key={state} value={state}>{state}</option>
            ))}
          </select>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-[var(--color-destructive)]/10 border border-[var(--color-destructive)]/30 rounded-lg p-3 text-sm text-[var(--color-destructive)] animate-fade-in">
            {error}
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          className="btn-primary w-full justify-center text-base py-3.5"
          disabled={isSubmitting}
          id="btn-find-schemes"
        >
          {isSubmitting ? (
            <>
              <svg className="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" strokeDasharray="60" strokeDashoffset="15" />
              </svg>
              Finding schemes...
            </>
          ) : (
            <>
              Find matching schemes
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
