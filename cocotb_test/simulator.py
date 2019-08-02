import subprocess
import os
import sys
import inspect
import pkg_resources
import tempfile

if sys.version_info.major >= 3:
    from tkinter import _stringify as as_tcl_value
else:
    from Tkinter import _stringify as as_tcl_value


class Simulator(object):
    def __init__(
        self,
        toplevel,
        run_filename,
        module=None,
        python_search=[],
        toplevel_lang="verilog",
        verilog_sources=[],
        vhdl_sources=[],
        includes=[],
        defines=[],
        compile_args=[],
        simulation_args=[],
        extra_args=[],
        plus_args=[],
        **kwargs
    ):

        self.sim_dir = os.path.join(os.getcwd(), "sim_build")

        libs_dir = os.path.join(os.path.dirname(__file__), "libs")
        self.lib_dir = os.path.join(libs_dir, os.getenv("SIM"))

        self.lib_ext = "so"
        if os.name == "nt":
            self.lib_ext = "dll"

        self.run_dir = os.path.dirname(run_filename)

        self.module = module
        if self.module is None:
            self.module = os.path.splitext(os.path.split(run_filename)[-1])[0]

        self.python_search = python_search

        self.toplevel = toplevel
        self.toplevel_lang = toplevel_lang
        self.verilog_sources = self.get_abs_paths(verilog_sources)
        self.vhdl_sources = self.get_abs_paths(vhdl_sources)
        self.includes = self.get_abs_paths(includes)

        self.defines = defines
        self.compile_args = compile_args + extra_args
        self.simulation_args = simulation_args + extra_args
        self.plus_args = plus_args

        for arg in kwargs:
            setattr(self, arg, kwargs[arg])

        self.env = {}

    def set_env(self):

        for e in os.environ:
            self.env[e] = os.environ[e]

        lib_dir_sep = os.pathsep + self.lib_dir + os.pathsep
        if lib_dir_sep not in self.env["PATH"]:  # without checking will add forever casing error
            self.env["PATH"] += lib_dir_sep

        python_path = os.pathsep.join(sys.path)
        self.env["PYTHONPATH"] = os.pathsep + self.lib_dir
        self.env["PYTHONPATH"] += os.pathsep + self.run_dir
        self.env["PYTHONPATH"] += os.pathsep + python_path

        for path in self.python_search:
            self.env["PYTHONPATH"] += os.pathsep + path

        self.env["TOPLEVEL"] = self.toplevel
        self.env["COCOTB_SIM"] = "1"
        self.env["MODULE"] = self.module
        self.env["VERSION"] = pkg_resources.get_distribution("cocotb").version

        if not os.path.exists(self.sim_dir):
            os.makedirs(self.sim_dir)

    def build_command(self):
        raise NotImplementedError()

    def run(self):
        results_xml_file_defulat = os.path.join(self.sim_dir, "results.xml")
        if os.path.isfile(results_xml_file_defulat):
            os.remove(results_xml_file_defulat)

        fo = tempfile.NamedTemporaryFile()
        results_xml_file = fo.name
        fo.close()
        self.env["COCOTB_RESULTS_FILE_NAME"] = results_xml_file

        cmds = self.build_command()
        self.execute(cmds)

        # HACK: for compatibility to be removed
        if os.path.isfile(results_xml_file_defulat):
            results_xml_file = results_xml_file_defulat

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
                paths_abs.append(os.path.abspath(os.path.join(self.run_dir, path)))

        return paths_abs

    def execute(self, cmds):
        self.set_env()
        for cmd in cmds:
            print(" ".join(cmd))
            process = subprocess.check_call(cmd, cwd=self.sim_dir, env=self.env)

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
        return ["vvp", "-M", self.lib_dir, "-m", "libvpi"] + self.simulation_args + [self.sim_file] + self.plus_args

    def build_command(self):
        cmd = []
        if self.outdated(self.sim_file, self.verilog_sources):
            cmd.append(self.compile_command())
        else:
            print("Skipping compilation:" + self.sim_file)

        # TODO: check dependency
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

    def build_script(self):

        do_script = """# Autogenerated file
        onerror {
            quit -f -code 1
        }
        """

        if self.vhdl_sources:
            do_script += "vcom -mixedsvvh +define+COCOTB_SIM {DEFINES} {INCDIR} {EXTRA_ARGS} {VHDL_SOURCES}\n".format(
                VHDL_SOURCES=" ".join(as_tcl_value(v) for v in self.vhdl_sources),
                DEFINES=" ".join(self.get_define_commands(self.defines)),
                INCDIR=" ".join(self.get_include_commands(self.includes)),
                EXTRA_ARGS=" ".join(as_tcl_value(v) for v in self.compile_args),
            )
            self.env["GPI_EXTRA"] = "fli"

        if self.verilog_sources:
            do_script += "vlog -mixedsvvh +define+COCOTB_SIM -sv {DEFINES} {INCDIR} {EXTRA_ARGS} {VERILOG_SOURCES}\n".format(
                VERILOG_SOURCES=" ".join(as_tcl_value(v) for v in self.verilog_sources),
                DEFINES=" ".join(self.get_define_commands(self.defines)),
                INCDIR=" ".join(self.get_include_commands(self.includes)),
                EXTRA_ARGS=" ".join(as_tcl_value(v) for v in self.compile_args),
            )

        if self.toplevel_lang == "vhdl":
            do_script += "vsim -onfinish exit -foreign {EXT_NAME} {EXTRA_ARGS} {TOPLEVEL}\n".format(
                TOPLEVEL=as_tcl_value(self.toplevel),
                EXT_NAME=as_tcl_value("cocotb_init {}".format(os.path.join(self.lib_dir, "libfli." + self.lib_ext))),
                EXTRA_ARGS=" ".join(as_tcl_value(v) for v in self.simulation_args),
            )
        else:
            do_script += "vsim -onfinish exit -pli {EXT_NAME} {EXTRA_ARGS} {TOPLEVEL} {PLUS_ARGS}\n".format(
                TOPLEVEL=as_tcl_value(self.toplevel),
                EXT_NAME=as_tcl_value(os.path.join(self.lib_dir, "libvpi." + self.lib_ext)),
                EXTRA_ARGS=" ".join(as_tcl_value(v) for v in self.simulation_args),
                PLUS_ARGS=" ".join(as_tcl_value(v) for v in self.plus_args),
            )

        do_script += """log -recursive /*
        onbreak resume
        run -all
        quit
        """

        return do_script

    def build_command(self):

        do_file_path = os.path.join(self.sim_dir, "runsim.do")
        with open(do_file_path, "w") as do_file:
            do_file.write(self.build_script())

        cmd = ["vsim", "-c", "-do", do_file_path]
        return [cmd]


