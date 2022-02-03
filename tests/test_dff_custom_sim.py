
from cocotb_test.simulator import Icarus, Ius, run
import pytest
import os
import cocotb

hdl_dir = os.path.dirname(__file__)

class IcarusCustom(Icarus):
    def __init__(self, logfile, *argv, **kwargs):
        self.logfile = logfile
        super().__init__(*argv, **kwargs)

    def run_command(self):
        return (
            ["vvp", "-v", "-l", self.logfile, "-M", self.lib_dir, "-m", cocotb.config.lib_name("vpi", "icarus")]
            + self.simulation_args
            + [self.sim_file]
            + self.plus_args
        )
    
@pytest.fixture(scope="module", autouse=True)
def module_run_at_beginning(request):
    print("\n\nIn module_run_at_beginning()\n\n")

    def module_run_at_end():
        print("\n\nIn module_run_at_end()\n\n")

    request.addfinalizer(module_run_at_end)


@pytest.mark.skipif(os.getenv("SIM") != "icarus", reason="Custom for Icarus")
def test_dff_custom_icarus():
    IcarusCustom(
        verilog_sources=[os.path.join(hdl_dir, "dff.sv")],
        toplevel="dff_test",
        python_search=[hdl_dir],
        module="dff_cocotb",
        logfile="custom_log.log",  # extra custom argument
    ).run()


class IusCustom(Ius):
    def __init__(self, defsfile, *argv, **kwargs):
        self.defsfile = defsfile
        super().__init__(*argv, **kwargs)

    def build_command(self):
        cmd = [
            "xrun",
            "-loadvpi",
            os.path.join(self.lib_dir, "libvpi." + self.lib_ext) + ":vlog_startup_routines_bootstrap",
            "-plinowarn",
            "-access",
            "+rwc",
            "-f",
            self.defsfile,
        ]

        return [cmd]


@pytest.mark.skipif(os.getenv("SIM") != "ius", reason="Custom for IUS")
def test_dff_custom_ius():
    IusCustom(
        verilog_sources=[os.path.join(hdl_dir, "dff.sv")],
        toplevel="dff_test",
        python_search=[hdl_dir],
        module="dff_cocotb",
        defsfile="ius_defines.f"
    )
