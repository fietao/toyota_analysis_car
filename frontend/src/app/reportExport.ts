// Shared between the report table renderer and the Excel export: one definition of the
// manual-report shape and sheet list, and the row builder used to turn a sheet's rows
// into worksheet-ready objects (XLSX.utils.json_to_sheet consumes Record<string, ...>[]).

export type ReportRow = {
  key: string;
  label: string;
  prev_months: (number | null)[];
  prev_total: number | null;
  prev_ytd: number | null;
  prev_total_share: number | null;
  prev_month_units?: number | null;
  prev_month_share?: number | null;
  prev_ytd_share: number | null;
  curr_months: number[];
  curr_month_units?: number | null;
  curr_month_share?: number | null;
  curr_month_diff?: number | null;
  curr_ytd: number;
  curr_ytd_share: number | null;
  curr_ytd_diff?: number | null;
  growth_vs_prev_month: number | null;
  growth_vs_same_month_prev_year: number | null;
  growth_vs_prev_ytd: number | null;
  prev_rank?: number | null;
  curr_rank?: number | null;
  rank_diff?: number | null;
  level?: "grand" | "brand" | "model" | "province";
  group?: string;
  brand?: string;
  model?: string;
  overall?: number | null;
};

// Sheets 1-6/9 are fuel-derived and carry `powertrain`; sheets 7-8 are model-grain and
// carry `model_report_filter` instead (model rows never get a Powertrain label — see
// CLAUDE.md data contract). A section has exactly one of the two, never both.
export type SectionMeta = {
  title: string;
  source: string;
  filter: string;
  powertrain?: string;
  model_report_filter?: string;
};

export type ManualReportMeta = {
  reporting_period: string;
  latest_year: number;
  latest_month: string;
  latest_month_num: number;
  prev_year: number;
  has_prev_year?: boolean;
  months: string[];
  default_vehicle_types: string[];
  source_files: { brand_powertrain: string; model: string };
  sections: Record<string, SectionMeta>;
  known_mismatches?: { sheets: string[]; row: string; note: string }[];
  generated_at: string;
};

export type YearReport = { meta: ManualReportMeta; sheets: Record<string, ReportRow[]> };

export type ManualReport = YearReport & {
  reports_by_year?: Record<string, YearReport>;
};

// The latest year's report lives at the top level for backward compatibility; every
// other year lives under reports_by_year. This is the one place that distinction is
// resolved so callers never special-case the latest year.
export function getReportForYear(report: ManualReport, year: number): YearReport {
  if (year === report.meta.latest_year) return { meta: report.meta, sheets: report.sheets };
  const found = report.reports_by_year?.[String(year)];
  return found ?? { meta: report.meta, sheets: report.sheets };
}

export function getReportYears(report: ManualReport): number[] {
  const years = new Set<number>([report.meta.latest_year]);
  Object.keys(report.reports_by_year ?? {}).forEach((y) => years.add(Number(y)));
  return Array.from(years).sort((a, b) => b - a);
}

export type SheetKind = "powertrain" | "brand" | "model_tree" | "model_rank" | "province_tree";

export type SheetDef = { id: string; kind: SheetKind; rowLabel: string };

export const MANUAL_REPORT_SHEETS: SheetDef[] = [
  { id: "sheet1_powertrain", kind: "powertrain", rowLabel: "Powertrain" },
  { id: "sheet2_brand_all", kind: "brand", rowLabel: "Brand" },
  { id: "sheet3_brand_ice", kind: "brand", rowLabel: "Brand" },
  { id: "sheet4_brand_bev", kind: "brand", rowLabel: "Brand" },
  { id: "sheet5_brand_hev", kind: "brand", rowLabel: "Brand" },
  { id: "sheet6_brand_phev", kind: "brand", rowLabel: "Brand" },
  { id: "sheet7_bev_by_model", kind: "model_tree", rowLabel: "Brand / Model" },
  { id: "sheet8_model_top_rank", kind: "model_rank", rowLabel: "Model" },
  { id: "sheet9_by_province", kind: "province_tree", rowLabel: "Province / Brand" },
];

// Matches the table's own num()/pct() convention: null/undefined/NaN/0 all render as
// blank. Kept consistent with the existing Excel exports in this app (models/page.tsx,
// analyst/page.tsx both use `value || ""`), so a downloaded workbook never shows a
// number the screen didn't.
function blank(n: number | null | undefined): number | "" {
  return n === null || n === undefined || Number.isNaN(n) || n === 0 ? "" : n;
}

function pctBlank(n: number | null | undefined): number | "" {
  if (n === null || n === undefined || Number.isNaN(n)) return "";
  const v = Math.round(n * 1000) / 10;
  return v === 0 ? "" : v;
}

