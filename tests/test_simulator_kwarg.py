from cocotb_test.simulator import run
import pytest
import os

tests_dir = os.path.dirname(__file__)

# The regression test system currently runs all tests with SIM=(something valid)
# It would be nice to include a test this with SIM unset in the automated regressions.


# Check that SIM= environment variable takes priority over kwarg
@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
@pytest.mark.xfail(os.getenv("SIM") is None,
                   reason="Bad simulator name should be used when SIM is unset",
                   strict=True,
                   raises=NotImplementedError)
def test_env_takes_priority():
    run(
        verilog_sources=[
            os.path.join(tests_dir, "dff.sv"),
        ],
        toplevel="dff_test",
        module="dff_cocotb",
        simulator="bad_sim_name"
    )
