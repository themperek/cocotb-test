# Test if compile errors are caught

from cocotb_test.simulator import run
import pytest
import os

tests_dir = os.path.dirname(__file__)


@pytest.mark.skipif(os.getenv("SIM") == "verilator", reason="VHDL not suported")
@pytest.mark.skipif(os.getenv("SIM") == "icarus", reason="VHDL not suported")
@pytest.mark.xfail(strict=True, raises=SystemExit)
def test_invalid_vhdl():
    run(
        vhdl_sources=[
            os.path.join(tests_dir, "dff.vhdl"),
            os.path.join(tests_dir, "invalid.vhdl"),
        ],
        toplevel="dff_test_vhdl",
        module="dff_cocotb",
        toplevel_lang="vhdl"
    )

@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
@pytest.mark.xfail(strict=True, raises=SystemExit)
def test_invalid_verilog():
    run(
        verilog_sources=[
            os.path.join(tests_dir, "dff.v"),
            os.path.join(tests_dir, "invalid.v"),
        ],
        toplevel="dff_test",
        module="dff_cocotb"
    )

@pytest.mark.skipif(os.getenv("SIM") == "verilator", reason="VHDL not suported")
@pytest.mark.skipif(os.getenv("SIM") == "icarus", reason="VHDL not suported")
@pytest.mark.xfail(strict=True)
def test_missing_vhdl():
    run(
        vhdl_sources=[
            os.path.join(tests_dir, "dff.vhdl"),
            os.path.join(tests_dir, "missing_file.vhdl"),
        ],
        toplevel="dff_test_vhdl",
        module="dff_cocotb",
        toplevel_lang="vhdl"
    )

@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
@pytest.mark.xfail(strict=True)
def test_missing_verilog():
    run(
        verilog_sources=[
            os.path.join(tests_dir, "dff.v"),
            os.path.join(tests_dir, "missing_file.v"),
        ],
        toplevel="dff_test",
        module="dff_cocotb"
    )
