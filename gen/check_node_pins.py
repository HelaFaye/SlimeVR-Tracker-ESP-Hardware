#!/usr/bin/env python3
"""
Check the node board's ATtiny412 wiring against the ports the node firmware uses.

    python3 gen/check_node_pins.py

Needs no KiCad. The pin-number -> port map comes from parts.ATTINY412.pin_functions,
which verify.py checks against KiCad's own symbol when a KiCad library is installed. The
port -> signal map below is what extras/attiny-cs-node/src/main.cpp in
SlimeVR-Tracker-ESP drives: change one, change both.

An earlier revision of gen/boards.py had six of the eight pins on the wrong pads (UPDI on
pin 2, the strobe on pin 6). It passed every other check, because nothing compared the
board's nets with the part's ports.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boards as B  # noqa: E402
import parts as P  # noqa: E402

# Port -> net, as the node firmware and the node schematic intend it.
FIRMWARE_PORTS = {
    "VCC": "VBUS",
    "PA6": "CS_STROBE",      # PinStrobe = PIN_PA6, CCL/event input
    "PA7": "CS_IMU",         # PinChipSelect = PIN_PA7, CCL output
    "PA1": "CHAIN_SDA",      # TWI0 default SDA on 8-pin tinyAVR
    "PA2": "CHAIN_SCL",      # TWI0 default SCL
    "~{RESET}/PA0": "UPDI",  # programming
    "PA3": "SENSOR_PWR_G",   # PinSensorPower = PIN_PA3
    "GND": "GND",
}

failures = []
node = B.BOARDS["node"]["comps"]
attiny = [c for c in node if c.part == "ATTINY412"]
if len(attiny) != 1:
    failures.append(f"expected one ATTINY412 on the node board, found {len(attiny)}")
else:
    u = attiny[0]
    functions = P.ATTINY412.pin_functions
    for num, port in sorted(functions.items(), key=lambda kv: int(kv[0])):
        want = FIRMWARE_PORTS[port]
        got = u.pins.get(num, "<unconnected>")
        ok = got == want
        print(f"  [{'ok' if ok else 'FAIL'}] {u.ref} pin {num} ({port}): {got}"
              + ("" if ok else f", should be {want}"))
        if not ok:
            failures.append(f"{u.ref} pin {num}")

print(f"\n{len(failures)} wrong")
sys.exit(1 if failures else 0)
