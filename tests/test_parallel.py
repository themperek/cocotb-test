from cocotb_test.simulator import run
import pytest
import os

tests_dir = os.path.dirname(__file__)

# For parallel runs
# Pre-compile:
# pytest -m compile test_parallel.py
# Run:
# pytest -m 'not compile' -n 2 test_parallel.py
# There are possibly better ways to do this

@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not suported")
@pytest.mark.compile
def test_complile():
    run(
        verilog_sources=[os.path.join(tests_dir, "dff.sv")],
        toplevel="dff_test",
        module="dff_cocotb",
        compile_only=True,
    )


@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not suported")
@pytest.mark.parametrize("seed", range(6))
def test_dff_verilog_param(seed):
    run(
        verilog_sources=[os.path.join(tests_dir, "dff.sv")],
        toplevel="dff_test",
        module="dff_cocotb",
        seed=seed,
    )


@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not suported")
@pytest.mark.parametrize("seed", range(2))
def test_dff_verilog_testcase(seed):
    run(
        verilog_sources=[os.path.join(tests_dir, "dff.sv")],
        toplevel="dff_test",
        module="dff_cocotb",
        seed=seed
    )


# For GHDL create new build/direcotry for every run
@pytest.mark.skipif(os.getenv("SIM") == "verilator", reason="VHDL not suported")
@pytest.mark.skipif(os.getenv("SIM") == "icarus", reason="VHDL not suported")
@pytest.mark.parametrize("seed", range(8))
def test_dff_vhdl_param(seed):
    run(
        vhdl_sources=[os.path.join(tests_dir, "dff.vhdl")],
        toplevel="dff_test_vhdl",
        module="dff_cocotb",
        toplevel_lang="vhdl",
        seed=seed,
        sim_build="sim_build/" + str(seed)
    )
