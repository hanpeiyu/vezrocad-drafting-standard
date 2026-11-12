#!/usr/bin/env python3
"""Check auto-fit examples and SQLite SQL constraints. Proposal, not paper validation."""
import sys, json, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from resolve_scale_fit import resolve,read
layouts=read("data/paper-fit-layouts.v2.1.json")
policies=read("data/auto-scale-policies.v2.1.json")
cases=read("examples/scale-fit-cases.v2.1.json")["cases"]
lw=read("data/lineweight-profiles.v2.1.json")
known={p["id"] for p in lw["presets"]}
for policy in policies["policies"]:
    assert len(policy["candidateDenominators"])==len(set(policy["candidateDenominators"]))
    assert policy["preferredDenominator"] in policy["candidateDenominators"]
    assert all(x>0 for x in policy["candidateDenominators"])
assert len({p["id"] for p in layouts["paperLayouts"]})==len(layouts["paperLayouts"])
for case in cases:
    got=resolve(case["viewId"],case["widthMm"],case["heightMm"],
                allowed_layouts=case["allowedPaperLayouts"],
                annotation_reserve_width_mm=case.get("annotationReserveWidthMm",0),
                annotation_reserve_height_mm=case.get("annotationReserveHeightMm",0),
                locked=case.get("locked"))
    for key,expected in case["expected"].items():
        actual={"denominator":"scaleDenominator"}.get(key,key)
        assert got.get(actual)==expected, (case["id"],actual,expected,got)
    assert got["fitVerified"] is False
    if got.get("status")=="fit-suggested":assert got["lineweightProfileId"] in known
schema=(ROOT/"schema"/"standard-management-v2.1.sql").read_text(encoding="utf-8")
db=sqlite3.connect(":memory:")
db.execute("PRAGMA foreign_keys=ON")
db.executescript(schema)
db.execute("INSERT INTO standard_revision(revision_id,semver,status) VALUES(?,?,?)",("test","2.1.0","DRAFT"))
db.execute("INSERT INTO profession(revision_id,profession_id,name) VALUES(?,?,?)",("test","ARCH","建筑"))
try:
    db.execute("INSERT INTO sheet_type(revision_id,sheet_type_id,profession_id,name) VALUES(?,?,?,?)",("test","BAD","NONEXISTENT","错例"))
    raise AssertionError("FOREIGN KEY not enforced")
except sqlite3.IntegrityError:pass
db.execute("INSERT INTO sheet_type(revision_id,sheet_type_id,profession_id,name) VALUES(?,?,?,?)",("test","EXI-MEASURE","ARCH","原始测量"))
db.execute("INSERT INTO frame_template(revision_id,frame_id,paper_id,name,bounds_json,title_block_ref) VALUES(?,?,?,?,?,?)",("test","A3-L-VZ","A3","示例图框","{}","VZ-TB-HORIZONTAL"))
db.execute("INSERT INTO sheet_layout_template(revision_id,layout_id,frame_id,name) VALUES(?,?,?,?)",("test","A3-SINGLE","A3-L-VZ","单视图"))
db.execute("INSERT INTO layout_slot(revision_id,layout_id,slot_id,view_role,x_mm,y_mm,width_mm,height_mm) VALUES(?,?,?,?,?,?,?,?)",("test","A3-SINGLE","PRIMARY","PRIMARY",18,60,384,216))
db.execute("UPDATE standard_revision SET status='PUBLISHED' WHERE revision_id='test'")
for statement in [
 "INSERT INTO profession(revision_id,profession_id,name) VALUES('test','FAKE','异常')",
 "UPDATE profession SET name='异常' WHERE revision_id='test'",
 "DELETE FROM profession WHERE revision_id='test' AND profession_id='ARCH'",
 "UPDATE standard_revision SET semver='9.9' WHERE revision_id='test'"]:
    try:
        db.execute(statement)
        raise AssertionError("published revision was editable: "+statement)
    except sqlite3.IntegrityError:pass
db.close()
project_sql=(ROOT/"schema"/"project-sheet-index-v2.1.sql").read_text(encoding="utf-8")
pdb=sqlite3.connect(":memory:")
pdb.execute("PRAGMA foreign_keys=ON")
pdb.executescript(project_sql)
pdb.execute("INSERT INTO project_document(project_uid,standard_revision_id,standard_bundle_sha256) VALUES(?,?,?)",("demo","test","abc"))
pdb.execute("INSERT INTO sheet_instance(project_uid,sheet_uid,sheet_type_id,sheet_title) VALUES(?,?,?,?)",("demo","sheet-a","INT-LAYOUT","家具图"))
pdb.execute("INSERT INTO viewport_instance(project_uid,viewport_uid,sheet_uid,layout_slot_id,source_view_id,scale_denominator) VALUES(?,?,?,?,?,?)",("demo","vp-a","sheet-a","PRIMARY","plan-furniture",75))
try:
    pdb.execute("INSERT INTO viewport_instance(project_uid,viewport_uid,sheet_uid,layout_slot_id,source_view_id,scale_denominator) VALUES(?,?,?,?,?,?)",("demo","vp-b","nonexistent","PRIMARY","plan-furniture",75))
    raise AssertionError("project viewport FK not enforced")
except sqlite3.IntegrityError:pass
pdb.close()
print(f"PASS automatic scale-fit: {len(cases)} cases; missing views/profiles fail safely")
print("PASS SQLite schemas: 24 standard tables with published-revision immutability guards; project sheet index FKs")
print("NOT VERIFIED: title blocks, margins, plotter paper, room segmentation or AutoCAD output")
