"use client";

import { useEffect, useState } from "react";
import { ClipboardList, Search, X, AlertTriangle, CheckCircle2 } from "lucide-react";

/* Local-only Series Admin review widget (Step 5B).
   Talks directly to the Step 5A stdlib service at 127.0.0.1:8765 — never a
   frontend write route. Rendered only under `next dev`; see page.tsx guard. */

const ADMIN_BASE = "http://127.0.0.1:8765";
const POWERTRAINS = ["ICE", "HEV", "PHEV", "BEV"] as const;
type Powertrain = (typeof POWERTRAINS)[number];

type QueueItem = {
  canonical_brand: string;
  raw_series: string;
  canonical_series: string;
  total_units: number;
  status: string;
};

export function AdminReviewPanel() {
  const [queue, setQueue] = useState<QueueItem[] | null>(null);
  const [serviceDown, setServiceDown] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const loadQueue = () => {
    fetch(`${ADMIN_BASE}/queue`)
      .then((r) => {
        if (!r.ok) throw new Error("bad status");
        return r.json();
      })
      .then((rows: QueueItem[]) => {
        setQueue(rows);
        setServiceDown(false);
      })
      .catch(() => setServiceDown(true));
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const removeFromQueue = (item: QueueItem) => {
    setQueue((prev) => prev?.filter(
      (q) => !(q.canonical_brand === item.canonical_brand && q.raw_series === item.raw_series)
    ) ?? null);
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-wider transition-colors ${
          serviceDown
            ? "border-red-900/60 bg-red-950/30 text-red-300 hover:bg-red-900/40"
            : "border-amber-900/60 bg-amber-950/30 text-amber-300 hover:bg-amber-900/40"
        }`}
      >
        <ClipboardList className="h-3 w-3" />
        {serviceDown ? "Admin service unavailable" : `${queue?.length ?? 0} unresolved series`}
      </button>

      {isOpen && (
        <ReviewModal
          queue={queue ?? []}
          serviceDown={serviceDown}
          onClose={() => setIsOpen(false)}
          onSaved={removeFromQueue}
          onRetry={loadQueue}
        />
      )}
    </>
  );
}

function ReviewModal({ queue, serviceDown, onClose, onSaved, onRetry }: {
  queue: QueueItem[];
  serviceDown: boolean;
  onClose: () => void;
  onSaved: (item: QueueItem) => void;
  onRetry: () => void;
}) {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<QueueItem | null>(null);

  const filtered = queue.filter((q) =>
    `${q.canonical_brand} ${q.raw_series}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true">
      <div className="flex max-h-[85vh] w-full max-w-3xl flex-col rounded-md border border-slate-800 bg-slate-900 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">Series Powertrain Review</h2>
          <button type="button" onClick={onClose} className="text-slate-500 hover:text-slate-200">
            <X className="h-4 w-4" />
          </button>
        </div>

        {serviceDown ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
            <AlertTriangle className="h-8 w-8 text-red-500" />
            <p className="text-xs text-slate-400">Admin service unavailable at {ADMIN_BASE}.</p>
            <button
              type="button"
              onClick={onRetry}
              className="rounded-sm border border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800"
            >
              Retry
            </button>
          </div>
        ) : selected ? (
          <ReviewForm
            item={selected}
            onCancel={() => setSelected(null)}
            onSaved={(item) => {
              onSaved(item);
              setSelected(null);
            }}
          />
        ) : (
          <>
            <div className="border-b border-slate-800 p-3">
              <div className="flex items-center gap-2 rounded-sm border border-slate-800 bg-slate-950 px-2 py-1.5">
                <Search className="h-3.5 w-3.5 text-slate-500" />
                <input
                  autoFocus
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search brand or raw series..."
                  className="w-full bg-transparent text-xs text-slate-200 outline-none placeholder:text-slate-600"
                />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar">
              {filtered.length === 0 ? (
                <p className="p-6 text-center text-xs text-slate-500">
                  {queue.length === 0 ? "No unresolved series — everything is reviewed." : "No matches."}
                </p>
              ) : (
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-slate-900">
                    <tr className="border-b border-slate-800 text-slate-500">
                      <th className="px-3 py-2 text-left font-medium">Brand</th>
                      <th className="px-3 py-2 text-left font-medium">Raw Series</th>
                      <th className="px-3 py-2 text-right font-medium">Units</th>
                      <th className="px-3 py-2 text-left font-medium">Status</th>
                      <th className="px-3 py-2" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {filtered.map((q) => (
                      <tr key={`${q.canonical_brand}/${q.raw_series}`} className="hover:bg-slate-800/60">
                        <td className="px-3 py-2 font-medium text-slate-200">{q.canonical_brand}</td>
                        <td className="px-3 py-2 text-slate-300">{q.raw_series}</td>
                        <td className="px-3 py-2 text-right tabular-nums text-slate-300">{q.total_units.toLocaleString()}</td>
                        <td className="px-3 py-2 text-slate-400">{q.status}</td>
                        <td className="px-3 py-2 text-right">
                          <button
                            type="button"
                            onClick={() => setSelected(q)}
                            className="rounded-sm bg-brand-primary px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-white hover:bg-brand-light"
                          >
                            Review
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ReviewForm({ item, onCancel, onSaved }: {
  item: QueueItem;
  onCancel: () => void;
  onSaved: (item: QueueItem) => void;
}) {
  const [canonicalSeries, setCanonicalSeries] = useState(item.canonical_series);
  const [powertrain, setPowertrain] = useState<Powertrain | null>(null);
  const [evidence, setEvidence] = useState("");
  const [reviewer, setReviewer] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const submit = () => {
    setSaving(true);
    setErrors([]);
    fetch(`${ADMIN_BASE}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        canonical_brand: item.canonical_brand,
        raw_series: item.raw_series,
        canonical_series: canonicalSeries,
        powertrain,
        evidence,
        reviewer,
      }),
    })
      .then(async (r) => {
        const body = await r.json();
        if (!r.ok) {
          setErrors(body.errors ?? ["Save failed."]);
          return;
        }
        setSaved(true);
        setTimeout(() => onSaved(item), 900);
      })
      .catch(() => setErrors(["Could not reach the Admin service."]))
      .finally(() => setSaving(false));
  };

  const canSubmit = canonicalSeries.trim() && powertrain && evidence.trim() && reviewer.trim();

  return (
    <div className="flex flex-1 flex-col overflow-y-auto p-4">
      <button type="button" onClick={onCancel} className="mb-3 self-start text-[10px] font-bold uppercase tracking-wider text-slate-500 hover:text-slate-300">
        ← Back to queue
      </button>

      {saved ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-2 py-8 text-center">
          <CheckCircle2 className="h-8 w-8 text-brand-light" />
          <p className="text-xs font-semibold text-slate-200">Saved.</p>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Canonical Brand"><StaticValue>{item.canonical_brand}</StaticValue></Field>
            <Field label="Raw Series"><StaticValue>{item.raw_series}</StaticValue></Field>
            <Field label="Total Registrations"><StaticValue>{item.total_units.toLocaleString()}</StaticValue></Field>
            <Field label="Status"><StaticValue>{item.status}</StaticValue></Field>
          </div>

          <Field label="Canonical Series">
            <input
              value={canonicalSeries}
              onChange={(e) => setCanonicalSeries(e.target.value)}
              className="w-full rounded-sm border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-slate-200 outline-none focus:border-brand-primary"
            />
          </Field>

          <Field label="Powertrain">
            <div className="flex gap-2">
              {POWERTRAINS.map((pt) => (
                <button
                  key={pt}
                  type="button"
                  onClick={() => setPowertrain(pt)}
                  className={`flex-1 rounded-sm border px-2 py-1.5 text-xs font-semibold transition-colors ${
                    powertrain === pt
                      ? "border-brand-primary bg-brand-primary text-white"
                      : "border-slate-700 text-slate-400 hover:border-slate-500"
                  }`}
                >
                  {pt}
                </button>
              ))}
            </div>
          </Field>

          <Field label="Evidence (required)">
            <textarea
              value={evidence}
              onChange={(e) => setEvidence(e.target.value)}
              rows={2}
              placeholder="e.g. manufacturer spec sheet, official brochure URL..."
              className="w-full resize-none rounded-sm border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-slate-200 outline-none placeholder:text-slate-600 focus:border-brand-primary"
            />
          </Field>

          <Field label="Reviewer (required)">
            <input
              value={reviewer}
              onChange={(e) => setReviewer(e.target.value)}
              className="w-full rounded-sm border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-slate-200 outline-none focus:border-brand-primary"
            />
          </Field>

          {errors.length > 0 && (
            <div role="alert" className="rounded-sm border border-red-900/60 bg-red-950/30 p-2 text-xs text-red-300">
              {errors.map((e, i) => <p key={i}>{e}</p>)}
            </div>
          )}

          <button
            type="button"
            disabled={!canSubmit || saving}
            onClick={submit}
            className="w-full rounded-sm bg-brand-primary px-3 py-2 text-xs font-bold uppercase tracking-wider text-white transition-colors hover:bg-brand-light disabled:cursor-not-allowed disabled:opacity-40"
          >
            {saving ? "Saving..." : "Save Review"}
          </button>
        </div>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</span>
      {children}
    </label>
  );
}

function StaticValue({ children }: { children: React.ReactNode }) {
  return <div className="rounded-sm border border-slate-800 bg-slate-950/60 px-2 py-1.5 text-xs text-slate-300">{children}</div>;
}
