#!/usr/bin/env python3
"""Validate frame geometry, viewport rules and layout scorer; no AutoCAD side effects."""
from pathlib import Path
import json,math,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from plan_sheet_layout import plan_layout,paper_rect_of_slot,read,fit_model
frames=read("data/sheet-frame-templates.v2.1.json")
layouts=read("data/sheet-layout-compositions.v2.1.json")
vp=read("data/viewport-standards.v2.1.json")
views=set(read("data/view-presets.json")["views"])
lineweights=read("data/lineweight-profiles.v2.1.json")
frame_by_id={f["id"]:f for f in frames["templates"]}
assert len(frame_by_id)==len(frames["templates"])
assert frames["units"]=="paper mm" and layouts["units"]=="paper mm"
def contains(container,inner):
    return inner["x"]>=container["x"] and inner["y"]>=container["y"] and inner["x"]+inner["width"]<=container["x"]+container["width"] and inner["y"]+inner["height"]<=container["y"]+container["height"]
def intersects(a,b):
    return min(a["x"]+a["width"],b["x"]+b["width"])>max(a["x"],b["x"]) and min(a["y"]+a["height"],b["y"]+b["height"])>max(a["y"],b["y"])
for f in frames["templates"]:
    page=f["paperRect"];printable=f["printableRectExample"];border=f["borderRect"]
    assert contains(page,printable) and contains(printable,border),f["id"]
    assert f["calibratedPrinter"] is False
    zones={z["id"]:z for z in f["zones"]}
    assert all(contains(border,z["rect"]) for z in zones.values())
    assert contains(zones["footer"]["rect"],zones["title-block"]["rect"])
    assert not intersects(zones["footer"]["rect"],zones["drawing"]["rect"])
    assert zones["drawing"]["kind"]=="drawable"
templateids=[l["id"] for l in layouts["templates"]]
assert len(templateids)==len(set(templateids))
for lay in layouts["templates"]:
    frame=frame_by_id[lay["frameId"]]
    drawable=next(z["rect"] for z in frame["zones"] if z["id"]=="drawing")
    assert len({s["slotId"] for s in lay["slots"]})==len(lay["slots"])
    for s in lay["slots"]:
        assert contains(drawable,s["slotRect"]),(lay["id"],s["slotId"])
        content=paper_rect_of_slot(s)
        assert content["width"]>0 and content["height"]>0
        assert contains(s["slotRect"],content)
    for i,a in enumerate(lay["slots"]):
        for b in lay["slots"][i+1:]:
            assert not intersects(a["slotRect"],b["slotRect"]),(lay["id"],a["slotId"],b["slotId"])
            # Require real physical gap in at least one dimension.
            ra,rb=a["slotRect"],b["slotRect"]
            gap=max(rb["x"]-(ra["x"]+ra["width"]),ra["x"]-(rb["x"]+rb["width"]),rb["y"]-(ra["y"]+ra["height"]),ra["y"]-(rb["y"]+rb["height"]))
            assert gap>=lay["gapMinMm"]-1e-8
assert set(vp["viewportKinds"][0]["viewIds"])=={x for x in views if x.startswith("plan-")}
assert vp["autoCADInvariants"]["displayLocked"] is True
assert frames["sheetBorderPolicies"]["plotScale"]=="1:1"
assert len(frames["titleBlocks"][0]["mandatoryFields"])>=8
layers=read("data/layers-v2.json")["layers"]
layer_by_name={l["图层名称"]:l for l in layers}
policy=frames["sheetBorderPolicies"]
for key in ("frameLayer","titleBlockLayer","titleBlockTextLayer","viewportBoundaryLayer"):
    assert policy[key] in layer_by_name, (key,policy[key])
assert layer_by_name[policy["viewportBoundaryLayer"]]["是否打印"]==0
assert layer_by_name[policy["frameLayer"]]["是否打印"]==1
primary=[{"slotId":"PRIMARY","viewId":"plan-furniture","boundsMm":{"widthMm":24000,"heightMm":12000}}]
saving=plan_layout(primary,"paper-saving-first")
readable=plan_layout(primary,"readability-first")
assert saving["recommended"]["paperId"]=="A3",saving
assert saving["recommended"]["viewports"][0]["scaleDenominator"]==75,saving
assert readable["recommended"]["paperId"]=="A2",readable
assert readable["recommended"]["viewports"][0]["scaleDenominator"]==50,readable
assert saving["provisional"] is True and readable["provisional"] is True
mixed=[{"slotId":"PRIMARY","viewId":"plan-furniture","boundsMm":{"widthMm":12000,"heightMm":8000}},
       {"slotId":"DETAIL","viewId":"detail","boundsMm":{"widthMm":1200,"heightMm":800}}]
combo=plan_layout(mixed,"paper-saving-first")
assert combo["recommended"]["layoutId"]=="A3-MAIN-DETAIL",combo
assert set(x["scaleDenominator"] for x in combo["recommended"]["viewports"])=={10,50},combo
locked_bad=plan_layout([{"slotId":"PRIMARY","viewId":"plan-furniture",
    "boundsMm":{"widthMm":24000,"heightMm":12000},
    "locked":{"frameId":"A3-L-VZ","denominator":50,"rotationDegrees":0}}],
    allowed_frames=["A3-L-VZ"])
assert locked_bad["status"]=="locked-overflow"
locked_good=plan_layout([{"slotId":"PRIMARY","viewId":"plan-furniture",
    "boundsMm":{"widthMm":24000,"heightMm":12000},
    "locked":{"frameId":"A3-L-VZ","denominator":75,"rotationDegrees":0}}],
    allowed_frames=["A3-L-VZ"])
assert locked_good["recommended"]["viewports"][0]["scaleDenominator"]==75
missing=plan_layout([{"slotId":"PRIMARY","viewId":"plan-furniture"}])
assert missing["status"]=="unmeasured"
oversize=plan_layout([{"slotId":"PRIMARY","viewId":"plan-furniture","boundsMm":{"widthMm":100000,"heightMm":100000}}])
assert oversize["status"]=="no-fit"
try:
    plan_layout([primary[0],primary[0]])
    raise AssertionError("duplicate slot must fail")
except ValueError:pass
assert set(v["id"] for v in vp["viewportKinds"])=={"plan","elevation","detail"}
print(f"PASS frame/viewport contract: {len(frames['templates'])} frames, {len(layouts['templates'])} layout templates, {len(vp['viewportKinds'])} viewport kinds")
print("PASS candidate layout scoring: A3 1:75 paper-saving vs A2 1:50 readability; mixed-scale slots and fail-safe constraints")
print("NOT VERIFIED: actual plotter margins, annotated bounds, custom VPCLIP, AutoCAD 2027 PDF and physical paper")
