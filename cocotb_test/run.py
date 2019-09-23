import os
import inspect
import shutil

import cocotb_test.simulator

from xml.etree import cElementTree as ET


def run(simulator=None, **kwargs):

    sim_env = os.getenv("SIM", "icarus")

    supported_sim = ["icarus", "questa", "ius", "vcs", "ghdl", "aldec"]
    if (sim_env in supported_sim) or simulator:
        pass
    else:
        raise NotImplementedError("Set SIM/sim variable. Supported: " + ", ".join(supported_sim))

    run_filename = inspect.getframeinfo(inspect.currentframe().f_back)[0]
    kwargs["run_filename"] = run_filename
    kwargs["sim_name"] = sim_env

    if simulator:
        sim = simulator(**kwargs)
    elif sim_env == "icarus":
        sim = cocotb_test.simulator.Icarus(**kwargs)
    elif sim_env == "questa":
        sim = cocotb_test.simulator.Questa(**kwargs)
    elif sim_env == "ius":
        sim = cocotb_test.simulator.Ius(**kwargs)
    elif sim_env == "vcs":
        sim = cocotb_test.simulator.Vcs(**kwargs)
    elif sim_env == "ghdl":
        sim = cocotb_test.simulator.Ghdl(**kwargs)
    elif sim_env == "aldec":
        sim = cocotb_test.simulator.Aldec(**kwargs)

    results_xml_file = sim.run()

    assert os.path.isfile(results_xml_file), "Simulation terminated abnormally. Results file not found."

    tree = ET.parse(results_xml_file)
    for ts in tree.iter("testsuite"):
        for tc in ts.iter("testcase"):
            for failure in tc.iter("failure"):
                assert False, '{} class="{}" test="{}" error={}'.format(
                    failure.get("message"), tc.get("classname"), tc.get("name"), failure.get("stdout")
                )

    return results_xml_file


def clean(recursive=False, all=False):
    dir = os.getcwd()

    def rm_clean():
        sim_build_dir = os.path.join(dir, "sim_build")
        if os.path.isdir(sim_build_dir):
            print("Removing:", sim_build_dir)
            shutil.rmtree(sim_build_dir, ignore_errors=True)
            if all:
                libs_build_dir = os.path.join(dir, "cocotb_build")
                if os.path.isdir(libs_build_dir):
                    print("Removing:", libs_build_dir)
                    shutil.rmtree(libs_build_dir, ignore_errors=True)

    rm_clean()

    if recursive:
        for dir, subFolders, files in os.walk(dir):
            rm_clean()
