![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# 30-Second Basketball Shot Clock — Tiny Tapeout

A single-tile Tiny Tapeout (sky130) design that implements a 30-second
basketball shot clock with reset, pause, and a buzzer output. The current
count can be displayed either as a 5-bit value on LEDs or as two 7-segment
digits, selectable with a mode pin.

**Author:** Zach Nielsen
**Course:** ECE429, Spring 2026 — Valparaiso University
**Top module:** `tt_um_znielsen123`

- [Datasheet (`docs/info.md`)](docs/info.md)

## Files

| Path | What it is |
|---|---|
| `src/project.v` | Verilog RTL (clock divider + countdown + 7-seg decode). |
| `info.yaml` | Tiny Tapeout project metadata and pinout. |
| `test/tb.v` | Verilog testbench wrapper, with `TICK_DIV` overridden for fast sim. |
| `test/test.py` | cocotb tests: full countdown, reset button, pause, 7-seg decode. |
| `docs/info.md` | Datasheet content (How it works, How to test, pinout). |

## Pinout

| Pin | Function |
|---|---|
| `ui[0]` | RESET button (reload count to 30) |
| `ui[1]` | PAUSE (hold high to freeze the count) |
| `ui[2]` | MODE (0 = binary LEDs, 1 = 7-segment) |
| `uo[7]` | BUZZER (high when count == 0) |
| `uo[4:0]` (mode 0) | 5-bit binary count |
| `uo[6:0]` (mode 1) | Ones-digit 7-segment (a..g) |
| `uio[6:0]` (mode 1) | Tens-digit 7-segment (a..g) |

## Running the tests locally

Requires `iverilog` and `cocotb`:

```sh
cd test
make
```

Otherwise, push to the repo and GitHub Actions will run the tests
automatically (~30 seconds).

## Acknowledgements

Project workflow adapted from a guide put together by classmate
**Fayol Ateufack** based on his ECE429 LFSR project.
