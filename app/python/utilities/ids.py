import re

"""
eid / did / aid convenience functions

* did, aid
* eid is is did and aid separated by comma,
  comma in did is replaced by underscore
* css "sanitizes" eid for use as css class name, 
  replacing all non-alphanumeric characters 
  except comma and dash with underscore
"""


_RE = re.compile('[^a-zA-Z0-9-,_]')

def eid(did: str, aid: str) -> str:
    return f"{did.replace(',', '_')},{aid}"

def did(eid: str) -> str:
    return eid.split(',', 1)[0]

def aid(eid: str) -> str:
    return eid.split(',', 1)[1]

def css(eid: str) -> str:
    global _RE
    assert eid.count(',') == 1, "eid must contain exactly one comma"
    return _RE.sub('_', eid)
