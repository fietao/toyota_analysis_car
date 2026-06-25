"use client";

import { useEffect, useMemo, useState } from "react";
import {
  PieChart as PieChartIcon, Trophy, Battery, Car, Filter, Layers, Upload
} from "lucide-react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell,
  Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import UploadModal from "@/components/UploadModal";

/* ── Palette & constants ─────────────────────────────────────────────── */

const BRAND_COLOR = "#169387"; // brand-light
const PT_COLORS: Record<string, string> = {
  ICE: "#64748b", BEV: BRAND_COLOR, HEV: "#fbbf24", PHEV: "#fb923c"
};
const RANK_COLORS = ["#0f6e65", "#169387", "#21b0a2", "#42d4c6", "#6ceae0",
  "#96fcf5", "#e879f9", "#f472b6", "#fb7185", "#fbbf24"];

const TT = {
  contentStyle: {
    backgroundColor: "#0f172a", border: "1px solid #1e293b",
    borderRadius: "2px", color: "#f1f5f9", fontSize: "11px",
    padding: "8px"
  },
  itemStyle: { color: "#94a3b8" },
  cursor: { fill: "rgba(255,255,255,0.05)" }
};

const VEHICLE_TYPE_DICT: Record<string, string> = {
  "รย.1": "รย.1 (รถยนต์นั่งส่วนบุคคลไม่เกิน 7 คน / เก๋ง)",
  "รย.2": "รย.2 (รถยนต์นั่งส่วนบุคคลเกิน 7 คน / ตู้)",
  "รย.3": "รย.3 (รถยนต์บรรทุกส่วนบุคคล / กระบะ)",
  "รย.6": "รย.6 (รถยนต์รับจ้างบรรทุกคนโดยสารไม่เกิน 7 คน / แท็กซี่)",
  "รย.9": "รย.9 (รถยนต์บริการธุรกิจ)",
  "รย.10": "รย.10 (รถยนต์บริการทัศนาจร)",
  "รย.11": "รย.11 (รถยนต์บริการให้เช่า / รถเช่า)"
};

/* ── Types ────────────────────────────────────────────────────────── */

type FuelRow = { y: number; m: string; pt: string; f: string; v: string; u: number };
type BrandRow = { y: number; m: string; pt: string; b: string; v: string; u: number };
type ModelRow = { y: number; m: string; pt: string; b: string; mod: string; v: string; u: number };
type PowertrainMasterRow = { f: string; pt: string; y: number; u: number };

type DashboardData = {
  meta: { years: number[]; months: string[] };
  powertrain_master: PowertrainMasterRow[];
  fuel_monthly: FuelRow[];
  brand_monthly: BrandRow[];
  model_monthly: ModelRow[];
};

type Rec = Record<string, string | number | null>;

/* ── Helpers ──────────────────────────────────────────────────────── */

const fmt = (n: unknown) => {
  const v = Number(n);
  if (v === 0) return "—";
  return isNaN(v) ? "—" : v.toLocaleString();
};

/* ── Components ───────────────────────────────────────────────────── */

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-sm border border-slate-800 bg-slate-900 p-4">
      <h2 className="mb-4 text-[10px] font-bold uppercase tracking-wider text-slate-400">
        {title}
      </h2>
      {children}
    </div>
  );
}

