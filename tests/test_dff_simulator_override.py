from cocotb_test.simulator import run
import pytest
import os

tests_dir = os.path.dirname(__file__)

# This test only executes for GHDL. If `simulator` override does not work, it should fail.
@pytest.mark.skipif(os.getenv("SIM") != "ghdl", reason="This test is supposed to fail.")
def test_dff_verilog():
    run(
        verilog_sources=[os.path.join(tests_dir,"dff.v")],
        toplevel="dff_test",
        module="dff_cocotb",
        simulator="icarus"
    )


if __name__ == "__main__":
    test_dff_verilog()
    #test_dff_vhdl()