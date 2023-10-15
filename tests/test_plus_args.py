import cocotb
from cocotb.triggers import Timer

import pytest
from cocotb_test.simulator import run
import os

hdl_dir = os.path.dirname(__file__)

@cocotb.test(skip=False)
def run_test(dut):

    yield Timer(1)

    user_mode = int(dut.user_mode)

    assert user_mode == 1, "user_mode mismatch detected : got %d, exp %d!" % (dut.user_mode, 1)


@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not suported")
def test_plus_args():
    run(
        verilog_sources=[os.path.join(hdl_dir, "plus_args.sv")],
        module="test_plus_args",
        toplevel="plus_args",
        plus_args=["+USER_MODE", "+TEST=ARB_TEST"],
    )


@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not suported")
@pytest.mark.xfail
def test_plus_args_fail():
    run(verilog_sources=[os.path.join(hdl_dir,"plus_args.sv")], toplevel="plus_args")


@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not suported")
@pytest.mark.xfail
def test_plus_args_test_wrong():
    run(
        verilog_sources=[os.path.join(hdl_dir, "plus_args.sv")], toplevel="plus_args", plus_args=["+XUSER_MODE"]
    )


if __name__ == "__main__":
    test_plus_args()
