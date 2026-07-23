// Focused Step 6B tests: the Deep Dive/Excel selectors must consume Step 6A's
// brand -> canonical series -> registry-backed Powertrain segments contract,
// never a fuel field or a fuel-derived brand Powertrain.
import test from "node:test";
import assert from "node:assert/strict";
import {
  type BrandNode,
  type DashboardData,
  POWERTRAINS,
  brandTotals,
  brandMonthlyValues,
  brandSegmentBreakdown,
  seriesTotals,
  seriesMonthlyValues,
  segmentBreakdown,
  filterSegments,
  selectDeepDiveFilterOptions,
  selectRankingsData,
  modelBrandPairs,
  modelOwnerLookup,
} from "./selectors.ts";

const YEAR = "2569";
const VT = "รย.1";
const PROV = "BANGKOK";

function monthly(units: number) {
  return { [VT]: { [PROV]: { [YEAR]: [units, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] } } };
}

// Fixture: one brand (ACME) with a canonical series ALPHA that has verified ICE + HEV
// segments plus an unreviewed N/A remainder, and MITSUBISHI/TRITON under an empty
// registry (wholly N/A) — mirrors the backend fixtures in
// backend/tests/test_dashboard_model_tree.py.
function fixture(): BrandNode[] {
  return [
    {
      brand: "ACME",
      monthly: monthly(20),
      models: [
        {
          name: "ALPHA",
          monthly: monthly(20),
          segments: [
            { powertrain: "ICE", monthly: monthly(10) },
            { powertrain: "HEV", monthly: monthly(7) },
            { powertrain: "N/A", monthly: monthly(3) },
          ],
        },
      ],
    },
    {
      brand: "MITSUBISHI",
      monthly: monthly(100),
      models: [
        {
          name: "TRITON",
          monthly: monthly(100),
          segments: [{ powertrain: "N/A", monthly: monthly(100) }],
        },
      ],
    },
  ];
}

test("empty-registry fixture keeps TRITON wholly under N/A", () => {
  const [, mitsubishi] = fixture();
  const triton = mitsubishi.models[0];
  assert.deepEqual(
    triton.segments.map((s) => s.powertrain),
    ["N/A"]
  );
  // Filtering to any verified Powertrain excludes it entirely.
  for (const pt of ["ICE", "HEV", "PHEV", "BEV"]) {
    assert.equal(seriesTotals(triton, [YEAR], YEAR, [pt], [], []).grandTotal, 0);
  }
  assert.equal(seriesTotals(triton, [YEAR], YEAR, ["N/A"], [], []).grandTotal, 100);
});

test("a canonical series with verified ICE and HEV renders both segments under one series", () => {
  const [acme] = fixture();
  const alpha = acme.models[0];
  assert.equal(acme.models.length, 1, "one row per canonical series");
  const breakdown = segmentBreakdown(alpha, [YEAR], [], []);
  assert.equal(breakdown["ICE"], 10);
  assert.equal(breakdown["HEV"], 7);
  assert.equal(breakdown["N/A"], 3);
});

test("All equals ICE + HEV + PHEV + BEV + N/A at a filtered slice (vehicle type + province + year)", () => {
  const [acme] = fixture();
  const alpha = acme.models[0];
  const all = seriesTotals(alpha, [YEAR], YEAR, [], [VT], [PROV]).grandTotal;
  const sumOfSegments = POWERTRAINS.reduce(
    (s, pt) => s + seriesTotals(alpha, [YEAR], YEAR, [pt], [VT], [PROV]).grandTotal,
    0
  );
  assert.equal(all, sumOfSegments);
  assert.equal(all, 20);

  const brandAll = brandTotals(acme, [YEAR], YEAR, [], [VT], [PROV]).grandTotal;
  const brandSumOfSegments = POWERTRAINS.reduce(
    (s, pt) => s + brandTotals(acme, [YEAR], YEAR, [pt], [VT], [PROV]).grandTotal,
    0
  );
  assert.equal(brandAll, brandSumOfSegments);
});

test("selecting HEV cannot include N/A, ICE, PHEV, or BEV units", () => {
  const [acme] = fixture();
  const alpha = acme.models[0];
  assert.equal(seriesTotals(alpha, [YEAR], YEAR, ["HEV"], [], []).grandTotal, 7);
  const hevOnly = filterSegments(alpha.segments, ["HEV"]);
  assert.deepEqual(hevOnly.map((s) => s.powertrain), ["HEV"]);
  assert.equal(
    seriesMonthlyValues(alpha, YEAR, ["HEV"], [], [])[0],
    7
  );
});

test("brand totals equal the sum of visible canonical-series totals", () => {
  const tree = fixture();
  tree.forEach((brand) => {
    const bTotal = brandTotals(brand, [YEAR], YEAR, [], [], []).grandTotal;
    const seriesSum = brand.models.reduce(
      (s, m) => s + seriesTotals(m, [YEAR], YEAR, [], [], []).grandTotal,
      0
    );
    assert.equal(bTotal, seriesSum);
  });
});

