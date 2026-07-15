"""Export the canonical Manual Report (sheets 1-9) to frontend/public/data/manual_report.json.

This is the single source the /report page renders. It reproduces the markdown workbook
"รถใหม่ ... (test analyst)" sheets 1-9 so the frontend never recomputes spreadsheet logic.

Source rules (from specs/public_dashboard_markdown_parity_spec.md):
  * Sheets 1-6 and 9 -> test_fuel_cleaned.parquet, fuel-derived powertrain (PT).
  * Sheets 7-8      -> test_model_cleaned.parquet, model-table Powertrain == "BEV Major".
  * Vehicle types default to รย.1,2,3,6,9,10,11.
  * Current period is auto-detected from the fuel parquet (never hardcoded).

Known parity notes (do not "fix" by changing the source):
  * Fuel-derived sheets (1-6, 9) match the markdown exactly.
  * Model-table BEV Major (7-8) sits ~1% below the markdown because the workbook's
    BEV-by-model came through the BEV Series Name Table review layer. This is the
    documented open issue (BYD 2568: fuel 33,070 / markdown 33,077 / model BEV Major 31,536).
    validate_against_markdown.py reports these as known, non-blocking mismatches.
"""
import sys
import json
import datetime
from pathlib import Path

import pandas as pd

from export_dashboard import load_data, MONTH_MAP, FULL_MONTH_EN
from aggregate import current_period

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent
FUEL_PARQUET = BASE / "test_fuel_cleaned.parquet"
MODEL_PARQUET = BASE / "test_model_cleaned.parquet"
OUT = BASE.parent / "frontend" / "public" / "data" / "manual_report.json"

DEFAULT_VEHICLE_TYPES = ["รย.1", "รย.2", "รย.3", "รย.6", "รย.9", "รย.10", "รย.11"]
MONTHS = list(MONTH_MAP.values())  # Jan .. Dec
POWERTRAIN_ROWS = ["ICE", "BEV", "HEV", "PHEV"]


def _safe_div(num, den):
    return (num / den) if den else None


def month_matrix(df: pd.DataFrame, key_col: str) -> dict:
    """key -> {year -> [12 monthly ints]} from an already-filtered frame."""
    grp = df.groupby([key_col, "ปี", "เดือน"], observed=True)["จำนวนรถ"].sum()
    out: dict = {}
    for (key, year, month), units in grp.items():
        if month not in MONTHS:
            continue
        mi = MONTHS.index(month)
        out.setdefault(key, {}).setdefault(int(year), [0] * 12)
        out[key][int(year)][mi] += int(units)
    return out


