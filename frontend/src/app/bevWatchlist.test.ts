import test from "node:test";
import assert from "node:assert/strict";

import { parseBevWatchlist, bevWatchlistMessage, candidatesToCsv, type BevCandidate } from "./bevWatchlist.ts";

const candidate: BevCandidate = {
  brand: "BYD", raw_model: "BYD SEAL EV", model: "SEAL", units: 12,
  confidence: "high", reason_code: "approved_family_match",
  reason: "Same brand and canonical model family ('SEAL') as an already-approved BEV.",
  review_status: "pending",
};

test("missing/undefined payload is unavailable", () => {
  assert.deepEqual(parseBevWatchlist(undefined), { kind: "unavailable" });
  assert.deepEqual(parseBevWatchlist(null), { kind: "unavailable" });
});

test("well-formed JSON with the wrong shape is unavailable, not a crash", () => {
  assert.deepEqual(parseBevWatchlist({ hello: "world" }), { kind: "unavailable" });
  assert.deepEqual(parseBevWatchlist({ meta: {}, candidates: [] }), { kind: "unavailable" });
  assert.deepEqual(
    parseBevWatchlist({ meta: { year: 2569, month: 6, candidate_count: 0, total_units: 0 }, candidates: "nope" }),
    { kind: "unavailable" }
  );
});

test("a candidate missing required fields makes the whole payload unavailable", () => {
  const badCandidate = { ...candidate, confidence: "certain" };
  const payload = {
    meta: { year: 2569, month: 6, generated_at: "x", candidate_count: 1, total_units: 12 },
    candidates: [badCandidate],
  };
  assert.equal(parseBevWatchlist(payload).kind, "unavailable");
});

test("empty candidates list parses to the empty state with period", () => {
  const payload = {
    meta: { year: 2569, month: 6, generated_at: "x", candidate_count: 0, total_units: 0 },
    candidates: [],
  };
  assert.deepEqual(parseBevWatchlist(payload), { kind: "empty", year: 2569, month: 6 });
});

test("non-empty candidates list parses to the candidates state", () => {
  const payload = {
    meta: { year: 2569, month: 6, generated_at: "x", candidate_count: 1, total_units: 12 },
    candidates: [candidate],
  };
  const result = parseBevWatchlist(payload);
  assert.equal(result.kind, "candidates");
  if (result.kind === "candidates") {
    assert.equal(result.totalUnits, 12);
    assert.equal(result.candidates.length, 1);
    assert.equal(result.candidates[0].brand, "BYD");
  }
});

test("bevWatchlistMessage matches the exact operator-facing wording", () => {
  assert.equal(
    bevWatchlistMessage(3),
    "3 possible new BEV models need checking. Published data remains safe."
  );
  assert.equal(
    bevWatchlistMessage(0),
    "0 possible new BEV models need checking. Published data remains safe."
  );
});

test("candidatesToCsv emits a header row and one row per candidate", () => {
  const csv = candidatesToCsv([candidate]);
  const lines = csv.split("\n");
  assert.equal(lines[0], "brand,raw_model,model,units,confidence,reason_code,reason,review_status");
  assert.equal(lines.length, 2);
  assert.ok(lines[1].startsWith("BYD,BYD SEAL EV,SEAL,12,high,approved_family_match,"));
});

test("candidatesToCsv escapes commas and quotes in free-text reason", () => {
  const withComma: BevCandidate = { ...candidate, reason: 'Contains, a comma and a "quote"' };
  const csv = candidatesToCsv([withComma]);
  assert.ok(csv.includes('"Contains, a comma and a ""quote"""'));
});

test("candidatesToCsv on an empty list yields only the header", () => {
  const csv = candidatesToCsv([]);
  assert.equal(csv, "brand,raw_model,model,units,confidence,reason_code,reason,review_status");
});
