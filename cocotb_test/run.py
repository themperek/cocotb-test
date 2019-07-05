import os
import sys
import inspect

import cocotb_test.simulator
from cocotb_test.build_libs import build_libs

import pkg_resources
from xml.etree import cElementTree as ET


def run(toplevel, module=None, python_search=[], simulator=None, **kwargs):

    supported_sim = ["icarus", "questa", "ius", "vcs", "ghdl"]
    if ("SIM" in os.environ and os.environ["SIM"] in supported_sim) or simulator:
        pass
    else:
        raise NotImplementedError(
            "Set SIM variable. Supported: " + ", ".join(supported_sim)
        )

    libs_dir, ext_name = build_libs()

    previous_frame = inspect.currentframe().f_back
    (run_module_filename, _, _, _, _) = inspect.getframeinfo(previous_frame)

    run_dir_name = os.path.dirname(run_module_filename)
    run_module_name = os.path.splitext(os.path.split(run_module_filename)[-1])[0]

    if module is None:
        module = run_module_name

    env = os.environ

    env["PATH"] += os.pathsep + libs_dir

    python_path = os.pathsep.join(sys.path)
    env["PYTHONPATH"] = os.pathsep + python_path + os.pathsep + libs_dir
    env["PYTHONPATH"] += os.pathsep + run_dir_name

    for path in python_search:
        env["PYTHONPATH"] += os.pathsep + path

    env["TOPLEVEL"] = toplevel
    env["COCOTB_SIM"] = "1"
    env["MODULE"] = module
    env["VERSION"] = pkg_resources.get_distribution("cocotb").version

    sim_build_dir = os.path.abspath(os.path.join(run_dir_name, "sim_build"))
    results_xml_file = os.path.join(sim_build_dir, "results.xml")

    if not os.path.exists(sim_build_dir):
        os.makedirs(sim_build_dir)

    kwargs["toplevel"] = toplevel
    kwargs["run_dir"] = run_dir_name
    kwargs["sim_dir"] = sim_build_dir
    kwargs["lib_dir"] = libs_dir
    kwargs["lib_ext"] = ext_name

    if os.path.isfile(results_xml_file):
        os.remove(results_xml_file)

    if simulator:
        sim = simulator(**kwargs)
    elif env["SIM"] == "icarus":
        sim = cocotb_test.simulator.Icarus(**kwargs)
    elif env["SIM"] == "questa":
        sim = cocotb_test.simulator.Questa(**kwargs)
    elif env["SIM"] == "ius":
        sim = cocotb_test.simulator.Ius(**kwargs)
    elif env["SIM"] == "vcs":
        sim = cocotb_test.simulator.Vcs(**kwargs)
    elif env["SIM"] == "ghdl":
        sim = cocotb_test.simulator.Ghdl(**kwargs)

    sim.run()

    assert os.path.isfile(results_xml_file), "Simulation terminated abnormally. Results file not found."
    
    tree = ET.parse(results_xml_file)
    for ts in tree.iter("testsuite"):
        for tc in ts.iter("testcase"):
            for failure in tc.iter("failure"):
                assert False, '{} class="{}" test="{}" error={}'.format(
                    failure.get("message"),
                    tc.get("classname"),
                    tc.get("name"),
                    failure.get("stdout"),
                )
