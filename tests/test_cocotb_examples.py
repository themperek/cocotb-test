import os
import cocotb
import pytest

from cocotb_test.simulator import run

example_dir = os.path.join(os.path.dirname(os.path.dirname(cocotb.__file__)), "examples")

if os.path.isdir(example_dir) == False:
    raise IOError("Cocotb example directory not found. Please clone with git and install with `pip -e`")


@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
def test_ping_tun_tap():
    if not (os.name == "posix" and os.geteuid() == 0):
        pytest.skip("This test works only on a POSIX OS with admin rights")

    run(
        verilog_sources=[os.path.join(example_dir, "ping_tun_tap", "hdl", "icmp_reply.sv")],
        toplevel="icmp_reply",
        python_search=[os.path.join(example_dir, "ping_tun_tap", "tests")],
        module="test_icmp_reply",
    )


@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
def test_dff_verilog():
    run(
        verilog_sources=[os.path.join(example_dir, "dff", "hdl", "dff.v")],
        toplevel="dff",
        python_search=[os.path.join(example_dir, "dff", "tests")],
        module="dff_cocotb",
        force_compile=True,
    )


@pytest.mark.skipif(os.getenv("SIM") == "icarus", reason="VHDL not suported")
def test_dff_vhdl():
    run(
        vhdl_sources=[os.path.join(example_dir, "dff", "hdl", "dff.vhdl")],
        toplevel="dff",
        python_search=[os.path.join(example_dir, "dff", "tests")],
        module="dff_cocotb",
        toplevel_lang="vhdl",
        force_compile=True,
    )


@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
def test_adder_verilog():
    run(
        verilog_sources=[os.path.join(example_dir, "adder", "hdl", "adder.sv")],
        toplevel="adder",
        python_search=[os.path.join(example_dir, "adder", "tests"), os.path.join(example_dir, "adder", "model")],
        module="test_adder",
        force_compile=True,
    )


@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Errors in compilation cocotb example")
@pytest.mark.skipif(os.getenv("SIM") == "icarus", reason="VHDL not suported")
def test_adder_vhdl():
    run(
        vhdl_sources=[os.path.join(example_dir, "adder", "hdl", "adder.vhdl")],
        toplevel="adder",
        python_search=[os.path.join(example_dir, "adder", "tests"), os.path.join(example_dir, "adder", "model")],
        module="test_adder",
        toplevel_lang="vhdl",
        force_compile=True,
    )


@pytest.mark.skipif(os.getenv("SIM") == "questa", reason="Errors in cocotb")
@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
@pytest.mark.skipif(os.getenv("SIM") == "icarus", reason="VHDL not suported")
def test_mean():
    run(
        vhdl_sources=[os.path.join(example_dir, "mean", "hdl", "mean_pkg.vhd"), os.path.join(example_dir, "mean", "hdl", "mean.vhd")],
        verilog_sources=[os.path.join(example_dir, "mean", "hdl", "mean_sv.sv")],
        toplevel="mean_sv",
        python_search=[os.path.join(example_dir, "mean", "tests")],
        module="test_mean",
        force_compile=True,
    )


@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
@pytest.mark.skipif(os.getenv("SIM") == "icarus", reason="VHDL not suported")
def test_mixed_top_verilog():
    run(
        vhdl_sources=[os.path.join(example_dir, "endian_swapper", "hdl", "endian_swapper.vhdl")],
        verilog_sources=[
            os.path.join(example_dir, "endian_swapper", "hdl", "endian_swapper.sv"),
            os.path.join(example_dir, "mixed_language", "hdl", "toplevel.sv"),
        ],
        toplevel="endian_swapper_mixed",
        python_search=[os.path.join(example_dir, "mixed_language", "tests")],
        module="test_mixed_language",
        force_compile=True,
    )


@pytest.mark.skipif(os.getenv("SIM") == "questa", reason="Errors in cocotb")
@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
@pytest.mark.skipif(os.getenv("SIM") == "icarus", reason="VHDL not suported")
def test_mixed_top_vhdl():
    run(
        vhdl_sources=[
            os.path.join(example_dir, "endian_swapper", "hdl", "endian_swapper.vhdl"),
            os.path.join(example_dir, "mixed_language", "hdl", "toplevel.vhdl"),
        ],
        verilog_sources=[os.path.join(example_dir, "endian_swapper", "hdl", "endian_swapper.sv")],
        toplevel="endian_swapper_mixed",
        python_search=[os.path.join(example_dir, "mixed_language", "tests")],
        module="test_mixed_language",
        toplevel_lang="vhdl",
        force_compile=True,
    )


@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
def test_axi_lite_slave():
    run(
        verilog_sources=[
            os.path.join(example_dir, "axi_lite_slave", "hdl", "axi_lite_slave.v"),
            os.path.join(example_dir, "axi_lite_slave", "hdl", "axi_lite_demo.v"),
            os.path.join(example_dir, "axi_lite_slave", "hdl", "tb_axi_lite_slave.v"),
        ],
        toplevel="tb_axi_lite_slave",
        includes=[os.path.join(example_dir, "axi_lite_slave", "hdl")],
        python_search=[os.path.join(example_dir, "axi_lite_slave", "tests")],
        module="test_axi_lite_slave",
    )


@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
def test_endian_swapper_verilog():
    run(
        verilog_sources=[os.path.join(example_dir, "endian_swapper", "hdl", "endian_swapper.sv")],
        toplevel="endian_swapper_sv",
        python_search=[os.path.join(example_dir, "endian_swapper", "tests")],
        module="test_endian_swapper",
    )


@pytest.mark.skipif(os.getenv("SIM") == "icarus", reason="VHDL not suported")
def test_endian_swapper_vhdl():
    run(
        vhdl_sources=[os.path.join(example_dir, "endian_swapper", "hdl", "endian_swapper.vhdl")],
        toplevel="endian_swapper_vhdl",
        python_search=[os.path.join(example_dir, "endian_swapper", "tests")],
        module="test_endian_swapper",
        toplevel_lang="vhdl",
    )



