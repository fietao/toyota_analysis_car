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

export function buildManualReportSheetRows(
  def: SheetDef,
  rows: ReportRow[],
  meta: ManualReportMeta
): Record<string, string | number>[] {
  const hasRank = def.kind === "brand" || def.kind === "model_rank";
  const hasOverall = def.kind === "province_tree";
  const labels = latestMonthLabels(meta);

  return rows.map((row) => {
    const out: Record<string, string | number> = { [def.rowLabel]: row.label };
    out[`Units ${meta.prev_year}`] = blank(row.prev_total);
    out[`Share ${meta.prev_year} %`] = pctBlank(row.prev_total_share);
    out[`Units ${labels.prevMonthPeriod}`] = blank(row.prev_month_units ?? row.prev_months[meta.latest_month_num - 1]);
    out[`Share ${labels.prevMonthPeriod} %`] = pctBlank(row.prev_month_share);
    out[`Units ${labels.prevYtdPeriod}`] = blank(row.prev_ytd);
    out[`Share ${labels.prevYtdPeriod} %`] = pctBlank(row.prev_ytd_share);
    out[`Units ${labels.currMonthPeriod}`] = blank(row.curr_month_units ?? row.curr_months[meta.latest_month_num - 1]);
    out[`Share ${labels.currMonthPeriod} %`] = pctBlank(row.curr_month_share);
    out["Diff"] = pctBlank(row.curr_month_diff);
    out[`Growth vs ${labels.prevMonth} ${meta.latest_year} %`] = pctBlank(row.growth_vs_prev_month);
    out[`Growth vs ${labels.currMonth} ${meta.prev_year} %`] = pctBlank(row.growth_vs_same_month_prev_year);
    out[`Units ${labels.currYtdPeriod}`] = blank(row.curr_ytd);
    out[`Share ${labels.currYtdPeriod} %`] = pctBlank(row.curr_ytd_share);
    out["YTD Diff"] = pctBlank(row.curr_ytd_diff);
    out[`Growth vs ${labels.prevYtdPeriod} %`] = pctBlank(row.growth_vs_prev_ytd);
    if (hasOverall) out["Overall"] = blank(row.overall);
    if (hasRank) {
      out[String(meta.prev_year)] = blank(row.prev_rank);
      out[String(meta.latest_year)] = blank(row.curr_rank);
      out["Rank Diff"] = blank(row.rank_diff);
    }
    return out;
  });
}

export function buildManualReportFileName(meta: ManualReportMeta, sectionTitle?: string): string {
  const period = meta.reporting_period.replace(/\s+/g, "-");
  if (!sectionTitle) return `manual-report-${period}.xlsx`;
  const slug = sectionTitle.replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return `manual-report-${slug}-${period}.xlsx`;
}