def build_rows(mat: dict, latest_year: int, prev_year: int, lm_idx: int, *, ranked: bool) -> list:
    """Turn a month-matrix into report rows with a pinned Grand Total first.

    lm_idx is the 0-based index of the latest month (e.g. Jun -> 5).
    Every row carries the full field set the frontend renders without recomputation.
    """
    details = []
    for key, years in mat.items():
        prev_months = list(years.get(prev_year, [0] * 12))
        curr_months = list(years.get(latest_year, [0] * 12))
        prev_total = sum(prev_months)
        prev_ytd = sum(prev_months[: lm_idx + 1])
        curr_ytd = sum(curr_months[: lm_idx + 1])
        if prev_total == 0 and curr_ytd == 0:
            continue
        details.append({
            "key": str(key),
            "label": str(key),
            "prev_months": prev_months,
            "curr_months": curr_months,
            "prev_total": prev_total,
            "prev_ytd": prev_ytd,
            "curr_ytd": curr_ytd,
        })

    # Grand Total (sum of all detail rows)
    gt_prev = [0] * 12
    gt_curr = [0] * 12
    for r in details:
        for i in range(12):
            gt_prev[i] += r["prev_months"][i]
            gt_curr[i] += r["curr_months"][i]
    grand = {
        "key": "Grand Total",
        "label": "Grand Total",
        "prev_months": gt_prev,
        "curr_months": gt_curr,
        "prev_total": sum(gt_prev),
        "prev_ytd": sum(gt_prev[: lm_idx + 1]),
        "curr_ytd": sum(gt_curr[: lm_idx + 1]),
    }

    # Ranks over detail rows only
    if ranked:
        for r in details:
            r["_pt"] = r["prev_total"]
            r["_ct"] = r["curr_ytd"]
        prev_order = sorted(details, key=lambda r: -r["_pt"])
        curr_order = sorted(details, key=lambda r: -r["_ct"])
        prev_rank = {r["key"]: i + 1 for i, r in enumerate(prev_order)}
        curr_rank = {r["key"]: i + 1 for i, r in enumerate(curr_order)}
    else:
        prev_rank = curr_rank = {}

    base_prev_total = grand["prev_total"]
    base_prev_ytd = grand["prev_ytd"]
    base_curr_ytd = grand["curr_ytd"]

    def finalize(r: dict, is_grand: bool) -> dict:
        cm = r["curr_months"][lm_idx]
        pm = r["curr_months"][lm_idx - 1] if lm_idx > 0 else 0
        sm = r["prev_months"][lm_idx]
        row = {
            "key": r["key"],
            "label": r["label"],
            "prev_months": r["prev_months"],
            "prev_total": r["prev_total"],
            "prev_ytd": r["prev_ytd"],
            "prev_total_share": _safe_div(r["prev_total"], base_prev_total),
            "prev_ytd_share": _safe_div(r["prev_ytd"], base_prev_ytd),
            "curr_months": r["curr_months"],
            "curr_ytd": r["curr_ytd"],
            "curr_ytd_share": _safe_div(r["curr_ytd"], base_curr_ytd),
            "growth_vs_prev_month": _safe_div(cm - pm, pm),
            "growth_vs_same_month_prev_year": _safe_div(cm - sm, sm),
            "growth_vs_prev_ytd": _safe_div(r["curr_ytd"] - r["prev_ytd"], r["prev_ytd"]),
        }
        if ranked and not is_grand:
            pr = prev_rank.get(r["key"])
            cr = curr_rank.get(r["key"])
            row["prev_rank"] = pr
            row["curr_rank"] = cr
            row["rank_diff"] = (pr - cr) if (pr and cr) else None
        elif ranked:
            row["prev_rank"] = None
            row["curr_rank"] = None
            row["rank_diff"] = None
        return row

    ordered = sorted(details, key=lambda r: -r["curr_ytd"])
    return [finalize(grand, True)] + [finalize(r, False) for r in ordered]


def sheet_powertrain(df_fuel: pd.DataFrame, ly, py, lm) -> list:
    d = df_fuel[df_fuel["PT"].isin(POWERTRAIN_ROWS)]
    mat = month_matrix(d, "PT")
    # ensure all four powertrain rows exist even if empty
    for pt in POWERTRAIN_ROWS:
        mat.setdefault(pt, {})
    rows = build_rows(mat, ly, py, lm, ranked=False)
    # order details ICE, BEV, HEV, PHEV (grand stays first)
    order = {pt: i for i, pt in enumerate(POWERTRAIN_ROWS)}
    grand, details = rows[0], rows[1:]
    details.sort(key=lambda r: order.get(r["key"], 99))
    return [grand] + details


def sheet_brand(df_fuel: pd.DataFrame, ly, py, lm, powertrain=None) -> list:
    d = df_fuel if powertrain is None else df_fuel[df_fuel["PT"] == powertrain]
    mat = month_matrix(d, "ยี่ห้อรถ2")
    return build_rows(mat, ly, py, lm, ranked=True)


def sheet_bev_by_model(df_model: pd.DataFrame, ly, py, lm) -> list:
    """Brand header rows + child model rows, both from model-table BEV Major slice."""
    d = df_model[df_model["Powertrain"] == "BEV Major"]
    brand_mat = month_matrix(d, "ยี่ห้อรถ2")
    brand_rows = build_rows(brand_mat, ly, py, lm, ranked=True)
    grand, brand_details = brand_rows[0], brand_rows[1:]

    # model rows per brand
    model_mat_by_brand: dict = {}
    for brand, sub in d.groupby("ยี่ห้อรถ2", observed=True):
        model_mat_by_brand[brand] = build_rows(
            month_matrix(sub, "รุ่นรถ2"), ly, py, lm, ranked=False
        )[1:]  # drop the per-brand grand total

    grand["level"] = "grand"
    out = [grand]
    for b in brand_details:
        b["level"] = "brand"
        b["group"] = b["key"]
        out.append(b)
        for m in sorted(model_mat_by_brand.get(b["key"], []), key=lambda r: -r["curr_ytd"]):
            m["level"] = "model"
            m["group"] = b["key"]
            m["brand"] = b["key"]
            out.append(m)
    return out


