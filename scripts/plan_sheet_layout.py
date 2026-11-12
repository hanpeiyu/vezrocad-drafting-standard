#!/usr/bin/env python3
"""Proposal-only paper-space layout planner: never modifies CAD or certifies PDFs."""
import argparse
from itertools import product
from pathlib import Path
import json
import math
ROOT=Path(__file__).resolve().parents[1]

def read(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))

def paper_rect_of_slot(slot):
    r=slot["slotRect"]; m=slot["clipMarginMm"]; t=slot["titleBandMm"]
    return {"x":r["x"]+m, "y":r["y"]+m+t,
            "width":r["width"]-2*m, "height":r["height"]-2*m-t}

def fit_model(bounds, rect, scale, rotation=0):
    if scale<=0 or rotation not in (0,90):
        raise ValueError("invalid scale or content rotation")
    w,h=bounds["widthMm"],bounds["heightMm"]
    if any(not isinstance(x,(float,int)) or not math.isfinite(x) or x<0 for x in (w,h)):
        raise ValueError("model bounds must be finite nonnegative mm")
    if w==0 or h==0:raise ValueError("model bounds must be measured and positive")
    extra_w=bounds.get("annotationReserveWidthMm",0)
    extra_h=bounds.get("annotationReserveHeightMm",0)
    if any(not isinstance(x,(float,int)) or not math.isfinite(x) or x<0 for x in (extra_w,extra_h)):
        raise ValueError("annotation reserve must be finite nonnegative paper mm")
    if rotation==90:w,h=h,w
    pw=w/scale+extra_w;ph=h/scale+extra_h
    return {"fits":pw<=rect["width"]+1e-8 and ph<=rect["height"]+1e-8,
            "printedWidthMm":round(pw,3),"printedHeightMm":round(ph,3),
            "slotWidthMm":rect["width"],"slotHeightMm":rect["height"],
            "widthOccupancy":round(pw/rect["width"],3),"heightOccupancy":round(ph/rect["height"],3)}

def plan_layout(views, strategy="paper-saving-first", allowed_frames=None,
                frames=None,layouts=None,policies=None,lineweights=None,max_alternatives=5):
    frames=frames or read("data/sheet-frame-templates.v2.1.json")
    layouts=layouts or read("data/sheet-layout-compositions.v2.1.json")
    policies=policies or read("data/auto-scale-policies.v2.1.json")
    lineweights=lineweights or read("data/lineweight-profiles.v2.1.json")
    if strategy not in ("paper-saving-first","readability-first","balanced"):
        raise ValueError("unknown layout scoring strategy")
    if not views or not isinstance(views,list) or len(views)>6:
        raise ValueError("requires 1-6 explicitly identified viewports")
    names=[v["slotId"] for v in views]
    if len(names)!=len(set(names)):
        raise ValueError("duplicate viewport slot binding")
    if any("boundsMm" not in v for v in views):
        return {"status":"unmeasured","requiresReview":True,"reason":"actual CAD content bounds missing",
                "provisional":True,"alternatives":[]}
    fdict={f["id"]:f for f in frames["templates"]}
    policy_dict={view:policy for policy in policies["policies"] for view in policy["viewIds"]}
    profiles={x["id"] for x in lineweights["presets"]}
    if any(v["viewId"] not in policy_dict for v in views):
        raise ValueError("unknown viewId")
    if allowed_frames is None:
        allowed_frames=[f["id"] for f in frames["templates"]]
    if not allowed_frames or any(f not in fdict for f in allowed_frames):
        raise ValueError("invalid or empty frame selection")
    frame_rank={f:i for i,f in enumerate(allowed_frames)}
    candidates=[]
    for lay in layouts["templates"]:
        if lay["frameId"] not in frame_rank or len(lay["slots"])!=len(views):
            continue
        slots={s["slotId"]:s for s in lay["slots"]}
        if set(slots)!=set(names):continue
        paper=fdict[lay["frameId"]]["paperId"]
        possible=[]
        for v in views:
            p=policy_dict[v["viewId"]]; slot=slots[v["slotId"]]
            kind="plan" if v["viewId"].startswith("plan-") else v["viewId"]
            if kind not in slot["allowedViewportKinds"]:
                possible=[];break
            clip=paper_rect_of_slot(slot)
            variants=[]
            for denom in p["candidateDenominators"]:
                if denom>p["policyCeiling"] or f"{paper}-1-{denom}" not in profiles:continue
                rotations=(0,90) if p["allow90DegreeRotation"] else (0,)
                for rot in rotations:
                    geom=fit_model(v["boundsMm"],clip,denom,rot)
                    if geom["fits"]:
                        variants.append({"slotId":slot["slotId"],"viewId":v["viewId"],
                                         "scaleDenominator":denom,"rotationDegrees":rot,
                                         "lineweightPresetId":f"{paper}-1-{denom}",
                                         "viewportContentRect":clip,"fit":geom})
            if not variants:
                possible=[];break
            possible.append(variants)
        if not possible:continue
        for combination in product(*possible):
            combination=list(combination)
            primary=next((x for x in combination if x["slotId"]=="PRIMARY"),combination[0])
            denominator=primary["scaleDenominator"]
            rotation_count=sum(x["rotationDegrees"]!=0 for x in combination)
            denom_penalty=sum(x["scaleDenominator"] for x in combination)
            whitespace=sum(1-x["fit"]["widthOccupancy"]*x["fit"]["heightOccupancy"] for x in combination)
            if strategy=="paper-saving-first":score=(frame_rank[lay["frameId"]],denominator,denom_penalty,rotation_count,round(whitespace,3))
            elif strategy=="readability-first":score=(denominator,denom_penalty,frame_rank[lay["frameId"]],rotation_count,round(whitespace,3))
            else:score=(round(0.6*(denominator/50)+0.4*(frame_rank[lay["frameId"]]+1),4),denom_penalty,rotation_count,round(whitespace,3))
            candidates.append({"layoutId":lay["id"],"frameId":lay["frameId"],"paperId":paper,
                               "score":score,"viewports":combination,"provisional":True,
                               "plotterCalibrated":bool(fdict[lay["frameId"]].get("calibratedPrinter",False)),
                               "requiresReview":True})
    candidates.sort(key=lambda v:v["score"])
    if not candidates:
        return {"status":"no-fit","requiresReview":True,"provisional":True,
                "recommendation":"Try larger paper, separate room/detail sheets, or approved alternate scales",
                "alternatives":[]}
    return {"status":"fit-suggested","strategy":strategy,"recommended":candidates[0],
            "alternatives":candidates[:max_alternatives],
            "provisional":True,"requiresReview":True,
            "warnings":["Drawable zones and plot margins are examples, not validated PC3/AutoCAD viewports",
                        "Annotation collision, non-rectangular clips, labels and sheet numbering require CAD review"]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--strategy",choices=("paper-saving-first","readability-first","balanced"),default="readability-first")
    p.add_argument("--width-mm",type=float,default=24000)
    p.add_argument("--height-mm",type=float,default=12000)
    a=p.parse_args()
    views=[{"slotId":"PRIMARY","viewId":"plan-furniture",
            "boundsMm":{"widthMm":a.width_mm,"heightMm":a.height_mm}}]
    print(json.dumps(plan_layout(views,strategy=a.strategy),ensure_ascii=False,indent=2))

if __name__=="__main__":main()
