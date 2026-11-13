#!/usr/bin/env python3
"""Validate JSON data consistency; does not claim AutoCAD plot compatibility."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINEWEIGHTS = (0.13, 0.15, 0.18, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.53, 0.70)
errors = []


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def check(cond, msg):
    if not cond:
        errors.append(msg)


def main():
    manifest = load("manifest.json")
    config = load("data/layers-v2.json")
    roles = load("data/representation-roles.json")["roles"]
    views = load("data/view-presets.json")["views"]
    mapping = load("data/semantic-role-layer-mapping.example.json")["mappings"]
    sem_roles = load("data/semantic-to-role.json")["mappings"]

    role_ids = {r["id"] for r in roles}
    styles = set(config["plotStyleNames"])
    layers = config["layers"]
    names = {r["图层名称"] for r in layers}

    check(len(role_ids) == len(roles), "duplicate role ids")
    check(len(names) == len(layers), "duplicate layer names")
    check(len(layers) == manifest["layerCount"], f"layerCount {len(layers)} != manifest {manifest['layerCount']}")
    check(len(roles) == manifest["representationRoleCount"], "role count != manifest")
    check(len(views) == manifest["viewPresetCount"], "view count != manifest")
    check({"VZ-MAIN", "VZ-MASK"} <= styles, "missing VZ-MAIN/VZ-MASK style")

    for r in layers:
        n = r["图层名称"]
        segs = n.split("-")
        check(2 <= len(segs) <= 5, f"segment count: {n}")
        check(all(1 <= len(x) <= 3 and re.fullmatch(r"[\u4e00-\u9fff]+", x) for x in segs), f"name format: {n}")
        check(r["默认表达角色"] in role_ids, f"unknown role: {n}")
        check(r["STB样式"] in styles, f"unknown style: {n}")
        check(1 <= r["颜色ACI"] <= 255, f"ACI out of range: {n}")
        check(r["是否打印"] in (0, 1), f"plot flag: {n}")
        check(r["线宽mm"] in LINEWEIGHTS, f"lineweight: {n}")
        if r["默认表达角色"] == "WIPEOUT_MASK":
            check(r["是否打印"] == 1, f"mask layer must plot: {n}")
            check(r["STB样式"] == "VZ-MASK", f"mask layer style: {n}")

    used_roles = {r["默认表达角色"] for r in layers}
    for rid in sorted(role_ids - used_roles):
        print(f"WARN: role not used by any layer: {rid}")

    for m in mapping:
        check(m["layer"] in names, f"mapping layer: {m}")
        check(m["view"] in views, f"mapping view: {m}")
        check(m["representationRole"] in role_ids, f"mapping role: {m}")

    for vid, v in views.items():
        for key in ("focusRoles", "faintRoles"):
            for rid in v.get(key, []):
                check(rid in role_ids, f"view {vid}.{key} unknown role {rid}")

    seen = set()
    for s in sem_roles:
        check(s["semantic"] not in seen, f"duplicate semantic {s['semantic']}")
        seen.add(s["semantic"])
        check(s["role"] in role_ids, f"semantic {s['semantic']} -> unknown role {s['role']}")

    for p in sorted((ROOT / "examples").glob("*.json")):
        ex = load(f"examples/{p.name}")
        for item in ex.get("representation", []):
            check(item["role"] in role_ids, f"{p.name}: unknown role {item['role']}")
            check(item["layer"] in names, f"{p.name}: unknown layer {item['layer']}")

    if errors:
        print("FAIL:")
        for e in errors:
            print(" -", e)
        return 1
    print("PASS:", len(layers), "layers", len(roles), "roles", len(views), "views",
          len(mapping), "sample mappings", len(sem_roles), "semantic mappings")
    print("Note: AutoCAD 2027/STB actual plot compatibility still requires manual tests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