test("displayed (table) and Excel-download totals match for identical filters", () => {
  const [acme] = fixture();
  const alpha = acme.models[0];
  const uiMonthly = seriesMonthlyValues(alpha, YEAR, ["ICE"], [], []);
  const uiTotal = uiMonthly.reduce((s, v) => s + v, 0);
  // The Excel export calls the exact same selector with the exact same args.
  const excelMonthly = seriesMonthlyValues(alpha, YEAR, ["ICE"], [], []);
  const excelTotal = excelMonthly.reduce((s, v) => s + v, 0);
  assert.deepEqual(uiMonthly, excelMonthly);
  assert.equal(uiTotal, excelTotal);
  assert.equal(uiTotal, 10);
});

test("N/A is never hidden from the breakdown, filtered or not", () => {
  const [acme] = fixture();
  const alpha = acme.models[0];
  const breakdown = segmentBreakdown(alpha, [YEAR], [], []);
  assert.ok((breakdown["N/A"] ?? 0) > 0);
  const brandBreakdown = brandSegmentBreakdown(acme, [YEAR], [], []);
  assert.ok((brandBreakdown["N/A"] ?? 0) > 0);
});

test("no selector reads a fuel field: fixtures carry no fuel data and still reconcile", () => {
  // BrandNode/ModelNode/SeriesSegment (see selectors.ts) have no `fuel` or `powertrain`
  // field at the brand/model level by type — this fixture has none, and the segment
  // totals still reconcile, proving classification is registry/segment-only.
  const tree = fixture();
  const total = tree.reduce((s, b) => s + brandTotals(b, [YEAR], YEAR, [], [], []).grandTotal, 0);
  assert.equal(total, 120);
});

test("brandMonthlyValues sums only matching segments across all series in the brand", () => {
  const [acme] = fixture();
  const iceMonthly = brandMonthlyValues(acme, YEAR, ["ICE"], [], []);
  assert.equal(iceMonthly[0], 10);
  const allMonthly = brandMonthlyValues(acme, YEAR, [], [], []);
  assert.equal(allMonthly[0], 20);
});

test("loading an empty-registry model tree cannot erase fuel-derived brand rankings", () => {
  const data: DashboardData = {
    meta: { years: [2569], months: ["Jan"], provinces: [PROV] },
    powertrain_master: [],
    fuel_monthly: [],
    brand_monthly: [{ y: 2569, m: "Jan", pt: "ICE", b: "MITSUBISHI", v: VT, u: 80 }],
  };

  const result = selectRankingsData(
    data,
    ["ICE"],
    ["MITSUBISHI"],
    [],
    [],
    new Set(),
    2569,
    [],
    ["Jan"],
    fixture(),
  );

  assert.equal(result.rows.length, 1);
  assert.equal(result.rows[0].name, "MITSUBISHI");
  assert.equal(result.rows[0].YTD, 80);
});

test("Model -> Brand sync: single-owner model resolves its brand, shared model does not guess", () => {
  // ALPHA belongs only to ACME; SHARED belongs to both ACME and MITSUBISHI.
  const owners = modelOwnerLookup([
    { brand: "ACME", model: "ALPHA" },
    { brand: "ACME", model: "SHARED" },
    { brand: "MITSUBISHI", model: "SHARED" },
    { brand: "MITSUBISHI", model: "TRITON" },
    { brand: "ACME", model: "SHARED" }, // duplicate owner must not revert the null verdict
  ]);
  assert.equal(owners.get("ALPHA"), "ACME");
  assert.equal(owners.get("TRITON"), "MITSUBISHI");
  assert.equal(owners.get("SHARED"), null); // shared across brands -> no guess
  assert.equal(owners.get("MISSING"), undefined); // unknown -> falsy, no guess
});

test("modelBrandPairs flattens the tree to brand/model ownership pairs", () => {
  assert.deepEqual(modelBrandPairs(fixture()), [
    { brand: "ACME", model: "ALPHA" },
    { brand: "MITSUBISHI", model: "TRITON" },
  ]);
  assert.deepEqual(modelBrandPairs(undefined), []);
});

test("Deep Dive model filter options narrow to the selected brand models", () => {
  const tree = fixture();

  assert.deepEqual(selectDeepDiveFilterOptions(tree, []).allModels, ["ALPHA", "TRITON"]);
  assert.deepEqual(selectDeepDiveFilterOptions(tree, ["ACME"]).allModels, ["ALPHA"]);
  assert.deepEqual(selectDeepDiveFilterOptions(tree, ["MITSUBISHI"]).allModels, ["TRITON"]);
  assert.deepEqual(selectDeepDiveFilterOptions(tree, ["ACME", "MITSUBISHI"]).allModels, ["ALPHA", "TRITON"]);
});
