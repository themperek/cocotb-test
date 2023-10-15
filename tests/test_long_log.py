import cocotb
from cocotb.triggers import Timer

import pytest
from cocotb_test.simulator import run
import os

hdl_dir = os.path.dirname(__file__)


@cocotb.test()
def run_test_long_log(dut):

    yield Timer(1)

    dut._log.info("BEFORE")
    dut._log.info("LONGLOG" * 100000)
    dut._log.info("AFTER")


@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="VHDL not suported")
def test_long_log():
    run(verilog_sources=[os.path.join(hdl_dir, "dff.sv")], module="test_long_log", toplevel="dff_test")