def sheet_model_top_rank(df_model: pd.DataFrame, ly, py, lm) -> list:
    """Flat model ranking (brand||model) from model-table BEV Major slice."""
    d = df_model[df_model["Powertrain"] == "BEV Major"].copy()
    d["_mk"] = d["ยี่ห้อรถ2"].astype(str) + " || " + d["รุ่นรถ2"].astype(str)
    label_map = d.drop_duplicates("_mk").set_index("_mk")[["ยี่ห้อรถ2", "รุ่นรถ2"]].to_dict("index")
    mat = month_matrix(d, "_mk")
    rows = build_rows(mat, ly, py, lm, ranked=True)
    for r in rows:
        info = label_map.get(r["key"])
        if info:
            r["brand"] = info["ยี่ห้อรถ2"]
            r["model"] = info["รุ่นรถ2"]
            r["label"] = f'{info["รุ่นรถ2"]}  ·  {info["ยี่ห้อรถ2"]}'
    return rows


def sheet_by_province(df_fuel: pd.DataFrame, ly, py, lm) -> list:
    """Province header rows + child brand rows; each row also carries an overall total."""
    prov_rows = build_rows(month_matrix(df_fuel, "จังหวัด"), ly, py, lm, ranked=False)
    grand, prov_details = prov_rows[0], prov_rows[1:]

    brand_by_prov: dict = {}
    for prov, sub in df_fuel.groupby("จังหวัด", observed=True):
        brand_by_prov[prov] = build_rows(month_matrix(sub, "ยี่ห้อรถ2"), ly, py, lm, ranked=False)[1:]

    def with_overall(r):
        r["overall"] = r["prev_total"] + r["curr_ytd"]
        return r

    grand["level"] = "grand"
    out = [with_overall(grand)]
    prov_details.sort(key=lambda r: -(r["prev_total"] + r["curr_ytd"]))
    for p in prov_details:
        p["level"] = "province"
        p["group"] = p["key"]
        out.append(with_overall(p))
        for b in sorted(brand_by_prov.get(p["key"], []), key=lambda r: -(r["prev_total"] + r["curr_ytd"])):
            b["level"] = "brand"
            b["group"] = p["key"]
            out.append(with_overall(b))
    return out


