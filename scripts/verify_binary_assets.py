#!/usr/bin/env python3
"""Binary file structure checks; NOT a replacement for AutoCAD 2027 print testing."""
from pathlib import Path
import json
import ezdxf
from ezdxf.addons import acadctb
ROOT=Path(__file__).resolve().parents[1]
config=json.loads((ROOT/'data/layers-v2.json').read_text(encoding='utf-8'))
expected_styles=set(config['plotStyleNames'])|{'Normal'}
for mode in ('BW','COLOR'):
    p=ROOT/f'assets/stb/VZ-A3-{mode}.stb'
    table=acadctb.load(p)
    assert set(table.keys())==expected_styles
    for name in config['plotStyleNames']:
        s=table[name]
        assert s.lineweight==acadctb.OBJECT_LINEWEIGHT, (mode,name)
        assert s.linetype==acadctb.OBJECT_LINETYPE, (mode,name)
        if mode=='BW' and name!='VZ-MASK':
            assert s.color==(0,0,0), (mode,name,s.color)
        else:
            assert s.color is None, (mode,name,s.color)
    print('PASS STB',p.name,p.stat().st_size)
dxf=ezdxf.readfile(ROOT/'assets/dxf/VZ-图层目录-v2.dxf')
for row in config['layers']:
    layer=dxf.layers.get(row['图层名称'])
    assert layer.dxf.color==row['颜色ACI']
    assert layer.dxf.lineweight==round(row['线宽mm']*100)
    assert layer.dxf.plot==row['是否打印']
    assert layer.dxf.linetype==row['线型']
print('PASS DXF',len(config['layers']),'layers')
print('NOT TESTED: AutoCAD 2027 Plot Style Manager / actual PDF output / WIPEOUT masking')
