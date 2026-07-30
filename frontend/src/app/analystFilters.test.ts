import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import { buildAnalystRowsFromFacts, filterAnalystRows, selectAnalystFilterOptions } from "./analystFilters.ts";
import { modelOwnerLookup } from "./selectors.ts";

const rows = [
  { brand: "ACME", model: "ALPHA" },
  { brand: "ACME", model: "BETA" },
  { brand: "MITSUBISHI", model: "TRITON" },
  { brand: "Grand Total", is_grand_total: true },
];

test("Analyst Brand selection narrows Model options", () => {
  assert.deepEqual(selectAnalystFilterOptions(rows, "").models, ["ALPHA", "BETA", "TRITON"]);
  assert.deepEqual(selectAnalystFilterOptions(rows, "ACME").models, ["ALPHA", "BETA"]);
  assert.deepEqual(selectAnalystFilterOptions(rows, "MITSUBISHI").models, ["TRITON"]);
});

test("Analyst Model selection narrows rows while preserving Grand Total", () => {
  assert.deepEqual(
    filterAnalystRows(rows, "ACME", "BETA"),
    [rows[1], rows[3]],
  );
});

test("Analyst Brand selection becomes invalid when Vehicle Type narrows the brand universe", () => {
  const rowsForAllVehicleType = rows;
  const rowsForRy11 = [{ brand: "MITSUBISHI", model: "TRITON" }];

  assert.ok(selectAnalystFilterOptions(rowsForAllVehicleType, "").brands.includes("ACME"));
  assert.ok(!selectAnalystFilterOptions(rowsForRy11, "").brands.includes("ACME"));
});

test("Analyst Model selection syncs a single-owner brand but not a shared model", () => {
  // The page passes rows with is_grand_total excluded; TRITON is MITSUBISHI-only here.
  const owners = modelOwnerLookup(rows.filter((r) => !r.is_grand_total));
  assert.equal(owners.get("TRITON"), "MITSUBISHI");
  assert.equal(owners.get("ALPHA"), "ACME");

  const shared = modelOwnerLookup([
    { brand: "ACME", model: "COMMON" },
    { brand: "MITSUBISHI", model: "COMMON" },
  ]);
  assert.equal(shared.get("COMMON"), null);
});

test("Analyst model data never exposes Powertrain segmentation", () => {
  const artifact = JSON.parse(
    readFileSync(new URL("../../public/data/analyst_data.json", import.meta.url), "utf8"),
  );

  assert.deepEqual(Object.keys(artifact.data.model), ["ALL"]);
});

test("Analyst metadata exposes province filter options", () => {
  const artifact = JSON.parse(
    readFileSync(new URL("../../public/data/analyst_data.json", import.meta.url), "utf8"),
  );

  assert.ok(Array.isArray(artifact.meta.provinces));
  assert.ok(artifact.meta.provinces.length > 0);
});

test("Analyst province data preserves the analyst view contract", () => {
  const artifact = JSON.parse(
    readFileSync(new URL("../../public/data/analyst_province_data.json", import.meta.url), "utf8"),
  );

  assert.ok(Array.isArray(artifact.facts.brand));
  assert.ok(Array.isArray(artifact.facts.model));
  assert.ok(artifact.facts.brand.length > 0);
  assert.ok(artifact.facts.model.length > 0);
  assert.ok(["p", "b", "y", "mo", "v", "pt", "u"].every((key) => key in artifact.facts.brand[0]));
  assert.ok(["p", "b", "m", "y", "mo", "v", "u"].every((key) => key in artifact.facts.model[0]));
});

test("Analyst province facts can build province-scoped rows", () => {
  const facts = [
    { p: "BANGKOK", b: "ACME", y: 2568, mo: 6, v: "รย.1", pt: "ICE", u: 10 },
    { p: "BANGKOK", b: "ACME", y: 2569, mo: 5, v: "รย.1", pt: "ICE", u: 8 },
    { p: "BANGKOK", b: "ACME", y: 2569, mo: 6, v: "รย.1", pt: "ICE", u: 12 },
    { p: "CHIANG MAI", b: "ACME", y: 2569, mo: 6, v: "รย.1", pt: "ICE", u: 99 },
  ];

  const out = buildAnalystRowsFromFacts({
    facts,
    viewBy: "brand",
    powertrain: "ICE",
    vehicleType: "รย.1",
    province: "BANGKOK",
    currentYear: 2569,
    currentMonthNum: 6,
  });

  assert.equal(out[0].is_grand_total, true);
  assert.equal(out[0].curr_month_units, 12);
  assert.equal(out[1].brand, "ACME");
  assert.equal(out[1].curr_growth_vs_prev_month, 0.5);
});