export function latestMonthLabels(meta: ManualReportMeta): {
  prevMonth: string;
  currMonth: string;
  prevMonthPeriod: string;
  currMonthPeriod: string;
  prevYtdPeriod: string;
  currYtdPeriod: string;
} {
  const currMonth = meta.months[meta.latest_month_num - 1] ?? meta.latest_month;
  const prevMonth = meta.months[meta.latest_month_num - 2] ?? "";
  const ytdStart = meta.months[0] ?? "Jan";
  return {
    prevMonth,
    currMonth,
    prevMonthPeriod: `${currMonth} ${meta.prev_year}`,
    currMonthPeriod: `${currMonth} ${meta.latest_year}`,
    prevYtdPeriod: `${ytdStart}-${currMonth} ${meta.prev_year}`,
    currYtdPeriod: `${ytdStart}-${currMonth} ${meta.latest_year}`,
  };
}

export function safeSheetName(title: string, used: Set<string>): string {
  const base = title.replace(/[:\\/?*[\]]/g, "-").trim().slice(0, 31) || "Sheet";
  let candidate = base;
  let n = 2;
  while (used.has(candidate)) {
    const suffix = ` (${n})`;
    candidate = `${base.slice(0, 31 - suffix.length)}${suffix}`;
    n += 1;
  }
  used.add(candidate);
  return candidate;
}

// Keys are prefixed "Rank " (not bare years) because JS/JSON hoists integer-like string
// keys ("2568") to the front of the object regardless of insertion order, which would pull
// the Rank columns to the start of the exported row instead of the end where the table has them.
function rankCols(row: ReportRow, meta: ManualReportMeta, out: Record<string, string | number>) {
  out[`Rank ${meta.prev_year}`] = blank(row.prev_rank);
  out[`Rank ${meta.latest_year}`] = blank(row.curr_rank);
  out["Rank Diff"] = blank(row.rank_diff);
}

// Sheet 1: powertrain summary. No Diff columns, no Rank — a powertrain isn't ranked
// against itself and share-diff isn't part of the requested layout.
function powertrainRow(def: SheetDef, row: ReportRow, meta: ManualReportMeta, labels: ReturnType<typeof latestMonthLabels>) {
  const out: Record<string, string | number> = { [def.rowLabel]: row.label };
  out[`Units ${labels.prevYtdPeriod}`] = blank(row.prev_ytd);
  out[`Share ${labels.prevYtdPeriod} %`] = pctBlank(row.prev_ytd_share);
  out[`Units ${meta.prev_year} Total`] = blank(row.prev_total);
  out[`Share ${meta.prev_year} Total %`] = pctBlank(row.prev_total_share);
  out[`Units ${labels.currMonthPeriod}`] = blank(row.curr_month_units ?? row.curr_months[meta.latest_month_num - 1]);
  out[`Share ${labels.currMonthPeriod} %`] = pctBlank(row.curr_month_share);
  out[`Growth vs ${labels.prevMonth} ${meta.latest_year} %`] = pctBlank(row.growth_vs_prev_month);
  out[`Growth vs ${labels.currMonth} ${meta.prev_year} %`] = pctBlank(row.growth_vs_same_month_prev_year);
  out[`Units ${labels.currYtdPeriod} Total`] = blank(row.curr_ytd);
  out[`Share ${labels.currYtdPeriod} Total %`] = pctBlank(row.curr_ytd_share);
  out[`Growth vs ${labels.prevYtdPeriod} %`] = pctBlank(row.growth_vs_prev_ytd);
  return out;
}

// Sheets 2-6: brand + brand-by-powertrain summary. Same shape for all five sheets —
// only the source powertrain filter differs (handled upstream in the backend export).
function brandRow(def: SheetDef, row: ReportRow, meta: ManualReportMeta, labels: ReturnType<typeof latestMonthLabels>) {
  const out: Record<string, string | number> = { [def.rowLabel]: row.label };
  out[`Units ${labels.currMonth} ${meta.prev_year}`] = blank(row.prev_month_units ?? row.prev_months[meta.latest_month_num - 1]);
  out[`Share ${labels.currMonth} ${meta.prev_year} %`] = pctBlank(row.prev_month_share);
  out[`Units ${labels.prevYtdPeriod}`] = blank(row.prev_ytd);
  out[`Share ${labels.prevYtdPeriod} %`] = pctBlank(row.prev_ytd_share);
  out[`Units ${meta.prev_year} Total`] = blank(row.prev_total);
  out[`Share ${meta.prev_year} Total %`] = pctBlank(row.prev_total_share);
  out[`Units ${labels.currMonthPeriod}`] = blank(row.curr_month_units ?? row.curr_months[meta.latest_month_num - 1]);
  out[`Share ${labels.currMonthPeriod} %`] = pctBlank(row.curr_month_share);
  out["Diff"] = pctBlank(row.curr_month_diff);
  out[`Growth vs ${labels.prevMonth} ${meta.latest_year} %`] = pctBlank(row.growth_vs_prev_month);
  out[`Growth vs ${labels.currMonth} ${meta.prev_year} %`] = pctBlank(row.growth_vs_same_month_prev_year);
  out[`Units ${labels.currYtdPeriod}`] = blank(row.curr_ytd);
  out[`Share ${labels.currYtdPeriod} %`] = pctBlank(row.curr_ytd_share);
  out["YTD Diff"] = pctBlank(row.curr_ytd_diff);
  out[`Growth vs ${labels.prevYtdPeriod} %`] = pctBlank(row.growth_vs_prev_ytd);
  rankCols(row, meta, out);
  return out;
}

