from cocotb_test.simulator import run
import pytest
import os

tests_dir = os.path.dirname(__file__)

@pytest.mark.skipif(os.getenv("SIM") not in ("questa", "ghdl", "nvc"), reason="Named libraries only supported for Questa, GHDL, and NVC.")
def test_dff_vhdl():
    run(
        vhdl_sources = {
            "some_lib": [os.path.join(tests_dir, "dff.vhdl")],
            "some_other_lib": [os.path.join(tests_dir, "dff_wrapper.vhdl")],
        },
        toplevel="some_other_lib.dff_wrapper",
        module="dff_cocotb",
        toplevel_lang="vhdl",
    )


if __name__ == "__main__":
    test_dff_vhdl()
