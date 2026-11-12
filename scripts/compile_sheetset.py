#!/usr/bin/env python3
"""Compile proposed drawing sheets from a home-renovation scope.
Dry-run only: does not modify DWG or create validated STB/PDF drawings.
"""
import argparse
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))

def compile_project(project, tax=None, packages=None, profile=None, colors=None):
    tax=tax or read("data/sheet-taxonomy.v2.1.json")
    packages=packages or read("data/sheetset-presets.v2.1.json")
    profile=profile or read("data/lineweight-profiles.v2.1.json")
    colors=colors or read("data/print-color-profiles.v2.1.json")
    by_id={t["id"]:t for t in tax["sheetTypes"]}
    package=next((x for x in packages["templates"] if x["id"]==project["templateId"]),None)
    if package is None:raise ValueError("unknown templateId")
    if project.get("status")!="example-not-a-construction-deliverable":
        raise ValueError("This prototype only accepts clearly marked examples; do not generate production deliveries.")
    known_features={x["id"] for x in tax["scopeFeatures"]}
    if not set(project["features"]).issubset(known_features):
        raise ValueError("unknown project scope feature")
    selection=set()
    if "explicitSheetTypeIds" in package:
        selection.update(package["explicitSheetTypeIds"])
    else:
        for t in tax["sheetTypes"]:
            trigger=t["trigger"]
            typ=trigger["type"]
            if typ=="core" and "core" in package["includeTriggerTypes"]:selection.add(t["id"])
            if typ=="feature" and "feature" in package["includeTriggerTypes"]:
                if any(project["features"].get(feature,False) for feature in trigger["featuresAny"]):
                    selection.add(t["id"])
    selection.update(project.get("manualInclude",[]))
    warnings=[]
    for excluded in project.get("manualExclude",[]):
        key=excluded["sheetTypeId"]
        if key not in by_id:raise ValueError("unknown exclusion type")
        if not excluded.get("reason","").strip():raise ValueError("manual exclusion must provide reason")
        if key in selection:
            selection.remove(key)
            warnings.append({"severity":"REVIEW","code":"MANUAL_EXCLUDE","typeId":key,"reason":excluded["reason"]})
        if by_id[key]["trigger"]["type"]=="core":
            warnings.append({"severity":"WARNING","code":"CORE_EXCLUDED","typeId":key,"reason":"Recommended core sheet intentionally omitted; review before construction"})
    if not selection.issubset(by_id): raise ValueError("unknown manual sheet types")
    known_profiles={x["id"]:x for x in profile["presets"]}
    modes=colors["outputModes"]
    if not set(project.get("outputRequest",{}).get("requestedModes",[])).issubset(modes):
        raise ValueError("unknown print output mode")
    emitted=[]
    for t in tax["sheetTypes"]:
        if t["id"] not in selection: continue
        instances=t["instances"]
        repeat=instances["repeatBy"]
        targets=project.get("instanceTargets",{}).get(t["id"],[]) if repeat!="single" else [{}]
        if not targets:
            warnings.append({"severity":"REVIEW","code":"MISSING_INSTANCE_TARGETS","typeId":t["id"],"message":"repeatable drawing needs explicit room/cabinet/detail reference"})
            continue
        for target in targets:
            missing=[k for k in instances["requiresReference"] if not target.get(k)]
            if missing:
                warnings.append({"severity":"ERROR","code":"INCOMPLETE_REFERENCE","typeId":t["id"],"missing":missing})
                continue
            suggested=t["suggested"]
            paper=project.get("outputRequest",{}).get("defaultPaper",suggested["paper"])
            scale=suggested["scaleDenominator"]
            lw_id=f"{paper}-1-{scale}" if scale else None
            if lw_id and lw_id not in known_profiles:
                warnings.append({"severity":"ERROR","code":"MISSING_LINEWEIGHT_PRESET","typeId":t["id"],"requested":lw_id})
            mode=package.get("defaultMode") if project["templateId"]=="concept" else suggested["outputMode"]
            if mode not in modes:raise ValueError("unknown print mode")
            unverified=modes[mode]["assetStatus"]!="VERIFIED"
            if unverified:
                warnings.append({"severity":"BLOCKED","code":"UNVERIFIED_STB","typeId":t["id"],"mode":mode})
            emitted.append({
                "sheetInstanceId":f"S-{len(emitted)+1:03d}",
                "sheetTypeId":t["id"],"groupId":t["groupId"],
                "title":t["name"],"baseViewPresetId":t["baseViewPresetId"],
                "targetRef":target,
                "focusTags":t["expression"]["focus"],
                "contextTags":t["expression"]["context"],
                "hiddenTags":t["expression"]["hide"],
                "output":{"paper":paper,"scaleDenominator":scale,"lineweightPreset":lw_id,
                          "colorMode":mode,"stbTarget":modes[mode]["targetStbFile"],"readyForProduction":False},
                "specialistReviewRequired":t["review"]["specialistApproval"],
                "dependencies":t["prerequisites"]
            })
    included_types={x["sheetTypeId"] for x in emitted}
    for item in emitted:
        for dependency in item["dependencies"]:
            if dependency not in included_types:
                warnings.append({"severity":"REVIEW","code":"MISSING_PREREQUISITE","typeId":item["sheetTypeId"],"dependsOn":dependency})
    if any(x["specialistReviewRequired"] for x in emitted):
        warnings.append({"severity":"REVIEW","code":"SPECIALIST_SIGNOFF","message":"Drawing compilation does not validate electrical/mechanical system designs"})
    return {
        "schema":"vezrocad.sheetset-dryrun.v2.1",
        "projectId":project["id"],
        "packageId":package["id"],
        "status":"PROPOSAL_ONLY_NOT_FOR_CONSTRUCTION",
        "drawingCount":len(emitted),
        "sheetInstances":emitted,
        "diagnostics":warnings,
        "productionReady":False,
        "indexMeaning":"Generated from actual emitted sheets only; no assertion of statutory completeness"
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--project",default="examples/sheetset-project.v2.1.example.json")
    parser.add_argument("--output",help="Write dry-run JSON to a named path; never writes DWG")
    args=parser.parse_args()
    project=read(args.project)
    result=compile_project(project)
    content=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.output:
        Path(args.output).write_text(content,encoding="utf-8")
        print(f"Prepared {result['drawingCount']} proposed sheet instances at {args.output}")
    else:print(content)

if __name__=="__main__":main()
