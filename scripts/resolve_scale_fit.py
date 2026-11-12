#!/usr/bin/env python3
"""Proposal-only viewport scale fit resolver: never edits DWG or validates plots."""
import argparse, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def resolve(view_id, width_mm, height_mm, allowed_layouts=None, annotation_reserve_width_mm=0, annotation_reserve_height_mm=0, locked=None, layouts_data=None, policy_data=None, lineweights_data=None):
    layouts_data=layouts_data or read("data/paper-fit-layouts.v2.1.json")
    policy_data=policy_data or read("data/auto-scale-policies.v2.1.json")
    lineweights_data=lineweights_data or read("data/lineweight-profiles.v2.1.json")
    catalog={x["id"]:x for x in layouts_data["paperLayouts"]}
    policy=next((p for p in policy_data["policies"] if view_id in p["viewIds"]),None)
    if policy is None:raise ValueError("unknown view kind")
    order=allowed_layouts or layouts_data["suggestedLayoutOrder"]
    if not order or any(x not in catalog for x in order):raise ValueError("unknown paper layout")
    values=(width_mm,height_mm,annotation_reserve_width_mm,annotation_reserve_height_mm)
    if any(not isinstance(v,(int,float)) for v in values):raise ValueError("extent and annotations must be numbers")
    if width_mm<=0 or height_mm<=0:
        return {"status":"insufficient-geometry","viewId":view_id,"fitVerified":False,"reason":"CAD content bounds unavailable"}
    if annotation_reserve_width_mm<0 or annotation_reserve_height_mm<0:raise ValueError("annotation reserve must be nonnegative")
    presets={p["id"] for p in lineweights_data["presets"]}
    missing=[]
    def try_one(layout_id,scale,rotation):
        if scale<=0:raise ValueError("scale must be positive")
        q=catalog[layout_id]
        w,h=(width_mm,height_mm) if rotation==0 else (height_mm,width_mm)
        plotted_w=w/scale+annotation_reserve_width_mm
        plotted_h=h/scale+annotation_reserve_height_mm
        return (plotted_w<=q["usableViewportWidthMm"]+1e-8 and plotted_h<=q["usableViewportHeightMm"]+1e-8,
                round(plotted_w,3),round(plotted_h,3))
    if locked:
        lid=locked["layoutId"];den=locked["denominator"];rot=locked.get("rotationDegrees",0)
        if lid not in catalog or lid not in order:raise ValueError("locked paper is not allowed")
        if rot not in (0,90):raise ValueError("rotation must be 0 or 90")
        fits,pw,ph=try_one(lid,den,rot)
        profile=f'{catalog[lid]["paperId"]}-1-{den}'
        return {"status":"fit-suggested" if fits and profile in presets else "locked-overflow",
                "locked":True,"layoutId":lid,"paperId":catalog[lid]["paperId"],"scaleDenominator":den,"rotationDegrees":rot,
                "paperFeatureBoundsMm":{"width":pw,"height":ph},
                "lineweightProfileId":profile if profile in presets else None,"fitVerified":False,
                "requiresReview":True,"warnings":["User-locked scale must never be silently changed"] if not fits else []}
    pref=policy["preferredDenominator"]
    denominators=sorted(policy["candidateDenominators"],key=lambda x:(0 if x==pref else 1,x))
    for layout_id in order:
        paper=catalog[layout_id]["paperId"]
        for den in denominators:
            if den>policy["policyCeiling"]:continue
            profile=f"{paper}-1-{den}"
            if profile not in presets:
                missing.append(profile);continue
            rotations=[0,90] if policy["allow90DegreeRotation"] else [0]
            for rot in rotations:
                fits,pw,ph=try_one(layout_id,den,rot)
                if fits:
                    return {"status":"fit-suggested","layoutId":layout_id,"paperId":paper,
                            "scaleDenominator":den,"rotationDegrees":rot,
                            "paperFeatureBoundsMm":{"width":pw,"height":ph},
                            "lineweightProfileId":profile,"fitVerified":False,"requiresReview":True,
                            "warnings":(["Rotation changes drawing orientation; check north arrow, titles and notes"] if rot==90 else []),
                            "unavailablePresets":sorted(set(missing))}
    return {"status":"no-fit","viewId":view_id,"fitVerified":False,"requiresReview":True,
            "recommendation":policy["ifNoFit"],"unavailablePresets":sorted(set(missing)),
            "warnings":["Do not shrink below the policy ceiling without approval. Try another paper or split the view."]}

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--view",default="plan-furniture")
    arg.add_argument("--width-mm",type=float,default=24000)
    arg.add_argument("--height-mm",type=float,default=12000)
    args=arg.parse_args()
    print(json.dumps(resolve(args.view,args.width_mm,args.height_mm),ensure_ascii=False,indent=2))

if __name__=="__main__":main()