// Sheet 7: Brand/Model monthly. Uses the curr_months array directly, sliced to the
// latest reported month only — no future-month columns, no rank, no powertrain field.
function modelMonthlyRow(def: SheetDef, row: ReportRow, meta: ManualReportMeta, labels: ReturnType<typeof latestMonthLabels>) {
  const out: Record<string, string | number> = { [def.rowLabel]: row.label };
  out[`Units ${meta.prev_year} Total`] = blank(row.prev_total);
  out[`Share ${meta.prev_year} Total %`] = pctBlank(row.prev_total_share);
  for (let i = 0; i < meta.latest_month_num; i++) {
    out[meta.months[i]] = blank(row.curr_months[i]);
  }
  out[`Units ${labels.currYtdPeriod} Total`] = blank(row.curr_ytd);
  out[`Share ${labels.currYtdPeriod} Total %`] = pctBlank(row.curr_ytd_share);
  return out;
}

// Sheet 8: compact model rank. Model/Brand are split into their own columns (the
// fields already exist on the row; no need for the combined "Model  ·  Brand" label).
function modelRankRow(row: ReportRow, meta: ManualReportMeta, labels: ReturnType<typeof latestMonthLabels>) {
  const out: Record<string, string | number> = {};
  out["Model"] = row.model ?? row.label;
  out["Brand"] = row.brand ?? "";
  out[`${meta.prev_year} Total`] = blank(row.prev_total);
  out[`${meta.latest_year} Total`] = blank(row.curr_ytd);
  rankCols(row, meta, out);
  out[`${labels.currMonth}'${String(meta.latest_year).slice(-2)}`] = blank(row.curr_month_units ?? row.curr_months[meta.latest_month_num - 1]);
  return out;
}

// Sheet 9: province/brand monthly. จังหวัด (province) and ยี่ห้อรถ2 (brand) are split
// into their own columns per the workbook layout; prev-year shows all 12 months
// (complete year), current year is sliced to the latest reported month only.
function provinceMonthlyRow(row: ReportRow, meta: ManualReportMeta) {
  const out: Record<string, string | number> = {};
  out["จังหวัด"] = row.level === "brand" ? "" : row.group ?? row.label;
  out["ยี่ห้อรถ2"] = row.level === "brand" ? row.label : "";
  for (let i = 0; i < 12; i++) {
    out[`${meta.months[i]} ${meta.prev_year}`] = blank(row.prev_months[i]);
  }
  out[`${meta.prev_year} Total`] = blank(row.prev_total);
  for (let i = 0; i < meta.latest_month_num; i++) {
    out[`${meta.months[i]} ${meta.latest_year}`] = blank(row.curr_months[i]);
  }
  out[`${meta.latest_year} Total`] = blank(row.curr_ytd);
  return out;
}

export function buildManualReportSheetRows(
  def: SheetDef,
  rows: ReportRow[],
  meta: ManualReportMeta
): Record<string, string | number>[] {
  const labels = latestMonthLabels(meta);
  switch (def.kind) {
    case "powertrain":
      return rows.map((row) => powertrainRow(def, row, meta, labels));
    case "brand":
      return rows.map((row) => brandRow(def, row, meta, labels));
    case "model_tree":
      return rows.map((row) => modelMonthlyRow(def, row, meta, labels));
    case "model_rank":
      return rows.map((row) => modelRankRow(row, meta, labels));
    case "province_tree":
      return rows.map((row) => provinceMonthlyRow(row, meta));
  }
}

export function buildManualReportFileName(meta: ManualReportMeta, sectionTitle?: string): string {
  const period = meta.reporting_period.replace(/\s+/g, "-");
  if (!sectionTitle) return `manual-report-${period}.xlsx`;
  const slug = sectionTitle.replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return `manual-report-${slug}-${period}.xlsx`;
}
