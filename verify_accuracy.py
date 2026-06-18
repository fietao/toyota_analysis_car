import openpyxl
from pathlib import Path
import glob

def find_file(pattern):
    matches = glob.glob(pattern)
    return matches[0] if matches else None

def main():
    print("Verifying accuracy between Generated Output and Original Template...")
    
    # 1. Load Original
    orig_path = find_file("refer/*(calculation).xlsx")
    print(f"\nLoading original: {Path(orig_path).name}")
    wb_orig = openpyxl.load_workbook(orig_path, read_only=True, data_only=True)
    ws_orig = wb_orig["1.Reg by Powertrain"]
    
    orig_grand_total = ws_orig["B8"].value  # Jan 2568 Grand Total
    orig_ice_total   = ws_orig["B9"].value  # Jan 2568 ICE Total
    orig_bev_total   = ws_orig["B10"].value # Jan 2568 BEV Total
    
    # 2. Load Generated
    gen_path = find_file("*test analyst).xlsx")
    if not gen_path:
        print("Generated file not found yet. It might still be building.")
        return
        
    print(f"Loading generated: {Path(gen_path).name}")
    wb_gen = openpyxl.load_workbook(gen_path, read_only=True, data_only=True)
    ws_gen = wb_gen["1.Reg by Powertrain"]
    
    gen_grand_total = ws_gen["B7"].value  # In our generated sheet, data starts at row 7
    gen_ice_total   = ws_gen["B8"].value
    gen_bev_total   = ws_gen["B9"].value
    
    print("\n--- ACCURACY CHECK ---")
    print(f"Grand Total (Jan 2568) -> Original: {orig_grand_total} | Generated: {gen_grand_total} | Match? {orig_grand_total == gen_grand_total}")
    print(f"ICE Total   (Jan 2568) -> Original: {orig_ice_total} | Generated: {gen_ice_total} | Match? {orig_ice_total == gen_ice_total}")
    print(f"BEV Total   (Jan 2568) -> Original: {orig_bev_total} | Generated: {gen_bev_total} | Match? {orig_bev_total == gen_bev_total}")

if __name__ == "__main__":
    main()
