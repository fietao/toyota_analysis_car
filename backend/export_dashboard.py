"""Export multi-year dashboard data from parquet to flat JSON."""
import sys
import json
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent
MODEL_PARQUET = BASE / "test_model_cleaned.parquet"
FUEL_PARQUET  = BASE / "test_fuel_cleaned.parquet"
FRONTEND_DATA_DIR = BASE.parent / "frontend" / "public" / "data"
FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Master dictionary for vehicle types from user prompt
VEHICLE_TYPE_DICT = {
    "รย.1": "รย.1 (รถยนต์นั่งส่วนบุคคลไม่เกิน 7 คน / เก๋ง)",
    "รย.2": "รย.2 (รถยนต์นั่งส่วนบุคคลเกิน 7 คน / ตู้)",
    "รย.3": "รย.3 (รถยนต์บรรทุกส่วนบุคคล / กระบะ)",
    "รย.6": "รย.6 (รถยนต์รับจ้างบรรทุกคนโดยสารไม่เกิน 7 คน / แท็กซี่)",
    "รย.9": "รย.9 (รถยนต์บริการธุรกิจ / รถเช่า)",
    "รย.10": "รย.10 (รถยนต์บริการทัศนาจร / รถตู้เช่า)",
    "รย.11": "รย.11 (รถยนต์บริการให้เช่า)"
}

INCLUDE_RY = {"1", "2", "3", "6", "9", "10", "11"}

# User's strict mapping for fuel
FUEL_MAP = {
    "CNG": "ICE",
    "CNG-LPG": "ICE",
    "CNG-ดีเซล": "ICE",
    "CNG-เบนซิน": "ICE",
    "LPG-ดีเซล-ไฟฟ้าแบบเสียบปลั๊ก": "PHEV",
    "LPG-เบนซิน-ไฟฟ้า": "HEV",
    "LPGและดีเซล": "ICE",
    "LPGและเบนซิน": "ICE",
    "ก๊าซ LPG": "ICE",
    "ดีเซล": "ICE",
    "ดีเซล-ไฟฟ้า": "HEV",
    "ดีเซล-ไฟฟ้าแบบเสียบปลั๊ก": "PHEV",
    "เบนซิน": "ICE",
    "เบนซิน-ไฟฟ้า": "HEV",
    "เบนซิน-ไฟฟ้าแบบเสียบปลั๊ก": "PHEV",
    "ไฟฟ้า": "BEV",
    "ไม่ใช้เชื้อเพลิง": "N/A",
    "ไฮโดรเจน": "ICE",
    "CNG-LPG-ดีเซล": "ICE",
    "CNG-LPG-เบนซิน": "ICE",
    "CNG-ดีเซล-ไฟฟ้า": "HEV",
    "CNG-ดีเซล-ไฟฟ้าแบบเสียบปลั๊ก": "PHEV",
    "CNG-เบนซิน-ไฟฟ้า": "HEV",
    "CNG-เบนซิน-ไฟฟ้าแบบเสียบปลั๊ก": "PHEV",
    "LNG": "ICE",
    "LNG-ดีเซล": "ICE",
    "LPG-ดีเซล-ไฟฟ้า": "HEV",
    "LPG-เบนซิน-ไฟฟ้าแบบเสียบปลั๊ก": "PHEV",
    "ไม่ใช้เชื้อเพลิง-ไฟฟ้า": "N/A",
    "เบนซิน-E20": "ICE",
    "เบนซิน-เอทานอล": "ICE",
    "ไม่มีข้อมูล": "N/A"
}

MONTH_MAP = {
    "มกราคม": "Jan", "กุมภาพันธ์": "Feb", "มีนาคม": "Mar",
    "เมษายน": "Apr", "พฤษภาคม": "May", "มิถุนายน": "Jun",
    "กรกฎาคม": "Jul", "สิงหาคม": "Aug", "กันยายน": "Sep",
    "ตุลาคม": "Oct", "พฤศจิกายน": "Nov", "ธันวาคม": "Dec",
}

