## Goal

Make the dashboard truthful and easy to follow: never guess a model series' powertrain, show
`N/A` until a local administrator verifies it, preserve authoritative registration totals, and
reduce overlapping mapping files and dead pipeline paths.

## Deliverable

- A backend pipeline that keeps the two DLT source grains separate:
  - model source -> brand and series registration totals;
  - fuel source -> brand and powertrain registration totals.
- One canonical, versioned series registry at `backend/refer/series_registry.csv`.
- A local-only admin review flow opened from the dashboard index for resolving `N/A` mappings.
- A read-only public dashboard with a reliable Brand & Model Deep Dive.
- Deterministic validators and regression tests that block guessed or unreconciled releases.
- A smaller mapping surface and a documented deletion list for obsolete files and code paths.

## Chosen Approach (+ rationale)

Use conservative publication plus a governed registry.

The raw model file contains series but no fuel. The raw fuel file contains fuel but no series.
Their shared aggregate fields cannot prove a series-powertrain relationship. Therefore:

1. Delete the dominant-fuel enrichment from the model pipeline.
2. Preserve facts at their source grain.
3. Classify a raw series only through an administrator-reviewed registry entry.
4. Default absent, ambiguous, conflicting, or unreviewed entries to `N/A`.
5. Split a canonical series by powertrain only when its raw variant text has a verified,
   evidence-backed single-powertrain mapping.
6. Never split an ambiguous raw row, even when the canonical series supports several
   powertrains.

Registry MVP schema:

| Column | Rule |
|---|---|
| `canonical_brand` | Required; part of the key |
| `raw_series` | Required; normalized for matching; part of the key |
| `canonical_series` | Required display/grouping name |
| `powertrain` | `ICE`, `HEV`, `PHEV`, `BEV`, or `N/A` |
| `review_status` | `verified`, `unreviewed`, or `conflicting` |
| `evidence` | Required when status is `verified` |
| `reviewer` | Required when status is `verified` |
| `reviewed_at` | Required ISO timestamp when status is `verified` |

Use `(canonical_brand, normalized_raw_series)` as the unique MVP key. Use Git history instead of
effective-date rows initially. If model-year evidence later requires time-varying mappings, add
non-overlapping effective periods as a separately planned migration.

The review queue is computed from source keys missing or unverified in the registry; it is not
stored as another file.

### Deep Dive contract

- Keep `/models` as the general Brand & Model Deep Dive.
- Group by canonical brand, then canonical series.
- Series totals come only from the model source.
- Show verified powertrain segments and an explicit `N/A` segment.
- For every brand and canonical series:

  `ICE + HEV + PHEV + BEV + N/A = source series total`

- Filters include `ICE`, `HEV`, `PHEV`, `BEV`, and `N/A`; they operate only on registry-backed
  classifications.
- Excel export contains the same totals, powertrain, and review status as the UI.
- Sheets 7-8 remain BEV-only: include only raw variants explicitly verified as BEV. Never include
  `N/A` rows in BEV totals.

### Local admin contract

- Public static deployment remains read-only and contains no write endpoint.
- Local operator mode shows unresolved/conflicting series on the index and opens a review popup.
- The popup edits canonical series, powertrain, evidence, and reviewer.
- A small local Python service validates the payload and writes the CSV atomically using a
  temporary file plus replace.
- Reject invalid enums, empty verified evidence, duplicate keys, and conflicting updates.
- After save, regenerate affected exports and show validation results; do not silently publish.

### Consolidation boundary

Reduce sources of truth, not useful generated partitions. After migration and reconciliation
pass, remove runtime dependence on:

- `backend/refer/model2_map.csv`;
- `backend/refer/bev_series_name_table_template_rows.csv`;
- the Excel `BEV Series Name Table` as an input mapping source;
- the hard-coded dashboard `FUEL_MAP` duplicate;
- dominant-fuel model enrichment and auto-approval paths.

Retain `brand_map.csv` and `powertrain_map.csv`: they solve distinct brand normalization and
fuel-to-powertrain problems. Keep public JSON split where it materially controls bundle size;
do not merge files merely to reduce file count. Preserve removed artifacts through Git history or
an external backup, not duplicate archive files inside the repository.

## Alternatives Considered

| Alternative | Decision | Reason |
|---|---|---|
| Obtain joint model+fuel source from DLT | Future gold standard | Only source that can prove all joint counts, but not currently available |
| Governed registry | Chosen | Supports truthful classification and local review with current inputs |
| External manufacturer/type-approval enrichment | Optional future input | Useful evidence, but Thai-market variants and dates still require review |
| Statistical matching/IPF | Rejected for public facts | Produces estimates, not observed registrations |
| Dominant fuel per brand bucket | Delete | Proven to create false assignments such as TRITON -> HEV |
| Hide all series data | Rejected | Series totals are valid and useful when kept separate from guessed fuel |

## Existing Tools & Similar Programs

- Pandera can express dataframe schemas and reconciliation checks, but custom pytest assertions
  are preferred initially to avoid another dependency.
- Great Expectations provides richer quality reports but is too heavy for this file-based pipeline.
- OpenRefine can help a human normalize messy names, but string similarity is not proof of
  powertrain.
- Splink requires entity-level identifiers and cannot link these separate aggregate margins.
- IPF can reconcile estimated margins but must not be presented as factual registration data.
- OpenLineage and DVC are useful at larger operational scale; Git plus source hashes and a run
  manifest are sufficient for this MVP.

## Key Resources

