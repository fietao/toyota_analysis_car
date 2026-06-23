# DEEPAL + CHANGAN China Pitch Website Requirements And Plan

## 1. Purpose

Build an internal-facing pitch website for presenting Thailand market performance and opportunity to CHANGAN / DEEPAL leadership in China.

This is not a public consumer website and not only an analyst dashboard. It is a structured business case: use verified Thailand registration data to show where DEEPAL and CHANGAN stand, what is changing in the market, and what strategic actions the parent company should support.

The site should feel like a premium executive market briefing with live analytical depth underneath.

## 2. Core Audience

Primary audience:

- CHANGAN / DEEPAL leadership in China.
- Regional strategy teams.
- Export / overseas business development teams.
- Product planning and brand teams.

Secondary audience:

- Thailand management.
- Local distributor or partner teams.
- Analysts preparing monthly reporting for leadership.

The audience needs a clear argument, not just charts. Every page should help answer: **why Thailand matters, how DEEPAL + CHANGAN are performing, and what the company should do next.**

## 3. Strategic Story

The website should combine three layers:

- **Brand layer:** CHANGAN and DEEPAL are future-facing intelligent low-carbon mobility brands.
- **Market layer:** Thailand is a meaningful BEV growth market with competitive pressure and visible monthly movement.
- **Proof layer:** registration data shows the real performance of brands, models, share, rank, and momentum.

The story should be:

1. Thailand is a strategically important EV market in Southeast Asia.
2. DEEPAL + CHANGAN already have measurable market presence.
3. Model-level performance reveals where the brand is strong or weak.
4. Competitor data shows the urgency and opportunity.
5. China HQ support can turn current traction into stronger market position.

## 4. Reference Blend

Use these references for different purposes:

- **CHANGAN Thailand:** local-market presence, product lineup, test-drive/promotion context.
- **Global CHANGAN / DEEPAL:** brand ambition, technology, low-carbon mobility narrative.
- **Auto Innovators EV Dashboard:** EV market share and registration-data interaction patterns.
- **Bloomberg Terminal:** trusted, dense, executive data feel.
- **Tremor / disciplined React dashboard patterns:** clean chart and table implementation.

Avoid copying the public car-brand showroom style. The pitch site should be more serious: a strategy room, not a landing page.

## 5. Website Structure

### 5.1 Executive Summary

Purpose: give China HQ the full message in one screen.

Required sections:

- Thailand EV market snapshot.
- DEEPAL + CHANGAN current registration performance.
- Latest month and YTD totals.
- Market rank and BEV share.
- Biggest positive signal.
- Biggest risk or gap.
- Recommended HQ action.

This page should read like an executive one-page brief with charts beside the claims.

### 5.2 Thailand Market Context

Purpose: explain why Thailand deserves attention.

Required sections:

- Total vehicle registrations by year/month.
- BEV growth trend.
- Powertrain shift: ICE, BEV, HEV, PHEV.
- Leading brands in the BEV market.
- Competitive intensity from BYD, MG, Tesla, GAC Aion, Neta, and others when present in data.

Output should support the claim that Thailand is not a small side market; it is a signal market for Southeast Asia.

### 5.3 DEEPAL Performance

Purpose: show DEEPAL as the main EV-facing growth story.

Required sections:

- DEEPAL registrations by month.
- YTD total.
- BEV market share.
- Model ranking and model contribution.
- S07, L07, S05, or any detected DEEPAL models.
- Momentum versus previous months.
- Position against key BEV competitors.

This section should clearly show whether DEEPAL is gaining traction, plateauing, or losing momentum.

### 5.4 CHANGAN Group View

Purpose: show the total parent-brand position.

Required sections:

- Combined DEEPAL + CHANGAN registration performance.
- CHANGAN-branded versus DEEPAL-branded split if data supports it.
- Model portfolio contribution.
- Powertrain split if future CHANGAN non-BEV models appear.
- Thailand footprint as evidence for regional expansion.

This section should help HQ see DEEPAL not as an isolated model story, but as part of CHANGAN's overseas growth.

### 5.5 Competitor Benchmark

Purpose: show what the brand is up against.

Required sections:

- BEV brand ranking.
- DEEPAL + CHANGAN highlighted in the ranking.
- Monthly gain/loss versus competitors.
- Model-level benchmark where data supports it.
- Share gap to the next target competitor.

This page should make the strategic gap visible and measurable.

### 5.6 Strategic Recommendations

Purpose: convert data into an ask for China HQ.

Required sections:

- What is working.
- What is underperforming.
- Which models deserve support.
- Which competitor threat needs attention.
- Recommended product, pricing, marketing, dealer, or supply actions.
- Impact metrics to track monthly.

This is the main pitch page. It should use concise claims backed by visible data.

### 5.7 Analyst Appendix

Purpose: provide detailed data behind the pitch.

Required sections:

- Full tables.
- Filtered DEEPAL / CHANGAN rows.
- Market ranking tables.
- Model tables.
- Exportable evidence if feasible.

This lets the site stay executive at the top while still being auditable.

## 6. Content Requirements

The website needs two types of content:

### Narrative Content

