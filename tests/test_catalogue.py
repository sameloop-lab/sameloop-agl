import json
from pathlib import Path
import unittest
from sameloop_agl.contract import SIGNALS

class CatalogueTests(unittest.TestCase):
    def test_metadata_matches_runtime_contract(self):
        doc=json.loads((Path(__file__).resolve().parents[1]/'config/vss.json').read_text())
        children=doc['Vehicle']['children']['SameLoop']['children']
        self.assertEqual(set(children),set(SIGNALS))
        for n,(datatype,kind,description) in SIGNALS.items():
            self.assertEqual(children[n],dict(type=kind,datatype=datatype,description=description))
