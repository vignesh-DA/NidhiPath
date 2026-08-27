"use client";

import { useState } from "react";
import Link from "next/link";
import { askQuestion, ApiError } from "@/lib/apiClient";
import type { QAResult } from "@/lib/types";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  source?: string;
  verified?: boolean;
  intent?: "structured" | "narrative";
}

export default function QAPage() {
  const [inputMessage, setInputMessage] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "assistant",
      text: "Namaste! I am the NidhiPath AI Assistant. You can ask me questions about NSFDC schemes, required documents, interest rates, or eligibility criteria. How can I assist you today?",
      source: "Grounded in scheme records",
      verified: true,
    },
  ]);

  const sampleQuestions = [
    "What documents do I need for a Term Loan?",
    "What is the maximum income limit to be eligible?",
    "How does the 3-month moratorium period work?",
    "What is the interest rate for women beneficiaries?",
  ];

  // Calls the real backend RAG Q&A endpoint (POST /api/v1/qa).
  // Structured questions are answered from scheme records with zero LLM calls;
  // narrative questions use retrieval + generation. Never a mock response.
  const handleSend = async (text: string) => {
    if (!text.trim() || isThinking) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: text,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage("");
    setIsThinking(true);

    try {
      const res: QAResult = await askQuestion(text.trim());

      const sourceLabel =
        res.sources && res.sources.length > 0
          ? `${res.sources[0].scheme_name} — ${res.sources[0].section}`
          : res.scheme_name
            ? `${res.scheme_name} (scheme record)`
            : res.used_llm
              ? "RAG retrieval + LLM generation"
              : "Scheme records (structured lookup)";

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: res.answer,
        source: sourceLabel,
        verified: true,
        intent: res.intent,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: unknown) {
      const detail =
        err instanceof ApiError
          ? err.detail
          : "Could not reach the NidhiPath API. Is the backend running on port 8000?";

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: `Sorry, I could not answer that. ${detail}`,
        verified: false,
      };

      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <div className="w-full bg-[#F8FAF8] min-h-[calc(100vh-80px)] py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        
        {/* Navigation & Header */}
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#6B7280] hover:text-[#16A34A] transition-colors mb-3"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            <span>Back to Home</span>
          </Link>

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0F1F0F] tracking-tight">
                Scheme AI Assistant
              </h1>
              <p className="text-sm text-[#6B7280] mt-0.5">
                Module 4 — Verified scheme facts grounded in official MoSJE/NSFDC documentation.
              </p>
            </div>

            <span className="inline-flex items-center gap-1.5 text-xs font-bold text-[#16A34A] bg-[#DCFCE7] px-3 py-1.5 rounded-full self-start sm:self-auto shadow-xs">
              <span className="w-2 h-2 rounded-full bg-[#16A34A] animate-pulse" />
              RAG Fact-Grounded
            </span>
          </div>
        </div>

        {/* Conversational Container */}
        <div className="bg-white border border-[#E5EBE5] rounded-3xl shadow-sm overflow-hidden flex flex-col h-[580px]">
          
          {/* Chat Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-4">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 ${m.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                {m.sender === "assistant" && (
                  <div className="w-9 h-9 rounded-xl bg-[#DCFCE7] text-[#16A34A] flex items-center justify-center shrink-0 mt-0.5">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 2L2 7l10 5 10-5-10-5z" />
                      <path d="M2 17l10 5 10-5" />
                      <path d="M2 12l10 5 10-5" />
                    </svg>
                  </div>
                )}

                <div className={`max-w-xl rounded-2xl p-4 text-sm leading-relaxed ${
                  m.sender === "user"
                    ? "bg-[#16A34A] text-white rounded-br-none"
                    : "bg-[#F8FAF8] border border-[#E5EBE5] text-[#111827] rounded-bl-none shadow-xs"
                }`}>
                  <p>{m.text}</p>
                  
                  {m.source && (
                    <div className="mt-2.5 pt-2 border-t border-[#E5EBE5] flex items-center gap-1.5 text-[11px] text-[#047857] font-semibold">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      <span>Source: {m.source}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Suggested Questions Pills */}
          <div className="px-5 py-3 bg-[#F8FAF8] border-t border-[#E5EBE5] flex items-center gap-2 overflow-x-auto">
            <span className="text-[11px] font-bold text-[#6B7280] shrink-0">Suggested:</span>
            {sampleQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                className="text-xs bg-white hover:bg-[#F0FDF4] border border-[#D1D5DB] hover:border-[#86EFAC] text-[#374151] px-3 py-1 rounded-full whitespace-nowrap transition-colors"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Input Bar */}
          <div className="p-4 bg-white border-t border-[#E5EBE5]">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend(inputMessage);
              }}
              className="flex items-center gap-3"
            >
              <input
                type="text"
                placeholder="Ask any question about NSFDC schemes, documents, or subsidies..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                className="flex-1 bg-[#F9FAFB] border border-[#D1D5DB] rounded-xl px-4 py-3 text-sm text-[#111827] placeholder:text-[#9CA3AF] focus:outline-none focus:border-[#16A34A] focus:ring-2 focus:ring-[#16A34A]/20"
              />
              <button
                type="submit"
                disabled={isThinking}
                className="px-5 py-3 rounded-xl bg-[#16A34A] hover:bg-[#15803D] text-white text-sm font-bold shadow-xs hover:shadow-sm transition-all flex items-center gap-1.5 shrink-0 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <span>{isThinking ? "Thinking…" : "Ask"}</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            </form>
          </div>

        </div>

      </div>
    </div>
  );
}
