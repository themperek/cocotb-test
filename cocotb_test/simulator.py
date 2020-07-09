import subprocess
import os
import sys
import tempfile
import re
import cocotb
import logging
import shutil
from xml.etree import cElementTree as ET
import signal

from distutils.spawn import find_executable
from distutils.sysconfig import get_config_var

_magic_re = re.compile(r"([\\{}])")
_space_re = re.compile(r"([\s])", re.ASCII)


def as_tcl_value(value):
    # add '\' before special characters and spaces
    value = _magic_re.sub(r"\\\1", value)
    value = value.replace("\n", r"\n")
    value = _space_re.sub(r"\\\1", value)
    if value[0] == '"':
        value = "\\" + value

    return value


class Simulator(object):
    def __init__(
        self,
        toplevel,
        module,
        work_dir=None,
        python_search=None,
        toplevel_lang="verilog",
        verilog_sources=None,
        vhdl_sources=None,
        includes=None,
        defines=None,
        compile_args=None,
        simulation_args=None,
        extra_args=None,
        plus_args=None,
        force_compile=False,
        testcase=None,
        sim_build="sim_build",
        seed=None,
        extra_env=None,
        compile_only=False,
        gui=False,
        **kwargs
    ):

        self.sim_dir = os.path.join(os.getcwd(), sim_build)
        if not os.path.exists(self.sim_dir):
            os.makedirs(self.sim_dir)

        self.logger = logging.getLogger("cocotb")
        self.logger.setLevel(logging.INFO)
        logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")

        self.lib_dir = os.path.join(os.path.dirname(cocotb.__file__), "libs")

        self.lib_ext = "so"
        if os.name == "nt":
            self.lib_ext = "dll"

        self.module = module  # TODO: Auto discovery, try introspect ?

        self.work_dir = self.sim_dir

        if work_dir is not None:
            absworkdir = os.path.abspath(work_dir)
            if os.path.isdir(absworkdir):
                self.work_dir = absworkdir

        if python_search is None:
            python_search = []

        self.python_search = python_search

        self.toplevel = toplevel
        self.toplevel_lang = toplevel_lang

        if verilog_sources is None:
            verilog_sources = []

        self.verilog_sources = self.get_abs_paths(verilog_sources)

        if vhdl_sources is None:
            vhdl_sources = []

        self.vhdl_sources = self.get_abs_paths(vhdl_sources)

        if includes is None:
            includes = []

        self.includes = self.get_abs_paths(includes)

        if defines is None:
            defines = []

        self.defines = defines

        if compile_args is None:
            compile_args = []

        if extra_args is None:
            extra_args = []

        self.compile_args = compile_args + extra_args

        if simulation_args is None:
            simulation_args = []

        self.simulation_args = simulation_args + extra_args

        if plus_args is None:
            plus_args = []

        self.plus_args = plus_args
        self.force_compile = force_compile
        self.compile_only = compile_only

        for arg in kwargs:
            setattr(self, arg, kwargs[arg])

        self.env = extra_env if extra_env is not None else {}

        if testcase is not None:
            self.env["TESTCASE"] = testcase

        if seed is not None:
            self.env["RANDOM_SEED"] = str(seed)

        self.gui = gui

        # Catch SIGINT and SIGTERM
        self.old_sigint_h = signal.getsignal(signal.SIGINT)
        self.old_sigterm_h = signal.getsignal(signal.SIGTERM)

        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def set_env(self):

        for e in os.environ:
            self.env[e] = os.environ[e]

        self.env["PATH"] += os.pathsep + self.lib_dir

        self.env["PYTHONPATH"] = os.pathsep.join(sys.path)
        for path in self.python_search:
            self.env["PYTHONPATH"] += os.pathsep + path

        self.env["PYTHONHOME"] = get_config_var("prefix")

        self.env["TOPLEVEL"] = self.toplevel
        self.env["MODULE"] = self.module

        if not os.path.exists(self.sim_dir):
            os.makedirs(self.sim_dir)

    def build_command(self):
        raise NotImplementedError()

    def run(self):

        sys.tracebacklimit = 0  # remove not needed traceback from assert

        # use temporary results file
        if not os.getenv("COCOTB_RESULTS_FILE"):
            tmp_results_file = tempfile.NamedTemporaryFile(prefix=self.sim_dir + os.path.sep, suffix="_results.xml")
            results_xml_file = tmp_results_file.name
            tmp_results_file.close()
            self.env["COCOTB_RESULTS_FILE"] = results_xml_file
        else:
            results_xml_file = os.getenv("COCOTB_RESULTS_FILE")

        cmds = self.build_command()
        self.set_env()
        self.execute(cmds)

        if not self.compile_only:
            results_file_exist = os.path.isfile(results_xml_file)
            assert results_file_exist, "Simulation terminated abnormally. Results file not found."

            tree = ET.parse(results_xml_file)
            for ts in tree.iter("testsuite"):
                for tc in ts.iter("testcase"):
                    for failure in tc.iter("failure"):
                        assert False, '{} class="{}" test="{}" error={}'.format(
                            failure.get("message"), tc.get("classname"), tc.get("name"), failure.get("stdout"),
                        )

        print("Results file: %s" % results_xml_file)
        return results_xml_file

    def get_include_commands(self, includes):
        raise NotImplementedError()

    def get_define_commands(self, defines):
        raise NotImplementedError()

    def get_abs_paths(self, paths):
        paths_abs = []
        for path in paths:
            if os.path.isabs(path):
                paths_abs.append(os.path.abspath(path))
            else:
                paths_abs.append(os.path.abspath(os.path.join(os.getcwd(), path)))

        return paths_abs

    def execute(self, cmds):
        self.set_env()
        for cmd in cmds:
            self.logger.info("Running command: " + " ".join(cmd))

            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=self.work_dir, env=self.env
            )

            while True:
                out = self.process.stdout.readline()

                if not out and self.process.poll() is not None:
                    break

                log_out = out.decode("utf-8").rstrip()
                if log_out != "":
                    self.logger.info(log_out)

            if self.process.returncode:
                self.logger.error("Command terminated with error %d" % self.process.returncode)
                return

    # def execute(self, cmds):
    #     self.set_env()
    #     for cmd in cmds:
    #         print(" ".join(cmd))
    #         process = subprocess.check_call(cmd, cwd=self.work_dir, env=self.env)

    def outdated(self, output, dependencies):

        if not os.path.isfile(output):
            return True

        output_mtime = os.path.getmtime(output)

        dep_mtime = 0
        for file in dependencies:
            mtime = os.path.getmtime(file)
            if mtime > dep_mtime:
                dep_mtime = mtime

        if dep_mtime > output_mtime:
            return True

        return False

    def exit_gracefully(self, signum, frame):
        pid = None
        if self.process is not None:
            pid = self.process.pid
            self.process.stdout.flush()
            self.process.kill()
            self.process.wait()
        # Restore previous handlers
        signal.signal(signal.SIGINT, self.old_sigint_h)
        signal.signal(signal.SIGTERM, self.old_sigterm_h)
        assert False, "Exiting pid: {} with signum: {}".format(str(pid), str(signum))


