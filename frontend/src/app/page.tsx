"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import {
  PieChart as PieChartIcon, Trophy, Battery, Car, Filter, Layers, Upload, ChevronDown, Check, Search, ChevronRight
} from "lucide-react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell,
  Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import UploadModal from "@/components/UploadModal";

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

const VEHICLE_TYPE_DICT: Record<string, string> = {
  "รย.1": "รย.1 (รถยนต์นั่งส่วนบุคคลไม่เกิน 7 คน / เก๋ง)",
  "รย.2": "รย.2 (รถยนต์นั่งส่วนบุคคลเกิน 7 คน / ตู้)",
  "รย.3": "รย.3 (รถยนต์บรรทุกส่วนบุคคล / กระบะ)",
  "รย.6": "รย.6 (รถยนต์รับจ้างบรรทุกคนโดยสารไม่เกิน 7 คน / แท็กซี่)",
  "รย.9": "รย.9 (รถยนต์บริการธุรกิจ)",
  "รย.10": "รย.10 (รถยนต์บริการทัศนาจร)",
  "รย.11": "รย.11 (รถยนต์บริการให้เช่า / รถเช่า)"
};

function normalizeBrandName(rawBrand: string): string {
  const clean = rawBrand.replace(/\s+/g, '').toLowerCase();
  if (
    clean === 'deepal+chang' ||
    clean === 'deepal+changan' ||
    clean === 'changan+deepal' ||
    clean === 'change+depal' ||
    clean === 'changan' ||
    clean === 'deepal'
  ) {
    return 'Deepal + Changan';
  }
  return rawBrand;
}

/* ── Types ────────────────────────────────────────────────────────── */

type PowertrainMasterRow = { f: string; pt: string; y: number; u: number };
type FuelRow = { y: number; m: string; pt: string; f: string; v: string; u: number };
type TreeMonthly = Record<string, Record<string, Record<string, number[]>>>;

type ModelNode = {
  name: string;
  fuel: string;
  monthly: TreeMonthly;
};

type BrandNode = {
  brand: string;
  powertrain: string;
  fuel: string;
  monthly: TreeMonthly;
  models: ModelNode[];
};

type DashboardData = {
  meta: { years: number[]; months: string[]; provinces: string[] };
  powertrain_master: PowertrainMasterRow[];
  fuel_monthly: FuelRow[];
  brand_model_tree: BrandNode[];
};

type Rec = Record<string, string | number | boolean | null>;

/* ── Helpers ──────────────────────────────────────────────────────── */

const fmt = (n: unknown) => {
  const v = Number(n);
  if (v === 0) return "—";
  return isNaN(v) ? "—" : v.toLocaleString();
};

function getNodeSums(node: { monthly: TreeMonthly }, selectedYear: number | "All", selectedVehicleTypes: string[], selectedProvinces: string[]) {
  const timeVals: Record<string, number> = {};
  let grandTotal = 0;
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

  selectedVehicleTypes.forEach(vc => {
    const vcBucket = node.monthly?.[vc];
    if (!vcBucket) return;
    
    const provs = selectedProvinces.length > 0 ? selectedProvinces : Object.keys(vcBucket);
    provs.forEach(prov => {
      const pBucket = vcBucket[prov];
      if (!pBucket) return;

      Object.keys(pBucket).forEach(yStr => {
        if (selectedYear !== "All" && yStr !== String(selectedYear)) return;

        const arr = pBucket[yStr];
        if (!Array.isArray(arr)) return;

        if (selectedYear === "All") {
          let ySum = 0;
          for (let i = 0; i < 12; i++) ySum += arr[i] || 0;
          timeVals[yStr] = (timeVals[yStr] || 0) + ySum;
          grandTotal += ySum;
        } else {
          for (let i = 0; i < 12; i++) {
            const mStr = months[i];
            timeVals[mStr] = (timeVals[mStr] || 0) + (arr[i] || 0);
            grandTotal += (arr[i] || 0);
          }
        }
      });
    });
  });

  return { timeVals, grandTotal };
}

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
    <Card className="flex flex-col justify-center border-t-2 border-t-brand-light/30 h-24 shadow-md">
      <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{title}</div>
      <div className="mt-1 font-mono text-2xl font-semibold tracking-tight text-slate-100 truncate" title={String(value)}>{value}</div>
      {subtitle && <div className="mt-1 text-xs text-brand-light font-medium">{subtitle}</div>}
    </Card>
  );
}

