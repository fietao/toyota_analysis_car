/* bevWatchlist.ts — types + pure parsing for frontend/public/data/new_bev_candidates.json.
 * Written by backend/bev_candidates.py after every monthly update. Candidate-only: this
 * data never reflects an approval decision — review_status is always "pending" here. */

export type BevCandidateConfidence = "high" | "medium";
export type BevCandidateReasonCode =
  | "approved_family_match"
  | "approved_model_match"
  | "electric_name_marker";

export type BevCandidate = {
  brand: string;
  raw_model: string;
  model: string;
  units: number;
  confidence: BevCandidateConfidence;
  reason_code: BevCandidateReasonCode;
  reason: string;
  review_status: string;
};

export type BevWatchlistPayload = {
  meta: {
    year: number;
    month: number;
    generated_at: string;
    candidate_count: number;
    total_units: number;
  };
  candidates: BevCandidate[];
};

export type BevWatchlistState =
  | { kind: "unavailable" }
  | { kind: "empty"; year: number; month: number }
  | { kind: "candidates"; year: number; month: number; totalUnits: number; candidates: BevCandidate[] };

const REASON_CODES = new Set<string>(["approved_family_match", "approved_model_match", "electric_name_marker"]);
const CONFIDENCES = new Set<string>(["high", "medium"]);

function isValidCandidate(c: unknown): c is BevCandidate {
  if (!c || typeof c !== "object") return false;
  const r = c as Record<string, unknown>;
  return (
    typeof r.brand === "string" &&
    typeof r.raw_model === "string" &&
    typeof r.model === "string" &&
    typeof r.units === "number" &&
    typeof r.confidence === "string" && CONFIDENCES.has(r.confidence) &&
    typeof r.reason_code === "string" && REASON_CODES.has(r.reason_code) &&
    typeof r.reason === "string" &&
    typeof r.review_status === "string"
  );
}

// Parses + shape-validates the raw fetch payload. A well-formed-but-wrong-shape JSON
// (or a network/parse failure the caller catches before calling this) must read the same
// as a missing file: "Watchlist unavailable", never a crash.
export function parseBevWatchlist(data: unknown): BevWatchlistState {
  if (!data || typeof data !== "object") return { kind: "unavailable" };
  const d = data as Record<string, unknown>;
  const meta = d.meta as Record<string, unknown> | undefined;
  if (
    !meta ||
    typeof meta.year !== "number" ||
    typeof meta.month !== "number" ||
    typeof meta.candidate_count !== "number" ||
    typeof meta.total_units !== "number"
  ) {
    return { kind: "unavailable" };
  }
  const candidates = d.candidates;
  if (!Array.isArray(candidates) || !candidates.every(isValidCandidate)) {
    return { kind: "unavailable" };
  }
  if (candidates.length === 0) {
    return { kind: "empty", year: meta.year, month: meta.month };
  }
  return {
    kind: "candidates",
    year: meta.year,
    month: meta.month,
    totalUnits: meta.total_units,
    candidates,
  };
}

export function bevWatchlistMessage(candidateCount: number): string {
  return `${candidateCount} possible new BEV models need checking. Published data remains safe.`;
}

const CSV_HEADER = ["brand", "raw_model", "model", "units", "confidence", "reason_code", "reason", "review_status"];

function csvEscape(value: string | number): string {
  const s = String(value);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

// Client-side CSV export (Blob) — new_bev_candidates.csv lives under backend/output/,
// which the frontend never serves, so the download button builds its own CSV from the
// already-fetched JSON rather than linking to a backend path.
export function candidatesToCsv(candidates: BevCandidate[]): string {
  const lines = [CSV_HEADER.join(",")];
  for (const c of candidates) {
    lines.push(CSV_HEADER.map((key) => csvEscape((c as unknown as Record<string, string | number>)[key])).join(","));
  }
  return lines.join("\n");
}
