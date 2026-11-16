#!/usr/bin/env python3
"""
Check the hub's chain I2C pull-ups against the chains they have to drive.

    python3 gen/check_chain_pullups.py

Reads the pull-up value from gen/boards.py, so changing R4/R5 is checked here. The bus
model is the firmware repo's (docs/I2SPI.md §14.2, pinned in its sim/check_numbers.py):
a 300 ns Fast-mode rise time at 400 kHz lets a pull-up R drive 300 ns / (0.8473 R) of bus
capacitance. The host's own pin and traces are not counted, so leave some margin.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boards as B  # noqa: E402

RISE_NS = 300             # I2C Fast mode
NODE_PF = 15              # per node per line: ATtiny pin, two jacks, traces - ESTIMATE
CABLE_PF_PER_M = 60       # flat 8P8C cable, midpoint of 50-70 pF/m - MEASURE YOURS
STRONGEST_OHM = 970       # (3.3 V - 0.4 V) / 3 mA: the Fast-mode sink limit

# Chains a hub must drive. The 18-point example build runs at most two nodes per hub
# over the longest run, thigh to foot.
REQUIRED = [("18-point build, longest chain", 2, 0.85)]

failures = []


def ohms(value: str) -> float:
    m = re.fullmatch(r"(\d+)([kKmM]?)(\d*)", value)
    if not m:
        raise ValueError(f"unreadable resistor value {value!r}")
    whole, unit, frac = m.groups()
    scale = {"": 1, "k": 1e3, "K": 1e3, "m": 1e6, "M": 1e6}[unit]
    return float(f"{whole}.{frac or 0}") * scale


def capacity_pf(r_ohm: float) -> float:
    return RISE_NS * 1e-9 / (0.8473 * r_ohm) * 1e12


hub = {c.ref: c for c in B.BOARDS["hub"]["comps"]}
values = {hub[ref].value for ref in ("R4", "R5")}
nets = {frozenset(hub[ref].pins.values()) for ref in ("R4", "R5")}
ok = len(values) == 1 and nets == {frozenset({"CHAIN_SDA", "3V3"}),
                                    frozenset({"CHAIN_SCL", "3V3"})}
print(f"  [{'ok' if ok else 'FAIL'}] R4/R5 pull CHAIN_SDA/SCL to 3V3 with one value")
if not ok:
    failures.append("R4/R5 wiring or values")
r = ohms(next(iter(values)))
cap = capacity_pf(r)
print(f"\nHub pull-up {r:g} ohm drives {cap:.0f} pF at 400 kHz")

for name, nodes, metres in REQUIRED:
    need = nodes * NODE_PF + metres * CABLE_PF_PER_M
    fits = need <= cap
    print(f"  [{'ok' if fits else 'FAIL'}] {name}: {nodes} nodes + {metres} m = {need:.0f} pF")
    if not fits:
        failures.append(name)

print("\nLongest cable per node count (for docs/BOARD-SPECS.md)")
print(f"  {'nodes':>5}  {'at ' + format(r, 'g') + ' ohm':>12}  {'at 1k':>8}")
for nodes in (1, 2, 4, 6, 8, 10, 15):
    def fit(res):
        metres = (capacity_pf(res) - nodes * NODE_PF) / CABLE_PF_PER_M
        return f"{metres:.1f} m" if metres > 0 else "none"
    print(f"  {nodes:>5}  {fit(r):>12}  {fit(1000):>8}")

if r < STRONGEST_OHM:
    failures.append(f"{r:g} ohm is below the {STRONGEST_OHM} ohm Fast-mode sink limit")
print(f"\n{len(failures)} failed" + "".join(f"\n  - {f}" for f in failures))
sys.exit(1 if failures else 0)
