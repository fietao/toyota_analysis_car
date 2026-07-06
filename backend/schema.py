COLS = [
    "ปี", "เดือน", "ประเภทรถ", "จังหวัด",
    "ยี่ห้อรถ", "ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2",
    "ชนิดเชื้อเพลิง", "Powertrain", "จำนวนรถ"
]

def validate(df):
    missing = [c for c in COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