class Icarus(Simulator):
    def __init__(self, *argv, **kwargs):
        super(Icarus, self).__init__(*argv, **kwargs)

        if self.vhdl_sources:
            raise ValueError("This simulator does not support VHDL")

        self.sim_file = os.path.join(self.sim_dir, self.toplevel + ".vvp")

    def get_include_commands(self, includes):
        include_cmd = []
        for dir in includes:
            include_cmd.append("-I")
            include_cmd.append(dir)

        return include_cmd

    def get_define_commands(self, defines):
        defines_cmd = []
        for define in defines:
            defines_cmd.append("-D")
            defines_cmd.append(define)

        return defines_cmd

    def compile_command(self):

        cmd_compile = (
            ["iverilog", "-o", self.sim_file, "-D", "COCOTB_SIM=1", "-s", self.toplevel, "-g2012"]
            + self.get_define_commands(self.defines)
            + self.get_include_commands(self.includes)
            + self.compile_args
            + self.verilog_sources
        )

        return cmd_compile

    def run_command(self):
        return (
            ["vvp", "-M", self.lib_dir, "-m", "libcocotbvpi_icarus"]
            + self.simulation_args
            + [self.sim_file]
            + self.plus_args
        )

    def build_command(self):
        cmd = []
        if self.outdated(self.sim_file, self.verilog_sources) or self.force_compile:
            cmd.append(self.compile_command())
        else:
            self.logger.warning("Skipping compilation:" + self.sim_file)

        # TODO: check dependency?
        if not self.compile_only:
            cmd.append(self.run_command())

        return cmd


