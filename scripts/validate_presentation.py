#!/usr/bin/env python3
"""Validate v2.1 PROPOSAL config; never certifies AutoCAD printed output."""
from pathlib import Path
import json
import re
from collections import defaultdict, deque
ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

roles = {x["id"] for x in load("data/representation-roles.json")["roles"]}
views = set(load("data/view-presets.json")["views"])
oldstyles = set(load("data/layers-v2.json")["plotStyleNames"])
order = load("data/draw-order-constraints.v2.1.json")
weights = load("data/lineweight-profiles.v2.1.json")
lod = load("data/detail-visibility-policy.v2.1.json")
colors = load("data/print-color-profiles.v2.1.json")
job = load("examples/print-job.v2.1.example.json")
assert all(x["status"] in ("proposal", "design-only") for x in (order,weights,lod,colors))
assert set(order["knownRoles"]) == roles
assert set(weights["baseRoleLineweightMm"]) == roles

def check_dag(edges):
    graph = defaultdict(set)
    indeg = {r: 0 for r in roles}
    for edge in edges:
        a,b = edge["below"],edge["above"]
        assert a in roles and b in roles and a != b, edge
        if b not in graph[a]:
            graph[a].add(b); indeg[b] += 1
    q=deque(sorted([r for r,d in indeg.items() if d==0]))
    seen=0
    while q:
        a=q.popleft();seen+=1
        for b in sorted(graph[a]):
            indeg[b]-=1
            if indeg[b]==0:q.append(b)
    assert seen == len(roles), "draw-order cyclic constraints"

check_dag(order["globalEdges"])
assert set(order["viewEdges"]).issubset(views)
for v,extra in order["viewEdges"].items():
    check_dag(order["globalEdges"]+extra)

allow=set(weights["allowedWidthsMm"])
for role,mm in weights["baseRoleLineweightMm"].items():
    assert mm is None or mm in allow, (role,mm)
assert weights["baseRoleLineweightMm"]["WIPEOUT_MASK"] is None
assert weights["baseRoleLineweightMm"]["NONPLOT_GUIDE"] is None
presets=weights["presets"]
assert len({p["id"] for p in presets}) == len(presets)
assert len({(p["paper"],p["scaleDenominator"]) for p in presets}) == len(presets)
for p in presets:
    assert p["scaleDenominator"] > 0 and p["paper"] in ("A1","A2","A3")
    assert p["id"] == f'{p["paper"]}-1-{p["scaleDenominator"]}'
    for role,w in p["overridesMm"].items():
        assert role in roles and w in allow and role not in ("WIPEOUT_MASK","NONPLOT_GUIDE")

th=lod["thresholds"]
assert len(th)==3 and th[0]["maxPaperFeatureMm"]==th[1]["minPaperFeatureMm"]
assert th[1]["maxPaperFeatureMm"]==th[2]["minPaperFeatureMm"]
assert set(lod["neverAutoHide"]) >= {"CUT_HEAVY","DIMENSION","ANNOTATION"}
styles=colors["stableStyleNames"]
assert len(set(styles))==len(styles)
assert oldstyles.issubset(styles)
assert colors["status"]=="design-only"
assert len(colors["proposedV21Styles"])>=1
assert set(colors["outputModes"])=={"BW","GRAY","COLOR","PRESENTATION"}
for mode,config in colors["outputModes"].items():
    assert config["assetStatus"]=="DESIGN_ONLY_NOT_GENERATED"
    assert config["lineweight"]=="USE_OBJECT"
    assert config["linetype"]=="USE_OBJECT"
    assert set(config["stylePrintColor"])==set(styles)
    for name,value in config["stylePrintColor"].items():
        if name=="VZ-MASK": assert value=="OBJECT"
        else: assert re.fullmatch(r"#[0-9A-Fa-f]{6}",value), (mode,name,value)
assert not any((ROOT / "assets/stb" / f"VZ-{m}-v2.1.stb").exists() for m in colors["outputModes"]), "Unexpected unverified binary"
assert job["proposalOnly"] is True and job["dryRun"] is True
for vp in job["viewports"]:
    assert vp["viewId"] in views and vp["lineweightPreset"] in {p["id"] for p in presets}
    assert any(p["scaleDenominator"]==vp["scaleDenominator"] for p in presets if p["id"]==vp["lineweightPreset"])
print(f"PASS v2.1 proposal: {len(roles)} roles, {len(presets)} paper-scale presets, {len(styles)} stable print styles, {len(colors['outputModes'])} print color modes; draw-order graphs acyclic")
print("NOT VERIFIED: AutoCAD 2027 actual plot, STB v2.1 binary, nested block/wipeout behavior")
