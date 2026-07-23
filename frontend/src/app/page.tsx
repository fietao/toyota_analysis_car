"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  RefreshCw,
  Filter,
  Layers,
  Trophy,
  PieChart as PieChartIcon,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  DashboardData, Rec, BrandNode,
  selectFilterOptions,
  selectTrendData,
  selectRankingsData,
  selectBrandRankingsFromMonthly,
  selectDynamicChartData,
  selectDynamicChartDataFromMonthly,
  selectProvinceAnalysisData,
  modelBrandPairs,
  modelOwnerLookup
} from "./selectors";
import { FilterPillPopover } from "../components/FilterPillPopover";

const DATA_BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

/* ── Palette & constants ─────────────────────────────────────────────── */

const BRAND_COLOR = "#169387";
const PT_COLORS: Record<string, string> = {
  ICE: "#64748b", BEV: BRAND_COLOR, HEV: "#fbbf24", PHEV: "#fb923c"
};
const RANK_COLORS = ["#0f6e65", "#169387", "#21b0a2", "#42d4c6", "#6ceae0",
  "#96fcf5", "#e879f9", "#f472b6", "#fb7185", "#fbbf24", "#38bdf8", "#818cf8", "#c084fc", "#f472b6", "#fb7185"];

const TT = {
  contentStyle: {
    backgroundColor: "#0f172a", border: "1px solid #1e293b",
    borderRadius: "2px", color: "#f1f5f9", fontSize: "11px",
    padding: "8px"
  },
  itemStyle: { color: "#94a3b8" },
  cursor: { fill: "rgba(255,255,255,0.05)" }
};

/* ── Helpers ──────────────────────────────────────────────────────── */

const fmt = (n: unknown) => {
  const v = Number(n);
  if (v === 0) return "—";
  return isNaN(v) ? "—" : v.toLocaleString();
};

/* ── Components ───────────────────────────────────────────────────── */

