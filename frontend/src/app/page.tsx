"use client";

import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  PieChart as PieChartIcon, Trophy, Battery, Car, Filter, Layers, Upload
} from "lucide-react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell,
  Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import UploadModal from "@/components/UploadModal";

/* ── Palette & constants ─────────────────────────────────────────────── */

const PT_COLORS: Record<string, string> = {
  ICE: "#64748b", BEV: "#2dd4bf", HEV: "#fbbf24", PHEV: "#fb923c"
};
const RANK_COLORS = ["#2dd4bf", "#22d3ee", "#38bdf8", "#818cf8", "#a78bfa",
  "#c084fc", "#e879f9", "#f472b6", "#fb7185", "#fbbf24"];

const TT = {
  contentStyle: {
    backgroundColor: "rgba(15, 23, 42, 0.9)", border: "1px solid #334155",
    borderRadius: "8px", color: "#f1f5f9", fontSize: "12px",
    backdropFilter: "blur(8px)",
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
  return isNaN(v) ? "—" : v.toLocaleString();
};

/* ── Components ───────────────────────────────────────────────────── */

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-800/60 bg-slate-900/50 p-5 md:p-6 shadow-xl backdrop-blur-xl transition-all duration-300 hover:border-slate-700/80">
      <h2 className="mb-5 text-xs font-bold uppercase tracking-widest text-slate-400">
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
          <tr className="border-b border-slate-700/50">
            {columns.map((c) => (
              <th key={c.key} className={`whitespace-nowrap px-3 py-2.5 font-medium text-slate-400 ${c.align === "left" ? "text-left" : "text-right"}`}>
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/30">
          {rows.map((row, i) => (
            <tr key={i} className={`group transition-colors ${highlightFirst && i === rows.length - 1 ? "bg-slate-800/40 font-semibold text-teal-400" : "hover:bg-slate-800/30 text-slate-300"}`}>
              {columns.map((c) => (
                <td key={c.key} className={`whitespace-nowrap px-3 py-2 tabular-nums ${c.align === "left" ? "text-left" : "text-right"}`}>
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
      <div className="h-72 md:h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 12, left: 8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="2 4" stroke="#1e293b" horizontal={false} />
            <XAxis type="number" stroke="#334155" tick={{ fill: "#64748b", fontSize: 10 }} tickFormatter={(v: number) => (v / 1000).toFixed(0) + "k"} />
            <YAxis dataKey={nameKey} type="category" width={110} stroke="#334155" tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <Tooltip {...TT} formatter={(v: unknown) => Number(v).toLocaleString()} />
            <Bar dataKey="YTD" radius={[0, 4, 4, 0]} barSize={16}>
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
    return res;
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
    return res;
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
    return Array.from(fMap.values()).sort((a, b) => Number(b.YTD) - Number(a.YTD));
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
    return Array.from(mMap.values()).sort((a, b) => Number(b.YTD) - Number(a.YTD));
  };

  const bevModels = useMemo(() => buildModelList("BEV"), [modelFiltered, timeKeys, selectedYear]);
  const bmwModels = useMemo(() => buildModelList(undefined, "BMW"), [modelFiltered, timeKeys, selectedYear]);

  if (loading) return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-500 border-t-transparent"></div>
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
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-200 md:flex-row">
      
      {/* ── Sidebar Navigation ────────────────────────────────────── */}
      <aside className="sticky top-0 z-20 flex w-full flex-col border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md md:h-screen md:w-64 md:border-b-0 md:border-r">
        <div className="flex flex-col gap-2 p-5 md:p-6">
          <h1 className="text-lg font-bold tracking-tight text-teal-400">EV Analytics</h1>
          
          {/* Year Selector */}
          <div className="mt-4 flex flex-col gap-3">
            <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 p-2 transition-colors hover:border-slate-700">
              <Filter className="h-4 w-4 text-slate-400" />
              <select 
                className="w-full bg-transparent text-sm font-semibold text-slate-200 outline-none"
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
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-teal-500/10 px-4 py-2.5 text-sm font-medium text-teal-400 transition-colors hover:bg-teal-500/20"
            >
              <Upload className="h-4 w-4" />
              Upload Data
            </button>
          </div>
        </div>

        <nav className="flex flex-row overflow-x-auto p-2 scrollbar-hide md:flex-col md:gap-1 md:p-4">
          {tabs.map((t) => {
            const isActive = activeTab === t.id;
            const Icon = t.icon;
            if ("href" in t) {
              return (
                <a key={t.id} href={t.href}
                  className="group relative flex min-w-max items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-400 transition-all duration-200 hover:bg-slate-800/50 hover:text-slate-200">
                  <Icon className="relative z-10 h-4 w-4 text-slate-500 group-hover:text-slate-300" />
                  <span className="relative z-10">{t.label}</span>
                </a>
              );
            }
            return (
              <button key={t.id} onClick={() => setActiveTab(t.id)}
                className={`group relative flex min-w-max items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
                  isActive ? "text-teal-400" : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                }`}>
                {isActive && <motion.div layoutId="activeTabIndicator" className="absolute inset-0 rounded-lg bg-teal-500/10 border border-teal-500/20" transition={{ type: "spring", bounce: 0.2, duration: 0.6 }} />}
                <Icon className={`relative z-10 h-4 w-4 ${isActive ? "text-teal-400" : "text-slate-500 group-hover:text-slate-300"}`} />
                <span className="relative z-10">{t.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      {/* ── Main Content Area ─────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">
        <header className="sticky top-0 z-10 hidden border-b border-slate-800/50 bg-slate-950/80 px-8 py-5 backdrop-blur-xl md:block">
          <div className="flex items-center gap-8 text-sm">
            <div>
              <p className="text-xs font-medium text-slate-500">Total Registrations ({selectedYear})</p>
              <p className="mt-1 font-mono text-2xl font-semibold tracking-tight text-slate-100">{ytdTotal.toLocaleString()}</p>
            </div>
            <div className="h-10 w-px bg-slate-800" />
            <div>
              <p className="text-xs font-medium text-slate-500">BEV Market Share ({selectedYear})</p>
              <p className="mt-1 font-mono text-2xl font-semibold tracking-tight text-teal-400">{bevShare}%</p>
            </div>
            <div className="h-10 w-px bg-slate-800" />
            <div>
              <p className="text-xs font-medium text-slate-500">Top Brand ({selectedYear})</p>
              <p className="mt-1 font-mono text-2xl font-semibold tracking-tight text-slate-100">{String(topBrand)}</p>
            </div>
            {selectedVehicleTypes.length < Object.keys(VEHICLE_TYPE_DICT).length && (
              <>
                <div className="h-10 w-px bg-slate-800" />
                <p className="text-[11px] text-amber-500/80 italic">
                  {selectedVehicleTypes.length} of {Object.keys(VEHICLE_TYPE_DICT).length} vehicle types
                </p>
              </>
            )}
          </div>
        </header>

        <div className="p-5 md:p-8">
          {/* Vehicle Type Filter — filters this tab's data only; does not affect Powertrain Master */}
          <div className="mb-5 md:mb-6 rounded-lg border border-slate-800 bg-slate-900/50 overflow-hidden">
            <button
              onClick={() => setShowVehicleFilter(!showVehicleFilter)}
              className="flex w-full items-center justify-between px-4 py-2.5 text-sm font-medium text-slate-300 hover:bg-slate-800/50"
            >
              <span className="flex items-center gap-2">
                <Filter className="h-3.5 w-3.5 text-slate-400" />
                <span>Vehicle Types (this tab)</span>
              </span>
              <span className="rounded-full bg-teal-500/20 px-2 py-0.5 text-[10px] text-teal-400">
                {selectedVehicleTypes.length} / {Object.keys(VEHICLE_TYPE_DICT).length}
              </span>
            </button>
            <AnimatePresence>
              {showVehicleFilter && (
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: "auto" }}
                  exit={{ height: 0 }}
                  className="overflow-hidden border-t border-slate-800/50 bg-slate-950/50"
                >
                  <div className="flex flex-wrap gap-2 p-3">
                    {Object.entries(VEHICLE_TYPE_DICT).map(([code, label]) => (
                      <label key={code} title={label} className="flex cursor-pointer items-center gap-1.5 rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 hover:border-slate-600 hover:bg-slate-800 transition-colors">
                        <input
                          type="checkbox"
                          className="cursor-pointer accent-teal-500"
                          checked={selectedVehicleTypes.includes(code)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedVehicleTypes([...selectedVehicleTypes, code]);
                            } else {
                              setSelectedVehicleTypes(selectedVehicleTypes.filter(t => t !== code));
                            }
                          }}
                        />
                        <span className="text-[11px] text-slate-300">{code}</span>
                      </label>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <AnimatePresence mode="wait">
            <motion.div key={activeTab + selectedYear} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }} className="space-y-6 md:space-y-8">

              {/* ── Powertrain Tab ─────────────────────────────────── */}
              {activeTab === "powertrain" && (<>
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                  <Card title="Powertrain Distribution">
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={ptDonut} cx="50%" cy="50%" innerRadius="55%" outerRadius="75%" paddingAngle={3} dataKey="YTD" stroke="none" nameKey="name">
                            {ptDonut.map((e) => <Cell key={String(e.name)} fill={PT_COLORS[String(e.name)] ?? "#64748b"} />)}
                          </Pie>
                          <Tooltip {...TT} formatter={(v: unknown) => Number(v).toLocaleString()} />
                          <Legend verticalAlign="bottom" height={28} iconType="circle" wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </Card>
                  <Card title={`Trend — ${selectedYear}`}>
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={ptTrend} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
                          <defs>
                            {["ICE", "BEV", "HEV", "PHEV"].map((pt) => (
                              <linearGradient key={`grad-${pt}`} id={`grad-${pt}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={PT_COLORS[pt]} stopOpacity={0.3}/>
                                <stop offset="95%" stopColor={PT_COLORS[pt]} stopOpacity={0}/>
                              </linearGradient>
                            ))}
                          </defs>
                          <CartesianGrid strokeDasharray="2 4" stroke="#1e293b" vertical={false} />
                          <XAxis dataKey="name" stroke="#334155" tick={{ fill: "#64748b", fontSize: 10 }} />
                          <YAxis stroke="#334155" tick={{ fill: "#64748b", fontSize: 10 }} tickFormatter={(v) => (v/1000).toFixed(0)+"k"} />
                          <Tooltip {...TT} formatter={(v: unknown) => Number(v).toLocaleString()} />
                          <Legend verticalAlign="top" height={28} iconType="circle" wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }} />
                          {["ICE", "BEV", "HEV", "PHEV"].map((pt) => (
                            <Area key={pt} type="monotone" dataKey={pt} stroke={PT_COLORS[pt]} strokeWidth={2} fillOpacity={1} fill={`url(#grad-${pt})`} />
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

            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      <UploadModal 
        isOpen={isUploadModalOpen} 
        onClose={() => setIsUploadModalOpen(false)} 
      />
    </div>
  );
}
