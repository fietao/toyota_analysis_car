// Market-scope registry (dashboard research report: "Market-Scope Safety").
// The homepage denominator must be an explicit, named set of vehicle-type codes —
// never the empty-selection "All" convention used elsewhere, since an empty array
// is indistinguishable from an uninitialized/loading state (see bug trap notes).

export type MarketProfileId = "formal_report" | "all_dlt" | "custom";

// The seven รย. codes DLT's formal published report covers. Fixed by regulatory
// definition, not derived from whatever happens to be in this month's data.
export const FORMAL_REPORT_CODES = ["รย.1", "รย.2", "รย.3", "รย.6", "รย.9", "รย.10", "รย.11"];

export const MARKET_PROFILE_LABELS: Record<MarketProfileId, string> = {
  formal_report: "Formal report scope",
  all_dlt: "All DLT vehicle types",
  custom: "Custom selection",
};

function setsEqual(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false;
  const bSet = new Set(b);
  return a.every((x) => bSet.has(x));
}

// Codes a named profile resolves to, given the codes actually present in this
// month's data (so `all_dlt` always tracks reality, never a hardcoded count).
export function resolveProfileCodes(id: "formal_report" | "all_dlt", allCodes: string[]): string[] {
  if (id === "all_dlt") return [...allCodes];
  const available = new Set(allCodes);
  return FORMAL_REPORT_CODES.filter((c) => available.has(c));
}

// The global filter's "All" action reports [] (this module's own convention above
// notwithstanding — that's the popover's, not ours). Never let it through as-is:
// an empty selectedVehicleTypes would make the header and the denominator disagree.
export function resolveVehicleTypeSelection(selected: string[], allCodes: string[]): string[] {
  return selected.length > 0 ? selected : allCodes;
}

// Formal report codes absent from this month's metadata — a data-contract violation,
// not something to silently paper over by activating whatever subset does exist.
export function missingFormalReportCodes(allCodes: string[]): string[] {
  const available = new Set(allCodes);
  return FORMAL_REPORT_CODES.filter((c) => !available.has(c));
}

// Identifies which named profile the current selection matches, by set equality
// (order-independent). Falls back to "custom" for any other selection.
export function identifyMarketProfile(selectedCodes: string[], allCodes: string[]): { id: MarketProfileId; label: string } {
  if (setsEqual(selectedCodes, resolveProfileCodes("formal_report", allCodes))) {
    return { id: "formal_report", label: MARKET_PROFILE_LABELS.formal_report };
  }
  if (allCodes.length > 0 && setsEqual(selectedCodes, resolveProfileCodes("all_dlt", allCodes))) {
    return { id: "all_dlt", label: MARKET_PROFILE_LABELS.all_dlt };
  }
  return { id: "custom", label: MARKET_PROFILE_LABELS.custom };
}