class Questa(Simulator):
    def get_include_commands(self, includes):
        include_cmd = []
        for dir in includes:
            include_cmd.append("+incdir+" + as_tcl_value(dir))

        return include_cmd

    def get_define_commands(self, defines):
        defines_cmd = []
        for define in defines:
            defines_cmd.append("+define+" + as_tcl_value(define))

        return defines_cmd

    def build_command(self):

        self.rtl_library = self.toplevel

        cmd = []

        out_file = os.path.join(self.sim_dir, self.toplevel, "_info")

        if self.outdated(out_file, self.verilog_sources + self.vhdl_sources) or self.force_compile:

            if os.path.exists(os.path.join(self.sim_dir, self.rtl_library)):
                do_script = "vdel -lib {RTL_LIBRARY} -all".format(RTL_LIBRARY=as_tcl_value(self.rtl_library))
                cmd.append(["vsim"] + ["-c"] + ["-do"] + [do_script])

            if self.vhdl_sources:
                do_script = "vlib {RTL_LIBRARY}; vcom -mixedsvvh -work {RTL_LIBRARY} {EXTRA_ARGS} {VHDL_SOURCES}; quit".format(
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    VHDL_SOURCES=" ".join(as_tcl_value(v) for v in self.vhdl_sources),
                    EXTRA_ARGS=" ".join(as_tcl_value(v) for v in self.compile_args),
                )
                cmd.append(["vsim"] + ["-c"] + ["-do"] + [do_script])

            if self.verilog_sources:
                do_script = "vlog -mixedsvvh -work {RTL_LIBRARY} +define+COCOTB_SIM -sv {DEFINES} {INCDIR} {EXTRA_ARGS} {VERILOG_SOURCES}; quit".format(
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    VERILOG_SOURCES=" ".join(as_tcl_value(v) for v in self.verilog_sources),
                    DEFINES=" ".join(self.get_define_commands(self.defines)),
                    INCDIR=" ".join(self.get_include_commands(self.includes)),
                    EXTRA_ARGS=" ".join(as_tcl_value(v) for v in self.compile_args),
                )
                cmd.append(["vsim"] + ["-c"] + ["-do"] + [do_script])

        else:
            self.logger.warning("Skipping compilation:" + out_file)

        if not self.compile_only:
            if self.toplevel_lang == "vhdl":
                do_script = "vsim -onfinish {ONFINISH} -foreign {EXT_NAME} {EXTRA_ARGS} {RTL_LIBRARY}.{TOPLEVEL};".format(
                    ONFINISH="stop" if self.gui else "exit",
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    TOPLEVEL=as_tcl_value(self.toplevel),
                    EXT_NAME=as_tcl_value(
                        "cocotb_init {}".format(os.path.join(self.lib_dir, "libcocotbfli_modelsim." + self.lib_ext))
                    ),
                    EXTRA_ARGS=" ".join(as_tcl_value(v) for v in self.simulation_args),
                )

                if self.verilog_sources:
                    self.env["GPI_EXTRA"] = "cocotbvpi_modelsim:cocotbvpi_entry_point"

            else:
                do_script = "vsim -onfinish {ONFINISH} -pli {EXT_NAME} {EXTRA_ARGS} {RTL_LIBRARY}.{TOPLEVEL} {PLUS_ARGS};".format(
                    ONFINISH="stop" if self.gui else "exit",
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    TOPLEVEL=as_tcl_value(self.toplevel),
                    EXT_NAME=as_tcl_value(os.path.join(self.lib_dir, "libcocotbvpi_modelsim." + self.lib_ext)),
                    EXTRA_ARGS=" ".join(as_tcl_value(v) for v in self.simulation_args),
                    PLUS_ARGS=" ".join(as_tcl_value(v) for v in self.plus_args),
                )

                if self.vhdl_sources:
                    self.env["GPI_EXTRA"] = "cocotbfli_modelsim:cocotbfli_entry_point"

            # do_script += "log -recursive /*;"

            if not self.gui:
                do_script += "run -all; quit"

            cmd.append(["vsim"] + (["-gui"] if self.gui else ["-c"]) + ["-do"] + [do_script])

        return cmd


