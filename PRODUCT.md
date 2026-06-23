# Product

## Register

product

## Users

Thai automotive industry analysts who open this tool once a month after new DLT registration data drops. They are comfortable reading dense tables and charts; they are not casual users. Their primary task is to understand what changed — which powertrain gained or lost share, which brands moved, how BEV adoption is tracking. Speed to insight matters more than onboarding.

## Product Purpose

Monthly Thailand new-car registration analysis dashboard. Ingests raw DLT data, cleans and pivots it, and surfaces trends across powertrains (ICE / BEV / HEV / PHEV), brand rankings, and BEV model-level detail. Success looks like an analyst opening the dashboard and having their key questions answered within 30 seconds — without needing to touch the raw Excel.

Two surfaces: a Streamlit app (current working tool, tables + exports) and a Next.js dashboard (long-term product, charts + live data). Both should feel like they belong to the same instrument.

## Brand Personality

Precise. Authoritative. Understated.

The tool should feel like a Bloomberg Terminal crossed with a quality market brief — data-dense, no gratuitous decoration, trust earned through accuracy and consistency. Not cold; the subject matter (Thailand's EV transition) is genuinely interesting — but any warmth comes from the data telling its story, not from UI flourishes.

## Anti-references

- The current Next.js dashboard: gradient-blob glassmorphism, gradient text headings, hero-metric KPI cards with icon gradients — this is exactly the aesthetic to replace.
- Generic SaaS dashboards (Dribbble dark-mode demo shots, Vercel-style marketing dashboards).
- Anything that looks like it was designed to impress in a portfolio screenshot rather than to be used every month by someone who needs the numbers fast.

## Design Principles

1. **Data is the hero.** Layout, hierarchy, and color all defer to the numbers. Chrome recedes; the analyst's eye should land on the signal, not the frame.
2. **Trust through precision.** Every element earns its place by serving comprehension. Decoration that doesn't carry meaning gets cut.
3. **Bilingual by design.** Thai data labels (column headers, month names, brand names from the raw data) and English UI chrome coexist as first-class citizens — never an afterthought, never broken by font substitution.
4. **Analyst pacing.** This is opened every month for the same purpose. Information density is a feature. Don't solve it with excessive whitespace.
5. **Durable instrument.** This tool should feel like a trusted piece of professional equipment — consistent, predictable, reliable — not a demo or a dashboard of the week.

## Accessibility & Inclusion

WCAG AA as a floor. Body text ≥ 4.5:1 contrast against background. Thai script must render with a Thai-capable font stack; no relying on OS fallbacks that produce tofu or metric-shifted glyphs. Reduced motion respected via `prefers-reduced-motion`. Keyboard navigation on interactive controls.
