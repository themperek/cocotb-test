from cocotb.regression import TestFactory
from cocotb_test.simulator import run
import pytest
import os

import cocotb
from cocotb.triggers import Timer, ReadOnly
from cocotb.result import TestFailure

tests_dir = os.path.dirname(__file__)

@pytest.mark.skipif(os.getenv("SIM") not in ("icarus", "questa"), reason="Multitop feature only supported for Icarus and Questa")
def test_dff_verilog():
    run(
        verilog_sources=[
            os.path.join(tests_dir, "glbl.v"),
            os.path.join(tests_dir, "glbl_sink.v"),
        ],
        toplevel=["glbl_sink", "glbl"],
        module="test_multitop"
    )


@cocotb.test()
async def glbl(dut):
    await ReadOnly()
    if dut.rst.value == 0:
        raise TestFailure()
    await Timer(10)
    await ReadOnly()
    if dut.rst.value == 1:
        raise TestFailure()


if __name__ == "__main__":
    test_dff_verilog()