class Ius(Simulator):
    def __init__(self, *argv, **kwargs):
        super(Ius, self).__init__(*argv, **kwargs)

        self.env["GPI_EXTRA"] = "cocotbvhpi_ius:cocotbvhpi_entry_point"

    def get_include_commands(self, includes):
        include_cmd = []
        for dir in includes:
            include_cmd.append("-incdir")
            include_cmd.append(dir)

        return include_cmd

    def get_define_commands(self, defines):
        defines_cmd = []
        for define in defines:
            defines_cmd.append("-define")
            defines_cmd.append(define)

        return defines_cmd

    def build_command(self):

        out_file = os.path.join(self.sim_dir, "INCA_libs", "history")

        cmd = []

        if self.outdated(out_file, self.verilog_sources + self.vhdl_sources) or self.force_compile:
            cmd_elab = (
                [
                    "irun",
                    "-64",
                    "-elaborate",
                    "-v93",
                    "-define",
                    "COCOTB_SIM=1",
                    "-loadvpi",
                    os.path.join(self.lib_dir, "libcocotbvpi_ius." + self.lib_ext) + ":vlog_startup_routines_bootstrap",
                    "-plinowarn",
                    "-access",
                    "+rwc",
                    "-top",
                    self.toplevel,
                ]
                + self.get_define_commands(self.defines)
                + self.get_include_commands(self.includes)
                + self.compile_args
                + self.verilog_sources
                + self.vhdl_sources
            )
            cmd.append(cmd_elab)

        else:
            self.logger.warning("Skipping compilation:" + out_file)

        if not self.compile_only:
            cmd_run = ["irun", "-64", "-R", ("-gui" if self.gui else "")] + self.simulation_args + self.plus_args
            cmd.append(cmd_run)

        return cmd


class Xcelium(Simulator):
    def __init__(self, *argv, **kwargs):
        super(Xcelium, self).__init__(*argv, **kwargs)

        self.env["GPI_EXTRA"] = "cocotbvhpi_ius:cocotbvhpi_entry_point"

    def get_include_commands(self, includes):
        include_cmd = []
        for dir in includes:
            include_cmd.append("-incdir")
            include_cmd.append(dir)

        return include_cmd

    def get_define_commands(self, defines):
        defines_cmd = []
        for define in defines:
            defines_cmd.append("-define")
            defines_cmd.append(define)

        return defines_cmd

    def build_command(self):

        out_file = os.path.join(self.sim_dir, "INCA_libs", "history")

        cmd = []

        if self.outdated(out_file, self.verilog_sources + self.vhdl_sources) or self.force_compile:
            cmd_elab = (
                [
                    "xrun",
                    "-64",
                    "-elaborate",
                    "-v93",
                    "-define",
                    "COCOTB_SIM=1",
                    "-loadvpi",
                    os.path.join(self.lib_dir, "libcocotbvpi_ius." + self.lib_ext) + ":vlog_startup_routines_bootstrap",
                    "-plinowarn",
                    "-access",
                    "+rwc",
                    "-top",
                    self.toplevel,
                ]
                + self.get_define_commands(self.defines)
                + self.get_include_commands(self.includes)
                + self.compile_args
                + self.verilog_sources
                + self.vhdl_sources
            )
            cmd.append(cmd_elab)

        else:
            self.logger.warning("Skipping compilation:" + out_file)

        if not self.compile_only:
            cmd_run = ["xrun", "-64", "-R", ("-gui" if self.gui else "")] + self.simulation_args + self.plus_args
            cmd.append(cmd_run)

        return cmd


class Vcs(Simulator):
    def get_include_commands(self, includes):
        include_cmd = []
        for dir in includes:
            include_cmd.append("+incdir+" + dir)

        return include_cmd

    def get_define_commands(self, defines):
        defines_cmd = []
        for define in defines:
            defines_cmd.append("+define+" + define)

        return defines_cmd

    def build_command(self):

        pli_cmd = "acc+=rw,wn:*"

        cmd = []

        do_file_path = os.path.join(self.sim_dir, "pli.tab")
        with open(do_file_path, "w") as pli_file:
            pli_file.write(pli_cmd)

        cmd_build = (
            [
                "vcs",
                "-full64",
                "-debug",
                "+vpi",
                "-P",
                "pli.tab",
                "-sverilog",
                "+define+COCOTB_SIM=1",
                "-load",
                os.path.join(self.lib_dir, "libcocotbvpi_vcs." + self.lib_ext),
            ]
            + self.get_define_commands(self.defines)
            + self.get_include_commands(self.includes)
            + self.compile_args
            + self.verilog_sources
        )
        cmd.append(cmd_build)

        if not self.compile_only:
            cmd_run = [os.path.join(self.sim_dir, "simv"), "+define+COCOTB_SIM=1"] + self.simulation_args
            cmd.append(cmd_run)

        if self.gui:
            cmd.append("-gui")  # not tested!

        return cmd


