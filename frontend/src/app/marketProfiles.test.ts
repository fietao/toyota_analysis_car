import test from "node:test";
import assert from "node:assert/strict";

import {
  FORMAL_REPORT_CODES,
  resolveProfileCodes,
  identifyMarketProfile,
  resolveVehicleTypeSelection,
  missingFormalReportCodes,
} from "./marketProfiles.ts";

const ALL_CODES = [
  "รย.1", "รย.2", "รย.3", "รย.4", "รย.6", "รย.7", "รย.8", "รย.9",
  "รย.10", "รย.11", "รย.12", "รย.13", "รย.14", "รย.15", "รย.16", "รย.17",
];

test("formal_report resolves to exactly the seven required codes", () => {
  const codes = resolveProfileCodes("formal_report", ALL_CODES);
  assert.deepEqual([...codes].sort(), [...FORMAL_REPORT_CODES].sort());
  assert.equal(codes.length, 7);
});

test("all_dlt resolves to every available code", () => {
  assert.deepEqual(resolveProfileCodes("all_dlt", ALL_CODES), ALL_CODES);
});

test("matching selected codes identifies the correct profile regardless of order", () => {
  const shuffledFormal = [...FORMAL_REPORT_CODES].reverse();
  assert.equal(identifyMarketProfile(shuffledFormal, ALL_CODES).id, "formal_report");

  const shuffledAll = [...ALL_CODES].sort(() => 1);
  assert.equal(identifyMarketProfile(shuffledAll, ALL_CODES).id, "all_dlt");
});

test("a partial or altered selection resolves to Custom selection", () => {
  const partial = FORMAL_REPORT_CODES.slice(0, 5);
  assert.equal(identifyMarketProfile(partial, ALL_CODES).id, "custom");

  const altered = [...FORMAL_REPORT_CODES, "รย.4"];
  assert.equal(identifyMarketProfile(altered, ALL_CODES).id, "custom");

  // Empty selection must never be misread as either named profile — it is
  // the loading/uninitialized state, not "All DLT vehicle types".
  assert.equal(identifyMarketProfile([], ALL_CODES).id, "custom");
});

test("profile switching produces the expected selector totals", () => {
  const formalCodes = resolveProfileCodes("formal_report", ALL_CODES);
  const allDltCodes = resolveProfileCodes("all_dlt", ALL_CODES);
  assert.equal(formalCodes.length, 7);
  assert.equal(allDltCodes.length, ALL_CODES.length);
  assert.ok(formalCodes.length < allDltCodes.length);
});

test("the global filter's empty ('All') action resolves to every DLT code, never []", () => {
  const resolved = resolveVehicleTypeSelection([], ALL_CODES);
  assert.deepEqual(resolved, ALL_CODES);
  assert.ok(resolved.length > 0);

  // A real selection passes through untouched.
  const partial = FORMAL_REPORT_CODES.slice(0, 3);
  assert.deepEqual(resolveVehicleTypeSelection(partial, ALL_CODES), partial);
});

test("a formal-report code missing from dashboard metadata is reported, not silently dropped", () => {
  assert.deepEqual(missingFormalReportCodes(ALL_CODES), []);

  const withoutRy9 = ALL_CODES.filter((c) => c !== "รย.9");
  assert.deepEqual(missingFormalReportCodes(withoutRy9), ["รย.9"]);
});

test("displayed profile and selector denominator stay consistent for any resolved selection", () => {
  // Whatever the popover reports, once run through resolveVehicleTypeSelection the
  // selection must be non-empty and the identified profile's label must match a
  // denominator that agrees with the actual selected/all counts.
  for (const raw of [[], resolveProfileCodes("formal_report", ALL_CODES), ALL_CODES]) {
    const selected = resolveVehicleTypeSelection(raw, ALL_CODES);
    assert.ok(selected.length > 0);

    const profile = identifyMarketProfile(selected, ALL_CODES);
    if (profile.id === "all_dlt") assert.equal(selected.length, ALL_CODES.length);
    if (profile.id === "formal_report") assert.equal(selected.length, FORMAL_REPORT_CODES.length);
  }
});