def export():
    for p in (FUEL_PARQUET, MODEL_PARQUET):
        if not p.exists():
            print(f"ERROR: parquet not found: {p}")
            sys.exit(1)

    print(f"Reading {FUEL_PARQUET.name} ...")
    fuel = load_data(FUEL_PARQUET)
    print(f"Reading {MODEL_PARQUET.name} ...")
    model = load_data(MODEL_PARQUET)

    # Vehicle-type filter (default markdown set)
    fuel = fuel[fuel["v_code"].isin(DEFAULT_VEHICLE_TYPES)].copy()
    model = model[model["v_code"].isin(DEFAULT_VEHICLE_TYPES)].copy()

    latest_year, latest_month_num = current_period(fuel, year_col="ปี", month_col="เดือน", month_order=MONTHS)
    prev_year = latest_year - 1
    lm_idx = latest_month_num - 1
    latest_month = MONTHS[lm_idx]
    reporting_period = f"{FULL_MONTH_EN.get(latest_month, latest_month)} {latest_year}"
    print(f"Reporting period: {reporting_period} (prev year {prev_year}, YTD through month {latest_month_num})")

    sheets = {
        "sheet1_powertrain": sheet_powertrain(fuel, latest_year, prev_year, lm_idx),
        "sheet2_brand_all": sheet_brand(fuel, latest_year, prev_year, lm_idx, powertrain=None),
        "sheet3_brand_ice": sheet_brand(fuel, latest_year, prev_year, lm_idx, powertrain="ICE"),
        "sheet4_brand_bev": sheet_brand(fuel, latest_year, prev_year, lm_idx, powertrain="BEV"),
        "sheet5_brand_hev": sheet_brand(fuel, latest_year, prev_year, lm_idx, powertrain="HEV"),
        "sheet6_brand_phev": sheet_brand(fuel, latest_year, prev_year, lm_idx, powertrain="PHEV"),
        "sheet7_bev_by_model": sheet_bev_by_model(model, latest_year, prev_year, lm_idx),
        "sheet8_model_top_rank": sheet_model_top_rank(model, latest_year, prev_year, lm_idx),
        "sheet9_by_province": sheet_by_province(fuel, latest_year, prev_year, lm_idx),
    }

    vt_label = "ประเภทรถ = รย.1,2,3,6,9,10,11"
    sections = {
        "sheet1_powertrain": {"title": "1.Reg by Powertrain", "source": "test_fuel_cleaned.parquet", "filter": vt_label, "powertrain": "ICE/BEV/HEV/PHEV"},
        "sheet2_brand_all": {"title": "2.Rank by Brand", "source": "test_fuel_cleaned.parquet", "filter": vt_label, "powertrain": "All"},
        "sheet3_brand_ice": {"title": "3.ICE by Brand", "source": "test_fuel_cleaned.parquet", "filter": vt_label, "powertrain": "ICE (fuel-derived)"},
        "sheet4_brand_bev": {"title": "4.BEV by Brand", "source": "test_fuel_cleaned.parquet", "filter": vt_label, "powertrain": "BEV (fuel-derived)"},
        "sheet5_brand_hev": {"title": "5.HEV by Brand", "source": "test_fuel_cleaned.parquet", "filter": vt_label, "powertrain": "HEV (fuel-derived)"},
        "sheet6_brand_phev": {"title": "6.PHEV by Brand", "source": "test_fuel_cleaned.parquet", "filter": vt_label, "powertrain": "PHEV (fuel-derived)"},
        "sheet7_bev_by_model": {"title": "7.BEV by Model", "source": "test_model_cleaned.parquet", "filter": vt_label, "powertrain": 'model-table Powertrain == "BEV Major"'},
        "sheet8_model_top_rank": {"title": "8.Model Top Rank", "source": "test_model_cleaned.parquet", "filter": vt_label, "powertrain": 'model-table Powertrain == "BEV Major"'},
        "sheet9_by_province": {"title": "9.by Province", "source": "test_fuel_cleaned.parquet", "filter": vt_label, "powertrain": "All"},
    }

    payload = {
        "meta": {
            "reporting_period": reporting_period,
            "latest_year": latest_year,
            "latest_month": latest_month,
            "latest_month_num": latest_month_num,
            "prev_year": prev_year,
            "months": MONTHS,
            "default_vehicle_types": DEFAULT_VEHICLE_TYPES,
            "source_files": {
                "brand_powertrain": "test_fuel_cleaned.parquet",
                "model": "test_model_cleaned.parquet",
            },
            "sections": sections,
            "known_mismatches": [
                {
                    "sheets": ["sheet7_bev_by_model", "sheet8_model_top_rank"],
                    "row": "model-table BEV Major totals",
                    "note": "Sheets 7-8 use model-table Powertrain=='BEV Major', a slightly older BEV-review "
                            "vintage than the markdown workbook, so BEV model totals sit ~1% below it "
                            "(e.g. BYD 2568: model BEV Major 31,536 vs workbook 33,077; JAECOO 5 EV 2569 "
                            "11,133 vs 11,137). Fuel-derived sheets (1-6, 9) match the markdown exactly. "
                            "Documented, non-blocking.",
                }
            ],
            "generated_at": datetime.datetime.now().isoformat(),
        },
        "sheets": sheets,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    size_kb = OUT.stat().st_size / 1024
    print(f"Wrote {OUT.relative_to(BASE.parent)} ({size_kb:.0f} KB)")
    for sid, rows in sheets.items():
        print(f"  {sid}: {len(rows)} rows")


if __name__ == "__main__":
    export()