class Ghdl(Simulator):
    def get_include_commands(self, includes):
        include_cmd = []
        for dir in includes:
            include_cmd.append("-I")
            include_cmd.append(dir)

        return include_cmd

    def get_define_commands(self, defines):
        defines_cmd = []
        for define in defines:
            defines_cmd.append("-D")
            defines_cmd.append(define)

    def build_command(self):

        cmd = []

        for source_file in self.vhdl_sources:
            cmd.append(["ghdl"] + self.compile_args + ["-i", source_file])

        cmd_elaborate = ["ghdl"] + self.compile_args + ["-m", self.toplevel]
        cmd.append(cmd_elaborate)

        cmd_run = [
            "ghdl",
            "-r",
            self.toplevel,
            "--vpi=" + os.path.join(self.lib_dir, "libcocotbvpi_ghdl." + self.lib_ext),
        ] + self.simulation_args

        if not self.compile_only:
            cmd.append(cmd_run)

        return cmd


class Riviera(Simulator):
    def get_include_commands(self, includes):
        include_cmd = []
        for dir in includes:
            include_cmd.append("+incdir+" + as_tcl_value(dir))

        return include_cmd

    def get_define_commands(self, defines):
        defines_cmd = []
        for define in defines:
            defines_cmd.append("+define+" + as_tcl_value(define))

        return defines_cmd

    def build_command(self):

        self.rtl_library = self.toplevel

        do_script = "\nonerror {\n quit -code 1 \n} \n"

        out_file = os.path.join(self.sim_dir, self.rtl_library, self.rtl_library + ".lib")

        if self.outdated(out_file, self.verilog_sources + self.vhdl_sources) or self.force_compile:

            do_script += "alib {RTL_LIBRARY} \n".format(RTL_LIBRARY=as_tcl_value(self.rtl_library))

            if self.vhdl_sources:
                do_script += "acom -work {RTL_LIBRARY} {EXTRA_ARGS} {VHDL_SOURCES}\n".format(
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    VHDL_SOURCES=" ".join(as_tcl_value(v) for v in self.vhdl_sources),
                    EXTRA_ARGS=" ".join(as_tcl_value(v) for v in self.compile_args),
                )

            if self.verilog_sources:
                do_script += "alog -work {RTL_LIBRARY} +define+COCOTB_SIM -sv {DEFINES} {INCDIR} {EXTRA_ARGS} {VERILOG_SOURCES} \n".format(
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    VERILOG_SOURCES=" ".join(as_tcl_value(v) for v in self.verilog_sources),
                    DEFINES=" ".join(self.get_define_commands(self.defines)),
                    INCDIR=" ".join(self.get_include_commands(self.includes)),
                    EXTRA_ARGS=" ".join(as_tcl_value(v) for v in self.compile_args),
                )
        else:
            self.logger.warning("Skipping compilation:" + out_file)

        if not self.compile_only:
            if self.toplevel_lang == "vhdl":
                do_script += "asim +access +w -interceptcoutput -O2 -loadvhpi {EXT_NAME} {EXTRA_ARGS} {RTL_LIBRARY}.{TOPLEVEL} \n".format(
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    TOPLEVEL=as_tcl_value(self.toplevel),
                    EXT_NAME=as_tcl_value(os.path.join(self.lib_dir, "libcocotbvhpi_aldec")),
                    EXTRA_ARGS=" ".join(as_tcl_value(v) for v in self.simulation_args),
                )
                if self.verilog_sources:
                    self.env["GPI_EXTRA"] = "cocotbvpi_aldec:cocotbvpi_entry_point"
            else:
                do_script += "asim +access +w -interceptcoutput -O2 -pli {EXT_NAME} {EXTRA_ARGS} {RTL_LIBRARY}.{TOPLEVEL} {PLUS_ARGS} \n".format(
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    TOPLEVEL=as_tcl_value(self.toplevel),
                    EXT_NAME=as_tcl_value(os.path.join(self.lib_dir, "libcocotbvpi_aldec")),
                    EXTRA_ARGS=" ".join(as_tcl_value(v) for v in self.simulation_args),
                    PLUS_ARGS=" ".join(as_tcl_value(v) for v in self.plus_args),
                )
                if self.vhdl_sources:
                    self.env["GPI_EXTRA"] = "cocotbvhpi_aldec:cocotbvhpi_entry_point"

            do_script += "run -all \nexit"

        do_file = tempfile.NamedTemporaryFile(delete=False)
        do_file.write(do_script.encode())
        do_file.close()
        # print(do_script)

        return [["vsimsa"] + ["-do"] + ["do"] + [do_file.name]]


