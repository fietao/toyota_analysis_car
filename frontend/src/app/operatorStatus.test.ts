import test from "node:test";
import assert from "node:assert/strict";

import { healthTone, healthLabel } from "./operatorStatus.ts";

test("ok status with matching totals maps to green / OK label", () => {
  assert.equal(healthTone("ok", true), "green");
  assert.equal(healthLabel("ok"), "Live data OK");
});

test("ok status with mismatched totals is downgraded to yellow", () => {
  assert.equal(healthTone("ok", false), "yellow");
});

test("review_needed status maps to yellow regardless of totals", () => {
  assert.equal(healthTone("review_needed", true), "yellow");
  assert.equal(healthTone("review_needed", false), "yellow");
  assert.equal(healthLabel("review_needed"), "Review needed");
});

test("failed status maps to red regardless of totals", () => {
  assert.equal(healthTone("failed", true), "red");
  assert.equal(healthTone("failed", false), "red");
  assert.equal(healthLabel("failed"), "Update failed");
});
