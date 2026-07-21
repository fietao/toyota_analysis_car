"""
Focused test: the Series/Model page must not display, filter, or export
Powertrain in any form — no column, no badges, no filter pill/state, no
per-powertrain export columns. Powertrain stays in backend payloads/parquet/
registry and in the separate Powertrain report; this only checks the
frontend table + filters + Excel export in frontend/src/app/models/page.tsx.

No pytest — matches the existing test_*.py convention. Runs from any
directory. Exits 0 on PASS, 1 on FAIL.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
REPO_ROOT = BACKEND.parent
PAGE = REPO_ROOT / "frontend" / "src" / "app" / "models" / "page.tsx"

failures = []


def test_powertrain_column_filter_and_export_removed():
    if not PAGE.exists():
        failures.append(f"{PAGE} not found")
        return
    src = PAGE.read_text(encoding="utf-8")

    if 'className="p-3 w-48 text-slate-450 sticky top-0 bg-slate-800 z-30">Powertrain</th>' in src:
        failures.append("visible table still has a Powertrain <th> column")
    if "PowertrainBadges" in src:
        failures.append("PowertrainBadges component/usage still present")
    if "POWERTRAINS.forEach" in src:
        failures.append("Excel export still writes per-powertrain columns via POWERTRAINS.forEach")
    if 'label="Powertrain"' in src:
        failures.append("Powertrain filter pill is still present")
    if "selectedPts" in src or "setSelectedPts" in src:
        failures.append("selectedPts filter state/logic is still present")
    if "POWERTRAINS" in src:
        failures.append("POWERTRAINS import/usage is still present (now unused)")


if __name__ == "__main__":
    test_powertrain_column_filter_and_export_removed()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in models page Powertrain-removal test:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — Series/Model page has no Powertrain column, filter, or export.")
    sys.exit(0)
