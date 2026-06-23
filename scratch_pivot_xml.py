"""
Verify PivotTable6 field mapping and check which cache it uses.
Also check for hidden items on ชนิดเชื้อเพลิง in PivotTable6.
"""
import zipfile, sys, io
import xml.etree.ElementTree as etree

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FILE = r"C:\dev\ai-reading-car-analysis\backend\refer\refer\202605_รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - พฤษภาคม 2569(masttercal).xlsx"
ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'

with zipfile.ZipFile(FILE, 'r') as z:
    # Check which cache PivotTable2 (PivotTable6) uses
    pt2_rels = z.read('xl/pivotTables/_rels/pivotTable2.xml.rels').decode('utf-8')
    print("PivotTable2 rels:", pt2_rels)
    
    pt1_rels = z.read('xl/pivotTables/_rels/pivotTable1.xml.rels').decode('utf-8')
    print("PivotTable1 rels:", pt1_rels)
    
    # PivotTable6 (on master powertrain) - dump all pivotField details
    pt2 = etree.fromstring(z.read('xl/pivotTables/pivotTable2.xml'))
    pivot_fields = pt2.findall(f'{{{ns}}}pivotFields/{{{ns}}}pivotField')
    
    # Also check cache reference
    cache_id = pt2.get('cacheId')
    print(f"\nPivotTable6 cacheId: {cache_id}")
    
    # Determine cache: check which cache def matches
    # Load cache definition 2
    cache2 = etree.fromstring(z.read('xl/pivotCache/pivotCacheDefinition2.xml'))
    cf2 = cache2.findall(f'{{{ns}}}cacheFields/{{{ns}}}cacheField')
    print(f"\nCache 2 has {len(cf2)} fields:")
    for i, f in enumerate(cf2):
        print(f"  [{i}] {f.get('name')}")
    
    # Load cache definition 1  
    cache1 = etree.fromstring(z.read('xl/pivotCache/pivotCacheDefinition1.xml'))
    cf1 = cache1.findall(f'{{{ns}}}cacheFields/{{{ns}}}cacheField')
    print(f"\nCache 1 has {len(cf1)} fields:")
    for i, f in enumerate(cf1):
        print(f"  [{i}] {f.get('name')}")

    # PivotTable6 pivot fields detail
    print(f"\nPivotTable6 has {len(pivot_fields)} pivotFields:")
    for i, pf in enumerate(pivot_fields):
        axis = pf.get('axis')
        name = pf.get('name')
        items = pf.findall(f'{{{ns}}}items/{{{ns}}}item')
        
        # Check multipleItemSelectionAllowed
        multi = pf.get('multipleItemSelectionAllowed')
        
        info = f"  [{i}] axis={axis}, name={name}, items={len(items)}, multi={multi}"
        print(info)
        
        # List all items with their attributes
        if items and len(items) <= 25:
            for j, it in enumerate(items):
                attrs = dict(it.attrib)
                print(f"    item[{j}]: {attrs}")
    
    # Row fields
    row_fields = pt2.findall(f'{{{ns}}}rowFields/{{{ns}}}field')
    print(f"\nPivotTable6 rowFields:")
    for rf in row_fields:
        print(f"  x={rf.get('x')}")
