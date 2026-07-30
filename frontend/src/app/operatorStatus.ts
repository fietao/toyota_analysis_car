/* operatorStatus.ts — types + pure interpretation for frontend/public/data/operator_status.json.
 * Written by backend/monthly_update.py after every run (success, review-needed, or failure). */

export type OperatorStatusValue = "ok" | "review_needed" | "failed";

export type OperatorStatus = {
  status: OperatorStatusValue;
  reporting_period: string | null;
  generated_at: string;
  last_run_at: string;
  model_row_count: number | null;
  fuel_row_count: number | null;
  model_total_units: number | null;
  fuel_total_units: number | null;
  totals_match: boolean;
  pending_review_count: number;
  published_files: { file: string; updated_this_run: boolean }[];
  next_action: string;
  safe_live_data: boolean;
};

export type HealthTone = "green" | "yellow" | "red";

// A mismatched model/fuel unit total is a real anomaly the release gate does not
// itself assert on, so it must downgrade an otherwise-"ok" run to yellow rather than
// showing a silent green light.
export function healthTone(status: OperatorStatusValue, totalsMatch: boolean): HealthTone {
  if (status === "failed") return "red";
  if (status === "review_needed" || !totalsMatch) return "yellow";
  return "green";
}

export function healthLabel(status: OperatorStatusValue): string {
  if (status === "ok") return "Live data OK";
  if (status === "review_needed") return "Review needed";
  return "Update failed";
}
