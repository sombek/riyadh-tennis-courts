"""Explicit first-time initialization; refuses to replace an existing state."""
import json
import sys
from pathlib import Path
from monitor.state import Store

path=Path(sys.argv[1] if len(sys.argv)>1 else 'runtime/state.json')
path.parent.mkdir(parents=True,exist_ok=True)
with path.open('x') as f: json.dump(Store.initial(),f,indent=2)
print(f'Initialized {path}; first successful run will establish baseline')
