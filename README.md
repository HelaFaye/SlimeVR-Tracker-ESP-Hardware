# SlimeVR-Tracker-ESP-Hardware

Hardware for I2SPI, which carries several SlimeVR IMUs on one RJ45 cable: an ESP32-C5 hub
board and ATtiny412 sensor-node boards.

| Repo | What lives there |
|---|---|
| **this repo** | Board definitions, KiCad generator, vendored symbol libraries, BOM, panel |
| [SlimeVR-Tracker-ESP](https://github.com/HelaFaye/SlimeVR-Tracker-ESP) | Tracker firmware, the I2SPI protocol (`docs/I2SPI.md`, `ATTinyCSProtocol.h`), the ATtiny node firmware (`extras/attiny-cs-node`), cable pinout (`docs/dev/HARDWARE-RJ45-SPI-BUS.md`), chain simulation |
| [SlimeVR-Server](https://github.com/HelaFaye/SlimeVR-Server) | Server fork; synthetic tracker for end-to-end testing |

The wire protocol and cable pinout are defined in the firmware repo, in the I2SPI
specification: [`docs/I2SPI.md`](https://github.com/HelaFaye/SlimeVR-Tracker-ESP/blob/feat/esp32c5-rj45-spi-attiny-cs/docs/I2SPI.md).
It is the standard for any board that joins a chain. §4 covers node hardware, §15 is a
design checklist for new host and node boards. When changing a net here that crosses the
RJ45, change it there too.

Board specifications: [`docs/BOARD-SPECS.md`](docs/BOARD-SPECS.md).
Checks: `./verify.sh`.

## Generator

Generates KiCad projects, a JLCPCB BOM and a V-scored panel configuration for the two
I2SPI boards.

```sh
python3 gen/verify.py                    # check every symbol and footprint
python3 gen/mklib.py --allow-unverified  # build the project symbol library
python3 gen/wizard.py --preset 18point   # pick boards, emit everything
```

## What it generates

| Output | Status |
|---|---|
| `lib/slimevr-i2spi.kicad_sym` + `.pretty` | Symbols and footprints KiCad 7 doesn't ship |
| `out/<board>/*.kicad_sch` + `.kicad_pro` | Schematics, verified to parse |
| `out/bom-jlcpcb.csv` | Aggregated across all selected boards, with LCSC numbers |
| `out/panel.json` | KiKit config for a V-scored panel |

## What it does not generate, and why

**PCB layout.** Not placement, not routing, not copper pours. This is the honest limit of
the approach: auto-routing a two-layer board with a 4 MHz SPI bus, a switched supply rail
and an RF module to manufacturable quality is not something a script does well, and a
generator that emitted a plausible-looking layout would be worse than one that emits
nothing — you would trust it.

So the flow is: generate schematics → open in KiCad → ERC → lay out by hand → then
`kikit panelize --preset :out/panel.json` across the finished boards.

**Wires.** Connections are global labels, not drawn nets. Same reason in miniature:
labelling every pin is mechanical and correct, auto-placing readable wires is not.
Anything sharing a label is one net, and ERC and netlist export both understand that.

## Where each pinout comes from

KiCad 7 ships no symbol for the ESP32-C5, the ICM-45686 or the QMC6309.

| Part | Symbol source | Checked against |
|---|---|---|
| ESP32-C5-WROOM-1 | `lib/vendor/Espressif` (Espressif's own library) | The vendor symbol itself; hub pin map cross-checked pin by pin |
| QMC6309 | `lib/vendor/Mumo` | Datasheet: a 4-pad WLCSP, `A1` VSS, `A2` SCL, `B1` VDD, `B2` SDA |
| ICM-45686 | Generated from `gen/pinouts.py` | TDK DS-000577 Rev 1.0; `verified=True` |
| ATtiny412 | KiCad stock (`ATtiny412-SS`, extends `ATtiny202-SS`) | `pin_functions` in `gen/parts.py`, checked by `verify.py` and `gen/check_node_pins.py` |

The placeholder ESP32-C5 and QMC6309 entries in `pinouts.py` are still `verified=False`
and unused; `mklib.py` refuses to emit unverified parts without `--allow-unverified`.

Footprints carry the same risk with worse consequences: a wrong land pattern is a board
you cannot assemble. `verify.py` checks that each footprint exists, that it has a pad for
every pin on its symbol (catching a symbol drawn for a different package), and that every
pin a board wires exists on the symbol. It cannot check pad geometry: compare land
patterns against the datasheets before ordering.

Generating schematics needs KiCad's symbol library (or `KICAD_SYMBOL_DIR`), because the
MOSFET lists several candidate symbols and only the library says which has the right pin
order. Without it, `mksch.py` stops rather than guess.

## Panel notes

V-scoring needs straight cuts running the full width and height of the panel, so boards go
in a **uniform grid** rather than being nested tightly. That wastes some area and buys a
panel you can snap by hand. Cell size is the largest board in the selection plus clearance,
so mixing a 45 mm hub with a 26 mm node makes every cell 45 mm.

If the grid has empty cells, they are free boards — fill them with spares rather than
paying for panel area that comes back blank.

## Licence

Original work here is dual-licensed MIT / Apache-2.0, matching the firmware it was split
from. The libraries under `lib/vendor/` are third-party: Espressif's is CC-BY-SA 4.0 (with
the KiCad-style design exception), and the Mumo library's licence is **not yet known**.
See `lib/vendor/PROVENANCE.md`.

## Design provenance

Net names, terminator values, pull-up placement and the power-gating topology all come
from `docs/BOARD-SPECS.md` and the decision records. Two that are easy to undo by
accident when editing the layout:

- **`CS_LOCAL` never leaves the hub board.** If it reached the connector, every extension
  IMU would see it and the one-hot property would be broken by construction.
- **Chain I2C pull-ups exist only on the hub.** Nodes must not populate their own; several
  in parallel drop below what the parts can pull low.
