# SPDX-FileCopyrightText: © 2026 Zach Nielsen
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

# Must match the override in tb.v.
TICK_DIV = 4

SEG7 = {
    0: 0b0111111,
    1: 0b0000110,
    2: 0b1011011,
    3: 0b1001111,
    4: 0b1100110,
    5: 0b1101101,
    6: 0b1111101,
    7: 0b0000111,
    8: 0b1111111,
    9: 0b1101111,
}
SEG7_INV = {v: k for k, v in SEG7.items()}


async def start_clock(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="us").start())


async def reset(dut, mode=0):
    dut.ena.value = 1
    dut.uio_in.value = 0
    dut.ui_in.value = (mode & 1) << 2
    dut.rst_n.value = 0
    for _ in range(5):
        await FallingEdge(dut.clk)
    dut.rst_n.value = 1


def read_count(dut, mode):
    uo = int(dut.uo_out.value)
    if mode == 0:
        return uo & 0x1F
    ones = SEG7_INV.get(uo & 0x7F)
    tens = SEG7_INV.get(int(dut.uio_out.value) & 0x7F)
    assert ones is not None and tens is not None, (
        f"Bad 7-seg encoding: uo={uo:08b}, uio={int(dut.uio_out.value):08b}"
    )
    return tens * 10 + ones


def buzzer(dut):
    return (int(dut.uo_out.value) >> 7) & 1


@cocotb.test()
async def test_full_countdown(dut):
    """Mode 0: count 30 → 0 over 30 ticks; buzzer goes high at 0 and stays high."""
    await start_clock(dut)
    await reset(dut, mode=0)

    await FallingEdge(dut.clk)
    assert read_count(dut, 0) == 30, f"Initial count should be 30, got {read_count(dut, 0)}"
    assert buzzer(dut) == 0

    expected = 30
    while expected > 0:
        for _ in range(TICK_DIV):
            await FallingEdge(dut.clk)
        expected -= 1
        actual = read_count(dut, 0)
        assert actual == expected, f"At tick {30 - expected}, expected {expected}, got {actual}"

    assert buzzer(dut) == 1, "Buzzer must be high at count 0"

    # Count stays at 0 (doesn't underflow) and buzzer stays on.
    for _ in range(3 * TICK_DIV):
        await FallingEdge(dut.clk)
    assert read_count(dut, 0) == 0
    assert buzzer(dut) == 1


@cocotb.test()
async def test_reset_button(dut):
    """Pressing ui_in[0] mid-countdown reloads to 30."""
    await start_clock(dut)
    await reset(dut, mode=0)

    # Let it run for several ticks so the count is below 30.
    for _ in range(5 * TICK_DIV):
        await FallingEdge(dut.clk)
    assert read_count(dut, 0) < 30

    # Press the reset button.
    dut.ui_in.value = 0b001  # reset_btn=1, pause=0, mode=0
    await FallingEdge(dut.clk)
    assert read_count(dut, 0) == 30, "Reset button should reload count to 30"
    assert buzzer(dut) == 0

    # Release the button — should start counting down again.
    dut.ui_in.value = 0
    for _ in range(2 * TICK_DIV):
        await FallingEdge(dut.clk)
    assert read_count(dut, 0) < 30


@cocotb.test()
async def test_pause_holds_value(dut):
    """ui_in[1] held high freezes the count."""
    await start_clock(dut)
    await reset(dut, mode=0)

    for _ in range(3 * TICK_DIV):
        await FallingEdge(dut.clk)
    pre_pause = read_count(dut, 0)
    assert pre_pause < 30, "Count should have advanced before pause"

    # Assert pause and verify the count doesn't change for a long time.
    dut.ui_in.value = 0b010  # pause=1
    for _ in range(10 * TICK_DIV):
        await FallingEdge(dut.clk)
        assert read_count(dut, 0) == pre_pause, "Count must not advance while paused"

    # Release pause and confirm counting resumes.
    dut.ui_in.value = 0
    for _ in range(2 * TICK_DIV):
        await FallingEdge(dut.clk)
    assert read_count(dut, 0) < pre_pause, "Count should advance after un-pause"


@cocotb.test()
async def test_seven_segment_mode(dut):
    """Mode 1: outputs decode as expected 7-segment digits."""
    await start_clock(dut)
    await reset(dut, mode=1)

    await FallingEdge(dut.clk)
    assert read_count(dut, 1) == 30, "Initial 7-seg readout should be 30"

    # Run a handful of ticks and verify the decoded digits track the count.
    for tick_idx in range(1, 6):
        for _ in range(TICK_DIV):
            await FallingEdge(dut.clk)
        expected = 30 - tick_idx
        actual = read_count(dut, 1)
        assert actual == expected, f"At tick {tick_idx}, 7-seg decoded {actual}, expected {expected}"