function DataTable({ columns, rows, highlightFirst = false }: {
  columns: { key: string; label: string; align?: string }[];
  rows: Rec[];
  highlightFirst?: boolean;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-slate-700">
            {columns.map((c) => (
              <th key={c.key} className={`whitespace-nowrap px-2 py-1.5 font-medium text-slate-400 ${c.align === "left" ? "text-left" : "text-right"}`}>
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/50">
          {rows.map((row, i) => (
            <tr key={i} className={`group ${highlightFirst && i === rows.length - 1 ? "bg-slate-800 font-semibold text-brand-light" : "hover:bg-slate-800 text-slate-300"}`}>
              {columns.map((c) => (
                <td key={c.key} className={`whitespace-nowrap px-2 py-1 tabular-nums ${c.align === "left" ? "text-left" : "text-right"}`}>
                  {c.align === "left" ? String(row[c.key] ?? "") : fmt(row[c.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TopBarChart({ data, nameKey, title }: { data: Rec[], nameKey: string, title: string }) {
  return (
    <Card title={title}>
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
  const [activeTab, setActiveTab] = useState("powertrain");
  const [selectedYear, setSelectedYear] = useState<number | "All">("All");
  const [selectedVehicleTypes, setSelectedVehicleTypes] = useState<string[]>(Object.keys(VEHICLE_TYPE_DICT));
  const [showVehicleFilter, setShowVehicleFilter] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  useEffect(() => {
    fetch("/data/dashboard_data.json")
      .then((r) => r.json())
      .then((j: DashboardData) => { 
        setData(j); 
        // Default to latest year
        if (j.meta.years.length > 0) {
          setSelectedYear(j.meta.years[j.meta.years.length - 1]);
        }
        setLoading(false); 
      })
      .catch(() => { setLoading(false); });
  }, []);

  const years = data?.meta.years ?? [];
  const months = data?.meta.months ?? [];

  // Filter Data by Year and Vehicle Type
  const fuelFiltered = useMemo(() => {
    if (!data) return [];
    const d = data.fuel_monthly.filter(x => selectedVehicleTypes.includes(x.v));
    return selectedYear === "All" ? d : d.filter(x => x.y === selectedYear);
  }, [data, selectedYear, selectedVehicleTypes]);

  const brandFiltered = useMemo(() => {
    if (!data) return [];
    const d = data.brand_monthly.filter(x => selectedVehicleTypes.includes(x.v));
    return selectedYear === "All" ? d : d.filter(x => x.y === selectedYear);
  }, [data, selectedYear, selectedVehicleTypes]);

  const modelFiltered = useMemo(() => {
    if (!data) return [];
    const d = data.model_monthly.filter(x => selectedVehicleTypes.includes(x.v));
    return selectedYear === "All" ? d : d.filter(x => x.y === selectedYear);
  }, [data, selectedYear, selectedVehicleTypes]);

  // Columns logic (Months vs Years)
  const timeCols = selectedYear === "All" 
    ? years.map(y => ({ key: String(y), label: String(y) }))
    : months.map(m => ({ key: m, label: m }));
  
  const timeKeys = selectedYear === "All" ? years.map(String) : months;

  // -- Powertrain Calcs --
  const ptTrend = useMemo(() => {
    const res: Rec[] = [];
    timeKeys.forEach(t => {
      const point: Rec = { name: t, Total: 0 };
      ["ICE", "BEV", "HEV", "PHEV"].forEach(pt => {
        const sum = fuelFiltered
          .filter(d => d.pt === pt && String(selectedYear === "All" ? d.y : d.m) === t)
          .reduce((acc, curr) => acc + curr.u, 0);
        point[pt] = sum;
        point.Total = Number(point.Total) + sum;
      });
      res.push(point);
    });

    // Remove future months that have exactly 0 total sales so the chart doesn't crash to zero
    let lastValidIdx = res.length - 1;
    while (lastValidIdx >= 0 && res[lastValidIdx].Total === 0) {
      lastValidIdx--;
    }
    return res.slice(0, lastValidIdx + 1);
  }, [fuelFiltered, timeKeys, selectedYear]);

  const ptTable = useMemo(() => {
    const res: Rec[] = [];
    ["ICE", "BEV", "HEV", "PHEV", "Total"].forEach(pt => {
      const row: Rec = { name: pt === "Total" ? "Grand Total" : pt, YTD: 0 };
      timeKeys.forEach(t => {
        const val = ptTrend.find(x => x.name === t)?.[pt] ?? 0;
        row[t] = val;
        row.YTD = Number(row.YTD) + Number(val);
      });
      res.push(row);
    });
    return res.filter(r => Number(r.YTD) > 0);
  }, [ptTrend, timeKeys]);

  const ptDonut = useMemo(() => ptTable.filter(r => r.name !== "Grand Total"), [ptTable]);
  const ytdTotal = Number(ptTable.find(r => r.name === "Grand Total")?.YTD ?? 0);
  const bevYTD = Number(ptTable.find(r => r.name === "BEV")?.YTD ?? 0);
  const bevShare = ytdTotal ? ((bevYTD / ytdTotal) * 100).toFixed(1) : "—";

  // -- Fuel Type Calcs (from powertrain_master — full unfiltered data, year granularity) --
  const fuelMasterTable = useMemo(() => {
    if (!data?.powertrain_master) return [];
    const fMap = new Map<string, Rec>();
    data.powertrain_master.forEach(d => {
      if (!fMap.has(d.f)) {
        const row: Rec = { name: d.f, powertrain: d.pt, YTD: 0 };
        years.forEach(y => { row[String(y)] = 0; });
        fMap.set(d.f, row);
      }
      const row = fMap.get(d.f)!;
      row[String(d.y)] = Number(row[String(d.y)]) + d.u;
      row.YTD = Number(row.YTD) + d.u;
    });
    return Array.from(fMap.values())
      .filter(r => Number(r.YTD) > 0)
      .sort((a, b) => Number(b.YTD) - Number(a.YTD));
  }, [data, years]);

  // -- Brand Calcs --
  const buildBrandList = (filterPt?: string): Rec[] => {
    const bMap = new Map<string, Rec>();
    const source = filterPt ? brandFiltered.filter(d => d.pt === filterPt) : brandFiltered;
    
    source.forEach(d => {
      if (!bMap.has(d.b)) {
        const row: Rec = { name: d.b, YTD: 0 };
        timeKeys.forEach(t => row[t] = 0);
        bMap.set(d.b, row);
      }
      const row = bMap.get(d.b)!;
      const tKey = String(selectedYear === "All" ? d.y : d.m);
      row[tKey] = Number(row[tKey]) + d.u;
      row.YTD = Number(row.YTD) + d.u;
    });
    return Array.from(bMap.values())
      .filter(r => Number(r.YTD) > 0)
      .sort((a, b) => Number(b.YTD) - Number(a.YTD))
      .map((r, i): Rec => ({ ...r, rank: i + 1 }));
  };

  const allBrands = useMemo(() => buildBrandList(), [brandFiltered, timeKeys, selectedYear]);
  const topBrand = allBrands[0]?.name ?? "—";

  const brandCols = [
    { key: "rank", label: "#" },
    { key: "name", label: "Brand", align: "left" },
    ...timeCols,
    { key: "YTD", label: "Grand Total" }
  ];

  // -- Model Calcs --
  const buildModelList = (filterPt?: string, filterBrand?: string) => {
    const mMap = new Map<string, Rec>();
    let source = modelFiltered;
    if (filterPt) source = source.filter(d => d.pt === filterPt);
    if (filterBrand) source = source.filter(d => d.b === filterBrand);

    source.forEach(d => {
      const key = `${d.b}|${d.mod}`;
      if (!mMap.has(key)) {
        const row: Rec = { brand: d.b, model: d.mod, label: `${d.b} ${d.mod}`, YTD: 0 };
        timeKeys.forEach(t => row[t] = 0);
        mMap.set(key, row);
      }
      const row = mMap.get(key)!;
      const tKey = String(selectedYear === "All" ? d.y : d.m);
      row[tKey] = Number(row[tKey]) + d.u;
      row.YTD = Number(row.YTD) + d.u;
    });
    return Array.from(mMap.values())
      .filter(r => Number(r.YTD) > 0)
      .sort((a, b) => Number(b.YTD) - Number(a.YTD));
  };

  const bevModels = useMemo(() => buildModelList("BEV"), [modelFiltered, timeKeys, selectedYear]);
  const bmwModels = useMemo(() => buildModelList(undefined, "BMW"), [modelFiltered, timeKeys, selectedYear]);

  if (loading) return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-light border-t-transparent"></div>
    </div>
  );

  const tabs = [
    { id: "powertrain", label: "Powertrain & Fuel", icon: PieChartIcon },
    { id: "brands", label: "All Brands", icon: Trophy },
    { id: "deep-dive", label: "Brand & Model Deep-Dive", icon: Layers, href: "/models.html" },
    { id: "analyst", label: "Analyst Table", icon: Layers, href: "/analyst.html" },
    { id: "bev-models", label: "BEV Models", icon: Battery },
    { id: "bmw", label: "BMW Models", icon: Car },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-200 md:flex-row font-sans">
      
      {/* ── Sidebar Navigation ────────────────────────────────────── */}
      <aside className="sticky top-0 z-20 flex w-full flex-col border-b border-slate-800 bg-slate-950 md:h-screen md:w-56 md:border-b-0 md:border-r">
        <div className="flex flex-col gap-2 p-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="Eternity@One Logo" className="h-6 w-6 object-contain" />
            <h1 className="text-sm font-bold tracking-tight text-brand-light uppercase">EV Analytics</h1>
          </div>
          
          {/* Year Selector */}
          <div className="mt-4 flex flex-col gap-2">
            <div className="flex items-center gap-2 rounded-sm border border-slate-800 bg-slate-900 p-1.5 focus-within:border-brand-primary">
              <Filter className="h-3 w-3 text-slate-400 ml-1" />
              <select 
                className="w-full bg-transparent text-xs font-semibold text-slate-200 outline-none"
                value={selectedYear}
                onChange={(e) => setSelectedYear(e.target.value === "All" ? "All" : Number(e.target.value))}
              >
                <option value="All" className="bg-slate-900">All Years (2564-2569)</option>
                {years.slice().reverse().map(y => (
                  <option key={y} value={y} className="bg-slate-900">Year {y}</option>
                ))}
              </select>
            </div>

            {/* Upload Button */}
            <button
              onClick={() => setIsUploadModalOpen(true)}
              className="flex w-full items-center justify-center gap-2 rounded-sm bg-brand-primary px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-brand-accent"
            >
              <Upload className="h-3 w-3" />
              Upload Data
            </button>
          </div>
        </div>

        <nav className="flex flex-row overflow-x-auto p-2 scrollbar-hide md:flex-col md:gap-0.5 md:p-2">
          {tabs.map((t) => {
            const isActive = activeTab === t.id;
            const Icon = t.icon;
            if ("href" in t) {
              return (
                <a key={t.id} href={t.href}
                  className="flex min-w-max items-center gap-2.5 rounded-sm px-2.5 py-2 text-xs font-medium text-slate-400 transition-colors hover:bg-slate-900 hover:text-slate-200">
                  <Icon className="h-3.5 w-3.5 text-slate-500" />
                  <span>{t.label}</span>
                </a>
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
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Total Reg ({selectedYear})</p>
              <p className="mt-1 font-mono text-xl font-semibold tracking-tight text-slate-100">{ytdTotal.toLocaleString()}</p>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">BEV Share ({selectedYear})</p>
              <p className="mt-1 font-mono text-xl font-semibold tracking-tight text-brand-light">{bevShare}%</p>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Top Brand ({selectedYear})</p>
              <p className="mt-1 font-mono text-xl font-semibold tracking-tight text-slate-100">{String(topBrand)}</p>
            </div>
            {selectedVehicleTypes.length < Object.keys(VEHICLE_TYPE_DICT).length && (
              <>
                <div className="h-8 w-px bg-slate-800" />
                <p className="text-[10px] font-mono text-amber-500">
                  [{selectedVehicleTypes.length}/{Object.keys(VEHICLE_TYPE_DICT).length} VEHICLE TYPES]
                </p>
              </>
            )}
          </div>
        </header>

        <div className="p-4 md:p-6">
          {/* Vehicle Type Filter */}
          <div className="mb-4 md:mb-6 rounded-sm border border-slate-800 bg-slate-900 overflow-hidden">
            <button
              onClick={() => setShowVehicleFilter(!showVehicleFilter)}
              className="flex w-full items-center justify-between px-3 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800"
            >
              <span className="flex items-center gap-2">
                <Filter className="h-3 w-3 text-slate-400" />
                <span>Vehicle Types Filter</span>
              </span>
              <span className="rounded-sm bg-slate-800 px-1.5 py-0.5 text-[10px] text-brand-light font-mono">
                {selectedVehicleTypes.length}/{Object.keys(VEHICLE_TYPE_DICT).length}
              </span>
            </button>
            {showVehicleFilter && (
              <div className="border-t border-slate-800 bg-slate-950 p-2 flex flex-wrap gap-1.5">
                {Object.entries(VEHICLE_TYPE_DICT).map(([code, label]) => (
                  <label key={code} title={label} className="flex cursor-pointer items-center gap-1.5 rounded-sm border border-slate-800 bg-slate-900 px-2 py-1 hover:border-slate-700 transition-colors">
                    <input
                      type="checkbox"
                      className="cursor-pointer accent-brand-primary"
                      checked={selectedVehicleTypes.includes(code)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedVehicleTypes([...selectedVehicleTypes, code]);
                        } else {
                          setSelectedVehicleTypes(selectedVehicleTypes.filter(t => t !== code));
                        }
                      }}
                    />
                    <span className="text-[10px] font-mono text-slate-300">{code}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-4 md:space-y-6">
            {/* ── Powertrain Tab ─────────────────────────────────── */}
            {activeTab === "powertrain" && (<>
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 lg:gap-6">
                <Card title="Powertrain Distribution">
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={ptDonut} cx="50%" cy="50%" innerRadius="60%" outerRadius="80%" paddingAngle={1} dataKey="YTD" stroke="none" nameKey="name" isAnimationActive={false}>
                          {ptDonut.map((e) => <Cell key={String(e.name)} fill={PT_COLORS[String(e.name)] ?? "#64748b"} />)}
                        </Pie>
                        <Tooltip {...TT} formatter={(v: unknown) => Number(v).toLocaleString()} />
                        <Legend verticalAlign="bottom" height={20} iconType="square" wrapperStyle={{ fontSize: "10px", color: "#94a3b8" }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
                <Card title={`Trend — ${selectedYear}`}>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={ptTrend} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
                        <defs>
                          {["ICE", "BEV", "HEV", "PHEV"].map((pt) => (
                            <linearGradient key={`grad-${pt}`} id={`grad-${pt}`} x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor={PT_COLORS[pt]} stopOpacity={0.2}/>
                              <stop offset="95%" stopColor={PT_COLORS[pt]} stopOpacity={0}/>
                            </linearGradient>
                          ))}
                        </defs>
                        <CartesianGrid strokeDasharray="1 3" stroke="#1e293b" vertical={false} />
                        <XAxis dataKey="name" stroke="#334155" tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} />
                        <YAxis stroke="#334155" tick={{ fill: "#64748b", fontSize: 10 }} tickFormatter={(v) => (v/1000).toFixed(0)+"k"} tickLine={false} axisLine={false} />
                        <Tooltip {...TT} formatter={(v: unknown) => Number(v).toLocaleString()} />
                        <Legend verticalAlign="top" height={20} iconType="square" wrapperStyle={{ fontSize: "10px", color: "#94a3b8" }} />
                        {["ICE", "BEV", "HEV", "PHEV"].map((pt) => (
                          <Area key={pt} type="monotone" dataKey={pt} stroke={PT_COLORS[pt]} strokeWidth={1.5} fillOpacity={1} fill={`url(#grad-${pt})`} isAnimationActive={false} />
                        ))}
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
              </div>

              <Card title={`Powertrain Units — ${selectedYear}`}>
                <DataTable columns={[{ key: "name", label: "Powertrain", align: "left" }, ...timeCols, { key: "YTD", label: "Grand Total" }]} rows={ptTable} highlightFirst />
              </Card>

              <Card title="Fuel-Type Powertrain Master — All Years, All Vehicle Types (Unfiltered)">
                <DataTable columns={[{ key: "name", label: "Fuel Type", align: "left" }, { key: "powertrain", label: "Powertrain Mapped", align: "left" }, ...years.map(y => ({ key: String(y), label: String(y) })), { key: "YTD", label: "Grand Total" }]} rows={fuelMasterTable} />
              </Card>
            </>)}

            {/* ── Brands Tabs ─────────────────────────────────── */}
            {activeTab === "brands" && (<>
              <TopBarChart title={`Top 10 Brands — ${selectedYear}`} data={allBrands.slice(0, 10)} nameKey="name" />
              <Card title={`All Brand Rankings — ${selectedYear}`}><DataTable columns={brandCols} rows={allBrands} /></Card>
            </>)}

            {/* ── Models Tabs ─────────────────────────────────── */}
            {activeTab === "bev-models" && (<>
              <TopBarChart title={`Top 15 BEV Models — ${selectedYear}`} data={bevModels.slice(0, 15)} nameKey="label" />
              <Card title={`BEV by Model — ${selectedYear}`}><DataTable columns={[{ key: "brand", label: "Brand", align: "left" }, { key: "model", label: "Model", align: "left" }, ...timeCols, { key: "YTD", label: "Grand Total" }]} rows={bevModels} /></Card>
            </>)}

            {activeTab === "bmw" && (<>
              <TopBarChart title={`Top BMW Models — ${selectedYear}`} data={bmwModels.slice(0, 10)} nameKey="model" />
              <Card title={`BMW Registrations by Model — ${selectedYear}`}><DataTable columns={[{ key: "model", label: "Model Variant", align: "left" }, ...timeCols, { key: "YTD", label: "Grand Total" }]} rows={bmwModels} /></Card>
            </>)}

          </div>
        </div>
      </main>

      <UploadModal 
        isOpen={isUploadModalOpen} 
        onClose={() => setIsUploadModalOpen(false)} 
      />
    </div>
  );
}
