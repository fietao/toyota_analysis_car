# คู่มือผู้ดูแลรายเดือน / Monthly Operator Guide

สำหรับผู้ดูแลที่ไม่ต้องเขียนโค้ด — อัพเดทข้อมูลรถประจำเดือนแบบดับเบิลคลิก
For the non-coding maintainer — run the monthly car-data update by double-click.

คุณ **ไม่ต้อง** ใช้ Git, terminal, JSON, หรือแก้โค้ดใด ๆ
You never need Git, a terminal, JSON, or code.

---

## 1. วางไฟล์ / Put the files

ทุกเดือน กรมขนส่งจะให้ไฟล์ Excel **2 ไฟล์** วางทั้งสองไฟล์ไว้ในโฟลเดอร์นี้:
Each month you get **2 Excel files** from DLT. Put both into:

```
backend\raw data\
```

- ไฟล์ที่ 1: ชื่อมีคำว่า **ชนิดเชื้อเพลิง** (ยี่ห้อ-ชนิดเชื้อเพลิง-จังหวัด)
- ไฟล์ที่ 2: ชื่อมีคำว่า **รุ่นรถ** (ยี่ห้อ-รุ่นรถ-จังหวัด)

วางทับไฟล์เดิมได้เลย / It is fine to overwrite the old ones.

## 2. ดับเบิลคลิก / Double-click

**ก่อนรัน: ปิดไฟล์ Excel ทุกไฟล์ให้หมด** (โดยเฉพาะ 2 ไฟล์ข้อมูลดิบ และ `model_powertrain_review.csv`)
**Before running: close every open Excel file** (especially the 2 raw files and `model_powertrain_review.csv`) — an open file can lock the update.

ที่โฟลเดอร์หลักของโปรเจกต์ ดับเบิลคลิก:
In the project's top folder, double-click:

```
MONTHLY_UPDATE.bat
```

โปรแกรมจะตรวจไฟล์ ประมวลผล และสร้างข้อมูลให้อัตโนมัติ (อาจใช้เวลาหลายนาที)
It checks the files, processes the data, and rebuilds everything (may take a few minutes).
**ห้ามปิดหน้าต่างระหว่างที่กำลังทำงาน / Do not close the window while it runs.**

## 3. อ่านข้อความภาษาไทย / Read the Thai messages

โปรแกรมจะสร้างข้อมูลใหม่ในพื้นที่ชั่วคราวและตรวจสอบก่อน **ถ้าตรวจไม่ผ่านจะไม่แตะข้อมูลเดิม**
แดชบอร์ดจะเปิดด้วยข้อมูลชุดล่าสุดที่ใช้ได้เสมอ ต่อให้อัพเดทรอบนี้ล้มเหลว
The program builds the new data in a staging area and validates it first. **If anything fails,
the live data is never touched** — the dashboard always opens with the last known good data.

ข้อความผลลัพธ์มี 3 แบบ / There are three possible result lines:

| ข้อความ / Message | ความหมาย / Meaning |
|---|---|
| `สำเร็จ: เผยแพร่ข้อมูลใหม่แล้ว` | อัพเดทสำเร็จ ไม่มีรุ่นรอรีวิว / Done, nothing pending. |
| `ต้องตรวจเพิ่ม: เผยแพร่ข้อมูลใหม่แล้ว แต่ Sheets 7-8 อาจยังไม่รวมรุ่น BEV ใหม่` | เผยแพร่แล้ว แต่มีรุ่นใหม่รอรีวิว (ดูข้อ 4) / Published, but new models await review (see §4). |
| `ไม่สำเร็จ: ระบบยังใช้ข้อมูลเดิมอยู่ ไม่ได้เผยแพร่ข้อมูลใหม่` | ล้มเหลว ข้อมูลเดิมยังอยู่ครบ อ่านข้อความแล้วแก้ตามนั้น / Failed, old data intact — follow the message and re-run. |

- ถ้าขึ้นข้อความข้อผิดพลาด ให้ทำตามที่มันบอก (มันจะบอกว่าไฟล์ไหน แถวไหน คอลัมน์ไหน ต้องแก้อะไร)
  If it shows an error, follow it — it names the file, row, column, and the fix.

สรุปผลอ่านได้ที่ / A summary is written to:

```
reports\monthly_operator_summary.txt
```

บันทึกการทำงานทั้งหมดอยู่ที่ / Full log:

```
logs\monthly-update-<วันที่-เวลา>.txt
```

## 4. ถ้ามี "รุ่นรถรอรีวิว" / If there are "pending" models

เป็นเรื่องปกติและปลอดภัย รุ่นรถใหม่ทุกรุ่นจะถูกตั้งเป็น **pending** ไว้ก่อน และจะ **ยังไม่** ถูกนับเป็น BEV ใน Sheet 7-8 จนกว่าคนจะรีวิว
This is normal and safe. New models start as **pending** and are **excluded** from Sheets 7-8 until a human reviews them. Pending rows never break the build.

ถ้าต้องการให้รุ่น BEV ใหม่แสดงใน Sheet 7-8:
To make a new BEV model appear in Sheets 7-8, edit only:

```
backend\config\model_powertrain_review.csv
```

หาแถวที่ `review_status=pending` แล้วกรอก:
Find the `pending` row and fill in:

| คอลัมน์ / Column | ใส่อะไร / What to put |
|---|---|
| `candidate_powertrain` | `BEV` (ถ้าเป็นรถไฟฟ้าล้วน / if fully electric) |
| `evidence` | หลักฐาน เช่น ชื่อโบรชัวร์ / evidence, e.g. brochure name |
| `reviewer` | ชื่อคุณ / your name |
| `reviewed_at` | วันที่ / the date |
| `review_status` | เปลี่ยนเป็น `approved` |

