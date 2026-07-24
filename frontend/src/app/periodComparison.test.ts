import test from "node:test";
import assert from "node:assert/strict";

import {
  type DashboardData,
  availableComparisonMonths,
  defaultComparisonMonth,
  selectPeriodComparison,
} from "./selectors.ts";

const data: DashboardData = {
  meta: {
    years: [2024, 2025],
    months: ["Jan", "Feb", "Mar", "Apr"],
    provinces: [],
    latest_year: 2025,
    latest_month: "Mar",
  },
  powertrain_master: [],
  fuel_monthly: [
    { y: 2024, m: "Jan", pt: "ICE", f: "GAS", v: "VT1", u: 80 },
    { y: 2024, m: "Feb", pt: "ICE", f: "GAS", v: "VT1", u: 90 },
    { y: 2024, m: "Mar", pt: "ICE", f: "GAS", v: "VT1", u: 100 },
    { y: 2024, m: "Apr", pt: "ICE", f: "GAS", v: "VT1", u: 70 },
    { y: 2025, m: "Jan", pt: "ICE", f: "GAS", v: "VT1", u: 100 },
    { y: 2025, m: "Feb", pt: "ICE", f: "GAS", v: "VT1", u: 110 },
    { y: 2025, m: "Mar", pt: "ICE", f: "GAS", v: "VT1", u: 130 },
    { y: 2025, m: "Mar", pt: "BEV", f: "EV", v: "VT1", u: 40 },
    { y: 2024, m: "Mar", pt: "BEV", f: "EV", v: "VT1", u: 10 },
    { y: 2025, m: "Mar", pt: "ICE", f: "GAS", v: "VT2", u: 999 },
  ],
  brand_monthly: [
    { y: 2024, m: "Mar", pt: "ICE", b: "ACME", v: "VT1", u: 60 },
    { y: 2025, m: "Mar", pt: "ICE", b: "ACME", v: "VT1", u: 80 },
    { y: 2024, m: "Mar", pt: "BEV", b: "BYD", v: "VT1", u: 10 },
    { y: 2025, m: "Mar", pt: "BEV", b: "BYD", v: "VT1", u: 40 },
    { y: 2025, m: "Mar", pt: "ICE", b: "NOISE", v: "VT2", u: 999 },
  ],
};

test("availableComparisonMonths returns actual months for the target year", () => {
  assert.deepEqual(availableComparisonMonths(data, 2025), ["Jan", "Feb", "Mar"]);
});

test("defaultComparisonMonth prefers latest metadata when it is available", () => {
  assert.equal(defaultComparisonMonth(data, 2025), "Mar");
  assert.equal(defaultComparisonMonth(data, "All"), "Mar");
});

test("selectPeriodComparison compares month, previous month, same prior-year month, and equivalent YTD", () => {
  const comparison = selectPeriodComparison(data, 2025, "Mar", ["VT1"], [], []);
  assert.ok(comparison);
  assert.equal(comparison.currentMonthUnits, 170);
  assert.equal(comparison.previousMonthUnits, 110);
  assert.equal(comparison.sameMonthPriorYearUnits, 110);
  assert.equal(comparison.currentYtdUnits, 380);
  assert.equal(comparison.priorYtdUnits, 280);
  assert.equal(comparison.priorFullYearUnits, 350);
  assert.equal(comparison.momDeltaUnits, 60);
  assert.equal(comparison.yoyDeltaUnits, 60);
  assert.equal(comparison.ytdDeltaUnits, 100);
});

test("selectPeriodComparison respects Powertrain and Brand filters for mover context", () => {
  const comparison = selectPeriodComparison(data, 2025, "Mar", ["VT1"], ["BEV"], ["BYD"]);
  assert.ok(comparison);
  assert.equal(comparison.currentMonthUnits, 40);
  assert.equal(comparison.sameMonthPriorYearUnits, 10);
  assert.deepEqual(comparison.topPowertrainMover, { name: "BEV", delta: 30 });
  assert.deepEqual(comparison.topBrandMover, { name: "BYD", delta: 30 });
});

test("first-month previous-month comparison rolls back to the prior year's last metadata month", () => {
  const comparison = selectPeriodComparison(data, 2025, "Jan", ["VT1"], [], []);
  assert.ok(comparison);
  assert.equal(comparison.previousMonth, "Apr");
  assert.equal(comparison.previousMonthYear, 2024);
  assert.equal(comparison.previousMonthUnits, 70);
});
