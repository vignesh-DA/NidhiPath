/**
 * NidhiPath — Shared TypeScript Types
 *
 * Mirrors the backend Pydantic schemas for type safety across the stack.
 * Keep in sync with backend/app/modules/ and backend/app/api/ schemas.
 */

// ─── Enums ──────────────────────────────────────────────────────────────────

export type ProjectType = "business_self_employment" | "education";
export type EducationStatus = "admission_secured" | "currently_enrolled";
export type Language = "en" | "hi" | "ta" | "te" | "kn" | "mr";

// ─── Module 1: Scheme Recommender ───────────────────────────────────────────

export interface RecommendRequest {
  estimated_cost: number;
  income_level: number;
  project_type: ProjectType;
  education_status?: EducationStatus;
  user_state?: string;
  caste_scope?: string[];
}

export interface MatchedScheme {
  scheme_id: string;
  scheme_name: string;
  purpose: string;
  match_reason: string;
  interest_rate_beneficiary: number;
  interest_rate_sca?: number;
  max_loan_amount?: number;
  project_cost_min: number;
  project_cost_max: number;
  project_cost_coverage_pct: number;
  tenure_years?: number;
  moratorium_months?: number;
  channel_partners: string[];
  max_annual_income: number;
  raw: Record<string, unknown>;
}

export interface SchemeSummary {
  scheme_id: string;
  scheme_name: string;
  interest_rate_beneficiary: number;
  max_loan_amount?: number;
  match_reason: string;
}

export interface CreditRecommendationResult {
  top_pick: MatchedScheme | null;
  alternatives: SchemeSummary[];
  total_matches: number;
  input_summary: Record<string, unknown>;
}

export interface WelfareSchemeMatch {
  scheme_id: string;
  scheme_name: string;
  issuing_state: string;
  benefits: string;
  eligibility_summary: string;
  match_confidence: string;
  match_reasons: string[];
}

export interface WelfareRecommendationResult {
  matches: WelfareSchemeMatch[];
  total_matches: number;
  disclaimer: string;
}

export interface RecommendResponse {
  primary: CreditRecommendationResult;
  secondary: WelfareRecommendationResult;
  meta: Record<string, string>;
}

// ─── Module 2: Financial Calculator ─────────────────────────────────────────

export interface EmiRequest {
  scheme_id: string;
  requested_amount: number;
  requested_months: number;
  interest_rate_pct: number;
  max_loan_amount?: number;
  project_cost: number;
  project_cost_coverage_pct: number;
  tenure_years?: number;
  moratorium_months?: number;
  include_schedule?: boolean;
}

export interface ScheduleEntry {
  month: number;
  type: "moratorium" | "repayment";
  emi: number;
  principal: number;
  interest: number;
  balance: number;
}

export interface EmiBreakdown {
  scheme_id: string;
  effective_loan_amount: number;
  effective_tenure_months: number;
  effective_interest_rate_annual: number;
  effective_interest_rate_monthly: number;
  emi_amount: number;
  total_payment: number;
  total_interest: number;
  moratorium_months: number;
  first_emi_month: number;
  total_duration_months: number;
  caps_applied: string[];
  assumption_note: string;
  schedule: ScheduleEntry[];
}

// ─── Module 3: Partner Locator ──────────────────────────────────────────────

export interface LocateRequest {
  scheme_channel_partners: string[];
  user_state?: string;
  user_lat?: number;
  user_lon?: number;
}

export interface PartnerHealth {
  npa_ratio: number;
  utilization_pct: number;
  is_healthy: boolean;
  note: string;
  deprioritized_reason?: string[];
}

export interface Partner {
  partner_id: string;
  partner_name: string;
  partner_type: string;
  state: string;
  contact?: string;
  address?: string;
  address_raw?: string;
  pincode?: string;
  health?: PartnerHealth;
}

export interface LocateResponse {
  partners: Partner[];
  pipeline_summary: Record<string, unknown>;
  proximity_status: string;
  proximity_note: string;
  known_gaps: string[];
  total_results: number;
}

// ─── App State ──────────────────────────────────────────────────────────────

export interface UserIntake {
  estimated_cost: number;
  income_level: number;
  project_type: ProjectType;
  education_status?: EducationStatus;
  user_state?: string;
  caste_scope?: string[];
}

export interface AppState {
  language: Language;
  intake: UserIntake | null;
  recommendation: RecommendResponse | null;
  selectedScheme: MatchedScheme | null;
  emiResult: EmiBreakdown | null;
  locatorResult: LocateResponse | null;
}

// ─── Indian States ──────────────────────────────────────────────────────────

export const INDIAN_STATES = [
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
  "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
  "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
  "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
  "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
  "Uttar Pradesh", "Uttarakhand", "West Bengal",
  "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
  "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
] as const;