บันทึกไฟล์ แล้ว **ดับเบิลคลิก `MONTHLY_UPDATE.bat` อีกครั้ง**
Save, then **double-click `MONTHLY_UPDATE.bat` again**.

> เปิด/แก้ไฟล์นี้ใน Excel ได้ตามปกติ ระบบรองรับการเซฟแบบ "CSV UTF-8" แล้ว
> You may open/edit this file in Excel; "CSV UTF-8" saves are handled automatically.

## 4a. กรอกไฟล์รีวิวให้ถูกต้อง / Filling the review CSV correctly

ไฟล์เดียวที่คุณแก้ได้คือ / The only file you may edit is:

```
backend\config\model_powertrain_review.csv
```

**ค่าที่รับได้ของ `candidate_powertrain`** / Accepted `candidate_powertrain` values:
`BEV`, `HEV`, `PHEV`, `ICE`, `ambiguous`, `unknown` — หรือเว้นว่างได้เฉพาะเมื่อ `review_status=pending`
(blank only when `review_status=pending`). ใช้ `BEV` ไม่ใช่ `EV` / Use `BEV`, not `EV`.

**ค่าที่รับได้ของ `review_status`** / Accepted `review_status` values:
`pending`, `approved`, `rejected`, `ambiguous`.

แถวที่ `approved` ต้องกรอกครบ 4 ช่อง / An `approved` row must have all four of:
`candidate_powertrain`, `evidence`, `reviewer`, `reviewed_at`.
วันที่ต้องเป็นรูปแบบ / Date format must be `YYYY-MM-DD`.

### ตัวอย่างที่ถูก / Accepted examples

```csv
BYD,NEW MODEL,NEW MODEL,,pending,,,,auto-added from latest model data
BYD,ATTO 3,ATTO 3,BEV,approved,https://www.byd.com/th/car/atto3,Somchai,2026-07-23,
TOYOTA,CAMRY,CAMRY,HEV,approved,official Toyota spec page,Somchai,2026-07-23,
BRAND,MODEL,MODEL,ambiguous,ambiguous,conflicting official sources,Somchai,2026-07-23,
```

### ตัวอย่างที่ผิด (จะถูกปฏิเสธ) / Rejected examples

```csv
BYD,ATTO 3,ATTO 3,BEV,approved,,Somchai,2026-07-23,        # approved แต่ไม่มี evidence
BYD,ATTO 3,ATTO 3,EV,approved,official brochure,Somchai,2026-07-23,   # ใช้ EV แทน BEV
BYD,ATTO 3,ATTO 3,BEV,approve,official brochure,Somchai,2026-07-23,   # review_status สะกดผิด
```

โปรแกรมจะตรวจไฟล์นี้ก่อนเริ่มประมวลผล ถ้าผิดจะบอก **ไฟล์ / แถว / คอลัมน์ / ค่าที่ควรเป็น** เป็นภาษาไทย
The program preflights this file before building and reports **file / row / column / expected value** in Thai.

### ระวัง / Be careful

- อย่าเปลี่ยนหรือลบชื่อคอลัมน์ (แถวแรก) / Do not change or delete column names.
- อย่าแก้คอลัมน์ `raw_model` / Do not edit `raw_model`.
- อย่าตั้ง `approved` โดยไม่มีหลักฐานจริง / Do not approve without evidence.
- อย่าเดา BEV จากชื่อรุ่น / Do not guess BEV from the model name.
- อย่าใช้ยอดรวมของยี่ห้อมาตัดสิน Powertrain ของรุ่น / Do not use brand totals to decide a model's Powertrain.
- ปิด Excel ให้หมดก่อนรัน `MONTHLY_UPDATE.bat` / Close Excel before running `MONTHLY_UPDATE.bat`.

## 5. ห้ามทำ / Never do

- ❌ อย่าตั้ง `approved` ให้รุ่นรถโดยไม่มีหลักฐานจริง / Never approve a model without real evidence.
- ❌ อย่าแก้ชื่อคอลัมน์ (แถวแรก) ของไฟล์ CSV / Never rename the CSV header row.
- ❌ อย่าลบไฟล์ในโฟลเดอร์ `backend\config\` / Never delete files in `backend\config\`.
- ❌ อย่าแก้ไฟล์ `.py`, `.bat`, หรือ JSON / Never edit code, `.bat`, or JSON files.
- ❌ อย่าปิดหน้าต่างระหว่างที่กำลังประมวลผล / Never close the window mid-run.

## 6. รู้ได้ไงว่าสำเร็จ / How to know it worked

สำเร็จเมื่อครบทั้ง 3 อย่างนี้ / It succeeded when all three are true:

1. หน้าต่างขึ้นคำว่า **"สำเร็จ"** / the window shows **"สำเร็จ"**.
2. มีไฟล์ `reports\monthly_operator_summary.txt` ที่เพิ่งอัพเดท / the summary file is freshly updated.
3. ในสรุป ช่อง "ไฟล์ข้อมูลที่สร้างใหม่" มี `[x]` ครบทุกไฟล์ / every JSON in the summary is marked `[x]`.

ถ้าไม่สำเร็จ ให้ทำตามข้อความภาษาไทย (มักเป็นไฟล์หาย หรือไฟล์เปิดค้างใน Excel) แล้วรันใหม่
If not, follow the Thai message (usually a missing file or a file still open in Excel) and run again.
