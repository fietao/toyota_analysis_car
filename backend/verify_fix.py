"""Verification harness: check analyst_data.json HEV totals against Excel targets."""
import sys, json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

data_path = Path(__file__).resolve().parent.parent / "frontend" / "public" / "data" / "analyst_data.json"
if not data_path.exists():
    print("ERROR: analyst_data.json not found")
    sys.exit(1)

with open(data_path, encoding="utf-8") as f:
    payload = json.load(f)

meta = payload["meta"]
print(f"Meta: year={meta['current_year']} month={meta['current_month_num']} ({meta['current_month_th']})")

hev_rows = payload["data"]["brand"]["HEV"]
gt      = next((r for r in hev_rows if r["is_grand_total"]), None)
toyota  = next((r for r in hev_rows if not r["is_grand_total"] and r["brand"] == "TOYOTA"), None)
honda   = next((r for r in hev_rows if not r["is_grand_total"] and r["brand"] == "HONDA"), None)
mitsu   = next((r for r in hev_rows if not r["is_grand_total"] and r["brand"] == "MITSUBISHI"), None)

TARGETS = [
    ("HEV GT prev_month_units  (2568 May)",    gt,     "prev_month_units",  11_995),
    ("HEV GT prev_ytd_units    (2568 Jan-May)", gt,     "prev_ytd_units",    60_189),
    ("HEV GT prev_full_units   (2568 Total)",   gt,     "prev_full_units",  136_142),
    ("HEV GT curr_month_units  (2569 May)",     gt,     "curr_month_units",  15_102),
    ("HEV GT curr_ytd_units    (2569 Jan-May)", gt,     "curr_ytd_units",    75_631),
    ("TOYOTA  curr_month_units (2569 May)",     toyota, "curr_month_units",   7_052),
    ("TOYOTA  curr_ytd_units   (2569 Jan-May)", toyota, "curr_ytd_units",    36_617),
    ("HONDA   curr_month_units (2569 May)",     honda,  "curr_month_units",   5_664),
    ("HONDA   curr_ytd_units   (2569 Jan-May)", honda,  "curr_ytd_units",    27_700),
    ("MITSU   curr_month_units (2569 May)",     mitsu,  "curr_month_units",   1_655),
    ("MITSU   curr_ytd_units   (2569 Jan-May)", mitsu,  "curr_ytd_units",     6_980),
]

all_pass = True
for label, row, field, expected in TARGETS:
    if row is None:
        print(f"  [MISSING] {label}")
        all_pass = False
        continue
    actual = row.get(field)
    ok = actual is not None and abs(actual - expected) <= 5
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_pass = False
    print(f"  [{status}] {label}: expected={expected:,}  actual={actual}")

print()
print("RESULT: GREEN" if all_pass else "RESULT: RED")
sys.exit(0 if all_pass else 1)