- Clear English executive copy.
- Short strategic claims.
- No generic marketing filler.
- No public-consumer call-to-action language like "book a test drive" unless quoted as market context.
- Optional Chinese-language summary can be added later if the team wants a bilingual leadership version.

### Data Content

- Latest available month.
- Latest available year.
- Monthly registrations.
- YTD registrations.
- MoM change.
- YoY change where available.
- Brand rank.
- Model rank.
- BEV market share.
- Competitor comparison.
- Powertrain mix.
- Vehicle-type filtered totals.

All claims should be traceable to the dataset or clearly marked as strategic interpretation.

## 7. Visual Requirements

The site should follow the existing `DESIGN.md` direction but become more executive-presentation oriented.

Required visual style:

- Dark, premium, data-first.
- Dense but readable.
- Executive briefing layout, not consumer showroom.
- Monospaced numeric values.
- Small chart panels and concise insight blocks.
- 1px borders and flat surfaces.
- Minimal brand imagery.

Allowed brand expression:

- DEEPAL/BEV signal color can use electric teal or blue.
- CHANGAN can use a restrained secondary blue or neutral corporate treatment.
- Vehicle images may appear in compact model sections if approved assets exist.

Avoid:

- Marketing hero page.
- Generic SaaS dashboard look.
- Decorative gradients or glassmorphism.
- Big KPI cards with icon badges.
- Stock-looking EV imagery.
- Long brand slogans without data support.

## 8. Functional Requirements

Required pages or views:

- Executive Summary.
- Thailand Market.
- DEEPAL Performance.
- CHANGAN Group.
- Competitor Benchmark.
- Strategic Recommendations.
- Analyst Appendix.

Required interactions:

- Year filter.
- Month/latest-period filter.
- Brand filter.
- Model filter.
- Powertrain filter.
- Vehicle type filter.
- Competitor comparison selection.

Required output behavior:

- Metrics update dynamically from generated dashboard data.
- Latest period is detected automatically.
- No hardcoded current month or year.
- Missing values show a clear placeholder.
- Tables and charts must agree on totals.

## 9. Data Preparation Requirements

Add a brand-focus layer that can calculate:

- DEEPAL totals.
- CHANGAN totals.
- Combined DEEPAL + CHANGAN totals.
- DEEPAL model rankings.
- CHANGAN model rankings.
- Market rank.
- Market share.
- Competitor gaps.
- Monthly momentum.
- Strategic comparison metrics.

Brand/model handling:

- Normalize DEEPAL and CHANGAN aliases.
- Detect relevant model names from the dataset rather than hardcoding only S07/L07/S05.
- Preserve source names for auditability.
- Keep mappings in a configurable reference file if needed.

## 10. Implementation Plan

### Phase 1: Confirm Pitch Scope

- Confirm whether the presentation is for CHANGAN HQ, DEEPAL HQ, or both.
- Confirm whether the language is English-only or English with Chinese executive summaries.
- Confirm the default competitor set.
- Confirm whether approved vehicle/brand assets are available.

Deliverable:

- Final content outline and metric list.

### Phase 2: Build Brand-Focus Data Adapter

- Add calculations for DEEPAL, CHANGAN, combined totals, model rankings, and competitor gaps.
- Detect latest available period.
- Validate totals against existing dashboard tables.

Deliverable:

- Reliable brand-focus data object for the frontend.

### Phase 3: Create Executive Summary View

- Replace the current generic first screen with an executive market brief.
- Show headline argument, latest metrics, trend, competitor rank, and recommended action.
- Keep the view data-backed and concise.

Deliverable:

- First screen suitable for opening a pitch meeting.

### Phase 4: Create Market And Brand Detail Views

- Build Thailand Market, DEEPAL Performance, and CHANGAN Group views.
- Reuse consistent chart/table components.
- Keep narrative claims close to supporting charts.

Deliverable:

- Full evidence path from market context to brand performance.

### Phase 5: Create Competitor And Recommendation Views

- Build competitor ranking and gap analysis.
- Add strategic recommendation blocks.
- Tie each recommendation to a metric or chart.

Deliverable:

- Clear pitch ask for China HQ.

### Phase 6: Harden Analyst Appendix

- Add dense tables, filters, and export if feasible.
- Ensure Thai data values remain readable.
- Ensure numeric alignment and responsive overflow.

Deliverable:

- Auditable data appendix behind the pitch.

## 11. First Build Slice

The first build should be:

1. Create a `brandFocus` data adapter for DEEPAL + CHANGAN.
2. Create an Executive Summary view as the default landing screen.
3. Add a DEEPAL Performance view.
4. Add a Competitor Benchmark view.
5. Keep current broad dashboard tables as the Analyst Appendix.

This gives the site the right identity quickly: a pitch-ready China HQ briefing supported by live registration data.

## 12. Open Questions

- Is the pitch aimed at CHANGAN parent leadership, DEEPAL brand leadership, or overseas business leadership?
- Should the site ask for specific HQ support: marketing budget, model allocation, pricing action, dealer expansion, product localization, or supply priority?
- Should the executive copy be English only, or should we add Chinese summaries for leadership?
- Which competitor set matters most to HQ?
- Are approved CHANGAN/DEEPAL logos and model images available?
- Should the final website be interactive during meetings, or exported into a static presentation after each monthly update?
