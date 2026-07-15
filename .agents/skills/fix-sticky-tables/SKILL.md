---
name: fix-sticky-tables
description: Diagnose and harden sticky headers and frozen columns in HTML or React data tables. Use when table headers or first columns stop sticking, overlap, jitter, misalign, become transparent, disappear behind cells, break after filtering/resizing/font loading, fail with two-axis scrolling or multi-row headers, or behave differently across browsers.
---

# Fix Sticky Tables

Fix the demonstrated failure, not an imagined generic table. Prefer the smallest CSS correction;
add measurement code only when the layout is genuinely dynamic.

## Workflow

1. Reproduce the exact failure before editing. Record the route, viewport, zoom, scroll direction,
   table state, and which cell first behaves incorrectly.
2. Identify the scroll owner with computed styles. Trace every ancestor from the sticky cell to
   the viewport and record `overflow`, `position`, `transform`, `contain`, and clipping.
3. Map the sticky layers: body cells, frozen column, header rows, and the top-left intersection.
   Record each layer's `top`, `left`, `z-index`, background, width, and measured height.
4. State one falsifiable root-cause hypothesis. Identify the observation that would disprove it.
5. Make one minimal change and reproduce again before making another.
6. Verify the complete matrix below and report evidence.

When this is a bug investigation, invoke `debug-mantra` and `diagnosing-bugs`. Use browser control
for visual reproduction. Invoke `impeccable` only when the fix changes interface design rather
than repairing existing behavior.

## Failure Checks

Check these in order:

1. **Scroll container:** Sticky positioning is relative to the nearest scrolling ancestor, which
   may not be the element the author intended. Confirm both horizontal and vertical overflow.
2. **Sticky target:** For reliable tables, prefer sticky header cells (`th`) over relying on
   `thead` or `tr` behavior. Preserve semantic table markup.
3. **Offsets:** Every stacked header band needs a correct cumulative `top`; every frozen column
   needs a correct cumulative `left`. Never guess offsets from padding or font size.
4. **Reflow:** Test after fonts load, responsive wrapping, filters, sorting, pagination, row
   expansion, and column-label changes. Replace timer-based measurement with `ResizeObserver` only
   when CSS cannot express the layout.
5. **Stacking:** Use an explicit layer order. The top-left intersection must sit above both the
   header and frozen-column layers. Sticky cells need opaque backgrounds where content passes
   underneath.
6. **Borders and clipping:** If collapsed borders flicker or vanish, test `border-collapse:
   separate` with zero spacing. Check rounded/hidden ancestors for clipping before changing table
   borders.
7. **Widths:** Frozen columns require stable widths. Confirm header and body columns resolve to
   the same computed width at every tested viewport.
8. **Performance:** Do not update React state on scroll. Avoid layout reads followed by writes in
   a scroll loop. A `ResizeObserver` must be scoped, cleaned up, and free of resize loops.

Do not stack patches such as arbitrary `z-index`, extra wrappers, hardcoded pixel offsets, and
delayed timers without proving which condition caused the failure.

## Verification Matrix

Verify at minimum:

- vertical-only, horizontal-only, and diagonal scrolling;
- top, middle, far-right, and bottom table positions;
- the top-left sticky intersection and every multi-row header boundary;
- narrow and wide viewports at 100% zoom, plus one non-default zoom level;
- after resize, filter, sort, pagination, expansion/collapse, and data reload;
- keyboard focus visibility while sticky cells overlap scrolling content;
- Chromium and one independent browser engine when the release supports both;
- no new console errors, hydration errors, scroll jank, or clipped interactive controls.

If browser automation is unavailable, say which checks remain manual. Do not claim the issue is
fixed from a static code inspection alone.

## Required Handoff

Report:

- exact reproduction and root cause;
- the scroll owner and conflicting ancestor/style;
- files and lines changed;
- why the selected fix is smaller and more stable than the alternatives;
- verification results for each relevant matrix item;
- screenshots or a short recording before and after when visual tooling is available;
- any unverified browser or responsive state.