class Ius(Simulator):
    def __init__(self, *argv, **kwargs):
        super(Ius, self).__init__(*argv, **kwargs)

        self.env["GPI_EXTRA"] = "vhpi"

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
        cmd = (
            [
                "irun",
                "-64",
                "-v93",
                "-define",
                "COCOTB_SIM=1",
                "-loadvpi",
                os.path.join(self.lib_dir, "libvpi." + self.lib_ext) + ":vlog_startup_routines_bootstrap",
                "-plinowarn",
                "-access",
                "+rwc",
                "-top",
                self.toplevel,
            ]
            + self.get_define_commands(self.defines)
            + self.get_include_commands(self.includes)
            + self.compile_args
            + self.simulation_args
            + self.verilog_sources
            + self.vhdl_sources
        )

        return [cmd]


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
                os.path.join(self.lib_dir, "libvpi." + self.lib_ext),
            ]
            + self.get_define_commands(self.defines)
            + self.get_include_commands(self.includes)
            + self.compile_args
            + self.verilog_sources
        )

        cmd_run = [os.path.join(self.sim_dir, "simv"), "+define+COCOTB_SIM=1"] + self.simulation_args

        return [cmd_build, cmd_run]


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

        cmd_analyze = []
        for source_file in self.vhdl_sources:
            cmd_analyze.append(["ghdl"] + self.compile_args + ["-i", source_file])

        cmd_elaborate = ["ghdl"] + self.compile_args + ["-m", self.toplevel]

        cmd_run = ["ghdl", "-r", self.toplevel, "--vpi=" + os.path.join(self.lib_dir, "libvpi." + self.lib_ext)] + self.simulation_args

        cmd = cmd_analyze + [cmd_elaborate] + [cmd_run]
        return cmd
