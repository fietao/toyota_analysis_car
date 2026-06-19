import zipfile
import xml.etree.ElementTree as ET

NS = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

path = r'C:\dev\ai-reading-car-analysis\test_model_1.xlsx'

with zipfile.ZipFile(path) as z:
    # parse styles: fills list and cellXfs (style index → fillId)
    sr = ET.fromstring(z.read('xl/styles.xml'))
    fills = []
    for fill in sr.findall('.//x:fills/x:fill', NS):
        pf = fill.find('x:patternFill', NS)
        if pf is not None:
            fg = pf.find('x:fgColor', NS)
            fills.append(fg.get('rgb') if fg is not None else None)
        else:
            fills.append(None)

    xfs = []
    for xf in sr.findall('.//x:cellXfs/x:xf', NS):
        xfs.append(int(xf.get('fillId', 0)))

    def style_rgb(s_attr):
        if s_attr is None:
            return None
        idx = int(s_attr)
        if idx >= len(xfs):
            return f'xf_oob({idx})'
        fill_id = xfs[idx]
        if fill_id >= len(fills):
            return f'fill_oob({fill_id})'
        return fills[fill_id]

    # resolve BEV by Model sheet file
    wb_xml = ET.fromstring(z.read('xl/workbook.xml'))
    sheet_map = {}
    for s in wb_xml.findall('.//x:sheet', NS):
        sheet_map[s.get('name')] = s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')

    rels_xml = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rid_to_file = {}
    for r in rels_xml:
        rid_to_file[r.get('Id')] = r.get('Target')

    target = rid_to_file[sheet_map['BEV by Model']].lstrip('/')
    bev_file = target if target.startswith('xl/') else f'xl/{target}'
    print(f'Sheet file: {bev_file}')

    ws = ET.fromstring(z.read(bev_file))

    # collect all cells
    rows = {}
    for row in ws.findall('.//x:row', NS):
        r = int(row.get('r'))
        rows[r] = {}
        for c in row.findall('x:c', NS):
            col = ''.join(ch for ch in c.get('r') if ch.isalpha())
            rows[r][col] = style_rgb(c.get('s'))

    last_row = max(rows)
    print(f'Sheet: {last_row} rows')

    BLUE = 'FF4472C4'
    GREY = 'FFD9D9D9'

    def check(r, col):
        return rows.get(r, {}).get(col)

    print('\n=== Rows 1-3 A:B — expect BLUE ===')
    for r in [1, 2, 3]:
        for col in ['A', 'B']:
            rgb = check(r, col)
            status = 'OK' if rgb == BLUE else f'WRONG ({rgb})'
            print(f'  {col}{r}: {status}')

    print('\n=== Row 6 — year label=BLUE, total cols=GREY ===')
    for col, rgb in sorted(rows.get(6, {}).items()):
        print(f'  {col}6: {rgb}')

    print('\n=== Row 7 — all BLUE ===')
    for col, rgb in sorted(rows.get(7, {}).items()):
        print(f'  {col}7: {rgb}')

    print('\n=== Row 8 (first brand) — label=BLUE, year-total/grand=GREY ===')
    for col, rgb in sorted(rows.get(8, {}).items()):
        print(f'  {col}8: {rgb}')

    print(f'\n=== Last row {last_row} (Grand Total) — all GREY ===')
    for col, rgb in sorted(rows.get(last_row, {}).items()):
        print(f'  {col}{last_row}: {rgb}')