MONTH_IDX = {m: i for i, m in enumerate(MONTH_MAP.values())}

PT_FUEL_LABEL = {
    "BEV": "ไฟฟ้า (BEV)", "HEV": "ไฮบริด (HEV)",
    "PHEV": "ปลั๊กอินไฮบริด (PHEV)", "ICE": "เครื่องยนต์สันดาป (ICE)",
}

def build_brand_model_tree(df_brand: pd.DataFrame, df_model_rows: pd.DataFrame) -> list:
    """Brand monthly totals from df_brand (fuel parquet), model rows from df_model_rows (model parquet)."""
    # Brand-level monthly from fuel parquet
    brand_grp = df_brand.groupby(["ยี่ห้อรถ2", "PT", "v_code", "จังหวัด", "ปี", "เดือน"])["จำนวนรถ"].sum().reset_index()
    brand_grp = brand_grp[brand_grp["จำนวนรถ"] > 0]

    brand_map: dict = {}
    for _, row in brand_grp.iterrows():
        b, pt, vc = row["ยี่ห้อรถ2"], row["PT"], row["v_code"]
        province = row["จังหวัด"]
        year, m_idx, u = str(int(row["ปี"])), MONTH_IDX.get(row["เดือน"]), int(row["จำนวนรถ"])
        if m_idx is None:
            continue
        fuel_label = PT_FUEL_LABEL.get(pt, pt)
        bkey = f"{b}||{pt}"
        if bkey not in brand_map:
            brand_map[bkey] = {"brand": b, "powertrain": pt, "fuel": fuel_label, "monthly": {}, "models": {}}
        bn = brand_map[bkey]
        bn_p = bn["monthly"].setdefault(vc, {}).setdefault(province, {})
        bn_p.setdefault(year, [0] * 12)[m_idx] += u

    # Model-level monthly from model parquet
    model_grp = df_model_rows.groupby(["ยี่ห้อรถ2", "รุ่นรถ2", "PT", "v_code", "จังหวัด", "ปี", "เดือน"])["จำนวนรถ"].sum().reset_index()
    model_grp = model_grp[model_grp["จำนวนรถ"] > 0]

    for _, row in model_grp.iterrows():
        b, mod, pt, vc = row["ยี่ห้อรถ2"], row["รุ่นรถ2"], row["PT"], row["v_code"]
        province = row["จังหวัด"]
        year, m_idx, u = str(int(row["ปี"])), MONTH_IDX.get(row["เดือน"]), int(row["จำนวนรถ"])
        if m_idx is None:
            continue
        fuel_label = PT_FUEL_LABEL.get(pt, pt)
        bkey = f"{b}||{pt}"
        if bkey not in brand_map:
            brand_map[bkey] = {"brand": b, "powertrain": pt, "fuel": fuel_label, "monthly": {}, "models": {}}
        bn = brand_map[bkey]
        if mod not in bn["models"]:
            bn["models"][mod] = {"name": mod, "fuel": fuel_label, "monthly": {}}
        mn = bn["models"][mod]
        mn_p = mn["monthly"].setdefault(vc, {}).setdefault(province, {})
        mn_p.setdefault(year, [0] * 12)[m_idx] += u

    def total(node: dict) -> int:
        return sum(
            sum(arr)
            for province_buckets in node["monthly"].values()
            for year_buckets in province_buckets.values()
            for arr in year_buckets.values()
        )

    result = []
    for bn in sorted(brand_map.values(), key=lambda x: -total(x)):
        result.append({
            "brand": bn["brand"], "powertrain": bn["powertrain"], "fuel": bn["fuel"],
            "monthly": bn["monthly"],
            "models": sorted(bn["models"].values(), key=lambda x: -total(x)),
        })
    return result


def short_code(label: str) -> str:
    import re
    return re.split(r'[\s(]', str(label))[0].strip()

