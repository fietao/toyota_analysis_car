# AI Handoff Document: Thai DLT Car Registration Dashboard

## Project Overview
This is a Next.js Business Intelligence (BI) dashboard that visualizes Thailand Department of Land Transport (DLT) car registration data. The data is statically generated and fetched via `/data/dashboard_data.json`.

## Current State & Architecture
We have recently overhauled `frontend/src/app/page.tsx` to transition from a basic reporting view into a premium, interactive BI tool.

### Key Features in `page.tsx`:
1. **Bloomberg Terminal Aesthetic:** Dark mode UI utilizing `slate-950` backgrounds, `slate-800` cards, and a primary brand color (teal/amber).
2. **Filter Pills (Multi-Select Popovers):** All filters (Powertrain, Brand, Model, Province) have been upgraded from native `<select>` dropdowns to a custom `FilterPillPopover` component that opens a multi-select checkbox menu with a search bar.
3. **Cascading Filters:** The Model filter dynamically updates its options based on the currently selected Brands.
4. **Drill-Down Pivot Table:** The Leaderboard defaults to grouping by Brand. Clicking a Brand row expands it to reveal the specific Models making up those registration numbers.
5. **Dynamic "Group By" Bar Chart:** The top Top 10 chart has a segmented control allowing the user to instantly toggle between grouping by Brands, Models, or Provinces.

## Pending Implementation (Currently being handled by Gemini)
The user is currently using Gemini to implement two final BI features:
1. **Brand Alias Cleansing:** Normalizing messy data inputs (e.g., `"Deepal+Chang"`, `"Change+Depal"`) into a single, unified `"Deepal + Changan"` brand key via a `BRAND_ALIASES` dictionary at the top of the file.
2. **Trend Chart Grouping (Customer Segments):** Adding a "Group By" toggle to the Trend AreaChart so the user can switch between plotting *Powertrains* (ICE/BEV) and *Vehicle Types* (Passenger Cars/Motorcycles) over time to identify target customer segment trends.

## Rules of Engagement for AI Agents
1. **NO DIRECT CODE EDITS WITHOUT EXPLICIT PERMISSION.** The user reacted extremely negatively to direct file edits in the past. 
2. **Act as an Orchestrator/Architect.** When the user asks for a feature, create an **Implementation Plan** or a **Copy-Paste Prompt** that they can review and paste into Gemini themselves. Only write code directly if the user explicitly says "go ahead" or "Proceed".
3. **Maintain the Aesthetic.** If you are asked to design UI, ensure it looks premium, data-dense, and utilizes the established dark mode color palette. Do not use generic tailwind colors.

## Next Steps
Once the pending Gemini implementations (Brand Aliasing and Trend Grouping) are verified as working, the next phase will likely involve deploying the application to production so it can be accessed on any computer.
