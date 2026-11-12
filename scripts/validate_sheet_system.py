#!/usr/bin/env python3
"""Validate drawing taxonomy, per-sheet presentation matrix, and safe dry-run compilation."""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from compile_sheetset import compile_project

def read(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))
tax=read("data/sheet-taxonomy.v2.1.json")
matrix=read("data/sheet-expression-matrix.v2.1.json")
packages=read("data/sheetset-presets.v2.1.json")
project=read("examples/sheetset-project.v2.1.example.json")
views=set(read("data/view-presets.json")["views"])
weights=read("data/lineweight-profiles.v2.1.json")
colors=read("data/print-color-profiles.v2.1.json")
features={x["id"] for x in tax["scopeFeatures"]}
groups={x["id"] for x in tax["groups"]}
sheetids={t["id"] for t in tax["sheetTypes"]}
tags={x["id"] for x in matrix["semanticTags"]}
modes=set(colors["outputModes"])
assert len(groups)==len(tax["groups"])
assert len(features)==len(tax["scopeFeatures"])
assert len(sheetids)==len(tax["sheetTypes"]), "duplicated drawing type ID"
assert len(tags)==len(matrix["semanticTags"])
assert len({x["id"] for x in packages["templates"]})==len(packages["templates"])
assert set(project["features"])==features,"example explicitly declares all project features"
assert all(k in modes for k in project["outputRequest"]["requestedModes"])
assert all(v in {"BW","GRAY","COLOR","PRESENTATION"} for v in modes)
for t in tax["sheetTypes"]:
    assert t["groupId"] in groups
    assert t["baseViewPresetId"] in views if t["kind"]=="model-view" else t["baseViewPresetId"] is None
    for action in ("focus","context","hide"):
        assert set(t["expression"][action]).issubset(tags), (t["id"],action)
    assert t["trigger"]["type"] in {"core","feature","optional"}
    assert set(t["trigger"]["featuresAny"]).issubset(features)
    if t["trigger"]["type"]=="feature":assert t["trigger"]["featuresAny"]
    assert set(t["prerequisites"]).issubset(sheetids)
    assert t["suggested"]["outputMode"] in modes
    assert t["instances"]["repeatBy"] in {"single","room-wall","cabinet-instance","detail-instance"}
    if t["instances"]["repeatBy"]!="single":assert t["instances"]["requiresReference"],t["id"]
    if t["kind"]=="document":
        assert t["suggested"]["scaleDenominator"] is None
    else:
        p=f'{t["suggested"]["paper"]}-1-{t["suggested"]["scaleDenominator"]}'
        assert any(x["id"]==p for x in weights["presets"]), (t["id"],p)
    assert not(set(t["expression"]["focus"]) & set(t["expression"]["context"])), t["id"]
    assert not(set(t["expression"]["focus"]) & set(t["expression"]["hide"])), t["id"]
for pkg in packages["templates"]:
    assert set(pkg.get("includeTriggerTypes",[])).issubset({"core","feature"})
    assert set(pkg.get("explicitSheetTypeIds",[])).issubset(sheetids)
    assert set(pkg.get("additionalCandidateTypes",[])).issubset(sheetids)
    assert pkg["defaultMode"] in modes
for rule in matrix["crossDisciplineRules"]:
    if "sheetId" in rule:assert rule["sheetId"] in sheetids
    assert set(rule["tags"]).issubset(tags)
    assert rule["action"] in matrix["actions"] or rule["action"]=="KEEP"

compiled=compile_project(project,tax,packages,weights,colors)
assert compiled["productionReady"] is False
assert compiled["drawingCount"]==len(compiled["sheetInstances"])
assert {s["sheetTypeId"] for s in compiled["sheetInstances"]}.issubset(sheetids)
assert "MEC-HVAC" not in {s["sheetTypeId"] for s in compiled["sheetInstances"]}
assert "MEC-FLOOR-HEAT" not in {s["sheetTypeId"] for s in compiled["sheetInstances"]}
assert "MEC-RADIATOR" in {s["sheetTypeId"] for s in compiled["sheetInstances"]}
assert all(s["output"]["readyForProduction"] is False for s in compiled["sheetInstances"])
assert all(s["sheetInstanceId"]==f"S-{i:03d}" for i,s in enumerate(compiled["sheetInstances"],1))
assert any(w["code"]=="UNVERIFIED_STB" for w in compiled["diagnostics"])
assert any(w["code"]=="MANUAL_EXCLUDE" for w in compiled["diagnostics"])
assert len([s for s in compiled["sheetInstances"] if s["sheetTypeId"]=="ELV-ROOM"])==2
print(f"PASS sheet taxonomy: {len(groups)} groups, {len(sheetids)} types, {len(tags)} semantic tags, {len(features)} scope features, {len(packages['templates'])} packages")
print(f"PASS sheetset safe example: {compiled['drawingCount']} suggested instances, {len(compiled['diagnostics'])} review/blocking diagnostics")
print("NOT VERIFIED: actual AutoCAD generation, final regulatory completeness, specialist drawings, A3 physical plot")
