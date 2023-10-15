from cocotb_test.simulator import run
import pytest
import os

import cocotb
from cocotb.triggers import Timer

tests_dir = os.path.dirname(__file__)


@cocotb.test()
def run_test_paramters(dut):

    yield Timer(1)

    WIDTH_IN = int(os.environ.get("WIDTH_IN", "8"))
    WIDTH_OUT = int(os.environ.get("WIDTH_OUT", "8"))

    assert WIDTH_IN == len(dut.data_in)
    assert WIDTH_OUT == len(dut.data_out)


@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not suported")
@pytest.mark.parametrize(
    "parameters", [{"WIDTH_IN": "8", "WIDTH_OUT": "16"}, {"WIDTH_IN": "16"}]
)
def test_dff_verilog_testcase(parameters):
    run(
        verilog_sources=[os.path.join(tests_dir, "test_parameters.v")],
        toplevel="test_parameters",
        module="test_parameters",
        parameters=parameters,
        includes=[os.path.join(tests_dir, "includes")],
        defines= ["DEFINE=1"],
        extra_env=parameters,
        sim_build="sim_build/"
        + "_".join(("{}={}".format(*i) for i in parameters.items())),
    )


@pytest.mark.skipif(os.getenv("SIM") == "verilator", reason="VHDL not suported")
@pytest.mark.skipif(os.getenv("SIM") == "icarus", reason="VHDL not suported")
@pytest.mark.parametrize(
    "parameters", [{"WIDTH_IN": "8", "WIDTH_OUT": "16"}, {"WIDTH_IN": "16"}]
)
def test_dff_vhdl_testcase(parameters):
    run(
        toplevel_lang="vhdl",
        vhdl_sources=[os.path.join(tests_dir, "test_parameters.vhdl")],
        toplevel="test_parameters",
        module="test_parameters",
        parameters=parameters,
        extra_env=parameters,
        sim_build="sim_build/"
        + "_".join(("{}={}".format(*i) for i in parameters.items())),
    )

@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not suported")
def test_bad_timescales():

    kwargs = {
         'verilog_sources': [
                os.path.join(tests_dir, "dff.sv"),
            ],
        'module': "dff_cocotb",
        'toplevel': "dff_test",
        'sim_build': "sim_build/test_missing_verilog",
    }

    with pytest.raises(ValueError, match='Invalid timescale: 1ns'):
        run(timescale="1ns", **kwargs)

    with pytest.raises(ValueError, match='Invalid timescale: 1qs/1s'):
        run(timescale="1qs/1s", **kwargs)

    run(timescale="100ns/100ns", **kwargs)
    run(timescale="1ns/1ns", **kwargs)
    run(timescale=None, **kwargs)

