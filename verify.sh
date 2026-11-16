#!/usr/bin/env bash
# Every automated hardware check, in one place. The firmware-side checks (chain
# simulation, I2C address map, node firmware builds) live in the firmware repo's VERIFY.sh.
#
#   ./verify.sh
#
# Override KICAD_SYMBOL_DIR / KICAD_FOOTPRINT_DIR to point at a non-standard KiCad install.
set -uo pipefail
cd "$(dirname "$0")"

fail=0
run() {
  local title=$1; shift
  echo; echo "=== $title ==="
  "$@" || fail=1
}

run "Build totals (BOM placements, panel)" python3 gen/check_build_totals.py
run "Node ATtiny412 pins vs node firmware ports" python3 gen/check_node_pins.py
run "Chain I2C pull-ups vs chain capacitance" python3 gen/check_chain_pullups.py

# Both of these resolve stock KiCad symbols by pin function. Without an installed
# symbol library every part is unresolvable, so they would report the environment,
# not defects.
if python3 gen/verify.py --have-libs; then
  run "KiCad symbols and footprints" bash -c 'cd gen && python3 verify.py'
  run "Symbol pin-order guard" python3 gen/test_pin_order.py
else
  echo; echo "SKIPPED: KiCad symbol checks -- no KiCad symbol library" \
    "(Arch: kicad kicad-library, Debian: kicad-symbols kicad-footprints)"
fi

echo
[ $fail -eq 0 ] && echo "ALL CHECKS PASSED" || echo "FAILURES ABOVE"
exit $fail
