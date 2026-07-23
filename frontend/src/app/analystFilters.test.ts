import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import { filterAnalystRows, selectAnalystFilterOptions } from "./analystFilters.ts";

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

test("Analyst model data never exposes Powertrain segmentation", () => {
  const artifact = JSON.parse(
    readFileSync(new URL("../../public/data/analyst_data.json", import.meta.url), "utf8"),
  );

  assert.deepEqual(Object.keys(artifact.data.model), ["ALL"]);
});
