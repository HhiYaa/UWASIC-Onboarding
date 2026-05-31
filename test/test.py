# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import ClockCycles
from cocotb.types import Logic
from cocotb.types import LogicArray

async def await_half_sclk(dut):
    start_time = cocotb.utils.get_sim_time(units="ns")
    while True:
        await ClockCycles(dut.clk, 1)
        if (start_time + 100*100*0.5) < cocotb.utils.get_sim_time(units="ns"):
            break
    return

def ui_in_logicarray(ncs, bit, sclk):
    return LogicArray(f"00000{ncs}{bit}{sclk}")

async def send_spi_transaction(dut, r_w, address, data):
    if isinstance(data, LogicArray):
        data_int = int(data)
    else:
        data_int = data
    if address < 0 or address > 127:
        raise ValueError("Address must be 7-bit (0-127)")
    if data_int < 0 or data_int > 255:
        raise ValueError("Data must be 8-bit (0-255)")
    first_byte = (int(r_w) << 7) | address
    sclk = 0
    ncs = 0
    bit = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 1)
    for i in range(8):
        bit = (first_byte >> (7-i)) & 0x1
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    for i in range(8):
        bit = (data_int >> (7-i)) & 0x1
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    sclk = 0
    ncs = 1
    bit = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 600)
    return ui_in_logicarray(ncs, bit, sclk)

@cocotb.test()
async def test_spi(dut):
    dut._log.info("Start SPI test")
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    dut._log.info("Test project behavior")
    dut._log.info("Write transaction, address 0x00, data 0xF0")
    ui_in_val = await send_spi_transaction(dut, 1, 0x00, 0xF0)
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000)
    dut._log.info("Write transaction, address 0x01, data 0xCC")
    ui_in_val = await send_spi_transaction(dut, 1, 0x01, 0xCC)
    assert dut.uio_out.value == 0xCC, f"Expected 0xCC, got {dut.uio_out.value}"
    await ClockCycles(dut.clk, 100)
    dut._log.info("Write transaction, address 0x30 (invalid), data 0xAA")
    ui_in_val = await send_spi_transaction(dut, 1, 0x30, 0xAA)
    await ClockCycles(dut.clk, 100)
    dut._log.info("Read transaction (invalid), address 0x00, data 0xBE")
    ui_in_val = await send_spi_transaction(dut, 0, 0x30, 0xBE)
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 100)
    dut._log.info("Read transaction (invalid), address 0x41 (invalid), data 0xEF")
    ui_in_val = await send_spi_transaction(dut, 0, 0x41, 0xEF)
    await ClockCycles(dut.clk, 100)
    dut._log.info("Write transaction, address 0x02, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x02, 0xFF)
    await ClockCycles(dut.clk, 100)
    dut._log.info("Write transaction, address 0x04, data 0xCF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xCF)
    await ClockCycles(dut.clk, 30000)
    dut._log.info("Write transaction, address 0x04, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xFF)
    await ClockCycles(dut.clk, 30000)
    dut._log.info("Write transaction, address 0x04, data 0x00")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x00)
    await ClockCycles(dut.clk, 30000)
    dut._log.info("Write transaction, address 0x04, data 0x01")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x01)
    await ClockCycles(dut.clk, 30000)
    dut._log.info("SPI test completed successfully")


@cocotb.test()
async def test_pwm_freq(dut):
    dut._log.info("PWM Frequency test")
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())
    dut.ena.value = 1
    dut.ui_in.value = ui_in_logicarray(1, 0, 0)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    await send_spi_transaction(dut, 1, 0x00, 0xFF)
    await send_spi_transaction(dut, 1, 0x02, 0xFF)
    await send_spi_transaction(dut, 1, 0x04, 0x80)

    timeout = 10000
    count = 0
    while (int(dut.uo_out.value) & 0x1) == 1:
        await ClockCycles(dut.clk, 1)
        count += 1
        assert count < timeout, "Timeout waiting for signal to go LOW"
    count = 0
    while (int(dut.uo_out.value) & 0x1) == 0:
        await ClockCycles(dut.clk, 1)
        count += 1
        assert count < timeout, "Timeout waiting for first rising edge"
    t1 = cocotb.utils.get_sim_time(units="ns")

    await ClockCycles(dut.clk, 1)
    count = 0
    while (int(dut.uo_out.value) & 0x1) == 1:
        await ClockCycles(dut.clk, 1)
        count += 1
        assert count < timeout, "Timeout waiting for signal to go LOW again"
    count = 0
    while (int(dut.uo_out.value) & 0x1) == 0:
        await ClockCycles(dut.clk, 1)
        count += 1
        assert count < timeout, "Timeout waiting for second rising edge"
    t2 = cocotb.utils.get_sim_time(units="ns")

    period_ns = t2 - t1
    frequency = 1e9 / period_ns
    dut._log.info(f"Period: {period_ns} ns, Frequency: {frequency:.2f} Hz")
    assert 2970 <= frequency <= 3030, f"Frequency {frequency:.2f} Hz out of range!"
    dut._log.info("PWM Frequency test completed successfully")


@cocotb.test()
async def test_pwm_duty(dut):
    dut._log.info("PWM Duty Cycle test")
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())
    dut.ena.value = 1
    dut.ui_in.value = ui_in_logicarray(1, 0, 0)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    await send_spi_transaction(dut, 1, 0x00, 0xFF)
    await send_spi_transaction(dut, 1, 0x02, 0xFF)

    # Test 0% duty cycle
    await send_spi_transaction(dut, 1, 0x04, 0x00)
    await ClockCycles(dut.clk, 500)
    assert (int(dut.uo_out.value) & 0x1) == 0, "0% duty cycle should be always LOW"
    dut._log.info("0% duty cycle passed!")

    # Test 100% duty cycle
    await send_spi_transaction(dut, 1, 0x04, 0xFF)
    await ClockCycles(dut.clk, 500)
    assert (int(dut.uo_out.value) & 0x1) == 1, "100% duty cycle should be always HIGH"
    dut._log.info("100% duty cycle passed!")

    # Test 50% duty cycle
    await send_spi_transaction(dut, 1, 0x04, 0x80)
    timeout = 10000
    count = 0
    while (int(dut.uo_out.value) & 0x1) == 1:
        await ClockCycles(dut.clk, 1)
        count += 1
        assert count < timeout, "Timeout waiting for LOW before rising edge"
    count = 0
    while (int(dut.uo_out.value) & 0x1) == 0:
        await ClockCycles(dut.clk, 1)
        count += 1
        assert count < timeout, "Timeout waiting for rising edge"
    t_rising = cocotb.utils.get_sim_time(units="ns")

    count = 0
    while (int(dut.uo_out.value) & 0x1) == 1:
        await ClockCycles(dut.clk, 1)
        count += 1
        assert count < timeout, "Timeout waiting for falling edge"
    t_falling = cocotb.utils.get_sim_time(units="ns")

    count = 0
    while (int(dut.uo_out.value) & 0x1) == 0:
        await ClockCycles(dut.clk, 1)
        count += 1
        assert count < timeout, "Timeout waiting for second rising edge"
    t_rising2 = cocotb.utils.get_sim_time(units="ns")

    high_time = t_falling - t_rising
    period = t_rising2 - t_rising
    duty = (high_time / period) * 100
    dut._log.info(f"50% test — Duty cycle measured: {duty:.2f}%")
    assert 49 <= duty <= 51, f"Duty cycle {duty:.2f}% out of range!"
    dut._log.info("50% duty cycle passed!")
    dut._log.info("PWM Duty Cycle test completed successfully")