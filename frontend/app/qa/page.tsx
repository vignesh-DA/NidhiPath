"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function QAPage() {
  const router = useRouter();
  const [message, setMessage] = useState("");

  return (
    <div className="page-container pt-8 pb-16 max-w-2xl mx-auto">
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

        <h1 className="section-title">Ask about your scheme</h1>
        <p className="section-subtitle">
          Module 4 — AI-powered Q&amp;A scoped to your matched scheme.
        </p>
      </div>

      {/* Coming Soon Card */}
      <div className="glass-card p-8 text-center animate-slide-up">
        <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[#3B82F6]/20 to-[#3B82F6]/5 flex items-center justify-center">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
            <circle cx="12" cy="10" r="1" fill="#3B82F6" />
            <circle cx="8" cy="10" r="1" fill="#3B82F6" />
            <circle cx="16" cy="10" r="1" fill="#3B82F6" />
          </svg>
        </div>

        <h2 className="text-xl font-semibold text-[var(--color-foreground)] mb-3">
          Q&amp;A Coming Soon
        </h2>
        <p className="text-sm text-[var(--color-text-secondary)] max-w-md mx-auto mb-8 leading-relaxed">
          Ask natural language questions about your matched scheme — like
          &ldquo;What documents do I need?&rdquo; or &ldquo;Why don&apos;t I qualify for this one?&rdquo;
          Answers come from the scheme&apos;s own documentation, never hallucinated.
        </p>

        {/* Preview input */}
        <div className="max-w-md mx-auto">
          <div className="relative">
            <input
              type="text"
              className="input-field pr-12 opacity-60"
              placeholder="Ask a question about your scheme..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              disabled
            />
            <button
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg bg-[var(--color-surface-3)] flex items-center justify-center opacity-40 cursor-not-allowed"
              disabled
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-2 justify-center">
          {["What documents do I need?", "Explain the interest rate", "Am I eligible?"].map((q) => (
            <span key={q} className="text-xs bg-[var(--color-surface-3)] text-[var(--color-text-muted)] px-3 py-1.5 rounded-full">
              {q}
            </span>
          ))}
        </div>
      </div>

      {/* Architecture note */}
      <div className="mt-8 bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-lg p-4 text-xs text-[var(--color-text-muted)]">
        <p className="font-medium text-[var(--color-text-secondary)] mb-2">How Q&amp;A works (when built)</p>
        <ul className="space-y-1">
          <li>• <strong>Structured questions</strong> (interest rate, max loan) → answered directly from database, zero LLM calls</li>
          <li>• <strong>Narrative questions</strong> (why don&apos;t I qualify) → RAG retrieval from scheme chunks + LLM generation</li>
          <li>• Session-scoped to your matched scheme — no cross-contamination</li>
          <li>• Answers generated directly in your selected language (no translate-from-English step)</li>
        </ul>
      </div>
    </div>
  );
}
