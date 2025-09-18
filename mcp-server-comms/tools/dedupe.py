# tools/dedupe.py
from typing import List, Dict, Tuple

def dedupe(records: List[Dict]) -> List[Dict]:
    """
    Remove duplicates by (name,email) pair (case-insensitive).
    """
    seen: set[Tuple[str, str]] = set()
    out: List[Dict] = []
    for r in records:
        key = (str(r.get("name", "")).lower(), str(r.get("email", "")).lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out