- [UK DfT vehicle licensing data](https://www.gov.uk/government/statistical-data-sets/vehicle-licensing-statistics-data-files) — example of a joint schema containing make, model, and fuel.
- [GOV.UK reference-data guidance](https://www.gov.uk/guidance/publish-reference-data-for-use-across-government) — ownership, identifiers, versions, and validation.
- [US Census Statistical Quality Standard C4](https://www.census.gov/about/policies/quality/standards/standardc4.html) — linkage criteria, review, and accuracy evaluation.
- [UN statistical data-integration manual](https://unstats.un.org/unsd/statcom/51st-session/documents/BG-item-3n-compilers-manual-E.pdf) — limitations and uncertainty when variables are not jointly observed.
- [Pandera documentation](https://pandera.readthedocs.io/en/stable/) — dataframe validation patterns.

## Steps

1. **Freeze the failure and inventory the tree**
   - Add a regression check proving TRITON cannot be emitted as verified HEV.
   - Record source totals, existing outputs, mapping-file ownership, and candidate obsolete files.
   - Verify: the new check fails on the current output; inventory identifies every mapping reader
     and writer.

2. **Define and validate the registry**
   - Add `series_registry.csv`, parser, enum/schema validation, normalized composite key, and
     deterministic ordering.
   - Generate a migration report without changing classifications.
   - Migrate canonical names where safe. Convert every dominant-fuel-derived powertrain to
     `N/A/unreviewed`. Retain a verified value only when human review and evidence can be traced.
   - Verify: duplicate/conflicting keys fail; no contaminated value is marked verified.

3. **Separate backend source grains**
   - Remove `enrich_fuel_type` from model processing.
   - Build model facts from the model source plus registry only.
   - Build fuel/powertrain facts from the fuel source plus `powertrain_map.csv` only.
   - Replace the dashboard hard-coded fuel map with the canonical CSV loader.
   - Verify: raw totals reconcile independently and no model row inherits brand-dominant fuel.

4. **Build release validators before UI changes**
   - Assert source-grain reconciliation.
   - Assert per-series segment reconciliation including `N/A`.
   - Assert verified rows have evidence/reviewer/timestamp.
   - Assert Sheets 7-8 contain only verified BEV raw variants.
   - Assert public data labels observed/classified facts accurately and exposes no estimated facts.

5. **Add the local admin review flow**
   - Compute unresolved/conflicting registry entries dynamically.
   - Add a local-only validated API/service with atomic writes.
   - Add the index notification and review popup.
   - After updates, regenerate exports and display validator results.
   - Verify: an unknown fixture starts as `N/A`, can be reviewed, persists after restart, and cannot
     be saved with invalid/conflicting data.

6. **Repair public Deep Dive and reports**
   - Render canonical series totals and verified/N/A segments from the new export.
   - Rebuild filters, parent totals, and Excel export against the same selectors.
   - Rebuild Sheets 7-8 from verified BEV registry rows only and adjudicate golden differences.
   - Verify: TRITON never appears under HEV; all displayed and downloaded totals reconcile.

7. **Consolidate files and remove obsolete paths**
   - Switch all readers/writers to the registry and canonical fuel map.
   - Delete obsolete mappings, auto-approval code, and dead helpers only after equivalence and
     reconciliation pass.
   - Preserve unrelated dirty-worktree changes; never use broad reset, clean, stage, or commit.
   - Verify: repository search finds no runtime references to removed sources; documented file
     ownership is one source per concern.

8. **Run the full release gate**
   - Run backend tests and validators, lint, TypeScript, static build, and manual local checks of
     `/`, `/models`, `/analyst`, and `/report`.
   - Verify the public output has no admin control or write API.
   - Commit only scoped slices after explicit user approval.

## Done Criteria

- TRITON cannot appear as verified HEV or PHEV without an explicit evidence-backed registry row.
- New and ambiguous series display `N/A` until reviewed by the local administrator.
- No code assigns model powertrain from a brand-level dominant fuel.
- Every brand+canonical-series total reconciles exactly across verified PT segments plus `N/A`.
- Brand/powertrain totals reconcile exactly to the fuel source.
- General series totals reconcile exactly to the model source.
- Sheets 7-8 contain only explicitly verified BEV raw variants.
- Local registry writes are validated, atomic, persistent, and conflict-safe.
- Public static output is read-only and contains no admin writer.
- Obsolete mapping sources and dead generation paths are removed without touching unrelated work.
- Full release gate passes and manual Deep Dive/Excel checks agree.

## Risks

- **False migration confidence:** old powertrain values may look curated but originate from the
  dominant-fuel guess. Default them to unreviewed unless provenance proves otherwise.
- **Ambiguous raw names:** a canonical series may support multiple powertrains. Never allocate an
  ambiguous row; retain `N/A`.
- **Review workload:** thousands of historical names may be unresolved. Prioritize current-period
  and highest-volume rows while keeping all others visible as `N/A`.
- **Golden report changes:** corrected BEV inclusion may change Sheets 7-8. Treat differences as
  review decisions, not numbers to force-match.
- **Static/local boundary leakage:** keep the write service local and add a build assertion that
  public output contains no admin endpoints or controls.
- **Dirty tree cleanup:** delete only proven obsolete files after their consumers migrate; use
  scoped diffs and Git history for rollback.

## Copy-ready implementation prompt

Implement `plans/reliable-series-powertrain.md` in sequential, independently verified slices.
Start with Step 1 only: create a deterministic regression test for `MITSUBISHI / TRITON` being
incorrectly emitted as HEV and inventory every reader/writer of model, fuel, canonical-series, and
powertrain mappings. Do not change production behavior in the first slice. Preserve the dirty
working tree and do not reset, clean, broadly stage, or commit. Report the failing command, the
source-to-output trace, the proposed exact file list for Step 2, and any decision that would alter
the plan. After review, proceed one slice at a time. Never infer a series powertrain from aggregate
brand fuel data; unverified or ambiguous mappings must remain `N/A`. Every slice must include its
own reconciliation proof before the next slice begins.
