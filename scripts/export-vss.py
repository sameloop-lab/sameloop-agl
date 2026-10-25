#!/usr/bin/env python3
"""Export du sous-ensemble SameLoop ; ce n'est pas un compilateur VSS général."""
import json
from pathlib import Path
from sameloop_agl.contract import SIGNALS
root=Path(__file__).resolve().parents[1]
children={n:{'type':t,'datatype':dt,'description':desc} for n,(dt,t,desc) in SIGNALS.items()}
v={'Vehicle':{'type':'branch','description':'Vehicle root','children':{'SameLoop':{'type':'branch','description':'Extension de démonstration SameLoop','children':children}}}}
(root/'config/vss.json').write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
lines=['# Extension privée SameLoop ; pas un modèle standard COVESA.','Vehicle:','  type: branch','  description: Vehicle root','Vehicle.SameLoop:','  type: branch','  description: Démonstration SameLoop']
for n,(dt,t,desc) in SIGNALS.items():lines.extend([f'Vehicle.SameLoop.{n}:',f'  type: {t}',f'  datatype: {dt}',f'  description: {json.dumps(desc,ensure_ascii=False)}'])
(root/'config/sameloop.vspec').write_text('\n'.join(lines)+'\n')
