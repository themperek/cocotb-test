from cocotb_test.simulator import run
import pytest
import os

tests_dir = os.path.dirname(__file__)


@pytest.mark.skipif(os.getenv("SIM") != "questa", reason="-2008 only supported by Questa.")
def test_dff_vhdl():
    run(
        vhdl_sources=[os.path.join(tests_dir, "dff.vhdl")],
        toplevel="dff_test_vhdl",
        module="dff_cocotb",
        toplevel_lang="vhdl",
        vhdl_compile_args=["-2008"],
        force_compile=True,
    )