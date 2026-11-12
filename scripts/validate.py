#!/usr/bin/env python3
"""Validate JSON data consistency; does not claim AutoCAD plot compatibility."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
def get(p):return json.loads((ROOT/p).read_text(encoding="utf-8"))
config=get('data/layers-v2.json')
roles=get('data/representation-roles.json')['roles']
views=get('data/view-presets.json')['views']
mapping=get('data/semantic-role-layer-mapping.example.json')['mappings']
roleids={r['id'] for r in roles}
styles=set(config['plotStyleNames'])
assert len(roleids)==len(roles)
names={r['图层名称'] for r in config['layers']}
assert len(names)==len(config['layers']), 'duplicate names'
assert len(config['layers'])>=122
assert {'VZ-MAIN','VZ-MASK'} <= styles
for r in config['layers']:
 segs=r['图层名称'].split('-')
 assert 2<=len(segs)<=5, r['图层名称']
 assert all(1<=len(x)<=3 and re.fullmatch(r'[\u4e00-\u9fff]+',x) for x in segs),r['图层名称']
 assert r['默认表达角色'] in roleids,r['图层名称']
 assert r['STB样式'] in styles,r['图层名称']
 assert 1<=r['颜色ACI']<=255
 assert r['是否打印'] in (0,1)
 assert r['线宽mm'] in (0.13,0.15,0.18,0.20,0.25,0.30,0.35,0.40,0.50,0.53,0.70)
 if r['默认表达角色']=='WIPEOUT_MASK':
  assert r['是否打印']==1, r['图层名称']
  assert r['STB样式']=='VZ-MASK',r['图层名称']
for m in mapping:
 assert m['layer'] in names,m
 assert m['view'] in views,m
 assert m['representationRole'] in roleids,m
print('PASS:',len(config['layers']),'layers',len(roles),'roles',len(views),'views',len(mapping),'sample mappings')
print('Note: AutoCAD 2027/STB actual plot compatibility still requires manual tests.')