function Card({ title, children, className = "" }: { title?: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-sm border border-slate-800 bg-slate-900 p-4 ${className}`}>
      {title && (
        <h2 className="mb-4 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          {title}
        </h2>
      )}
      {children}
    </div>
  );
}

function MetricCard({ title, value, subtitle }: { title: string; value: string | number; subtitle?: string }) {
  return (
    <Card className="flex flex-col justify-center border-t-2 border-t-brand-light/30 h-24">
      <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{title}</div>
      <div className="mt-1 font-mono text-xs font-semibold tracking-tight tabular-nums text-slate-100 truncate" title={String(value)}>{value}</div>
      {subtitle && <div className="mt-1 text-xs text-brand-light font-medium">{subtitle}</div>}
    </Card>
  );
}


function DataTable({ columns, rows, onToggleRow, highlightFirst = false }: {
  columns: { key: string; label: string; align?: string }[];
  rows: Rec[];
  onToggleRow?: (id: string) => void;
  highlightFirst?: boolean;
}) {
  const [sortConfig, setSortConfig] = useState<{ key: string, direction: 'asc' | 'desc' } | null>(null);

  const sortedRows = useMemo(() => {
    // If we are using hierarchical rows, sorting can break the parent-child relationship
    // For a Pivot Table, we only sort the parent rows, and then sort the children within.
    // To make this simple, if we are grouping, we should ideally sort before passing to DataTable.
    // We will do a generic sort that keeps sub-rows attached to their parents if we implement it, 
    // but the instruction implies clicking the header sorts the rows.
    // If rows are already a mix of parents and subRows, sorting them flatly will detach models from brands.
    // Therefore, we must implement grouped sorting.
    const sortableItems = [...rows];
    if (sortConfig !== null) {
      // Split into parents and children mapping
      const parents = sortableItems.filter(r => !r.isSubRow);
      const childrenMap = new Map<string, Rec[]>();
      sortableItems.filter(r => r.isSubRow).forEach(r => {
         const pId = String(r.parentId);
         if (!childrenMap.has(pId)) childrenMap.set(pId, []);
         childrenMap.get(pId)!.push(r);
      });

      const sortFn = (a: Rec, b: Rec) => {
        const aVal = a[sortConfig.key];
        const bVal = b[sortConfig.key];
        if (aVal === bVal) return 0;
        if (aVal == null) return sortConfig.direction === 'asc' ? -1 : 1;
        if (bVal == null) return sortConfig.direction === 'asc' ? 1 : -1;
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
        }
        const aStr = String(aVal).toLowerCase();
        const bStr = String(bVal).toLowerCase();
        if (aStr < bStr) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aStr > bStr) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      };

      parents.sort(sortFn);
      
      const flattened: Rec[] = [];
      parents.forEach(p => {
         flattened.push(p);
         if (childrenMap.has(String(p.id))) {
            const children = childrenMap.get(String(p.id))!;
            children.sort(sortFn);
            flattened.push(...children);
         }
      });
      return flattened;
    }
    return sortableItems;
  }, [rows, sortConfig]);

  const requestSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'desc'; 
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfig({ key, direction });
  };

  return (
    <div className="overflow-x-auto custom-scrollbar">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-slate-700">
            {columns.map((c) => (
              <th 
                key={c.key} 
                onClick={() => requestSort(c.key)}
                className={`whitespace-nowrap px-2 py-1.5 font-medium text-slate-400 cursor-pointer hover:text-slate-200 select-none ${c.align === "left" ? "text-left" : "text-right"}`}
              >
                <div className={`flex items-center gap-1 ${c.align === "left" ? "justify-start" : "justify-end"}`}>
                  {c.label}
                  {sortConfig?.key === c.key ? (
                    <span className="text-[10px] text-brand-light">{sortConfig.direction === 'asc' ? '▲' : '▼'}</span>
                  ) : (
                    <span className="text-[10px] text-transparent group-hover:text-slate-600">▼</span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/50">
          {sortedRows.map((row, i) => (
            <tr key={i} className={`group ${highlightFirst && i === sortedRows.length - 1 ? "bg-slate-800 font-semibold text-brand-light" : (row.isSubRow ? "bg-slate-900/40 hover:bg-slate-800" : "hover:bg-slate-800 text-slate-300")}`}>
              {columns.map((c) => {
                const isNameCol = c.key === "name" || c.key === "brand";
                const val = row[c.key];
                const content = c.align === "left" || typeof val === "string" ? String(val ?? "") : fmt(val);
                
                return (
                  <td key={c.key} className={`whitespace-nowrap px-2 py-1.5 tabular-nums ${c.align === "left" ? "text-left" : "text-right"}`}>
                    {isNameCol ? (
                      <div className="flex items-center gap-2" style={{ paddingLeft: row.isSubRow ? '1.5rem' : '0' }}>
                        {row.hasChildren && onToggleRow ? (
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); onToggleRow(String(row.id)); }}
                            aria-expanded={!!row.isExpanded}
                            aria-label={`${row.isExpanded ? "Collapse" : "Expand"} ${row.name} models`}
                            className="flex h-4 w-4 items-center justify-center rounded-sm bg-slate-800 text-slate-400 hover:bg-brand-primary hover:text-white transition-colors"
                          >
                            <span aria-hidden="true">{row.isExpanded ? "▼" : "▶"}</span>
                          </button>
                        ) : (
                          !row.isSubRow && <div className="w-4" />
                        )}
                        {row.isSubRow && <div className="h-[1px] w-3 bg-slate-700" />}
                        <span className={row.isSubRow ? "text-slate-400" : "font-medium"}>{content}</span>
                      </div>
                    ) : (
                      <span className={row.isSubRow ? "text-slate-400" : ""}>{content}</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TopBarChart({ data, nameKey, title }: { data: Rec[], nameKey: string, title: string }) {
  return (
    <Card title={title} className="flex-1">
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 12, left: 8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="2 4" stroke="#1e293b" horizontal={false} />
            <XAxis type="number" stroke="#334155" tick={{ fill: "#64748b", fontSize: 10 }} tickFormatter={(v: number) => (v / 1000).toFixed(0) + "k"} />
            <YAxis dataKey={nameKey} type="category" width={110} stroke="#334155" tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <Tooltip {...TT} formatter={(v: unknown) => Number(v).toLocaleString()} />
            <Bar dataKey="YTD" radius={[0, 2, 2, 0]} barSize={12} isAnimationActive={false}>
              {data.map((_, i) => <Cell key={i} fill={RANK_COLORS[i % RANK_COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

/* ── Main Dashboard ───────────────────────────────────────────────── */


export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("rankings");
  const [selectedYear, setSelectedYear] = useState<number | "All">("All");
  const [selectedVehicleTypes, setSelectedVehicleTypes] = useState<string[]>([]);

  // Filter Pills (Arrays)
  const [rankingPt, setRankingPt] = useState<string[]>([]);
  const [rankingBrand, setRankingBrand] = useState<string[]>([]);
  const [rankingModel, setRankingModel] = useState<string[]>([]);
  const [rankingProvince, setRankingProvince] = useState<string[]>([]);

  // Expandable Table state
  const [expandedBrands, setExpandedBrands] = useState<Set<string>>(new Set());

  // Dynamic Chart Grouping state
  const [chartGroupBy, setChartGroupBy] = useState<"Brands" | "Models" | "Provinces">("Brands");
  const [trendGroupBy, setTrendGroupBy] = useState<"Powertrain" | "Vehicle Type">("Powertrain");

  // Trend Province Performance state
  const [trendProvBrand, setTrendProvBrand] = useState<string>("");
  const [trendProvModel, setTrendProvModel] = useState<string>("");

  // Model/brand tree (dashboard_models.json) is heavy and fetched lazily —
  // only once a tab that needs brand/model drill-down is active.
  const [brandModelTree, setBrandModelTree] = useState<BrandNode[] | null>(null);
  const modelsStatus = useRef<"idle" | "loading" | "loaded">("idle");
  const [modelsError, setModelsError] = useState<string | null>(null);
  
  const ensureModels = useCallback(() => {
    if (modelsStatus.current !== "idle") return;
    modelsStatus.current = "loading";
    setModelsError(null);
    fetch(`${DATA_BASE}/data/dashboard_models.json`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load models data");
        return r.json();
      })
      .then((models) => {
        modelsStatus.current = "loaded";
        setBrandModelTree(models.brand_model_tree);
      })
      .catch((err) => {
        console.error("Error loading model details:", err);
        modelsStatus.current = "idle";
        setModelsError("Failed to load brand/model data. Rankings and province breakdowns may be incomplete.");
      });
  }, []);

  useEffect(() => {
    fetch(`${DATA_BASE}/data/dashboard_summary.json`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load summary data");
        return r.json();
      })
      .then((summary: DashboardData) => {
        setData(summary);
        if (summary.meta?.years?.length > 0) {
          setSelectedYear(summary.meta.years[summary.meta.years.length - 1]);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error loading summary:", err);
        setError("Failed to load dashboard summary data.");
        setLoading(false);
      });
  }, []);

  const years = data?.meta?.years ?? [];
  const months = data?.meta?.months ?? [];
  const allDataProvinces = data?.meta?.provinces ?? [];
  const { allDataBrands, allDataModels } = useMemo(
    () => selectFilterOptions(data, rankingBrand, brandModelTree),
    [data, rankingBrand, brandModelTree]
  );


  // Clear stale selected models if they are no longer in the cascading `allDataModels` list
  useEffect(() => {
    if (rankingModel.length > 0) {
      const validModels = rankingModel.filter(m => allDataModels.includes(m));
      if (validModels.length !== rankingModel.length) {
        const timer = setTimeout(() => {
          setRankingModel(validModels);
        }, 0);
        return () => clearTimeout(timer);
      }
    }
  }, [allDataModels, rankingModel]);

  // Rebuilt only when the lazy tree loads, not on every model pick.
  const modelOwners = useMemo(
    () => modelOwnerLookup(modelBrandPairs(brandModelTree ?? undefined)),
    [brandModelTree]
  );

  // Selecting a model owned by exactly one brand syncs that brand in; a model shared across
  // brands is left alone (no guess). Needs the tree, so ensure it's loading.
  const handleRankingModelChange = (models: string[]) => {
    const added = models.filter((m) => !rankingModel.includes(m));
    setRankingModel(models);
    if (added.length === 0) return;
    ensureModels();
    setRankingBrand((prev) => {
      const next = new Set(prev);
      added.forEach((m) => { const b = modelOwners.get(m); if (b) next.add(b); });
      return next.size === prev.length ? prev : [...next];
    });
  };

  const timeCols = selectedYear === "All" 
    ? years.map(y => ({ key: String(y), label: String(y) }))
    : months.map(m => ({ key: m, label: m }));
  
  const timeKeys = selectedYear === "All" ? years.map(String) : months;

  // -- Powertrain Overview Engine (fuel_monthly) --
  const { trendKeys, trendData, trendTable } = useMemo(
    () => selectTrendData(data, selectedYear, selectedVehicleTypes, trendGroupBy, timeKeys),
    [data, selectedYear, selectedVehicleTypes, trendGroupBy, timeKeys]
  );


  // -- Drill-Down Rankings Engine (DataTable) --
  // Model drill-down and province filtering need brand_model_tree (lazy-loaded); until it's
  // loaded and neither is in play, rank by brand alone from the already-loaded brand_monthly.
  const rankingsData = useMemo(() => {
    if (activeTab !== "rankings") {
      return { rows: [], totalUnits: 0, bevUnits: 0, ptMix: [] };
    }
    if (brandModelTree) {
      return selectRankingsData(data, rankingPt, rankingBrand, rankingModel, rankingProvince, expandedBrands, selectedYear, selectedVehicleTypes, timeKeys, brandModelTree);
    }
    if (rankingProvince.length > 0 || rankingModel.length > 0) {
      return { rows: [], totalUnits: 0, bevUnits: 0, ptMix: [] }; // awaiting model/province data
    }
    return selectBrandRankingsFromMonthly(data, rankingPt, rankingBrand, expandedBrands, selectedYear, selectedVehicleTypes, timeKeys);
  }, [data, rankingPt, rankingBrand, rankingModel, rankingProvince, expandedBrands, selectedYear, selectedVehicleTypes, timeKeys, brandModelTree, activeTab]);

  // -- Dynamic Group By Engine (Charts) --
  const dynamicChartData = useMemo(() => {
    if (activeTab !== "rankings") return [];
    if (chartGroupBy === "Brands" && rankingProvince.length === 0 && rankingModel.length === 0) {
      return selectDynamicChartDataFromMonthly(data, rankingPt, rankingBrand, selectedYear, selectedVehicleTypes);
    }
    if (brandModelTree) {
      return selectDynamicChartData(data, chartGroupBy, rankingPt, rankingBrand, rankingModel, rankingProvince, selectedYear, selectedVehicleTypes, brandModelTree);
    }
    if (chartGroupBy !== "Brands") return []; // awaiting model/province data
    return selectDynamicChartDataFromMonthly(data, rankingPt, rankingBrand, selectedYear, selectedVehicleTypes);
  }, [data, chartGroupBy, rankingPt, rankingBrand, rankingModel, rankingProvince, selectedYear, selectedVehicleTypes, brandModelTree, activeTab]);


  const toggleBrandExpand = (brandId: string) => {
     ensureModels(); // expanding a brand row needs model-level data
     setExpandedBrands(prev => {
        const next = new Set(prev);
        if (next.has(brandId)) next.delete(brandId);
        else next.add(brandId);
        return next;
     });
  };

  const { rows: rankedRows, totalUnits: rankTotal, bevUnits: rankBev, ptMix: rankPtMix } = rankingsData;
  const bevPenetration = rankTotal > 0 ? ((rankBev / rankTotal) * 100).toFixed(1) + "%" : "0%";
  const topBrand = rankedRows[0] ? rankedRows[0]["name"] : "—";

  const rankingsCols = [ 
     { key: "name", label: "Brand / Model", align: "left" }, 
     ...timeCols, 
     { key: "YTD", label: "Grand Total" } 
  ];

  // -- Province Analysis Engine --
  const provinceAnalysisData = useMemo(() => {
    if (activeTab !== "powertrain") return [];
    return selectProvinceAnalysisData(data, trendProvBrand, trendProvModel, selectedVehicleTypes, selectedYear, brandModelTree);
  }, [data, trendProvBrand, trendProvModel, selectedVehicleTypes, selectedYear, brandModelTree, activeTab]);

  const topProvinces = useMemo(() => {
    if (!trendProvBrand) return [...provinceAnalysisData].sort((a,b)=>b.totalProvVol-a.totalProvVol);
    return provinceAnalysisData
       .filter(p => p.selectedVol > 0 && !["Weak Spot", "Possible Gap", "Low Demand"].includes(p.status))
       .sort((a, b) => (b.selectedVol - a.selectedVol) || (b.share - a.share));
  }, [provinceAnalysisData, trendProvBrand]);

  const weakProvinces = useMemo(() => {
    return provinceAnalysisData
       .filter(p => ["Weak Spot", "Possible Gap", "Low Demand"].includes(p.status))
       .sort((a, b) => (b.totalProvVol - a.totalProvVol) || (a.share - b.share) || (a.selectedVol - b.selectedVol));
  }, [provinceAnalysisData]);

  if (loading) return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-200 md:flex-row font-sans" role="status" aria-live="polite">
      <span className="sr-only">Loading dashboard…</span>
      <aside className="w-full border-b border-slate-800 bg-slate-950 md:h-screen md:w-56 md:border-b-0 md:border-r" aria-hidden="true" />
      <main className="flex-1 space-y-4 p-4 md:space-y-6 md:p-6" aria-hidden="true">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 rounded-sm border border-slate-800 bg-slate-900" />
          ))}
        </div>
        <div className="h-64 rounded-sm border border-slate-800 bg-slate-900" />
      </main>
    </div>
  );

  if (error || !data) {
    return (
      <div className="bg-slate-950 text-slate-100 min-h-screen flex flex-col items-center justify-center p-6" role="alert" aria-live="assertive">
        <div className="flex flex-col items-center gap-4 bg-slate-900 border border-slate-800 p-6 rounded-md max-w-md text-center">
          <AlertTriangle className="h-10 w-10 text-red-500" />
          <h2 className="text-sm font-semibold text-red-400">Failed to Load Dashboard</h2>
          <p className="text-xs text-slate-400">{error || "Data could not be loaded."}</p>
          <button onClick={() => window.location.reload()} className="bg-teal-600 hover:bg-teal-500 text-white font-medium text-xs px-4 py-2 rounded-md transition-colors flex items-center gap-1.5 focus:ring-2 focus:ring-teal-400 outline-none">
            <RefreshCw className="h-3 w-3" /> Reload
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: "rankings", label: "Rankings & Leaderboards", icon: Trophy },
    { id: "powertrain", label: "Powertrain & Fuel Type", icon: PieChartIcon },
    { id: "report", label: "Manual Report Mode", icon: Trophy, href: "/report" },
    { id: "deep-dive", label: "Brand & Model Deep-Dive", icon: Layers, href: "/models" },
    { id: "analyst", label: "Analyst Table", icon: Layers, href: "/analyst" },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-200 md:flex-row font-sans">
      
      {/* ── Sidebar Navigation ────────────────────────────────────── */}
      <aside className="sticky top-0 z-20 flex w-full flex-col border-b border-slate-800 bg-slate-950 md:h-screen md:w-56 md:border-b-0 md:border-r">
        <div className="flex flex-col gap-2 p-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.png" alt="Eternity@One Logo" className="h-6 w-6 object-contain" />
            <h1 className="text-sm font-bold tracking-tight text-brand-light uppercase">EV Analytics</h1>
          </div>
          
          <div className="mt-4 flex flex-col gap-2">
            <div className="flex items-center gap-2 rounded-sm border border-slate-800 bg-slate-900 p-1.5 focus-within:border-brand-primary">
              <Filter className="h-3 w-3 text-slate-400 ml-1" />
              <select 
                className="w-full bg-transparent text-xs font-semibold text-slate-200 outline-none"
                value={selectedYear}
                onChange={(e) => setSelectedYear(e.target.value === "All" ? "All" : Number(e.target.value))}
              >
                <option value="All" className="bg-slate-900">
                  All Years {years.length > 0 ? `(${years[0]}-${years[years.length - 1]})` : ""}
                </option>
                {years.slice().reverse().map(y => (
                  <option key={y} value={y} className="bg-slate-900">Year {y}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <nav className="flex flex-row overflow-x-auto p-2 scrollbar-hide md:flex-col md:gap-0.5 md:p-2">
          {tabs.map((t) => {
            const isActive = activeTab === t.id;
            const Icon = t.icon;
            if ("href" in t) {
              return (
                <Link key={t.id} href={t.href as string}
                  className="flex min-w-max items-center gap-2.5 rounded-sm px-2.5 py-2 text-xs font-medium text-slate-400 transition-colors hover:bg-slate-900 hover:text-slate-200">
                  <Icon className="h-3.5 w-3.5 text-slate-500" />
                  <span>{t.label}</span>
                </Link>
              );
            }
            return (
              <button key={t.id} onClick={() => setActiveTab(t.id)}
                className={`flex min-w-max items-center gap-2.5 rounded-sm px-2.5 py-2 text-xs font-medium transition-colors ${
                  isActive ? "bg-slate-800 text-brand-light" : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                }`}>
                <Icon className={`h-3.5 w-3.5 ${isActive ? "text-brand-light" : "text-slate-500"}`} />
                <span>{t.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      {/* ── Main Content Area ─────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">
        <header className="sticky top-0 z-10 hidden border-b border-slate-800 bg-slate-950 px-6 py-4 md:block">
          <div className="flex items-center gap-8 text-sm">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Selected Year</p>
              <p className="mt-1 font-mono text-xs font-semibold tracking-tight tabular-nums text-slate-100">{selectedYear}</p>
            </div>
            {selectedVehicleTypes.length > 0 && selectedVehicleTypes.length < (data?.meta?.vehicle_types_list?.length || 0) && (
              <>
                <div className="h-8 w-px bg-slate-800" />
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-amber-500">Vehicle Types Active</p>
                  <p className="mt-1 font-mono text-xs font-semibold tracking-tight tabular-nums text-slate-100">
                    {selectedVehicleTypes.length} <span className="text-sm text-slate-500 font-sans font-normal">of {data?.meta?.vehicle_types_list?.length || 0}</span>
                  </p>
                </div>
              </>
            )}
          </div>
        </header>

        <div className="p-4 md:p-6">
          {modelsError && (
            <div role="alert" className="mb-4 flex items-center justify-between gap-3 rounded-sm border border-red-900/60 bg-red-950/30 px-3 py-2 text-xs text-red-300">
              <span className="flex items-center gap-2"><AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" /> {modelsError}</span>
              <button
                type="button"
                onClick={ensureModels}
                className="flex items-center gap-1 rounded-sm border border-red-800/60 px-2 py-1 font-medium text-red-200 hover:bg-red-900/40 transition-colors"
              >
                <RefreshCw className="h-3 w-3" /> Retry
              </button>
            </div>
          )}
          {/* Vehicle Type Global Filter */}
          <div className="mb-4 md:mb-6 flex flex-wrap items-center gap-2">
            <FilterPillPopover 
              label="Global Vehicle Types" 
              placeholder="Search vehicle types..." 
              options={data?.meta?.vehicle_types_list?.map(v => ({ id: v.code, label: v.label })) || []} 
              value={selectedVehicleTypes} 
              onChange={setSelectedVehicleTypes} 
            />
          </div>

          <div className="space-y-4 md:space-y-6">
            
            {/* ── Rankings & Leaderboards ─────────────────────────────── */}
            {activeTab === "rankings" && (<>
              
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard title="Total Units" value={rankTotal.toLocaleString()} />
                <MetricCard title="BEV Units" value={rankBev.toLocaleString()} />
                <MetricCard title="BEV Penetration" value={bevPenetration} />
                <MetricCard title={`Top Brand`} value={String(topBrand)} />
              </div>

              {/* Filter Pills */}
              <div className="flex flex-wrap gap-2 items-center bg-slate-900 border border-slate-800 rounded-sm p-3">
                <FilterPillPopover label="Powertrain" placeholder="Powertrains" options={["ICE", "BEV", "HEV", "PHEV"]} value={rankingPt} onChange={setRankingPt} />
                <FilterPillPopover label="Brand" placeholder="Brands" options={allDataBrands} value={rankingBrand} onChange={setRankingBrand} />
                <FilterPillPopover label="Model" placeholder="Models" options={allDataModels} value={rankingModel} onChange={handleRankingModelChange} onOpen={ensureModels} />
                <FilterPillPopover label="Province" placeholder="Provinces" options={allDataProvinces} value={rankingProvince} onChange={setRankingProvince} onOpen={ensureModels} />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
                <div className="lg:col-span-2 flex flex-col gap-2">
                  {/* Segmented Control for Dynamic Chart Grouping */}
                  <div className="flex items-center gap-1 self-start rounded-full border border-slate-700 bg-slate-800 p-0.5">
                     {(["Brands", "Models", "Provinces"] as const).map(opt => (
                        <button
                           key={opt}
                           onClick={() => { setChartGroupBy(opt); if (opt !== "Brands") ensureModels(); }}
                           className={`px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full transition-colors ${
                              chartGroupBy === opt ? "bg-brand-primary text-white" : "text-slate-400 hover:text-slate-200"
                           }`}
                        >
                           {opt}
                        </button>
                     ))}
                  </div>
                  <TopBarChart title={`Top 10 by ${chartGroupBy}`} data={dynamicChartData} nameKey="name" />
                </div>
                <div>
                  <div className="h-8 mb-2"></div> {/* Spacer to align with chart */}
                  <Card title="Powertrain Mix">
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={rankPtMix} cx="50%" cy="50%" innerRadius="60%" outerRadius="80%" paddingAngle={1} dataKey="YTD" stroke="none" nameKey="name" isAnimationActive={false}>
                            {rankPtMix.map((e) => <Cell key={String(e.name)} fill={PT_COLORS[String(e.name)] ?? "#64748b"} />)}
                          </Pie>
                          <Tooltip {...TT} formatter={(v: unknown) => Number(v).toLocaleString()} />
                          <Legend verticalAlign="bottom" height={20} iconType="square" wrapperStyle={{ fontSize: "10px", color: "#94a3b8" }} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </Card>
                </div>
              </div>

              <Card title={`Pivot Leaderboard (Click Brand to Drill-Down)`}>
                <DataTable columns={rankingsCols} rows={rankedRows} onToggleRow={toggleBrandExpand} />
              </Card>

            </>)}


            {/* ── Powertrain & Fuel Type Tab ───────────────── */}
            {activeTab === "powertrain" && (<>
              <div className="flex items-center gap-1 mb-4 self-start rounded-full border border-slate-700 bg-slate-800 p-0.5 inline-flex">
                 {(["Powertrain", "Vehicle Type"] as const).map(opt => (
                    <button
                       key={opt}
                       onClick={() => setTrendGroupBy(opt)}
                       className={`px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full transition-colors ${
                          trendGroupBy === opt ? "bg-brand-primary text-white" : "text-slate-400 hover:text-slate-200"
                       }`}
                    >
                       Trend Grouping: {opt}
                    </button>
                 ))}
              </div>

              <Card title={`Trend — ${selectedYear}`}>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={trendData} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
                      <defs>
                        {trendKeys.map((key, i) => {
                          const color = trendGroupBy === "Powertrain" ? PT_COLORS[key] : RANK_COLORS[i % RANK_COLORS.length];
                          return (
                            <linearGradient key={`grad-${key}`} id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor={color} stopOpacity={0.2}/>
                              <stop offset="95%" stopColor={color} stopOpacity={0}/>
                            </linearGradient>
                          );
                        })}
                      </defs>
                      <CartesianGrid strokeDasharray="1 3" stroke="#1e293b" vertical={false} />
                      <XAxis dataKey="name" stroke="#334155" tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} />
                      <YAxis stroke="#334155" tick={{ fill: "#64748b", fontSize: 10 }} tickFormatter={(v) => (v/1000).toFixed(0)+"k"} tickLine={false} axisLine={false} />
                      <Tooltip {...TT} formatter={(v: unknown) => Number(v).toLocaleString()} />
                      <Legend verticalAlign="top" height={20} iconType="square" wrapperStyle={{ fontSize: "10px", color: "#94a3b8" }} />
                      {trendKeys.map((key, i) => {
                        const color = trendGroupBy === "Powertrain" ? PT_COLORS[key] : RANK_COLORS[i % RANK_COLORS.length];
                        return (
                          <Area key={key} type="monotone" dataKey={key} stroke={color} strokeWidth={1.5} fillOpacity={1} fill={`url(#grad-${key})`} isAnimationActive={false} />
                        );
                      })}
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </Card>

              <Card title={`Units by ${trendGroupBy} — ${selectedYear}`}>
                <DataTable columns={[{ key: "name", label: trendGroupBy, align: "left" }, ...timeCols, { key: "YTD", label: "Grand Total" }]} rows={trendTable} highlightFirst />
              </Card>

              {/* ── Province Performance Panel ───────────────── */}
              <div className="mt-8 border-t border-slate-800/50 pt-8">
                <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">Province Performance</h3>
                    <p className="text-xs text-slate-500 mt-0.5">Identify strongholds and gaps across regions</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <FilterPillPopover
                       label="Brand"
                       placeholder="Search brand..."
                       options={allDataBrands}
                       value={trendProvBrand ? [trendProvBrand] : []}
                       onChange={(val) => {
                          setTrendProvBrand(val[0] || "");
                          setTrendProvModel("");
                       }}
                       onOpen={ensureModels}
                       singleSelect
                    />

                    {trendProvBrand && (
                       <FilterPillPopover
                          label="Model"
                          placeholder="Search model..."
                           options={brandModelTree?.find(b => b.brand === trendProvBrand)?.models?.map(m => m.name) || []}
                          value={trendProvModel ? [trendProvModel] : []}
                          onChange={(val) => setTrendProvModel(val[0] || "")}
                          onOpen={ensureModels}
                          singleSelect
                       />
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
                 <Card title="Top Provinces">
                    <div className="max-h-[400px] overflow-y-auto custom-scrollbar pr-1">
                       {trendProvBrand && topProvinces.length === 0 ? (
                          <div className="flex h-32 items-center justify-center text-sm text-slate-500 text-center px-4">
                            No strong provinces found for this brand/model under the current filters.
                          </div>
                       ) : (
                          <DataTable 
                             columns={trendProvBrand ? [
                               { key: "prov", label: "Province", align: "left" },
                               { key: "selectedVol", label: "Volume" },
                               { key: "shareStr", label: "Mkt Share" },
                               { key: "myRank", label: "Rank" },
                               { key: "status", label: "Status", align: "left" }
                             ] : [
                               { key: "prov", label: "Province", align: "left" },
                               { key: "totalProvVol", label: "Market Volume" }
                             ]}
                             rows={topProvinces}
                          />
                       )}
                    </div>
                 </Card>
                 <Card title="Weak Spots & Gaps">
                    <div className="max-h-[400px] overflow-y-auto custom-scrollbar pr-1">
                       {!trendProvBrand ? (
                          <div className="flex h-32 items-center justify-center text-sm text-slate-500 text-center px-4">
                            Select a brand to identify weak spots and possible gaps.
                          </div>
                       ) : weakProvinces.length === 0 ? (
                          <div className="flex h-32 items-center justify-center text-sm text-slate-500 text-center px-4">
                            No major weak spots identified.
                          </div>
                       ) : (
                          <DataTable 
                             columns={[
                               { key: "prov", label: "Province", align: "left" },
                               { key: "totalProvVol", label: "Mkt Size" },
                               { key: "shareStr", label: "Share" },
                               { key: "topCompetitor", label: "Top Comp." },
                               { key: "status", label: "Status" }
                             ]}
                             rows={weakProvinces}
                          />
                       )}
                    </div>
                 </Card>
                </div>
              </div>
            </>)}

            {/* ── Disclosures Footer ───────────────── */}
            <footer className="mt-12 border-t border-slate-800/80 pt-6 text-[10px] text-slate-500 space-y-2">
              <div className="flex flex-col gap-1 sm:flex-row sm:justify-between">
                <p><strong>Source:</strong> Thailand Department of Land Transport (DLT) New Vehicle Registrations</p>
                <p><strong>Reporting Period:</strong> {data.meta?.reporting_period ?? "—"}</p>
              </div>
              <p>
                <strong>Vehicle Types Included:</strong> {data.meta?.vehicle_types_list?.map(v => v.label).join(", ") || "—"}
              </p>
              <p>
                <strong>Methodology:</strong> Historical and current registration data are unified and mapped against a canonical dictionary of brand/model aliases. Fuel classifications are derived from DLT category definitions.
              </p>
              <p>
                <strong>Limitations:</strong> Registration records may feature lag relative to purchase dates. Data is subject to corrections by the DLT. Normalization mappings are updated continuously to minimize classification discrepancies.
              </p>
              <p className="text-slate-600">Independent analysis; not an official DLT website.</p>
            </footer>

          </div>
        </div>
      </main>
    </div>
  );
}
