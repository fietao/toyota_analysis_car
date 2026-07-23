import test from "node:test";
import assert from "node:assert/strict";

import {
  MANUAL_REPORT_SHEETS,
  buildManualReportFileName,
  buildManualReportSheetRows,
  getReportForYear,
  getReportYears,
  safeSheetName,
  type ManualReport,
  type ManualReportMeta,
  type ReportRow,
} from "./reportExport.ts";

const meta: ManualReportMeta = {
  reporting_period: "June 2569",
  latest_year: 2569,
  latest_month: "Jun",
  latest_month_num: 6,
  prev_year: 2568,
  months: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  default_vehicle_types: [],
  source_files: { brand_powertrain: "", model: "" },
  sections: {},
  generated_at: "",
};

function row(overrides: Partial<ReportRow>): ReportRow {
  return {
    key: "k",
    label: "k",
    prev_months: new Array(12).fill(0),
    prev_total: 0,
    prev_ytd: 0,
    prev_total_share: null,
    prev_ytd_share: null,
    curr_months: new Array(12).fill(0),
    curr_ytd: 0,
    curr_ytd_share: null,
    growth_vs_prev_month: null,
    growth_vs_same_month_prev_year: null,
    growth_vs_prev_ytd: null,
    ...overrides,
  };
}

test("null/undefined/zero values export as blank, never a fabricated zero", () => {
  const r = row({ curr_ytd_share: null, growth_vs_prev_month: 0, curr_ytd: 0 });
  const [out] = buildManualReportSheetRows({ id: "sheet1_powertrain", kind: "powertrain", rowLabel: "Powertrain" }, [r], meta);
  assert.equal(out["Share YTD %"], "");
  assert.equal(out["MoM %"], "");
  assert.equal(out["YTD 2569"], "");
});

test("only Jan..latest_month_num current-year columns appear, no future-month zeros", () => {
  const r = row({});
  const [out] = buildManualReportSheetRows({ id: "sheet1_powertrain", kind: "powertrain", rowLabel: "Powertrain" }, [r], meta);
  assert.ok("Jun 2569" in out);
  assert.ok(!("Jul 2569" in out));
});

test("brand/model_rank sheets carry Rank columns; powertrain sheets do not", () => {
  const r = row({ prev_rank: 1, curr_rank: 2, rank_diff: -1 });
  const brandOut = buildManualReportSheetRows({ id: "sheet2_brand_all", kind: "brand", rowLabel: "Brand" }, [r], meta)[0];
  assert.equal(brandOut["Rank 2568"], 1);
  assert.equal(brandOut["Rank 2569"], 2);
  assert.equal(brandOut["Rank Delta"], -1);

  const ptOut = buildManualReportSheetRows({ id: "sheet1_powertrain", kind: "powertrain", rowLabel: "Powertrain" }, [r], meta)[0];
  assert.ok(!("Rank 2568" in ptOut));
});

test("model-grain sheets never expose a Powertrain/fuel column", () => {
  const r = row({ label: "BYD DOLPHIN" });
  const out = buildManualReportSheetRows({ id: "sheet7_bev_by_model", kind: "model_tree", rowLabel: "Brand / Model" }, [r], meta)[0];
  assert.ok(!Object.keys(out).some((k) => /powertrain|fuel/i.test(k)));
});

test("safeSheetName truncates and de-dupes collisions", () => {
  const used = new Set<string>();
  const longTitle = "A".repeat(40);
  const first = safeSheetName(longTitle, used);
  assert.ok(first.length <= 31);
  const second = safeSheetName(longTitle, used);
  assert.notEqual(first, second);
  assert.ok(second.length <= 31);
});

test("safeSheetName strips Excel-invalid characters", () => {
  const used = new Set<string>();
  const name = safeSheetName("7.BEV by Model: A/B [x]", used);
  assert.ok(!/[:\\/?*[\]]/.test(name));
});

test("file name embeds the reporting period", () => {
  assert.equal(buildManualReportFileName(meta), "manual-report-June-2569.xlsx");
});

test("file name embeds the exported sheet title when given", () => {
  assert.equal(
    buildManualReportFileName(meta, "7.BEV by Model"),
    "manual-report-7-BEV-by-Model-June-2569.xlsx"
  );
});

test("MANUAL_REPORT_SHEETS covers all 9 workbook sheets", () => {
  assert.equal(MANUAL_REPORT_SHEETS.length, 9);
});

function multiYearReport(): ManualReport {
  const historicalMeta: ManualReportMeta = { ...meta, reporting_period: "December 2564", latest_year: 2564, latest_month: "Dec", latest_month_num: 12, prev_year: 2563, has_prev_year: false };
  return {
    meta,
    sheets: { sheet1_powertrain: [row({ label: "latest" })] },
    reports_by_year: {
      "2568": { meta: { ...meta, latest_year: 2568, prev_year: 2567 }, sheets: { sheet1_powertrain: [row({ label: "2568" })] } },
      "2564": { meta: historicalMeta, sheets: { sheet1_powertrain: [row({ label: "2564" })] } },
    },
  };
}

test("getReportYears returns latest plus every historical year, newest first", () => {
  assert.deepEqual(getReportYears(multiYearReport()), [2569, 2568, 2564]);
});

test("getReportForYear resolves the latest year from the top-level meta/sheets", () => {
  const r = getReportForYear(multiYearReport(), 2569);
  assert.equal(r.sheets.sheet1_powertrain[0].label, "latest");
});

test("getReportForYear resolves a historical year from reports_by_year", () => {
  const r = getReportForYear(multiYearReport(), 2568);
  assert.equal(r.sheets.sheet1_powertrain[0].label, "2568");
  assert.equal(r.meta.prev_year, 2567);
});

test("2564 report has null prior-year fields and null ranks, not fabricated zeros", () => {
  const r = getReportForYear(multiYearReport(), 2564);
  assert.equal(r.meta.has_prev_year, false);
  const r64 = row({ prev_months: new Array(12).fill(null), prev_total: null, prev_ytd: null, prev_rank: null, curr_rank: 1, rank_diff: null });
  const out = buildManualReportSheetRows({ id: "sheet2_brand_all", kind: "brand", rowLabel: "Brand" }, [r64], r.meta)[0];
  assert.equal(out[`Total 2563`], "");
  assert.equal(out[`Rank 2563`], "");
  assert.equal(out["Rank Delta"], "");
});
