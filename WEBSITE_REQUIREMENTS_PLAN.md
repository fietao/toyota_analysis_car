# Website Requirements — Unfiled Feature Notes

Requirements dropped as loose scratch files at the project root (`BEVpage`,
`Sev_seriesnametable`) before this doc existed. Merged here verbatim from the operator's
original wording — not yet scoped into an implementation plan or checked against what
the `/models` React route (at `frontend/src/app/models/page.tsx`) / the BEV pipeline (`build_BEV.py`) already covers.

## BEV Page

Original note (`BEVpage`, undated):

> The BEV page should be able to select the type of powertrain and also show the trend of
> the powertrain registration in each month, up to date, and able to sort and pick year —
> all, or pick every year — and also showing a type of ชนิดเชื้อเพลิง (fuel type) and how many
> registrations there are. The table should update every month when new data is added to the
> raw file. Able to select the year, province, and type of car — for all months. Each BEV
> page also shows the series and the brand — brand as a head, model as a sub-row. Each year
> has a total, and the current year is shown as YTD. Also has a grand total combining both
> years.

Related note (`Sev_seriesnametable`, undated, incomplete):

> This page will show all the BEV Major powertrain, which is [note cuts off here — original
> file ended mid-sentence].

**Before scoping:** check whether the `/models` React route and `build_BEV.py`'s `BEV Series Name Table` already cover brand→model drill-down, year/province/vehicle-type filters, and YTD+grand-total rollups — several of these may already be shipped.
