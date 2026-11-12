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
db.close()
print(f"PASS automatic scale-fit: {len(cases)} cases; missing views/profiles fail safely")
print("PASS SQLite proposal schema: executable DDL and enforced foreign keys")
print("NOT VERIFIED: title blocks, margins, plotter paper, room segmentation or AutoCAD output")