def load_data(parquet: Path) -> pd.DataFrame:
    df = pd.read_parquet(str(parquet))

    # Strip whitespace from ประเภทรถ to match correctly
    df["ประเภทรถ"] = df["ประเภทรถ"].astype(str).str.strip()

    # Extract just the numbers for "รย.XX" to normalize them
    codes = df["ประเภทรถ"].str.extract(r"รย\.\s*0*(\d+)")[0]

    # Create clean vehicle type column
    df["v_code"] = "รย." + codes
    df["v_code"] = df["v_code"].fillna(df["ประเภทรถ"])

    # Map to full Thai name if in dictionary, otherwise keep the source label.
    df["v"] = df["v_code"].map(VEHICLE_TYPE_DICT).fillna(df["ประเภทรถ"])

    # Apply exact Powertrain mapping from ชนิดเชื้อเพลิง
    df["PT"] = df["ชนิดเชื้อเพลิง"].map(FUEL_MAP)
    df["PT"] = df["PT"].fillna("N/A")

    df["จำนวนรถ"] = pd.to_numeric(df["จำนวนรถ"], errors="coerce").fillna(0).astype(int)
    df["ปี"] = pd.to_numeric(df["ปี"], errors="coerce").dropna().astype(int)
    df["เดือน"] = df["เดือน"].map(MONTH_MAP)
    df = df.dropna(subset=["ปี", "เดือน"])
    df["จังหวัด"] = df["จังหวัด"].fillna("ไม่ระบุจังหวัด").astype(str).str.strip()
    df.loc[df["จังหวัด"] == "", "จังหวัด"] = "ไม่ระบุจังหวัด"
    return df

def _ry_filter(df: pd.DataFrame) -> pd.DataFrame:
    v_num = df["v_code"].str.extract(r"รย\.(\d+)")[0]
    return df[v_num.isin(INCLUDE_RY)]