class Verilator(Simulator):
    def __init__(self, *argv, **kwargs):
        super(Verilator, self).__init__(*argv, **kwargs)

        if self.vhdl_sources:
            raise ValueError("This simulator does not support VHDL")

    def get_include_commands(self, includes):
        include_cmd = []
        for dir in includes:
            include_cmd.append("-I" + dir)

        return include_cmd

    def get_define_commands(self, defines):
        defines_cmd = []
        for define in defines:
            defines_cmd.append("-D" + define)

        return defines_cmd

    def build_command(self):

        cmd = []

        out_file = os.path.join(self.sim_dir, self.toplevel)
        verilator_cpp = os.path.join(os.path.dirname(os.path.dirname(self.lib_dir)), "share", "verilator.cpp")
        verilator_cpp = os.path.join(os.path.dirname(cocotb.__file__), "share", "lib", "verilator", "verilator.cpp")

        verilator_exec = find_executable("verilator")
        if verilator_exec is None:
            raise ValueError("Verilator executable not found.")

        cmd.append(
            [
                "perl",
                verilator_exec,
                "-cc",
                "--exe",
                "-Mdir",
                self.sim_dir,
                "-DCOCOTB_SIM=1",
                "--top-module",
                self.toplevel,
                "--vpi",
                "--public-flat-rw",
                "--prefix",
                "Vtop",
                "-o",
                self.toplevel,
                "-LDFLAGS",
                "-Wl,-rpath,{LIB_DIR} -L{LIB_DIR} -lcocotbvpi_verilator".format(LIB_DIR=self.lib_dir),
            ]
            + self.compile_args
            + self.get_define_commands(self.defines)
            + self.get_include_commands(self.includes)
            + [verilator_cpp]
            + self.verilog_sources
        )

        self.env["CPPFLAGS"] = "-std=c++11"
        cmd.append(["make", "-C", self.sim_dir, "-f", "Vtop.mk"])

        if not self.compile_only:
            cmd.append([out_file])

        return cmd


def run(**kwargs):

    sim_env = os.getenv("SIM", "icarus")

    supported_sim = ["icarus", "questa", "ius", "xcelium", "vcs", "ghdl", "riviera", "verilator"]
    if sim_env not in supported_sim:
        raise NotImplementedError("Set SIM variable. Supported: " + ", ".join(supported_sim))

    if sim_env == "icarus":
        sim = Icarus(**kwargs)
    elif sim_env == "questa":
        sim = Questa(**kwargs)
    elif sim_env == "ius":
        sim = Ius(**kwargs)
    elif sim_env == "xcelium":
        sim = Xcelium(**kwargs)
    elif sim_env == "vcs":
        sim = Vcs(**kwargs)
    elif sim_env == "ghdl":
        sim = Ghdl(**kwargs)
    elif sim_env == "riviera":
        sim = Riviera(**kwargs)
    elif sim_env == "verilator":
        sim = Verilator(**kwargs)

    return sim.run()


def clean(recursive=False):
    dir = os.getcwd()

    def rm_clean():
        sim_build_dir = os.path.join(dir, "sim_build")
        if os.path.isdir(sim_build_dir):
            print("Removing:", sim_build_dir)
            shutil.rmtree(sim_build_dir, ignore_errors=True)

    rm_clean()

    if recursive:
        for dir, _, _ in os.walk(dir):
            rm_clean()
