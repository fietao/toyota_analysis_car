"use client";

import { useEffect, useId, useState, useRef } from "react";
import { ChevronDown, Check, Search } from "lucide-react";

export function FilterPillPopover({
  options,
  value,
  onChange,
  label,
  placeholder,
  singleSelect = false,
  onOpen
}: {
  options: (string | { id: string, label: string })[];
  value: string[];
  onChange: (v: string[]) => void;
  label: string;
  placeholder?: string;
  singleSelect?: boolean;
  onOpen?: () => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  const popupId = useId();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) setIsOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const normalizedOptions = options.map(o => typeof o === 'string' ? { id: o, label: o } : o);
  const filtered = normalizedOptions.filter(o => o.label.toLowerCase().includes(search.toLowerCase()) || o.id.toLowerCase().includes(search.toLowerCase()));

  const toggleOpt = (optId: string) => {
    if (singleSelect) {
      if (value.includes(optId)) {
        onChange([]);
      } else {
        onChange([optId]);
        setIsOpen(false);
      }
    } else {
      if (value.includes(optId)) onChange(value.filter(v => v !== optId));
      else onChange([...value, optId]);
    }
  };

  const btnText = value.length === 0 ? "All" : (singleSelect ? (normalizedOptions.find(o => o.id === value[0])?.label || value[0]) : `${value.length} / ${options.length}`);

  return (
    <div ref={ref} className="relative inline-block">
      <button
        type="button"
        onClick={() => {
          const next = !isOpen;
          setIsOpen(next);
          if (next) onOpen?.();
        }}
        aria-haspopup="true"
        aria-expanded={isOpen}
        aria-controls={popupId}
        className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
          value.length > 0
            ? "border-[#169387] bg-[#169387]/10 text-slate-100"
            : "border-slate-700 bg-slate-800 text-slate-300 hover:border-slate-500"
        }`}
      >
        <span>{label}: {btnText}</span>
        <ChevronDown className="h-3 w-3 opacity-70" />
      </button>

      {isOpen && (
        <div id={popupId} className="absolute z-50 mt-2 w-[300px] rounded-sm border border-slate-700 bg-slate-800">
          <div className="p-2 border-b border-slate-700">
            <div className="flex items-center rounded-sm bg-slate-900 px-2 py-1 text-xs border border-slate-700">
              <Search className="h-3 w-3 text-slate-500 mr-2" />
              <input
                type="text"
                autoFocus
                className="w-full bg-transparent text-slate-200 outline-none placeholder:text-slate-500"
                placeholder={placeholder || "Search..."}
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
          </div>
          <div className="max-h-60 overflow-y-auto custom-scrollbar p-1">
            {!singleSelect && (
              <label className={`flex w-full cursor-pointer items-center justify-between rounded-sm px-2 py-1.5 text-xs focus-within:ring-1 focus-within:ring-[#169387] ${value.length === 0 ? "bg-[#169387]/20 text-slate-100" : "text-slate-300 hover:bg-slate-700"}`}>
                <span>All {label}</span>
                <input type="checkbox" className="sr-only" checked={value.length === 0} onChange={() => onChange([])} />
                {value.length === 0 && <Check className="h-3 w-3" />}
              </label>
            )}
            {singleSelect && value.length > 0 && (
              <button
                type="button"
                className="flex w-full cursor-pointer items-center justify-between rounded-sm px-2 py-1.5 text-xs text-slate-300 hover:bg-slate-700"
                onClick={() => { onChange([]); setIsOpen(false); }}
              >
                <span>Clear Selection</span>
              </button>
            )}
            {filtered.map(opt => {
              const isChecked = value.includes(opt.id);
              return (
                <label key={opt.id} className={`flex w-full cursor-pointer items-center justify-between rounded-sm px-2 py-1.5 text-xs focus-within:ring-1 focus-within:ring-[#169387] ${isChecked ? "bg-[#169387]/20 text-slate-100" : "text-slate-300 hover:bg-slate-700"}`}>
                  <span className="truncate pr-2">{opt.label}</span>
                  <input type="checkbox" className="sr-only" checked={isChecked} onChange={() => toggleOpt(opt.id)} />
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
