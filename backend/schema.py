COMMON_COLS = [
    "ปี", "เดือน", "ประเภทรถ", "จังหวัด",
    "ยี่ห้อรถ", "ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2",
    "จำนวนรถ"
]
FUEL_ONLY_COLS = ["ชนิดเชื้อเพลิง", "Powertrain"]

MODEL_COLS = COMMON_COLS
FUEL_COLS = COMMON_COLS + FUEL_ONLY_COLS


def _validate(df, cols):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def validate_model(df):
    """Model-grain facts: series/brand fields, no ชนิดเชื้อเพลิง or Powertrain."""
    _validate(df, MODEL_COLS)
    forbidden = [c for c in FUEL_ONLY_COLS + ["include_in_bev_model_report"] if c in df.columns]
    if forbidden:
        raise ValueError(f"Model-grain data contains forbidden fuel/PT columns: {forbidden}")


def validate_fuel(df):
    """Fuel-grain facts: requires ชนิดเชื้อเพลิง in addition to the common fields."""
    _validate(df, FUEL_COLS)
