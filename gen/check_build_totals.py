#!/usr/bin/env python3
"""
Regression check on the build totals for the 18-point example build (5 hubs, 8 nodes).

Moved here from the firmware repo's sim/check_numbers.py when the hardware was split
out, because every value it checks is derived from gen/boards.py and gen/panel.py.

    python3 gen/check_build_totals.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boards as B  # noqa: E402
import panel as P  # noqa: E402

failures = []
checks = 0


def check(name, computed, documented, tolerance=0.0, unit=""):
    global checks
    checks += 1
    rel = abs(computed - documented) / max(abs(documented), 1e-12)
    ok = rel <= tolerance
    print(
        f"  [{'ok' if ok else 'FAIL'}] {name}: computed {computed:.4g}{unit}, "
        f"documented {documented:g}{unit}"
    )
    if not ok:
        failures.append(name)


print("Build totals")
hub_n = len(B.BOARDS["hub"]["comps"])
node_n = len(B.BOARDS["node"]["comps"])
check("BOM placements, 5 hubs + 8 nodes", 5 * hub_n + 8 * node_n, 303)

sel = {"hub": 5, "node": 8}
cols, rows, cw, ch = P.layout(sel)
check("panel cell width", cw, 45.4, 0.01, " mm")
check("panel cell height", ch, 30.4, 0.01, " mm")
check("panel width", cols * cw + 2 * P.PANEL_RAIL_MM, 373.2, 0.01, " mm")
check("panel height", rows * ch + 2 * P.PANEL_RAIL_MM, 70.8, 0.01, " mm")
checks += 1
if cols * rows >= sum(sel.values()):
    print(f"  [ok] {cols}x{rows} grid holds {sum(sel.values())} boards")
else:
    failures.append("panel grid too small")

print(f"\n{checks} checks, {len(failures)} failed")
sys.exit(1 if failures else 0)
