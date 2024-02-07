#!/usr/bin/env python3
from cocotb_test.simulator import run
from cocotb_test.testbench import Testbench
import pytest
import os
import subprocess

import cocotb
from cocotb.triggers import Timer

tests_dir = os.path.dirname(__file__)


@cocotb.test()
def run_test_paramters(dut):

    yield Timer(1)

    WIDTH_IN = int(os.environ.get("WIDTH_IN", "8"))
    WIDTH_OUT = int(os.environ.get("WIDTH_OUT", WIDTH_IN))

    assert WIDTH_IN == len(dut.data_in)
    assert WIDTH_OUT == len(dut.data_out)


tb = Testbench()

dut = "test_parameters"
tb.toplevel = dut
tb.module = os.path.splitext(os.path.basename(__file__))[0]

tb.verilog_sources = [
    os.path.join(tests_dir, dut+".v"),
]

tb.add_template_parameter('WIDTH_IN', 8)
tb.add_template_parameter('WIDTH_OUT', 'WIDTH_IN')

tb.python_search = [tests_dir]
tb.includes = [os.path.join(tests_dir, "includes")]
tb.defines = ["DEFINE=1"]

tb.force_compile = True

if __name__ == '__main__':
    tb.main()


@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not supported")
@pytest.mark.parametrize(
    "parameters", [{"WIDTH_IN": "8", "WIDTH_OUT": "16"}, {"WIDTH_IN": "16"}]
)
def test_testbench_pytest(request, parameters):
    tb.sim_build = os.path.join(tests_dir, "sim_build",
        request.node.name.replace('[', '-').replace(']', ''))
    tb.extra_env = parameters
    tb.run(parameters=parameters)


@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not supported")
@pytest.mark.parametrize(
    "parameters", [{"WIDTH_IN": "8", "WIDTH_OUT": "16"}, {"WIDTH_IN": "16"}]
)
def test_testbench_cli(request, parameters):
    env = {}
    for name, val in os.environ.items():
        env[name] = val
    args = [__file__]
    for name, val in parameters.items():
        args.append(f"--param_{name.lower()}={val}")
        env[name] = val
    c = subprocess.run(args, env=env)
    assert c.returncode == 0


@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
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

@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
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

