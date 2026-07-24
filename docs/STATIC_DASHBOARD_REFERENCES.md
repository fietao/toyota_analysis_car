# Static Dashboard Architecture References

Use this note when planning dashboard or pipeline changes. These references validate the
current architecture pattern:

```text
Python/backend computes once
-> static frontend data files
-> Next.js renders charts/tables from generated JSON
-> Windows batch files orchestrate setup/update/release
```

The goal is to borrow conventions, not migrate frameworks. Keep the existing Python + Next.js
+ `.bat` workflow unless a future spec explicitly says otherwise.

## Best Match

- Hugo + Python + Chart.js dashboard guide:
  https://neuromechanist.github.io/blog/004-hugo-dashboard-guide/

Relevant pattern:

- A Python script aggregates raw data.
- The script writes chart-ready JSON into the static site directory.
- The frontend renders charts from static JSON.
- The guide emphasizes pre-aggregated data, chart-shaped JSON, generation timestamps, and
  provenance metadata.

Borrowable ideas:

- `process_data.py -> static/*.json -> static dashboard`.
- Keep frontend display-only where practical.
- Emit timestamps/source metadata with generated data.
- Structure JSON around chart needs instead of raw source tables.

## Build-Time Static Data Dashboard Frameworks

- Evidence repo:
  https://github.com/evidence-dev/evidence
- Evidence docs:
  https://docs.evidence.dev/
- Evidence starter template:
  https://github.com/evidence-dev/template
- Evidence overview:
  https://motherduck.com/glossary/evidence/
- BI-as-code comparison:
  https://motherduck.com/blog/the-future-of-bi-bi-as-code-duckdb-impact/
- Observable:
  https://observablehq.com/@observablehq
- PortalJS repo:
  https://github.com/datopian/portaljs
- PortalJS overview:
  https://www.reddit.com/r/selfhosted/comments/1uqt8y9/selfhost_your_own_open_data_portal_open_source/

Relevant patterns:

- Build-time data loading.
- Static artifact output.
- Explicit data contracts between build step and rendered pages.
- Provenance/build metadata.
- Dataset-first project organization.

Use as references for:

- data-loader layout;
- generated artifact naming;
- metadata fields such as `generated_at`, source files, and build IDs;
- validation/check commands;
- chart-ready data contracts.

Do not copy by default:

- SQL-in-Markdown workflow;
- hosted framework assumptions;
- server APIs;
- browser-side analytical engines;
- database dependencies;
- broad framework rewrites.

## Related Live-Server Models

These are useful for ideas but are not drop-in matches because they assume a live server:

- Datasette:
  https://simonwillison.net/tags/datasette/
- dashdown-md:
  https://libraries.io/pypi/dashdown-md
- dashdown-md demo:
  https://github.com/DireAI/ddown-world-cup-demo
- Apache Superset CSV upload / FAQ:
  https://superset.apache.org/user-docs/faq/

Borrow only narrow ideas from these, such as validation concepts, table interactions, or
dashboard organization. Avoid adding a running server unless a future requirement explicitly
needs one.

## Repo-Specific Guidance

Preferred direction for this repository:

1. Keep backend-generated JSON as the source of truth.
2. Avoid frontend/backend calculation drift.
3. Do not hardcode current month, current year, or YTD windows.
4. Prefer extending existing generated files before adding a new JSON contract.
5. Add a new `index_summary.json` only if existing files cannot cleanly power the home page.
6. Validate generated chart totals against canonical backend/report totals.
7. Preserve the safe monthly operator flow: failed updates must leave the last good dashboard
   data usable.

## Home Page (`/`) Data Source - Resolved

The index page already satisfies the "extend before adding" rule above:

- `/` renders from `dashboard_summary.json` (fetched on load).
- `/` lazily fetches `dashboard_models.json` only when a drill-down view needs the
  brand/model tree - it is not needed for the initial render.
- No `index_summary.json` file exists, and none is needed: the two files above already
  cover the home page.
- Backend-generated JSON remains the source of truth; the frontend does not compute or
  aggregate its own summary data for `/`.

Questions for future implementation agents:

- Can the index page use `dashboard_summary.json`, `dashboard_models.json`, and
  `manual_report.json` without a new data file?
- Which chart values must exactly reconcile to manual report totals?
- What metadata is missing from current JSON outputs?
- Which validations should block public release?
- Should `MONTHLY_UPDATE.bat` open the dashboard after a successful run, or only print the URL?
