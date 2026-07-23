#!/usr/bin/env python3
"""monthly_update.py — one-call guided monthly update for a non-coding operator.

Driven by MONTHLY_UPDATE.bat (double-click). It:
  1. Checks the two DLT Excel files are present in raw data/ and not locked by Excel.
  2. Preflights config/model_powertrain_review.csv (Thai errors, no stack traces).
  3. Runs the existing build via update_raw_data.py, then export_manual_report.py.
  4. Writes reports/monthly_operator_summary.txt and a timestamped log.

All operator-facing messages are Thai and go to both the console and the log file.
Raw subprocess output (English, verbose) goes to the log file only, so common operator
mistakes surface as a friendly Thai line instead of a traceback.

Reuses existing scripts — no pipeline logic is duplicated here.
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
RAW_DIR = BASE / "raw data"
DATA_DIR = ROOT / "frontend" / "public" / "data"
STAGING_DIR = ROOT / "frontend" / "public" / "data.staging"  # build target; never served
BACKUP_DIR = ROOT / "frontend" / "public" / "data.bak"       # last-good copy during publish
LOGS_DIR = ROOT / "logs"
REPORTS_DIR = ROOT / "reports"
SUMMARY_PATH = REPORTS_DIR / "monthly_operator_summary.txt"
MANIFEST_PATH = DATA_DIR / "cleaned_data_manifest.json"
JSON_OUTPUTS = [
    "dashboard_summary.json", "dashboard_models.json", "cleaned_data_manifest.json",
    "analyst_data.json", "manual_report.json",
]

# Exact operator-facing result lines (contract — see docs/THAI_OPERATOR_MONTHLY_GUIDE.md).
RESULT_OK = "สำเร็จ: เผยแพร่ข้อมูลใหม่แล้ว"
RESULT_REVIEW = "ต้องตรวจเพิ่ม: เผยแพร่ข้อมูลใหม่แล้ว แต่ Sheets 7-8 อาจยังไม่รวมรุ่น BEV ใหม่"
RESULT_FAIL = "ไม่สำเร็จ: ระบบยังใช้ข้อมูลเดิมอยู่ ไม่ได้เผยแพร่ข้อมูลใหม่"

import operator_preflight  # stdlib-only safety net; import kept at top

LOG_FILE = None


def say(msg=""):
    """Operator-facing line: console + log."""
    print(msg)
    if LOG_FILE:
        LOG_FILE.write(msg + "\n")
        LOG_FILE.flush()


def rule():
    say("=" * 60)


def find_masters():
    """Return (fuel_path or None, model_path or None) from raw data/."""
    import update_raw_data  # lazy: reuse FUEL_PATTERN / MODEL_PATTERN (pandas-heavy import)
    def newest(pattern):
        matches = [p for p in RAW_DIR.glob(pattern) if not p.name.startswith("~$")]
        return max(matches, key=lambda p: p.stat().st_mtime) if matches else None
    return newest(update_raw_data.FUEL_PATTERN), newest(update_raw_data.MODEL_PATTERN)


def is_locked(path):
    """True if the file looks locked (open in Excel). Uses the ~$ lock file plus a
    non-destructive append-open probe (writes nothing)."""
    if (path.parent / ("~$" + path.name)).exists():
        return True
    try:
        with open(path, "a"):
            return False
    except OSError:
        return True


def check_inputs():
    """Verify both DLT files exist and are not locked. Returns True to proceed."""
    say("ขั้นที่ 1: ตรวจไฟล์ข้อมูลดิบใน backend/raw data/")
    fuel, model = find_masters()
    missing = []
    if fuel is None:
        missing.append("ไฟล์ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด (…ชนิดเชื้อเพลิง…2564….xlsx)")
    if model is None:
        missing.append("ไฟล์ยี่ห้อรถ-รุ่นรถ-จังหวัด (…รุ่นรถ…2564….xlsx)")
    if missing:
        say("  ไม่พบไฟล์ที่ต้องใช้:")
        for m in missing:
            say(f"    - {m}")
        say(f"  วิธีแก้: วางไฟล์ Excel จากกรมขนส่ง 2 ไฟล์ไว้ในโฟลเดอร์:")
        say(f"    {RAW_DIR}")
        say("  แล้วดับเบิลคลิก MONTHLY_UPDATE.bat อีกครั้ง")
        return False

    locked = [p for p in (fuel, model) if is_locked(p)]
    if locked:
        say("  ไฟล์กำลังถูกเปิดค้างอยู่ (น่าจะเปิดใน Excel):")
        for p in locked:
            say(f"    - {p.name}")
        say("  วิธีแก้: ปิดไฟล์เหล่านี้ใน Excel ให้หมด แล้วรันใหม่อีกครั้ง")
        return False

    say(f"  พบไฟล์ครบ: {fuel.name}")
    say(f"             {model.name}")
    return True


def check_review_csv():
    """Preflight the model review CSV. Returns True to proceed."""
    say("")
    say("ขั้นที่ 2: ตรวจไฟล์รีวิวรุ่นรถ (model_powertrain_review.csv)")
    errors = operator_preflight.validate_review_csv()
    if errors:
        say(f"  พบปัญหา {len(errors)} จุด — ต้องแก้ก่อนถึงจะรันต่อได้:")
        for e in errors:
            for line in e.splitlines():
                say(f"    {line}")
        say("")
        say("  แก้ไฟล์ backend/config/model_powertrain_review.csv ตามด้านบน แล้วรันใหม่")
        return False
    say(f"  ผ่าน (รอรีวิว {operator_preflight.count_pending()} แถว)")
    return True


def run_step(title, script_name):
    """Run a backend script; its raw output goes to the log only. Returns True on success."""
    say("")
    say(title)
    LOG_FILE.write(f"\n----- {script_name} -----\n")
    LOG_FILE.flush()
    result = subprocess.run(
        [sys.executable, str(BASE / script_name)],
        cwd=str(BASE),
        stdout=LOG_FILE, stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    if result.returncode != 0:
        say(f"  ไม่สำเร็จ — ดูรายละเอียดในไฟล์ log ท้ายข้อความนี้")
        say("  สาเหตุที่พบบ่อย: ไฟล์ผลลัพธ์ (Excel/JSON) ถูกเปิดค้างไว้ — ปิดแล้วรันใหม่")
        return False
    say("  เสร็จ")
    return True


def safe_publish(staging, public, backup, names):
    """Atomically move each staged JSON over its public copy, with rollback.

    Backs up the current public files first, then os.replace()s each staged file into
    place (per-file atomic rename, same volume). If any replace fails, every backed-up
    file is restored so `public` is left exactly as it was before the call. Extra files
    already in `public` are left untouched. Raises on failure after restoring.

    Pure filesystem / stdlib — no pandas, no pipeline import — so the no-collapse
    guarantee is unit-testable without the build environment.
    """
    staging, public, backup = Path(staging), Path(public), Path(backup)
    if backup.exists():
        shutil.rmtree(backup)
    backup.mkdir(parents=True)

    backed = []
    for n in names:
        src = public / n
        if src.exists():
            shutil.copy2(src, backup / n)  # copy (not move) so public stays intact if we abort here
            backed.append(n)

    public.mkdir(parents=True, exist_ok=True)
    try:
        for n in names:
            os.replace(staging / n, public / n)  # ponytail: same-volume rename, atomic per file
    except OSError:
        for n in backed:  # rollback: restore every original we saved
            shutil.copy2(backup / n, public / n)
        raise

    shutil.rmtree(backup)


def write_summary(run_start, result):
    """Write reports/monthly_operator_summary.txt. Best-effort; never aborts the run.

    `result` is one of RESULT_OK / RESULT_REVIEW / RESULT_FAIL and is printed verbatim
    as the first line (operator contract). On RESULT_FAIL the public data was left
    untouched, so period/row counts below reflect the last known good data still served.
    """
    REPORTS_DIR.mkdir(exist_ok=True)
    period = model_rows = fuel_rows = None
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        period = manifest.get("reporting_period")
        model_rows = manifest.get("model_row_count")
        fuel_rows = manifest.get("fuel_row_count")
    except (OSError, ValueError):  # ValueError = corrupt/partial JSON; summary must never traceback
        pass

    pending = operator_preflight.count_pending()

    # Model-grain count: how many BEV *models* actually appear in Sheets 7-8 (canonical
    # model2), not raw-model rows. Use model_map's own selector so it can't drift from
    # the sheet's real filter.
    try:
        import model_map
        approved_bev_models = len(model_map.approved_bev_model_keys())
    except Exception:
        approved_bev_models = "?"

    regenerated = []
    for name in JSON_OUTPUTS:
        p = DATA_DIR / name
        fresh = p.exists() and p.stat().st_mtime >= run_start
        regenerated.append((name, fresh))
    any_stale = any(not fresh for _, fresh in regenerated)

    lines = []
    lines.append("สรุปผลการอัพเดทประจำเดือน (Monthly Operator Summary)")
    lines.append("=" * 60)
    lines.append(f"ผลลัพธ์ (Result)                  : {result}")
    lines.append(f"เวลาที่รัน (Run time)              : {datetime.now():%Y-%m-%d %H:%M:%S}")
    lines.append(f"งวดข้อมูลล่าสุด (Reporting period) : {period or 'ไม่ทราบ'}")
    if model_rows is not None:
        lines.append(f"จำนวนแถวข้อมูลรุ่นรถ (Model rows)  : {model_rows:,}")
    if fuel_rows is not None:
        lines.append(f"จำนวนแถวข้อมูลเชื้อเพลิง (Fuel rows): {fuel_rows:,}")
    lines.append(f"รุ่นรถรอรีวิว (Pending model rows) : {pending}")
    lines.append(f"รุ่น BEV ที่อนุมัติใน Sheet 7-8    : {approved_bev_models}")
    lines.append("")
    lines.append("ข้อมูลที่เผยแพร่ (Published JSON, [x] = อัพเดทรอบนี้):")
    for name, fresh in regenerated:
        lines.append(f"  [{'x' if fresh else ' '}] {name}")
    lines.append("")
    lines.append("สิ่งที่ต้องทำต่อ (Next action):")
    if result == RESULT_FAIL:
        lines.append("  - อัพเดทไม่สำเร็จ ระบบยังใช้ข้อมูลเดิม (ยังเปิดแดชบอร์ดได้ตามปกติ)")
        lines.append("  - อ่านข้อความภาษาไทยในหน้าต่าง แล้วแก้ตามที่บอก")
        lines.append("  - สาเหตุที่พบบ่อย: ไฟล์ Excel/JSON เปิดค้างอยู่ หรือไฟล์ข้อมูลดิบไม่ครบ")
        lines.append("  - แก้แล้วดับเบิลคลิก MONTHLY_UPDATE.bat อีกครั้ง")
    elif pending > 0:
        lines.append(f"  - มีรุ่นรถใหม่รอรีวิว {pending} แถว")
        lines.append("  - Sheet 7-8 จะยังไม่รวมรุ่น BEV ที่ยังไม่ได้อนุมัติ (ถือว่าปกติ ปลอดภัย)")
        lines.append("  - ถ้าต้องการให้รุ่น BEV ใหม่แสดงใน Sheet 7-8:")
        lines.append("      เปิด backend/config/model_powertrain_review.csv")
        lines.append("      กรอก candidate_powertrain=BEV, evidence, reviewer, reviewed_at")
        lines.append("      ตั้ง review_status=approved แล้วรัน MONTHLY_UPDATE.bat อีกครั้ง")
    else:
        lines.append("  - ไม่มีรุ่นรอรีวิว")
        lines.append("  - ข้อมูลแดชบอร์ดพร้อมทดสอบ (smoke test) ได้เลย")
    if result != RESULT_FAIL and any_stale:
        lines.append("")
        lines.append("  หมายเหตุ: มีไฟล์ JSON บางไฟล์ไม่ได้ถูกอัพเดทรอบนี้ (ดูช่องที่ว่างด้านบน)")

    lines.append("")
    lines.append("ทดสอบก่อนใช้งานจริง (Smoke test — เปิดหน้าเหล่านี้แล้วดูว่าขึ้นข้อมูลใหม่):")
    for item in ("/models", "/analyst", "/report",
                 "Manual Report — ตัวเลือกปี (year selector)", "ปุ่ม Export Excel"):
        lines.append(f"  [ ] {item}")

    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    say("")
    say(f"เขียนสรุปผลไว้ที่: {SUMMARY_PATH}")


def finish(result, run_start):
    """Write the summary, print the verbatim result banner, return the exit code."""
    write_summary(run_start, result)
    say("")
    rule()
    for line in result.splitlines():
        say("  " + line)
    if result == RESULT_REVIEW:
        say("  (ปลอดภัย ไม่ใช่ error — ดู reports/monthly_operator_summary.txt)")
    rule()
    return 1 if result == RESULT_FAIL else 0


def main():
    global LOG_FILE
    LOGS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log_path = LOGS_DIR / f"monthly-update-{ts}.txt"
    LOG_FILE = open(log_path, "w", encoding="utf-8")
    run_start = datetime.now().timestamp()

    try:
        rule()
        say("  อัพเดทข้อมูลรถประจำเดือน (Monthly Data Update)")
        rule()

        if not check_inputs():
            return finish(RESULT_FAIL, run_start)
        if not check_review_csv():
            return finish(RESULT_FAIL, run_start)

        # Build into a staging dir. The live public data the dashboard serves is not
        # touched until the build passes validation, so a failed/aborted run always
        # leaves the last known good data in place.
        say("")
        say("ขั้นที่ 3: กำลังประมวลผลข้อมูล (สร้างในพื้นที่ชั่วคราวก่อน ยังไม่เผยแพร่ — ห้ามปิดหน้าต่าง)")
        shutil.rmtree(STAGING_DIR, ignore_errors=True)
        os.environ["PUBLIC_DATA_DIR"] = str(STAGING_DIR)  # inherited by every build subprocess

        built = (
            run_step("  - สร้างข้อมูลหลัก + แดชบอร์ด (update_raw_data.py)", "update_raw_data.py")
            and run_step("  - สร้างรายงาน Manual Report / Sheet 7-8 (export_manual_report.py)", "export_manual_report.py")
            and run_step("  - ตรวจสอบความถูกต้องก่อนเผยแพร่ (validate_public_release.py)", "validate_public_release.py")
        )
        if not built:
            shutil.rmtree(STAGING_DIR, ignore_errors=True)
            return finish(RESULT_FAIL, run_start)  # public data untouched

        # Publish: swap the validated staging files over the live ones, rollback on error.
        say("")
        say("ขั้นที่ 4: เผยแพร่ข้อมูลใหม่ (สลับข้อมูลแบบปลอดภัย)")
        try:
            safe_publish(STAGING_DIR, DATA_DIR, BACKUP_DIR, JSON_OUTPUTS)
        except OSError:
            say("  เผยแพร่ไม่สำเร็จ — คืนค่าข้อมูลเดิมกลับเรียบร้อยแล้ว")
            shutil.rmtree(STAGING_DIR, ignore_errors=True)
            return finish(RESULT_FAIL, run_start)
        shutil.rmtree(STAGING_DIR, ignore_errors=True)
        say("  เสร็จ")

        pending = operator_preflight.count_pending()
        return finish(RESULT_REVIEW if pending > 0 else RESULT_OK, run_start)
    finally:
        say("")
        say(f"บันทึก log ไว้ที่: {log_path}")
        LOG_FILE.close()


if __name__ == "__main__":
    sys.exit(main())
