"use client";

import { useEffect, useMemo, useState, Fragment } from "react";
import Link from "next/link";
import { Download, RefreshCw, AlertTriangle } from "lucide-react";
import { FilterPillPopover } from "../../components/FilterPillPopover";
import {
  DashboardData,
  BrandNode,
  ModelNode,
  brandTotals,
  brandMonthlyValues,
  seriesTotals,
  seriesMonthlyValues,
  selectDeepDiveFilterOptions,
  modelBrandPairs,
  modelOwnerLookup,
} from "../selectors";

const DATA_BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

type SeriesRow = ModelNode & { totals: { grandTotal: number; ytdTotal: number } };
type BrandRow = Omit<BrandNode, "models"> & {
  toggleKey: string;
  isExpanded: boolean;
  totals: { grandTotal: number; ytdTotal: number };
  models: SeriesRow[];
};

export default function ModelsPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters State
  const [activeYears, setActiveYears] = useState<string[]>([]);
  const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [selectedVehicleTypes, setSelectedVehicleTypes] = useState<string[]>([]);
  const [selectedProvinces, setSelectedProvinces] = useState<string[]>([]);

  const [expandedBrands, setExpandedBrands] = useState<Set<string>>(new Set());

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [exporting, setExporting] = useState(false);

  // Reset page to 1 whenever any filter or active year changes (using render-phase state updates)
  const [prevFilterKey, setPrevFilterKey] = useState("");
  const currentFilterKey = `${selectedBrands.join(",")}|${selectedModels.join(",")}|${selectedProvinces.join(",")}|${selectedVehicleTypes.join(",")}|${activeYears.join(",")}`;
  if (currentFilterKey !== prevFilterKey) {
    setPrevFilterKey(currentFilterKey);
    setCurrentPage(1);
  }

  const loadData = () => {
    setLoading(true);
    setError(null);
    fetch(`${DATA_BASE}/data/dashboard_models.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP error! status: ${r.status}`);
        return r.json();
      })
      .then((j: DashboardData) => {
        setData(j);
        if (j.meta?.years && j.meta.years.length > 0) {
          setActiveYears(j.meta.years.slice(-1).map(String));
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load dashboard_models.json:", err);
        setError("Failed to load dashboard data. Please try again.");
        setLoading(false);
      });
  };

  useEffect(() => {
    fetch(`${DATA_BASE}/data/dashboard_models.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP error! status: ${r.status}`);
        return r.json();
      })
      .then((j: DashboardData) => {
        setData(j);
        if (j.meta?.years && j.meta.years.length > 0) {
          setActiveYears(j.meta.years.slice(-1).map(String));
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load dashboard_models.json:", err);
        setError("Failed to load dashboard data. Please try again.");
        setLoading(false);
      });
  }, []);

  const meta = data?.meta;
  const years = meta?.years ?? [];
  const latestYear = years.length > 0 ? String(years[years.length - 1]) : null;

  // Available filter options based on raw tree data
  const { allBrands, allModels } = useMemo(
    () => selectDeepDiveFilterOptions(data?.brand_model_tree, selectedBrands),
    [data?.brand_model_tree, selectedBrands]
  );

  const handleSelectedBrandsChange = (brands: string[]) => {
    setSelectedBrands(brands);
    const validModels = new Set(selectDeepDiveFilterOptions(data?.brand_model_tree, brands).allModels);
    setSelectedModels((models) => models.filter((model) => validModels.has(model)));
  };

  // Built once per tree load; selection handler does an O(1) lookup instead of re-flattening.
  const modelOwners = useMemo(
    () => modelOwnerLookup(modelBrandPairs(data?.brand_model_tree)),
    [data?.brand_model_tree]
  );

  // Selecting a model whose name belongs to exactly one brand syncs that brand in; a model
  // shared across brands is left alone (no guess).
  const handleSelectedModelsChange = (models: string[]) => {
    const added = models.filter((m) => !selectedModels.includes(m));
    setSelectedModels(models);
    if (added.length === 0) return;
    setSelectedBrands((prev) => {
      const next = new Set(prev);
      added.forEach((m) => { const b = modelOwners.get(m); if (b) next.add(b); });
      return next.size === prev.length ? prev : [...next];
    });
  };

  // Filtered Rows Assembly — brand and series totals come only from segments matching the
  // active Powertrain filter; a brand/series with zero matching units is dropped entirely.
  const filteredTree: BrandRow[] = useMemo(() => {
    if (!data?.brand_model_tree) return [];

    return data.brand_model_tree
      .map((brandNode): BrandRow | null => {
        if (selectedBrands.length > 0 && !selectedBrands.includes(brandNode.brand)) return null;

        const toggleKey = brandNode.brand;
        const isExpanded = expandedBrands.has(toggleKey);

        const bTotals = brandTotals(brandNode, activeYears, latestYear, [], selectedVehicleTypes, selectedProvinces);
        if (bTotals.grandTotal === 0) return null;

        const filteredModels = (brandNode.models || [])
          .map((model): SeriesRow | null => {
            if (selectedModels.length > 0 && !selectedModels.includes(model.name)) return null;
            const mTotals = seriesTotals(model, activeYears, latestYear, [], selectedVehicleTypes, selectedProvinces);
            if (mTotals.grandTotal === 0) return null;
            return { ...model, totals: mTotals };
          })
          .filter((m): m is SeriesRow => m !== null)
          .sort((a, b) => b.totals.grandTotal - a.totals.grandTotal);

        return {
          ...brandNode,
          toggleKey,
          isExpanded,
          totals: bTotals,
          models: filteredModels,
        };
      })
      .filter((b): b is BrandRow => b !== null)
      .sort((a, b) => b.totals.grandTotal - a.totals.grandTotal);
  }, [data, selectedBrands, selectedModels, selectedVehicleTypes, selectedProvinces, activeYears, latestYear, expandedBrands]);

  // Compute Grand Total of all filtered rows
  const superGrandTotal = useMemo(() => {
    return filteredTree.reduce((sum, b) => sum + b.totals.grandTotal, 0);
  }, [filteredTree]);

  // Paginated Rows Assembly
  const paginatedTree = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    return filteredTree.slice(start, end);
  }, [filteredTree, currentPage, pageSize]);

  // Calculate Reference Grand Total of ALL data unfiltered (source totals, ignores every filter)
  const referenceTotal = useMemo(() => {
    if (!data?.brand_model_tree) return 0;
    let sum = 0;
    data.brand_model_tree.forEach((brandNode) => {
      Object.values(brandNode.monthly || {}).forEach((vehicleBucket) => {
        Object.values(vehicleBucket || {}).forEach((provinceBucket) => {
          Object.values(provinceBucket || {}).forEach((arr) => {
            sum += (arr || []).reduce((s, v) => s + (v || 0), 0);
          });
        });
      });
    });
    return sum;
  }, [data]);

  const toggleBrand = (key: string) => {
    setExpandedBrands((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleExportExcel = async () => {
    if (!data || exporting) return;
    setExporting(true);
    try {
      const XLSX = await import("xlsx");

      // Shared with the UI: same selectors, same filter args, so displayed and downloaded
      // totals always match exactly.
      const buildRows = (
        vehicleTypes: string[],
        provinces: string[],
        brandFilter: string[],
        modelFilter: string[]
      ) => {
        const rows: Record<string, string | number>[] = [];
        (data.brand_model_tree || []).forEach((brandNode) => {
          if (brandFilter.length > 0 && !brandFilter.includes(brandNode.brand)) return;
          const bTotals = brandTotals(brandNode, activeYears, latestYear, [], vehicleTypes, provinces);
          if (bTotals.grandTotal === 0) return;

          const bRow: Record<string, string | number> = { "Brand / Model": brandNode.brand };
          activeYears.forEach((year) => {
            const monthly = brandMonthlyValues(brandNode, year, [], vehicleTypes, provinces);
            monthly.forEach((val, mIdx) => { bRow[`${year} ${MONTHS_EN[mIdx]}`] = val || ""; });
            bRow[`${year} Total`] = monthly.reduce((s, v) => s + v, 0) || "";
          });
          bRow["YTD"] = bTotals.ytdTotal || "";
          bRow["Grand Total"] = bTotals.grandTotal || "";
          rows.push(bRow);

          (brandNode.models || []).forEach((model) => {
            if (modelFilter.length > 0 && !modelFilter.includes(model.name)) return;
            const mTotals = seriesTotals(model, activeYears, latestYear, [], vehicleTypes, provinces);
            if (mTotals.grandTotal === 0) return;

            const mRow: Record<string, string | number> = { "Brand / Model": `  ${model.name}` };
            activeYears.forEach((year) => {
              const monthly = seriesMonthlyValues(model, year, [], vehicleTypes, provinces);
              monthly.forEach((val, mIdx) => { mRow[`${year} ${MONTHS_EN[mIdx]}`] = val || ""; });
              mRow[`${year} Total`] = monthly.reduce((s, v) => s + v, 0) || "";
            });
            mRow["YTD"] = mTotals.ytdTotal || "";
            mRow["Grand Total"] = mTotals.grandTotal || "";
            rows.push(mRow);
          });
        });
        return rows;
      };

      // Full sheet: every brand/model, every segment, all vehicle types/provinces — ignores active filters.
      const fullRows = buildRows([], [], [], []);

      // Filtered sheet: the exact same selectors as the table, with the current filter state.
      const filteredRows = buildRows(selectedVehicleTypes, selectedProvinces, selectedBrands, selectedModels);

      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(fullRows), "Full");
      XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(filteredRows), "Filtered");
      XLSX.writeFile(wb, `Thailand_EV_Model_DeepDive.xlsx`);
    } catch (e) {
      console.error(e);
      alert("Excel export failed");
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-950 text-slate-100 min-h-screen p-6" role="status" aria-live="polite">
        <span className="sr-only">Loading Deep-Dive models data…</span>
        <div className="max-w-7xl mx-auto space-y-4" aria-hidden="true">
          <div className="h-20 rounded-md border border-slate-800 bg-slate-900" />
          <div className="h-96 rounded-md border border-slate-800 bg-slate-900" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-slate-950 text-slate-100 min-h-screen flex flex-col items-center justify-center p-6" role="alert" aria-live="assertive">
        <div className="flex flex-col items-center gap-4 bg-slate-900 border border-slate-800 p-6 rounded-md max-w-md text-center">
          <AlertTriangle className="h-10 w-10 text-red-500" />
          <h2 className="text-sm font-semibold text-red-400">Failed to Load Data</h2>
          <p className="text-xs text-slate-400">{error || "Data could not be retrieved."}</p>
          <button onClick={loadData} className="bg-teal-600 hover:bg-teal-500 text-white font-medium text-xs px-4 py-2 rounded-md transition-colors flex items-center gap-1.5 focus:ring-2 focus:ring-teal-400 outline-none">
            <RefreshCw className="h-3 w-3" /> Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-950 text-slate-100 px-4 py-4 md:px-6 min-h-screen select-none font-sans antialiased overflow-x-hidden">
      <div className="w-full max-w-none mx-auto space-y-3">
        {/* Navigation Breadcrumb */}
        <nav aria-label="Breadcrumb" className="flex items-center">
          <Link href="/" className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-teal-400 transition-colors focus:ring-1 focus:ring-teal-400 focus:outline-none rounded px-1 py-0.5">
            <span aria-hidden="true">←</span>
            <span>Back to Dashboard</span>
          </Link>
        </nav>

        {/* Header Section */}
        <div className="bg-slate-900 border border-slate-800 rounded-md p-4 space-y-3">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
            <div>
              <h1 className="text-sm font-semibold text-teal-400 tracking-tight">
                Brand & Model Deep-Dive Matrix
              </h1>
              <p className="text-[10px] text-slate-500 mt-0.5">Thailand Department of Land Transport — Multi-Year Registration Details</p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs bg-slate-950 text-teal-300 font-semibold px-3 py-2 rounded border border-slate-800">
                Data through: {meta?.reporting_period ?? "N/A"}
              </span>
              <span className="text-xs bg-slate-950 text-slate-400 px-3 py-2 rounded border border-slate-800 tabular-nums">
                Reference Grand Total: {referenceTotal.toLocaleString()}
              </span>
              <button
                onClick={handleExportExcel}
                disabled={exporting}
                className="bg-teal-600 hover:bg-teal-500 active:bg-teal-700 text-white text-xs px-4 py-2 rounded-md font-medium transition-colors flex items-center gap-1.5 focus:ring-2 focus:ring-teal-400 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Export all matrices to Excel spreadsheet"
              >
                {exporting ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Exporting...</span>
                  </>
                ) : (
                  <>
                    <Download className="h-3.5 w-3.5" />
                    <span>Export Excel</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Filters Bar */}
          <div className="flex flex-wrap items-end gap-x-5 gap-y-3 text-sm pt-1">
            <div className="min-w-[150px]"><FilterPillPopover label="Brand" placeholder="Search brands..." options={allBrands} value={selectedBrands} onChange={handleSelectedBrandsChange} /></div>
            <div className="min-w-[150px]"><FilterPillPopover label="Model" placeholder="Search models..." options={allModels} value={selectedModels} onChange={handleSelectedModelsChange} /></div>
            <div className="min-w-[170px]"><FilterPillPopover label="Province" placeholder="Search provinces..." options={meta?.provinces ?? []} value={selectedProvinces} onChange={setSelectedProvinces} /></div>
            <div className="min-w-[190px]"><FilterPillPopover label="Vehicle Type" placeholder="Search vehicle types..." options={meta?.vehicle_types_list?.map(v => ({ id: v.code, label: v.label })) ?? []} value={selectedVehicleTypes} onChange={setSelectedVehicleTypes} /></div>

            {/* Year Checklist */}
            <div className="flex flex-col justify-center md:ml-auto">
              <span className="block text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">Active Years (B.E.)</span>
              <div className="flex items-center gap-2 flex-wrap">
                {years.map((y) => {
                  const yStr = String(y);
                  const isChecked = activeYears.includes(yStr);
                  return (
                    <label key={yStr} className={`flex items-center gap-1 cursor-pointer text-xs font-semibold px-2 py-1 rounded border transition-colors ${isChecked ? "bg-teal-650/20 text-teal-400 border-teal-550/40" : "bg-slate-800 border-slate-700 text-slate-400"}`}>
                      <input
                        type="checkbox"
                        className="sr-only"
                        checked={isChecked}
                        onChange={() => {
                          if (isChecked) setActiveYears(activeYears.filter(x => x !== yStr));
                          else setActiveYears([...activeYears, yStr].sort());
                        }}
                      />
                      <span>{yStr}{yStr === latestYear ? " (YTD)" : ""}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Pivot/Matrix Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-md overflow-hidden">
          <div className="overflow-x-auto overflow-y-auto custom-scrollbar max-h-[calc(100vh-18rem)] min-h-[360px]">
            <table className="min-w-full w-max text-left border-collapse text-xs whitespace-nowrap">
              <thead>
                <tr className="bg-slate-800/80 border-b border-slate-700 text-slate-300 font-semibold align-middle">
                  <th scope="col" className="px-3 py-2.5 min-w-[220px] sticky top-0 left-0 bg-slate-800 z-40 border-r border-slate-700">Brand / Model</th>

                  {activeYears.map((year) => (
                    <Fragment key={year}>
                      {MONTHS_EN.map((m) => (
                        <th key={`${year}-${m}`} scope="col" className="px-2 py-2.5 border-l border-slate-700/60 text-center font-normal text-slate-400 min-w-[64px] sticky top-0 bg-slate-800 z-30">{m}</th>
                      ))}
                      <th scope="col" className="px-3 py-2.5 border-l-2 border-slate-600 bg-slate-800 text-center font-bold text-teal-300 min-w-[110px] sticky top-0 z-30">Total {year}</th>
                    </Fragment>
                  ))}

                  <th scope="col" className="px-3 py-2.5 border-l-2 border-slate-600 text-right text-emerald-400 font-bold bg-slate-800 min-w-[110px] sticky top-0 z-30">YTD</th>
                  <th scope="col" className="px-3 py-2.5 border-l border-slate-600 text-right text-amber-400 font-bold bg-slate-800 min-w-[120px] sticky top-0 z-30">Grand Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {filteredTree.length === 0 ? (
                  <tr>
                    <td colSpan={40} className="p-12 text-center text-slate-500 font-medium">
                      No matching brand or model registrations found for current selection.
                    </td>
                  </tr>
                ) : (
                  paginatedTree.map((brandNode) => (
                    <Fragment key={brandNode.toggleKey}>
                      {/* Brand Row */}
                      <tr
                        className="bg-slate-900/95 hover:bg-slate-850 font-semibold border-b border-slate-800/90 transition-colors"
                      >
                        <td className="px-3 py-2.5 sticky left-0 bg-slate-900 z-10 border-r border-slate-800/90">
                          <button
                            type="button"
                            onClick={() => toggleBrand(brandNode.toggleKey)}
                            aria-expanded={brandNode.isExpanded}
                            aria-label={`${brandNode.isExpanded ? "Collapse" : "Expand"} ${brandNode.brand} models`}
                            className="flex w-full items-center space-x-2 text-left text-teal-400"
                          >
                            <span aria-hidden="true" className="text-[10px] bg-slate-800 px-1 py-0.5 rounded text-slate-400">
                              {brandNode.isExpanded ? "▼" : "▶"}
                            </span>
                            <span className="font-bold text-xs tracking-wide">{brandNode.brand}</span>
                          </button>
                        </td>

                        {activeYears.map((year) => {
                          const monthly = brandMonthlyValues(brandNode, year, [], selectedVehicleTypes, selectedProvinces);
                          const total = monthly.reduce((s, v) => s + v, 0);
                          return (
                            <Fragment key={year}>
                              {monthly.map((val, idx) => (
                                <td key={`brand-val-${brandNode.toggleKey}-${year}-${idx}`} className="px-2 py-2.5 border-l border-slate-800/70 text-center font-mono text-slate-300">
                                  {val ? val.toLocaleString() : "—"}
                                </td>
                              ))}
                              <td className="px-3 py-2.5 border-l-2 border-slate-700/80 bg-slate-800/30 text-center font-mono font-bold text-teal-400">
                                {total ? total.toLocaleString() : "—"}
                              </td>
                            </Fragment>
                          );
                        })}

                        <td className="px-3 py-2.5 border-l-2 border-slate-800 text-right font-mono font-bold text-emerald-400 bg-emerald-950/10">
                          {brandNode.totals.ytdTotal ? brandNode.totals.ytdTotal.toLocaleString() : "—"}
                        </td>
                        <td className="px-3 py-2.5 border-l border-slate-800 text-right font-mono font-bold text-amber-400 bg-slate-950">
                          {brandNode.totals.grandTotal ? brandNode.totals.grandTotal.toLocaleString() : "—"}
                        </td>
                      </tr>

                      {/* Series (Model) Rows */}
                      {brandNode.isExpanded && brandNode.models.map((model) => (
                        <tr
                          key={`${brandNode.toggleKey}-${model.name}`}
                          className="bg-slate-950/50 hover:bg-slate-900/60 border-b border-slate-900/60 text-slate-300 transition-colors"
                        >
                          <td className="py-2.5 pl-8 pr-3 sticky left-0 bg-slate-950/90 z-10 border-r border-slate-900/60">
                            <div className="flex items-center space-x-1.5">
                              <span aria-hidden="true" className="w-1.5 h-1.5 rounded-full bg-slate-600 flex-shrink-0"></span>
                              <span className="font-medium text-slate-200 text-xs">{model.name}</span>
                            </div>
                          </td>

                          {activeYears.map((year) => {
                            const monthly = seriesMonthlyValues(model, year, [], selectedVehicleTypes, selectedProvinces);
                            const total = monthly.reduce((s, v) => s + v, 0);
                            return (
                              <Fragment key={year}>
                                {monthly.map((val, idx) => (
                                  <td key={`mod-val-${brandNode.toggleKey}-${model.name}-${year}-${idx}`} className="px-2 py-2.5 border-l border-slate-800/30 text-center font-mono text-slate-400/90">
                                    {val ? val.toLocaleString() : "—"}
                                  </td>
                                ))}
                                <td className="px-3 py-2.5 border-l-2 border-slate-800/50 bg-slate-950/30 text-center font-mono text-slate-300">
                                  {total ? total.toLocaleString() : "—"}
                                </td>
                              </Fragment>
                            );
                          })}

                          <td className="px-3 py-2.5 border-l-2 border-slate-900 text-right font-mono text-emerald-500">
                            {model.totals.ytdTotal ? model.totals.ytdTotal.toLocaleString() : "—"}
                          </td>
                          <td className="px-3 py-2.5 border-l border-slate-900 text-right font-mono font-bold text-amber-500/90 bg-slate-950/50">
                            {model.totals.grandTotal ? model.totals.grandTotal.toLocaleString() : "—"}
                          </td>
                        </tr>
                      ))}
                    </Fragment>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {filteredTree.length > 0 && (
            <div className="bg-slate-900 px-5 py-3 border-t border-slate-800 flex flex-col sm:flex-row justify-between items-center gap-3 text-xs text-slate-400">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5">
                  <span>Show</span>
                  <select
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(Number(e.target.value));
                      setCurrentPage(1);
                    }}
                    className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-100 font-semibold focus:outline-none focus:border-teal-500"
                  >
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                  <span>brands per page</span>
                </div>
                <span>
                  Showing {Math.min(filteredTree.length, (currentPage - 1) * pageSize + 1)}-{Math.min(filteredTree.length, currentPage * pageSize)} of {filteredTree.length} brands
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:hover:bg-slate-800 text-slate-100 px-3 py-1.5 rounded transition-colors disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="font-semibold text-slate-200 px-1">
                  Page {currentPage} of {Math.ceil(filteredTree.length / pageSize) || 1}
                </span>
                <button
                  onClick={() => setCurrentPage(prev => Math.min(Math.ceil(filteredTree.length / pageSize), prev + 1))}
                  disabled={currentPage >= Math.ceil(filteredTree.length / pageSize)}
                  className="bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:hover:bg-slate-800 text-slate-100 px-3 py-1.5 rounded transition-colors disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}

          {/* Table Footer / Summary Row */}
          <div className="bg-slate-950 p-5 border-t border-slate-800 flex justify-between items-center text-xs font-bold text-slate-300">
            <span>Filtered Grand Total registrations:</span>
            <span className="text-slate-100 text-xs font-mono tabular-nums text-right">
              {superGrandTotal.toLocaleString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