function FilterPillPopover({ 
  options, 
  value, 
  onChange, 
  label,
  placeholder
}: { 
  options: string[]; 
  value: string[]; 
  onChange: (v: string[]) => void;
  label: string;
  placeholder?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) setIsOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filtered = options.filter(o => o.toLowerCase().includes(search.toLowerCase()));

  const toggleOpt = (opt: string) => {
    if (value.includes(opt)) onChange(value.filter(v => v !== opt));
    else onChange([...value, opt]);
  };

  const btnText = value.length === 0 ? "All" : `${value.length} Selected`;

  return (
    <div ref={ref} className="relative inline-block">
      <button 
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
          value.length > 0 
            ? "border-brand-primary bg-brand-primary/10 text-brand-light" 
            : "border-slate-700 bg-slate-800 text-slate-300 hover:border-slate-500"
        }`}
      >
        <span>{label}: {btnText}</span>
        <ChevronDown className="h-3 w-3 opacity-70" />
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-2 w-[260px] rounded-sm border border-slate-700 bg-slate-800 shadow-2xl">
          <div className="p-2 border-b border-slate-700">
            <div className="flex items-center rounded-sm bg-slate-900 px-2 py-1 text-xs border border-slate-700">
              <Search className="h-3 w-3 text-slate-500 mr-2" />
              <input 
                type="text"
                autoFocus
                className="w-full bg-transparent text-slate-200 outline-none placeholder:text-slate-500"
                placeholder="Search..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
          </div>
          <div className="max-h-60 overflow-y-auto custom-scrollbar p-1">
            <label className={`flex w-full cursor-pointer items-center justify-between rounded-sm px-2 py-1.5 text-xs ${value.length === 0 ? "bg-brand-primary/20 text-brand-light" : "text-slate-300 hover:bg-slate-700"}`}>
              <span>All {label}</span>
              <input type="checkbox" className="hidden" checked={value.length === 0} onChange={() => onChange([])} />
              {value.length === 0 && <Check className="h-3 w-3" />}
            </label>
            {filtered.map(opt => {
              const isChecked = value.includes(opt);
              return (
                <label key={opt} className={`flex w-full cursor-pointer items-center justify-between rounded-sm px-2 py-1.5 text-xs ${isChecked ? "bg-brand-primary/20 text-brand-light" : "text-slate-300 hover:bg-slate-700"}`}>
                  <span className="truncate pr-2">{opt}</span>
                  <input type="checkbox" className="hidden" checked={isChecked} onChange={() => toggleOpt(opt)} />
                  {isChecked && <Check className="h-3 w-3 flex-shrink-0" />}
                </label>
              );
            })}
            {filtered.length === 0 && (
              <div className="px-2 py-3 text-center text-xs text-slate-500">No results found</div>
            )}
          </div>
        </div>
      )}
    </div>
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
    let sortableItems = [...rows];
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
                const content = c.align === "left" ? String(row[c.key] ?? "") : fmt(row[c.key]);
                
                return (
                  <td key={c.key} className={`whitespace-nowrap px-2 py-1.5 tabular-nums ${c.align === "left" ? "text-left" : "text-right"}`}>
                    {isNameCol ? (
                      <div className="flex items-center gap-2" style={{ paddingLeft: row.isSubRow ? '1.5rem' : '0' }}>
                        {row.hasChildren && onToggleRow ? (
                          <button 
                            onClick={(e) => { e.stopPropagation(); onToggleRow(String(row.id)); }}
                            className="flex h-4 w-4 items-center justify-center rounded-sm bg-slate-800 text-slate-400 hover:bg-brand-primary hover:text-white transition-colors"
                          >
                            {row.isExpanded ? "▼" : "▶"}
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
  const [activeTab, setActiveTab] = useState("rankings");
  const [selectedYear, setSelectedYear] = useState<number | "All">("All");
  const [selectedVehicleTypes, setSelectedVehicleTypes] = useState<string[]>(Object.keys(VEHICLE_TYPE_DICT));
  const [showVehicleFilter, setShowVehicleFilter] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

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

  useEffect(() => {
    fetch("/data/dashboard_data.json")
      .then((r) => r.json())
      .then((j: DashboardData) => { 
        setData(j); 
        if (j.meta?.years?.length > 0) {
          setSelectedYear(j.meta.years[j.meta.years.length - 1]);
        }
        setLoading(false); 
      })
      .catch(() => { setLoading(false); });
  }, []);

  const years = data?.meta?.years ?? [];
  const months = data?.meta?.months ?? [];
  const allDataProvinces = data?.meta?.provinces ?? [];
  const allDataBrands = useMemo(() => {
     if (!data?.brand_model_tree) return [];
     return Array.from(new Set(data.brand_model_tree.map(b => normalizeBrandName(b.brand)))).sort();
  }, [data]);
  const allDataModels = useMemo(() => {
     if (!data?.brand_model_tree) return [];
     const mSet = new Set<string>();
     data.brand_model_tree.forEach(b => {
        // If specific brands are selected, skip any brands that aren't in the selection
        const cleanBrand = normalizeBrandName(b.brand);
        if (rankingBrand.length > 0 && !rankingBrand.includes(cleanBrand)) return;
        
        b.models?.forEach(m => mSet.add(m.name));
     });
     return Array.from(mSet).sort();
  }, [data, rankingBrand]);

  // Clear stale selected models if they are no longer in the cascading `allDataModels` list
  useEffect(() => {
    if (rankingModel.length > 0) {
      const validModels = rankingModel.filter(m => allDataModels.includes(m));
      if (validModels.length !== rankingModel.length) {
        setRankingModel(validModels);
      }
    }
  }, [allDataModels, rankingModel]);

  const timeCols = selectedYear === "All" 
    ? years.map(y => ({ key: String(y), label: String(y) }))
    : months.map(m => ({ key: m, label: m }));
  
  const timeKeys = selectedYear === "All" ? years.map(String) : months;

  // -- Powertrain Overview Engine (fuel_monthly) --
  const fuelFiltered = useMemo(() => {
    if (!data?.fuel_monthly) return [];
    const d = data.fuel_monthly.filter(x => selectedVehicleTypes.includes(x.v));
    return selectedYear === "All" ? d : d.filter(x => x.y === selectedYear);
  }, [data, selectedYear, selectedVehicleTypes]);

  const trendKeys = useMemo(() => {
     if (trendGroupBy === "Powertrain") return ["ICE", "BEV", "HEV", "PHEV"];
     return Array.from(new Set(fuelFiltered.map(x => VEHICLE_TYPE_DICT[x.v] || x.v)));
  }, [trendGroupBy, fuelFiltered]);

  const trendData = useMemo(() => {
    const res: Rec[] = [];
    timeKeys.forEach(t => {
      const point: Rec = { name: t, Total: 0 };
      
      if (trendGroupBy === "Powertrain") {
        ["ICE", "BEV", "HEV", "PHEV"].forEach(pt => {
          const sum = fuelFiltered
            .filter(d => d.pt === pt && String(selectedYear === "All" ? d.y : d.m) === t)
            .reduce((acc, curr) => acc + curr.u, 0);
          point[pt] = sum;
          point.Total = Number(point.Total) + sum;
        });
      } else {
        trendKeys.forEach(vKey => {
          const sum = fuelFiltered
            .filter(d => (VEHICLE_TYPE_DICT[d.v] || d.v) === vKey && String(selectedYear === "All" ? d.y : d.m) === t)
            .reduce((acc, curr) => acc + curr.u, 0);
          point[vKey] = sum;
          point.Total = Number(point.Total) + sum;
        });
      }

      res.push(point);
    });
    let lastValidIdx = res.length - 1;
    while (lastValidIdx >= 0 && res[lastValidIdx].Total === 0) lastValidIdx--;
    return res.slice(0, lastValidIdx + 1);
  }, [fuelFiltered, timeKeys, selectedYear, trendGroupBy, trendKeys]);

  const trendTable = useMemo(() => {
    const res: Rec[] = [];
    [...trendKeys, "Total"].forEach(key => {
      const row: Rec = { name: key === "Total" ? "Grand Total" : key, YTD: 0 };
      timeKeys.forEach(t => {
        const val = trendData.find(x => x.name === t)?.[key] ?? 0;
        row[t] = val;
        row.YTD = Number(row.YTD) + Number(val);
      });
      res.push(row);
    });
    return res.filter(r => Number(r.YTD) > 0);
  }, [trendData, timeKeys, trendKeys]);


  // -- Drill-Down Rankings Engine (DataTable) --
  const rankingsData = useMemo(() => {
    if (!data?.brand_model_tree) return { rows: [], totalUnits: 0, bevUnits: 0, ptMix: [] };

    const map = new Map<string, Rec>();
    const modelsMap = new Map<string, Rec[]>(); // parentId -> array of model rows

    let totalUnits = 0;
    let bevUnits = 0;
    const ptMixMap: Record<string, number> = { ICE: 0, BEV: 0, HEV: 0, PHEV: 0 };

    data.brand_model_tree.forEach(brandNode => {
      if (rankingPt.length > 0 && !rankingPt.includes(brandNode.powertrain)) return;
      const cleanBrand = normalizeBrandName(brandNode.brand);
      if (rankingBrand.length > 0 && !rankingBrand.includes(cleanBrand)) return;

      const key = cleanBrand;
      if (!map.has(key)) {
         const row: Rec = { 
            id: key, name: cleanBrand, YTD: 0, 
            hasChildren: (brandNode.models?.length ?? 0) > 0, 
            isExpanded: expandedBrands.has(key) 
         };
         timeKeys.forEach(t => row[t] = 0);
         map.set(key, row);
         modelsMap.set(key, []);
      }
      const row = map.get(key)!;
      // Update hasChildren in case we see models later
      if ((brandNode.models?.length ?? 0) > 0) row.hasChildren = true;
      row.isExpanded = expandedBrands.has(key);

      const { timeVals, grandTotal } = getNodeSums(brandNode, selectedYear, selectedVehicleTypes, rankingProvince);
      
      timeKeys.forEach(t => { row[t] = Number(row[t]) + (timeVals[t] || 0); });
      row.YTD = Number(row.YTD) + grandTotal;

      totalUnits += grandTotal;
      if (brandNode.powertrain === "BEV") bevUnits += grandTotal;
      if (brandNode.powertrain in ptMixMap) ptMixMap[brandNode.powertrain] += grandTotal;

      // Calculate models if expanded
      if (expandedBrands.has(key)) {
         brandNode.models?.forEach(model => {
            if (rankingModel.length > 0 && !rankingModel.includes(model.name)) return;
            const mKey = `${key}|${model.name}`;
            const mList = modelsMap.get(key)!;
            let mRow = mList.find(r => r.id === mKey);
            if (!mRow) {
               mRow = { id: mKey, parentId: key, name: model.name, YTD: 0, isSubRow: true };
               timeKeys.forEach(t => mRow![t] = 0);
               mList.push(mRow);
            }
            const mSums = getNodeSums(model, selectedYear, selectedVehicleTypes, rankingProvince);
            timeKeys.forEach(t => { mRow![t] = Number(mRow![t]) + (mSums.timeVals[t] || 0); });
            mRow!.YTD = Number(mRow!.YTD) + mSums.grandTotal;
         });
      }
    });

    // Assemble final flat array correctly preserving hierarchy for the table
    const finalRows: Rec[] = [];
    const sortedBrands = Array.from(map.values())
       .filter(r => Number(r.YTD) > 0)
       .sort((a, b) => Number(b.YTD) - Number(a.YTD))
       .map((r, i) => ({ ...r, rank: i + 1 } as Rec));

    sortedBrands.forEach(b => {
       finalRows.push(b);
       if (expandedBrands.has(String(b.id))) {
          const mList = modelsMap.get(String(b.id)) || [];
          const sortedModels = mList
             .filter(r => Number(r.YTD) > 0)
             .sort((a, b) => Number(b.YTD) - Number(a.YTD));
          finalRows.push(...sortedModels);
       }
    });

    const ptMix = Object.entries(ptMixMap).map(([name, val]) => ({ name, YTD: val })).filter(d => d.YTD > 0);

    return { rows: finalRows, totalUnits, bevUnits, ptMix };
  }, [data, rankingPt, rankingBrand, rankingModel, rankingProvince, expandedBrands, selectedYear, selectedVehicleTypes, timeKeys]);

  // -- Dynamic Group By Engine (Charts) --
  const dynamicChartData = useMemo(() => {
     if (!data?.brand_model_tree) return [];
     const cMap = new Map<string, number>();

     data.brand_model_tree.forEach(brandNode => {
        if (rankingPt.length > 0 && !rankingPt.includes(brandNode.powertrain)) return;
        const cleanBrand = normalizeBrandName(brandNode.brand);
        if (rankingBrand.length > 0 && !rankingBrand.includes(cleanBrand)) return;

        if (chartGroupBy === "Brands") {
           const { grandTotal } = getNodeSums(brandNode, selectedYear, selectedVehicleTypes, rankingProvince);
           cMap.set(cleanBrand, (cMap.get(cleanBrand) || 0) + grandTotal);
        } else if (chartGroupBy === "Models") {
           brandNode.models?.forEach(model => {
              if (rankingModel.length > 0 && !rankingModel.includes(model.name)) return;
              const { grandTotal } = getNodeSums(model, selectedYear, selectedVehicleTypes, rankingProvince);
              const label = `${cleanBrand} ${model.name}`;
              cMap.set(label, (cMap.get(label) || 0) + grandTotal);
           });
        } else if (chartGroupBy === "Provinces") {
           selectedVehicleTypes.forEach(vc => {
              const vcBucket = brandNode.monthly?.[vc];
              if (!vcBucket) return;
              Object.keys(vcBucket).forEach(prov => {
                 if (rankingProvince.length > 0 && !rankingProvince.includes(prov)) return;
                 const pBucket = vcBucket[prov];
                 let pTotal = 0;
                 Object.keys(pBucket).forEach(yStr => {
                    if (selectedYear !== "All" && yStr !== String(selectedYear)) return;
                    const arr = pBucket[yStr];
                    if (Array.isArray(arr)) for (let i=0; i<12; i++) pTotal += arr[i] || 0;
                 });
                 cMap.set(prov, (cMap.get(prov) || 0) + pTotal);
              });
           });
        }
     });

     return Array.from(cMap.entries())
       .map(([name, YTD]) => ({ name, YTD }))
       .sort((a, b) => b.YTD - a.YTD)
       .slice(0, 10);
  }, [data, chartGroupBy, rankingPt, rankingBrand, rankingModel, rankingProvince, selectedYear, selectedVehicleTypes]);


  const toggleBrandExpand = (brandId: string) => {
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

  if (loading) return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-light border-t-transparent"></div>
    </div>
  );

  const tabs = [
    { id: "rankings", label: "Rankings & Leaderboards", icon: Trophy },
    { id: "powertrain", label: "Trend Overview", icon: PieChartIcon },
    { id: "deep-dive", label: "Brand & Model Deep-Dive", icon: Layers, href: "/models.html" },
    { id: "analyst", label: "Analyst Table", icon: Layers, href: "/analyst.html" },
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
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Selected Year</p>
              <p className="mt-1 font-mono text-xl font-semibold tracking-tight text-slate-100">{selectedYear}</p>
            </div>
            {selectedVehicleTypes.length < Object.keys(VEHICLE_TYPE_DICT).length && (
              <>
                <div className="h-8 w-px bg-slate-800" />
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-amber-500">Vehicle Types Active</p>
                  <p className="mt-1 font-mono text-xl font-semibold tracking-tight text-slate-100">
                    {selectedVehicleTypes.length} <span className="text-sm text-slate-500 font-sans font-normal">of {Object.keys(VEHICLE_TYPE_DICT).length}</span>
                  </p>
                </div>
              </>
            )}
          </div>
        </header>

        <div className="p-4 md:p-6">
          {/* Vehicle Type Global Filter */}
          <div className="mb-4 md:mb-6 rounded-sm border border-slate-800 bg-slate-900 overflow-hidden">
            <button
              onClick={() => setShowVehicleFilter(!showVehicleFilter)}
              className="flex w-full items-center justify-between px-3 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800"
            >
              <span className="flex items-center gap-2">
                <Filter className="h-3 w-3 text-slate-400" />
                <span>Global Vehicle Types Filter</span>
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
                        if (e.target.checked) setSelectedVehicleTypes([...selectedVehicleTypes, code]);
                        else setSelectedVehicleTypes(selectedVehicleTypes.filter(t => t !== code));
                      }}
                    />
                    <span className="text-[10px] font-mono text-slate-300">{code}</span>
                  </label>
                ))}
              </div>
            )}
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
                <FilterPillPopover label="Model" placeholder="Models" options={allDataModels} value={rankingModel} onChange={setRankingModel} />
                <FilterPillPopover label="Province" placeholder="Provinces" options={allDataProvinces} value={rankingProvince} onChange={setRankingProvince} />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
                <div className="lg:col-span-2 flex flex-col gap-2">
                  {/* Segmented Control for Dynamic Chart Grouping */}
                  <div className="flex items-center gap-1 self-start rounded-full border border-slate-700 bg-slate-800 p-0.5">
                     {(["Brands", "Models", "Provinces"] as const).map(opt => (
                        <button
                           key={opt}
                           onClick={() => setChartGroupBy(opt)}
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


            {/* ── Trend Overview Tab (Legacy Powertrain) ───────────────── */}
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
