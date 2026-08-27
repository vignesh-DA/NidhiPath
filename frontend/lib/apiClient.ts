/**
 * NidhiPath — API Client
 *
 * Typed fetch wrappers for each backend module.
 * Mirrors backend/app/api/ routes.
 */

import type {
  RecommendRequest,
  RecommendResponse,
  EmiRequest,
  EmiResponse,
  LocateRequest,
  LocateResponse,
  IntakeExtractResult,
  QAResult,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ─── Generic Fetch Wrapper ──────────────────────────────────────────────────

class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API Error ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

async function apiPost<TReq, TRes>(endpoint: string, body: TReq): Promise<TRes> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, errorBody.detail || response.statusText);
  }

  return response.json() as Promise<TRes>;
}

async function apiGet<TRes>(endpoint: string): Promise<TRes> {
  const response = await fetch(`${API_BASE}${endpoint}`);

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, errorBody.detail || response.statusText);
  }

  return response.json() as Promise<TRes>;
}

// ─── Module 1: Scheme Recommender ───────────────────────────────────────────

export async function recommendSchemes(input: RecommendRequest): Promise<RecommendResponse> {
  return apiPost<RecommendRequest, RecommendResponse>("/recommend", input);
}

// ─── Module 2: Financial Calculator ─────────────────────────────────────────

export async function calculateEmi(input: EmiRequest): Promise<EmiResponse> {
  return apiPost<EmiRequest, EmiResponse>("/calculate-emi", input);
}

// ─── Module 3: Partner Locator ──────────────────────────────────────────────

export async function locatePartners(input: LocateRequest): Promise<LocateResponse> {
  return apiPost<LocateRequest, LocateResponse>("/locate-partners", input);
}

// ─── Module 4: LLM Intake + RAG Q&A ─────────────────────────────────────────

export async function extractIntake(text: string): Promise<IntakeExtractResult> {
  return apiPost<{ text: string }, IntakeExtractResult>("/intake/extract", { text });
}

export async function askQuestion(
  question: string,
  schemeId?: string,
  language: string = "en",
): Promise<QAResult> {
  return apiPost("/qa", { question, scheme_id: schemeId, language });
}

// ─── Health Check ───────────────────────────────────────────────────────────
// NOTE: /health is defined at the API ROOT (http://localhost:8000/health),
// NOT under the /api/v1 prefix — so we strip the prefix before calling.

const API_ROOT = API_BASE.replace(/\/api\/v1\/?$/, "");

export async function healthCheck(): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_ROOT}/health`);
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, errorBody.detail || response.statusText);
  }
  return response.json() as Promise<Record<string, unknown>>;
}

export { ApiError };