def export_data():
    missing = [p for p in [MODEL_PARQUET, FUEL_PARQUET] if not p.exists()]
    if missing:
        print(f"Parquet not found: {', '.join(str(p) for p in missing)}")
        return

    print(f"Reading {MODEL_PARQUET.name} for model data...")
    df_model_all = load_data(MODEL_PARQUET)
    df_model_all["ชนิดเชื้อเพลิง"] = df_model_all["ชนิดเชื้อเพลิง"].fillna("")
    print(f"  {len(df_model_all):,} model rows loaded")

    print(f"Reading {FUEL_PARQUET.name} for brand/powertrain data...")
    df_fuel_all = load_data(FUEL_PARQUET)
    df_fuel_all["ชนิดเชื้อเพลิง"] = df_fuel_all["ชนิดเชื้อเพลิง"].fillna("")
    print(f"  {len(df_fuel_all):,} fuel rows loaded")

    # Apply รย filter to both parquets
    df = _ry_filter(df_model_all)
    df_fuel = _ry_filter(df_fuel_all)
    print(f"  {len(df):,} model rows after รย filter")
    print(f"  {len(df_fuel):,} fuel rows after รย filter")

    # 1. Powertrain master from fuel parquet + รย filter
    pm_grp = df_fuel.groupby(["ชนิดเชื้อเพลิง", "PT", "ปี"])["จำนวนรถ"].sum().reset_index()
    pm_grp = pm_grp[pm_grp["จำนวนรถ"] > 0]
    pm_data = []
    for _, row in pm_grp.iterrows():
        pm_data.append({
            "f": row["ชนิดเชื้อเพลิง"], "pt": row["PT"],
            "y": int(row["ปี"]), "u": int(row["จำนวนรถ"])
        })

    # 2. Brand/model tree — fuel for brand monthly, model for model rows, both รย-filtered
    print("  Building brand_model_tree...")
    brand_model_tree = build_brand_model_tree(df_fuel, df)
    tree_total = sum(
        sum(arr)
        for bn in brand_model_tree
        for province_buckets in bn["monthly"].values()
        for year_buckets in province_buckets.values()
        for arr in year_buckets.values()
    )
    print(f"  brand_model_tree total units (fuel, รย-filtered): {tree_total:,}")

    # 3. Fuel & Powertrain monthly (from fuel parquet)
    fuel_grp = df_fuel.groupby(["ปี", "เดือน", "PT", "ชนิดเชื้อเพลิง", "v"])["จำนวนรถ"].sum().reset_index()
    fuel_grp = fuel_grp[fuel_grp["จำนวนรถ"] > 0]
    fuel_data = []
    for _, row in fuel_grp.iterrows():
        fuel_data.append({
            "y": int(row["ปี"]), "m": row["เดือน"], "pt": row["PT"],
            "f": row["ชนิดเชื้อเพลิง"], "v": short_code(row["v"]), "u": int(row["จำนวนรถ"])
        })

    # 4. Brand monthly (from fuel parquet)
    brand_grp = df_fuel.groupby(["ปี", "เดือน", "PT", "ยี่ห้อรถ2", "v"])["จำนวนรถ"].sum().reset_index()
    brand_grp = brand_grp[brand_grp["จำนวนรถ"] > 0]
    brand_data = []
    for _, row in brand_grp.iterrows():
        brand_data.append({
            "y": int(row["ปี"]), "m": row["เดือน"], "pt": row["PT"],
            "b": row["ยี่ห้อรถ2"], "v": short_code(row["v"]), "u": int(row["จำนวนรถ"])
        })

    # 5. Model monthly from model parquet (BEV/HEV/PHEV/BMW — approximate fuel, exact model)
    model_df = df[(df["PT"] == "BEV") | (df["ยี่ห้อรถ2"] == "BMW") | (df["PT"] == "PHEV") | (df["PT"] == "HEV")]
    model_grp = model_df.groupby(["ปี", "เดือน", "PT", "ยี่ห้อรถ2", "รุ่นรถ2", "v"])["จำนวนรถ"].sum().reset_index()
    model_grp = model_grp[model_grp["จำนวนรถ"] > 0]
    model_data = []
    for _, row in model_grp.iterrows():
        model_data.append({
            "y": int(row["ปี"]), "m": row["เดือน"], "pt": row["PT"],
            "b": row["ยี่ห้อรถ2"], "mod": row["รุ่นรถ2"], "v": short_code(row["v"]), "u": int(row["จำนวนรถ"])
        })

    # Meta from model parquet (has province + full vehicle type list)
    years = sorted(df_model_all["ปี"].unique().tolist())
    all_v = sorted(df["v"].unique().tolist())
    provinces = sorted(df_model_all["จังหวัด"].unique().tolist())
    vehicle_labels = (
        df_model_all[["v_code", "v"]]
        .drop_duplicates()
        .sort_values("v_code", key=lambda s: s.str.extract(r"(\d+)")[0].astype(int))
    )
    vehicle_types_list = [
        {"code": row["v_code"], "label": row["v"]}
        for _, row in vehicle_labels.iterrows()
    ]

    # --- BRAND FOCUS ---
    TARGET_BRAND = "Deepal+ChangAn"
    BEV_PT = "BEV"

    month_order = list(MONTH_MAP.values())
    
    all_periods = set((row["y"], row["m"]) for row in brand_data)
    sorted_periods = sorted(list(all_periods), key=lambda x: (x[0], month_order.index(x[1])))
    latest_y, latest_m = sorted_periods[-1] if sorted_periods else (None, None)

    if latest_y is not None:
        latest_m_idx = month_order.index(latest_m)
        if latest_m_idx == 0:
            prev_m_idx = 11
            prev_y = latest_y - 1
        else:
            prev_m_idx = latest_m_idx - 1
            prev_y = latest_y
        prev_m = month_order[prev_m_idx]

        monthly_units_dict = {}
        monthly_bev_dict = {}
        total_bev_monthly_dict = {}
        latest_month_bev = {}

        for row in brand_data:
            k = (row["y"], row["m"])
            u = row["u"]
            b = row["b"]
            pt = row["pt"]
            
            if b == TARGET_BRAND:
                monthly_units_dict[k] = monthly_units_dict.get(k, 0) + u
                if pt == BEV_PT:
                    monthly_bev_dict[k] = monthly_bev_dict.get(k, 0) + u
                    
            if pt == BEV_PT:
                total_bev_monthly_dict[k] = total_bev_monthly_dict.get(k, 0) + u
                if k == (latest_y, latest_m):
                    latest_month_bev[b] = latest_month_bev.get(b, 0) + u

        monthly_units = []
        monthly_bev = []
        bev_share_monthly = []

        for y, m in sorted_periods:
            k = (y, m)
            mu = monthly_units_dict.get(k, 0)
            mbev = monthly_bev_dict.get(k, 0)
            tbev = total_bev_monthly_dict.get(k, 0)
            
            monthly_units.append({"y": y, "m": m, "u": mu})
            monthly_bev.append({"y": y, "m": m, "u": mbev})
            
            share = mbev / tbev if tbev > 0 else 0.0
            bev_share_monthly.append({"y": y, "m": m, "share": round(share, 4)})

        ytd = sum(u for (y, m), u in monthly_units_dict.items() if y == latest_y)
        ytd_bev = sum(u for (y, m), u in monthly_bev_dict.items() if y == latest_y)

        latest_units = monthly_units_dict.get((latest_y, latest_m), 0)
        prev_units = monthly_units_dict.get((prev_y, prev_m), 0)
        mom_change = latest_units - prev_units

        bev_competitor_ranking = [{"brand": b, "u": u} for b, u in latest_month_bev.items() if u > 0]
        bev_competitor_ranking.sort(key=lambda x: -x["u"])
        
        bev_rank_latest = next((i + 1 for i, item in enumerate(bev_competitor_ranking) if item["brand"] == TARGET_BRAND), None)

        top_models_dict = {}
        for row in model_data:
            if row["b"] == TARGET_BRAND and row["y"] == latest_y and row["m"] == latest_m:
                k = (row["mod"], row["pt"])
                top_models_dict[k] = top_models_dict.get(k, 0) + row["u"]
                
        top_models = [{"mod": mod, "pt": pt, "u": u} for (mod, pt), u in top_models_dict.items()]
        top_models.sort(key=lambda x: -x["u"])

        brand_focus = {
            "monthly_units": monthly_units,
            "monthly_bev": monthly_bev,
            "ytd": ytd,
            "ytd_bev": ytd_bev,
            "mom_change": mom_change,
            "bev_share_monthly": bev_share_monthly,
            "bev_rank_latest": bev_rank_latest,
            "bev_competitor_ranking": bev_competitor_ranking,
            "top_models": top_models,
            "latest": {"y": latest_y, "m": latest_m}
        }
    else:
        brand_focus = {}
        
    print("brand_focus keys: " + str(list(brand_focus.keys())))

    data = {
        "meta": {"years": years, "months": list(MONTH_MAP.values()),
                 "vehicle_types": all_v, "vehicle_types_list": vehicle_types_list,
                 "provinces": provinces},
        "powertrain_master": pm_data,
        "fuel_monthly": fuel_data,
        "brand_monthly": brand_data,
        "model_monthly": model_data,
        "brand_model_tree": brand_model_tree,
        "brand_focus": brand_focus,
    }

    print(f"  powertrain_master rows: {len(pm_data):,}")
    print(f"  fuel_monthly rows: {len(fuel_data):,}")
    print(f"  brand_monthly rows: {len(brand_data):,}")
    print(f"  model_monthly rows: {len(model_data):,}")
    print(f"  brand_model_tree brands: {len(brand_model_tree):,}")

    out_file = FRONTEND_DATA_DIR / "dashboard_data.json"
    with open(out_file, "w", encoding="utf-8") as f:
        # no indent to save space, it will be around 1-3MB
        json.dump(data, f, ensure_ascii=False)

    mb = out_file.stat().st_size / (1024 * 1024)
    print(f"Exported to {out_file.name} ({mb:.1f} MB)")

    print(f"Filtered model summary total: {df['จำนวนรถ'].sum():,}")

if __name__ == "__main__":
    export_data()
