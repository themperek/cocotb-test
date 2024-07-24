import os
import sys
import tempfile
import re
import cocotb
import logging
import shutil
from xml.etree import cElementTree as ET
import threading
import signal
import warnings
import find_libpython
import cocotb.config
import asyncio
import sysconfig

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


class Simulator:
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
        parameters=None,
        compile_args=None,
        vhdl_compile_args=None,
        verilog_compile_args=None,
        sim_args=None,
        extra_args=None,
        plus_args=None,
        force_compile=False,
        testcase=None,
        sim_build="sim_build",
        seed=None,
        extra_env=None,
        compile_only=False,
        waves=None,
        timescale=None,
        gui=False,
        simulation_args=None,
        **kwargs,
    ):

        self.sim_dir = os.path.abspath(sim_build)
        os.makedirs(self.sim_dir, exist_ok=True)

        self.logger = logging.getLogger("cocotb")
        self.logger.setLevel(logging.INFO)
        logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")

        warnings.simplefilter("always", DeprecationWarning)

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

        if parameters is None:
            parameters = {}

        self.parameters = parameters

        if compile_args is None:
            compile_args = []

        if vhdl_compile_args is None:
            self.vhdl_compile_args = []
        else:
            self.vhdl_compile_args = vhdl_compile_args

        if verilog_compile_args is None:
            self.verilog_compile_args = []
        else:
            self.verilog_compile_args = verilog_compile_args

        if extra_args is None:
            extra_args = []

        self.compile_args = compile_args + extra_args

        if sim_args is None:
            sim_args = []

        if simulation_args is not None:
            sim_args += simulation_args
            warnings.warn(
                "Using simulation_args is deprecated. Please use sim_args instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        self.simulation_args = sim_args + extra_args

        if plus_args is None:
            plus_args = []

        self.plus_args = plus_args
        self.force_compile = force_compile
        self.compile_only = compile_only

        if kwargs:
            warnings.warn(
                "Using kwargs is deprecated. Please explicitly declare or arguments instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        for arg in kwargs:
            setattr(self, arg, kwargs[arg])

        # by copy since we modify
        self.env = dict(extra_env) if extra_env is not None else {}

        if testcase is not None:
            self.env["TESTCASE"] = testcase

        if seed is not None:
            self.env["RANDOM_SEED"] = str(seed)

        if waves is None:
            self.waves = bool(int(os.getenv("WAVES", 0)))
        else:
            self.waves = bool(waves)

        if timescale is None or re.fullmatch("\\d+[npu]?s/\\d+[npu]?s", timescale):
            self.timescale = timescale
        else:
            raise ValueError("Invalid timescale: {}".format(timescale))

        self.gui = gui

        # format sources and toplevel
        self.format_input()

        # Catch SIGINT and SIGTERM
        self.old_sigint_h = signal.getsignal(signal.SIGINT)
        self.old_sigterm_h = signal.getsignal(signal.SIGTERM)

        # works only if main thread
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

        self.process = None

    def set_env(self):

        for e in os.environ:
            self.env[e] = os.environ[e]

        self.env["LIBPYTHON_LOC"] = find_libpython.find_libpython()

        self.env["PATH"] += os.pathsep + self.lib_dir

        self.env["PYTHONPATH"] = os.pathsep.join(sys.path)
        for path in self.python_search:
            self.env["PYTHONPATH"] += os.pathsep + path

        self.env["PYTHONHOME"] = sysconfig.get_config_var("prefix")

        self.env["TOPLEVEL"] = self.toplevel_module
        self.env["MODULE"] = self.module

        if not os.path.exists(self.sim_dir):
            os.makedirs(self.sim_dir)

    def build_command(self):
        raise NotImplementedError()

    def run(self):

        __tracebackhide__ = True  # Hide the traceback when using PyTest.

        # use temporary results file
        if not os.getenv("COCOTB_RESULTS_FILE"):
            tmp_results_file = tempfile.NamedTemporaryFile(
                prefix=self.sim_dir + os.path.sep, suffix="_results.xml", delete=False
            )
            results_xml_file = tmp_results_file.name
            tmp_results_file.close()
            self.env["COCOTB_RESULTS_FILE"] = results_xml_file
        else:
            results_xml_file = os.getenv("COCOTB_RESULTS_FILE")

        self.set_env()
        cmds = self.build_command()
        self.execute(cmds)

        failed = 0

        if not self.compile_only:
            results_file_exist = os.path.isfile(results_xml_file)
            if not results_file_exist:
                raise SystemExit("ERROR: Simulation terminated abnormally. Cocotb results file not found.")

            tree = ET.parse(results_xml_file)
            for ts in tree.iter("testsuite"):
                for tc in ts.iter("testcase"):
                    for _ in tc.iter("failure"):
                        self.logger.error(f'Failed: {tc.get("classname")}::{tc.get("name")}')
                        failed += 1

        if failed:
            raise SystemExit(f"FAILED {failed} tests.")

        self.logger.info(f"Results file: {results_xml_file}")

        return results_xml_file

    def get_include_commands(self, includes):
        raise NotImplementedError()

    def get_define_commands(self, defines):
        raise NotImplementedError()

    def get_parameter_commands(self, parameters):
        raise NotImplementedError()

    def normalize_paths(self, paths):
        paths_abs = []
        for path in paths:
            if os.path.isabs(path):
                paths_abs.append(os.path.abspath(path))
            else:
                paths_abs.append(os.path.abspath(os.path.join(os.getcwd(), path)))
        return paths_abs

    def get_abs_paths(self, paths):
        if isinstance(paths, list):
            return self.normalize_paths(paths)
        else:
            libs = dict()
            for lib, src in paths.items():
                libs[lib] = self.normalize_paths(src)
            return libs

    async def _log_pipe(self, level, stream):
        line = bytearray()
        while not stream.at_eof():
            try:
                line.extend(await stream.readuntil())
            except asyncio.IncompleteReadError as e:
                line.extend(e.partial)
            except asyncio.LimitOverrunError as e:
                line.extend(await stream.read(e.consumed))
                continue

            if line:
                self.logger.log(level, line.decode("utf-8").rstrip())
            line.clear()

    async def _exec(self, cmds):

        p = await asyncio.create_subprocess_exec(
            *cmds,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.work_dir,
            env=self.env,
        )

        self.process = p

        await asyncio.wait(
            [
                asyncio.create_task(self._log_pipe(logging.INFO, p.stdout)),
                asyncio.create_task(self._log_pipe(logging.ERROR, p.stderr)),
            ]
        )

        await p.wait()

    def execute(self, cmds):

        __tracebackhide__ = True  # Hide the traceback when using PyTest.

        for cmd in cmds:
            self.logger.info("Running command: " + " ".join(cmd))

            asyncio.run(self._exec(cmd))

            if self.process.returncode:
                raise SystemExit(f"Process {cmd[0]} terminated with error {self.process.returncode}")

            self.process = None

    def outdated_list(self, output, dependencies):

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

    def outdated(self, output, dependencies):
        if isinstance(dependencies, list):
            return self.outdated_list(output, dependencies)

        for sources in dependencies.values():
            if self.outdated_list(output, sources):
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
        assert False, f"Exiting pid: {str(pid)} with signum: {str(signum)}"

    @property
    def toplevel_module_list(self):
        """Return list of toplevel module names"""
        return [top.rsplit(".", 1)[-1] for top in self.toplevel]

    @property
    def toplevel_library_list(self):
        """Return list of library names of toplevel modules"""
        assert all(["." in top for top in self.toplevel]), "`self.toplevel` does not yet contain library information."
        return [top.split(".", 1)[0] for top in self.toplevel]

    @property
    def toplevel_module(self):
        """Return name of first toplevel module"""
        return self.toplevel_module_list[0]

    @property
    def toplevel_library(self):
        """Return name of library of first toplevel"""
        return self.toplevel_library_list[0]

    @property
    def vhdl_sources_flat(self):
        if not self.vhdl_sources:
            return []
        assert len(self.vhdl_sources) == 1, "Flattened sources only available when using a single library name."
        return list(self.vhdl_sources.values())[0]

    @property
    def verilog_sources_flat(self):
        if not self.verilog_sources:
            return []
        assert len(self.verilog_sources) == 1, "Flattened sources only available when using a single library name."
        return list(self.verilog_sources.values())[0]

    def format_input(self):
        """Format sources and toplevel strings."""

        if not isinstance(self.toplevel, list):
            self.toplevel = [self.toplevel]

        if self.vhdl_sources:
            if isinstance(self.vhdl_sources, list):
                # create named library with first toplevel module as its name
                self.vhdl_sources = {f"{self.toplevel_module}": self.vhdl_sources}

        if self.verilog_sources:
            if isinstance(self.verilog_sources, list):
                # create named library with toplevel module as its name
                self.verilog_sources = {f"{self.toplevel_module}": self.verilog_sources}

        # format toplevel as `<lib>.<module>`, if lib was not given
        for i, top in enumerate(self.toplevel):
            if not "." in top:
                self.toplevel[i] = ".".join((self.toplevel_module, top))


class Icarus(Simulator):
    def __init__(self, *argv, **kwargs):
        super().__init__(*argv, **kwargs)

        if self.vhdl_sources:
            raise ValueError("This simulator does not support VHDL")

        self.sim_file = os.path.join(self.sim_dir, f"{self.toplevel_module}.vvp")

    def get_include_commands(self, includes):
        return [f"-I{dir}" for dir in includes]

    def get_define_commands(self, defines):
        return [f"-D{define}" for define in defines]

    def get_parameter_commands(self, parameters):
        return [f"-P{self.toplevel_module}.{name}={str(value)}" for name, value in parameters.items()]

    def compile_command(self):

        compile_args = self.compile_args + self.verilog_compile_args

        toplevel = []
        for t in self.toplevel_module_list:
            toplevel += ["-s", t]

        cmd_compile = (
            [
                "iverilog",
                "-o",
                self.sim_file,
                "-D",
                "COCOTB_SIM=1",
                "-g2012",
            ]
            + toplevel
            + self.get_define_commands(self.defines)
            + self.get_include_commands(self.includes)
            + self.get_parameter_commands(self.parameters)
            + compile_args
            + self.verilog_sources_flat
        )

        return cmd_compile

    def run_command(self):
        return (
            ["vvp", "-M", self.lib_dir, "-m", cocotb.config.lib_name("vpi", "icarus")]
            + self.simulation_args
            + [self.sim_file]
            + self.plus_args
        )

    def build_command(self):
        verilog_sources = self.verilog_sources_flat.copy()
        if self.waves:
            dump_mod_name = "iverilog_dump"
            dump_file_name = self.toplevel_module + ".fst"
            dump_mod_file_name = os.path.join(self.sim_dir, dump_mod_name + ".v")

            if not os.path.exists(dump_mod_file_name):
                with open(dump_mod_file_name, "w") as f:
                    f.write("module iverilog_dump();\n")
                    f.write("initial begin\n")
                    f.write('    $dumpfile("%s");\n' % dump_file_name)
                    f.write("    $dumpvars(0, %s);\n" % self.toplevel_module)
                    f.write("end\n")
                    f.write("endmodule\n")

            first_lib_src = next(iter(self.verilog_sources.items()))[1]
            first_lib_src += [dump_mod_file_name]

            self.compile_args.extend(["-s", dump_mod_name])
            self.plus_args.append("-fst")

        if self.timescale:
            timescale_cmd_file = os.path.join(self.sim_dir, "timescale.f")
            with open(timescale_cmd_file, "w") as f:
                f.write(f"+timescale+{self.timescale}\n")
            self.compile_args.extend(["-f", timescale_cmd_file])

        cmd = []
        if self.outdated(self.sim_file, verilog_sources) or self.force_compile:
            cmd.append(self.compile_command())
        else:
            self.logger.warning(f"Skipping compilation:{self.sim_file}")

        # TODO: check dependency?
        if not self.compile_only:
            cmd.append(self.run_command())

        return cmd


class Questa(Simulator):
    def get_include_commands(self, includes):
        return [f"+incdir+{as_tcl_value(dir)}" for dir in includes]

    def get_define_commands(self, defines):
        return [f"+define+{as_tcl_value(define)}" for define in defines]

    def get_parameter_commands(self, parameters):
        return [f"-g{name}={str(value)}" for name, value in parameters.items()]

    def do_script(self):
        do_script = ""
        if self.waves:
            do_script += "log -recursive /*;"
        if not self.gui:
            do_script += "run -all; quit"
        return do_script

    def build_command(self):

        cmd = []

        do_script = self.do_script()

        if self.vhdl_sources:
            compile_args = self.compile_args + self.vhdl_compile_args

            for lib, src in self.vhdl_sources.items():
                cmd.append(["vlib", as_tcl_value(lib)])
                cmd.append(
                    ["vcom", "-mixedsvvh"]
                    + ["-work", as_tcl_value(lib)]
                    + compile_args
                    + [as_tcl_value(v) for v in src]
                )

        if self.verilog_sources:
            compile_args = self.compile_args + self.verilog_compile_args
            if self.timescale:
                compile_args += ["-timescale", self.timescale]

            for lib, src in self.verilog_sources.items():
                cmd.append(["vlib", as_tcl_value(lib)])
                cmd.append(
                    ["vlog", "-mixedsvvh"]
                    + ([] if self.force_compile else ["-incr"])
                    + ["-work", as_tcl_value(lib)]
                    + ["+define+COCOTB_SIM"]
                    + ["-sv"]
                    + self.get_define_commands(self.defines)
                    + self.get_include_commands(self.includes)
                    + compile_args
                    + [as_tcl_value(v) for v in src]
                )

        if not self.compile_only:
            if self.toplevel_lang == "vhdl":
                cmd.append(
                    ["vsim"]
                    + ["-gui" if self.gui else "-c"]
                    + ["-onfinish", "stop" if self.gui else "exit"]
                    + [
                        "-foreign",
                        "cocotb_init " + as_tcl_value(cocotb.config.lib_name_path("fli", "questa")),
                    ]
                    + self.simulation_args
                    + [as_tcl_value(v) for v in self.get_parameter_commands(self.parameters)]
                    + self.toplevel
                    + ["-do", do_script]
                )
                if self.verilog_sources:
                    self.env["GPI_EXTRA"] = cocotb.config.lib_name_path("vpi", "questa") + ":cocotbvpi_entry_point"
            else:
                cmd.append(
                    ["vsim"]
                    + ["-gui" if self.gui else "-c"]
                    + ["-onfinish", "stop" if self.gui else "exit"]
                    + [
                        "-pli",
                        as_tcl_value(cocotb.config.lib_name_path("vpi", "questa")),
                    ]
                    + self.simulation_args
                    + [as_tcl_value(v) for v in self.get_parameter_commands(self.parameters)]
                    + self.toplevel
                    + [as_tcl_value(v) for v in self.plus_args]
                    + ["-do", do_script]
                )
                if self.vhdl_sources:
                    self.env["GPI_EXTRA"] = cocotb.config.lib_name_path("fli", "questa") + ":cocotbfli_entry_point"

        return cmd


class Modelsim(Questa):
    # Understood to be the same as Questa - for now.
    pass


class Ius(Simulator):
    def __init__(self, *argv, **kwargs):
        super().__init__(*argv, **kwargs)

        self.env["GPI_EXTRA"] = cocotb.config.lib_name_path("vhpi", "ius") + ":cocotbvhpi_entry_point"

    def get_include_commands(self, includes):
        include_cmd = []
        for dir in includes:
            include_cmd += ["-incdir", dir]

        return include_cmd

    def get_define_commands(self, defines):
        defines_cmd = []
        for define in defines:
            defines_cmd += ["-define", define]

        return defines_cmd

    def get_parameter_commands(self, parameters):
        parameters_cmd = []
        for name, value in parameters.items():
            if self.toplevel_lang == "vhdl":
                parameters_cmd.append("-generic")
                parameters_cmd.append('"' + self.toplevel_module + "." + name + "=>" + str(value) + '"')
            else:
                parameters_cmd.append("-defparam")
                parameters_cmd.append('"' + self.toplevel_module + "." + name + "=" + str(value) + '"')

        return parameters_cmd

    def build_command(self):

        assert (
            not self.verilog_compile_args and not self.vhdl_compile_args
        ), "'Ius' simulator does not allow HDL specific compile arguments."

        out_file = os.path.join(self.sim_dir, "INCA_libs", "history")

        cmd = []

        if self.outdated(out_file, self.verilog_sources_flat + self.vhdl_sources_flat) or self.force_compile:
            cmd_elab = (
                [
                    "irun",
                    "-64",
                    "-elaborate",
                    "-define",
                    "COCOTB_SIM=1",
                    "-loadvpi",
                    cocotb.config.lib_name_path("vpi", "ius") + ":vlog_startup_routines_bootstrap",
                    "-plinowarn",
                    "-access",
                    "+rwc",
                    "-top",
                    self.toplevel_module,
                ]
                + self.get_define_commands(self.defines)
                + self.get_include_commands(self.includes)
                + self.get_parameter_commands(self.parameters)
                + self.compile_args
                + self.verilog_sources_flat
                + self.vhdl_sources_flat
            )
            cmd.append(cmd_elab)

        else:
            self.logger.warning("Skipping compilation:" + out_file)

        if not self.compile_only:
            cmd_run = (
                ["irun", "-64", "-R", ("-gui" if self.gui else "")]
                + self.simulation_args
                + self.get_parameter_commands(self.parameters)
                + self.plus_args
            )
            cmd.append(cmd_run)

        return cmd


class Xcelium(Simulator):
    def __init__(self, *argv, **kwargs):
        super().__init__(*argv, **kwargs)

        self.env["GPI_EXTRA"] = cocotb.config.lib_name_path("vhpi", "xcelium") + ":cocotbvhpi_entry_point"

    def get_include_commands(self, includes):
        include_cmd = []
        for dir in includes:
            include_cmd += ["-incdir", dir]

        return include_cmd

    def get_define_commands(self, defines):
        defines_cmd = []
        for define in defines:
            defines_cmd += ["-define", define]

        return defines_cmd

    def get_parameter_commands(self, parameters):
        parameters_cmd = []
        for name, value in parameters.items():
            if self.toplevel_lang == "vhdl":
                parameters_cmd.extend(("-generic", '"' + self.toplevel_module + "." + name + "=>" + str(value) + '"'))

            else:
                parameters_cmd.extend(("-defparam", '"' + self.toplevel_module + "." + name + "=" + str(value) + '"'))

        return parameters_cmd

    def build_command(self):

        assert (
            not self.verilog_compile_args and not self.vhdl_compile_args
        ), "'Xcelium' simulator does not allow HDL specific compile arguments."

        out_file = os.path.join(self.sim_dir, "INCA_libs", "history")

        cmd = []

        if self.outdated(out_file, self.verilog_sources_flat + self.vhdl_sources_flat) or self.force_compile:

            cmd_elab = (
                [
                    "xrun",
                    "-64",
                    "-elaborate",
                    "-define",
                    "COCOTB_SIM=1",
                    "-loadvpi",
                    cocotb.config.lib_name_path("vpi", "xcelium") + ":vlog_startup_routines_bootstrap",
                    "-plinowarn",
                    "-access",
                    "+rwc",
                    "-top",
                    self.toplevel_module,
                ]
                + self.get_define_commands(self.defines)
                + self.get_include_commands(self.includes)
                + self.get_parameter_commands(self.parameters)
                + self.compile_args
                + self.verilog_sources_flat
                + self.vhdl_sources_flat
            )
            if self.timescale:
                cmd_elab += ["-timescale", self.timescale]

            cmd.append(cmd_elab)

        else:
            self.logger.warning(f"Skipping compilation:{out_file}")

        if not self.compile_only:
            cmd_run = (
                ["xrun", "-64", "-R", ("-gui" if self.gui else "")]
                + self.simulation_args
                + self.get_parameter_commands(self.parameters)
                + self.plus_args
            )
            cmd.append(cmd_run)

        return cmd


class Vcs(Simulator):
    def get_include_commands(self, includes):
        return [f"+incdir+{dir}" for dir in includes]

    def get_define_commands(self, defines):
        return [f"+define+{define}" for define in defines]

    def get_parameter_commands(self, parameters):
        return [f"-pvalue+{self.toplevel_module}/{name}={str(value)}" for name, value in parameters.items()]

    def build_command(self):

        pli_cmd = "acc+=rw,wn:*"

        cmd = []

        do_file_path = os.path.join(self.sim_dir, "pli.tab")
        with open(do_file_path, "w") as pli_file:
            pli_file.write(pli_cmd)

        compile_args = self.compile_args + self.verilog_compile_args
        debug_access = "-debug_access"
        if self.waves:
            debug_access += "+all+dmptf"
            compile_args += ["-kdb", "-debug_region+cell"]

        simv_path = os.path.join(self.sim_dir, self.module)
        cmd_build = (
            [
                "vcs",
                "-full64",
                "-sverilog",
                debug_access,
                "-P",
                "pli.tab",
                "+define+COCOTB_SIM=1",
                "-load",
                cocotb.config.lib_name_path("vpi", "vcs"),
                "-top",
                self.toplevel_module,
            ]
            + self.get_define_commands(self.defines)
            + self.get_include_commands(self.includes)
            + self.get_parameter_commands(self.parameters)
            + compile_args
            + self.verilog_sources_flat
            + ["-o", simv_path]
        )
        if self.timescale:
            cmd_build += [f"-timescale={self.timescale}"]
        else:
            cmd_build += [f"-timescale=1ns/1ps"]
        cmd.append(cmd_build)

        if not self.compile_only:
            cmd_run = [
                simv_path,
                "+define+COCOTB_SIM=1",
            ] + self.simulation_args
            if self.waves:
                ucli_do = os.path.join(self.sim_dir, f"{self.module}_ucli.do")
                with open(ucli_do, "w") as f:
                    f.write(f"fsdbDumpfile {simv_path}.fsdb; fsdbDumpvars 0 {self.toplevel_module}; run; quit;")
                cmd_run += ["+fsdb+all=on", "-ucli", "-do", ucli_do]
            if self.gui:
                cmd_run.append("-gui")
            cmd.append(cmd_run)

        return cmd


class Ghdl(Simulator):
    def get_parameter_commands(self, parameters):
        return [f"-g{name}={str(value)}" for name, value in parameters.items()]

    def build_command(self):

        ghdl_exec = shutil.which("ghdl")
        if ghdl_exec is None:
            raise ValueError("GHDL executable not found.")

        cmd = []

        out_file = os.path.join(self.sim_dir, self.toplevel_module)
        compile_args = self.compile_args + self.vhdl_compile_args

        if self.outdated(out_file, self.vhdl_sources) or self.force_compile:
            for lib, src in self.vhdl_sources.items():
                cmd.append(["ghdl", "-i"] + compile_args + [f"--work={lib}"] + src)

            cmd_elaborate = ["ghdl", "-m", f"--work={self.toplevel_library}"] + compile_args + [self.toplevel_module]
            cmd.append(cmd_elaborate)

        if self.waves:
            self.simulation_args.append(f"--wave={self.toplevel_module}.ghw")

        self.env["PATH"] += os.pathsep + os.path.join(os.path.dirname(os.path.dirname(ghdl_exec)), "lib")

        cmd_run = (
            ["ghdl", "-r", f"--work={self.toplevel_library}"]
            + compile_args
            + [self.toplevel_module]
            + ["--vpi=" + cocotb.config.lib_name_path("vpi", "ghdl")]
            + self.simulation_args
            + self.get_parameter_commands(self.parameters)
        )

        if not self.compile_only:
            cmd.append(cmd_run)

        return cmd


class Riviera(Simulator):
    def get_include_commands(self, includes):
        return ["+incdir+" + as_tcl_value(dir) for dir in includes]

    def get_define_commands(self, defines):
        return ["+define+" + as_tcl_value(define) for define in defines]

    def get_parameter_commands(self, parameters):
        return ["-g" + name + "=" + str(value) for name, value in parameters.items()]

    def build_command(self):

        self.rtl_library = self.toplevel_module

        do_script = "\nonerror {\n quit -code 1 \n} \n"

        out_file = os.path.join(self.sim_dir, self.rtl_library, self.rtl_library + ".lib")

        if self.outdated(out_file, self.verilog_sources_flat + self.vhdl_sources_flat) or self.force_compile:

            do_script += f"alib {as_tcl_value(self.rtl_library)} \n"

            if self.vhdl_sources:
                compile_args = self.compile_args + self.vhdl_compile_args
                do_script += "acom -work {RTL_LIBRARY} {EXTRA_ARGS} {VHDL_SOURCES}\n".format(
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    VHDL_SOURCES=" ".join(as_tcl_value(v) for v in self.vhdl_sources_flat),
                    EXTRA_ARGS=" ".join(as_tcl_value(v) for v in compile_args),
                )

            if self.verilog_sources:
                compile_args = self.compile_args + self.verilog_compile_args
                do_script += "alog -work {RTL_LIBRARY} +define+COCOTB_SIM -sv {DEFINES} {INCDIR} {EXTRA_ARGS} {VERILOG_SOURCES} \n".format(
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    VERILOG_SOURCES=" ".join(as_tcl_value(v) for v in self.verilog_sources_flat),
                    DEFINES=" ".join(self.get_define_commands(self.defines)),
                    INCDIR=" ".join(self.get_include_commands(self.includes)),
                    EXTRA_ARGS=" ".join(as_tcl_value(v) for v in compile_args),
                )
        else:
            self.logger.warning("Skipping compilation:" + out_file)

        if not self.compile_only:
            if self.toplevel_lang == "vhdl":
                do_script += "asim +access +w -interceptcoutput -O2 -loadvhpi {EXT_NAME} {EXTRA_ARGS} {RTL_LIBRARY}.{TOPLEVEL} \n".format(
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    TOPLEVEL=as_tcl_value(self.toplevel_module),
                    EXT_NAME=as_tcl_value(cocotb.config.lib_name_path("vhpi", "riviera") + ":vhpi_startup_routines_bootstrap"),
                    EXTRA_ARGS=" ".join(
                        as_tcl_value(v) for v in (self.simulation_args + self.get_parameter_commands(self.parameters))
                    ),
                )
                if self.verilog_sources:
                    self.env["GPI_EXTRA"] = cocotb.config.lib_name_path("vpi", "riviera") + "cocotbvpi_entry_point"
            else:
                do_script += "asim +access +w -interceptcoutput -O2 -pli {EXT_NAME} {EXTRA_ARGS} {RTL_LIBRARY}.{TOPLEVEL} {PLUS_ARGS} \n".format(
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    TOPLEVEL=as_tcl_value(self.toplevel_module),
                    EXT_NAME=as_tcl_value(cocotb.config.lib_name_path("vpi", "riviera")),
                    EXTRA_ARGS=" ".join(
                        as_tcl_value(v) for v in (self.simulation_args + self.get_parameter_commands(self.parameters))
                    ),
                    PLUS_ARGS=" ".join(as_tcl_value(v) for v in self.plus_args),
                )
                if self.vhdl_sources:
                    self.env["GPI_EXTRA"] = cocotb.config.lib_name_path("vhpi", "riviera") + ":cocotbvhpi_entry_point"

            if self.waves:
                do_script += "trace -recursive /*;"

            if not self.gui:
                do_script += "run -all \nexit"

        do_file = tempfile.NamedTemporaryFile(delete=False)
        do_file.write(do_script.encode())
        do_file.close()

        command = "riviera" if self.gui else "vsimsa"
        return [[command] + ["-do"] + ["do"] + [do_file.name]]


class Activehdl(Simulator):
    def get_include_commands(self, includes):
        return [f"+incdir+{as_tcl_value(dir)}" for dir in includes]

    def get_define_commands(self, defines):
        return [f"+define+{as_tcl_value(define)}" for define in defines]

    def get_parameter_commands(self, parameters):
        return [f"-g{name}={str(value)}" for name, value in parameters.items()]

    def build_script_compile(self):
        do_script = ""

        out_file = os.path.join(self.sim_dir, self.rtl_library, f"{self.rtl_library}.lib")

        if self.outdated(out_file, self.verilog_sources_flat + self.vhdl_sources_flat) or self.force_compile:

            do_script += f"alib {as_tcl_value(self.rtl_library)} \n"

            if self.vhdl_sources:
                compile_args = self.compile_args + self.vhdl_compile_args
                do_script += "acom -work {RTL_LIBRARY} {EXTRA_ARGS} {VHDL_SOURCES}\n".format(
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    VHDL_SOURCES=" ".join(as_tcl_value(v) for v in self.vhdl_sources_flat),
                    EXTRA_ARGS=" ".join(as_tcl_value(v) for v in compile_args),
                )

            if self.verilog_sources:
                compile_args = self.compile_args + self.verilog_compile_args
                do_script += "alog {RTL_LIBRARY} +define+COCOTB_SIM -sv {DEFINES} {INCDIR} {EXTRA_ARGS} {VERILOG_SOURCES} \n".format(
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    VERILOG_SOURCES=" ".join(as_tcl_value(v) for v in self.verilog_sources_flat),
                    DEFINES=" ".join(self.get_define_commands(self.defines)),
                    INCDIR=" ".join(self.get_include_commands(self.includes)),
                    EXTRA_ARGS=" ".join(as_tcl_value(v) for v in compile_args),
                )
        else:
            self.logger.warning(f"Skipping compilation:{out_file}")

        return do_script

    def build_script_sim(self):

        do_script = ""

        if self.toplevel_lang == "vhdl":
            do_script += f"set worklib {as_tcl_value(self.rtl_library)}" + "\n"
            do_script += (
                'asim +access +w -interceptcoutput -O2 -loadvhpi "{EXT_NAME}" {EXTRA_ARGS} {TOPLEVEL} \n'.format(
                    RTL_LIBRARY=as_tcl_value(self.rtl_library),
                    TOPLEVEL=as_tcl_value(self.toplevel_module),
                    EXT_NAME=as_tcl_value(
                        cocotb.config.lib_name_path("vhpi", "activehdl") + ":vhpi_startup_routines_bootstrap"
                    ),
                    EXTRA_ARGS=" ".join(self.simulation_args + self.get_parameter_commands(self.parameters)),
                )
            )
            if self.verilog_sources:
                self.env["GPI_EXTRA"] = cocotb.config.lib_name_path("vpi", "activehdl") + "cocotbvpi_entry_point"
        else:
            do_script += 'asim +access +w -interceptcoutput -O2 -pli "{EXT_NAME}" {EXTRA_ARGS} {RTL_LIBRARY}.{TOPLEVEL} {PLUS_ARGS} \n'.format(
                RTL_LIBRARY=as_tcl_value(self.rtl_library),
                TOPLEVEL=as_tcl_value(self.toplevel_module),
                EXT_NAME=as_tcl_value(cocotb.config.lib_name_path("vpi", "activehdl")),
                EXTRA_ARGS=" ".join(
                    as_tcl_value(v) for v in (self.simulation_args + self.get_parameter_commands(self.parameters))
                ),
                PLUS_ARGS=" ".join(as_tcl_value(v) for v in self.plus_args),
            )
            if self.vhdl_sources:
                self.env["GPI_EXTRA"] = cocotb.config.lib_name_path("vhpi", "activehdl") + ":cocotbvpi_entry_point"

        if self.waves:
            do_script += "trace -recursive /*;"

        return do_script

    def build_script_run(self):

        return "run -all \nexit"

    def build_command(self):

        self.rtl_library = self.toplevel_module

        do_script = "\nonerror {\n quit -code 1 \n} \n"

        do_script += self.build_script_compile()
        if not self.compile_only:
            do_script += self.build_script_sim()
            do_script += self.build_script_run()

        do_file = tempfile.NamedTemporaryFile(delete=False)
        do_file.write(do_script.encode())
        do_file.close()

        return [["vsimsa"] + ["-do"] + [do_file.name]]


class Verilator(Simulator):
    def __init__(self, make_args=None, *argv, **kwargs):
        super().__init__(*argv, **kwargs)

        if make_args is None:
            make_args = []

        self.make_args = make_args

        if self.vhdl_sources:
            raise ValueError("This simulator does not support VHDL")

    def get_include_commands(self, includes):
        return [f"-I{dir}" for dir in includes]

    def get_define_commands(self, defines):
        return [f"-D{define}" for define in defines]

    def get_parameter_commands(self, parameters):
        return [f"-G{name}={str(value)}" for name, value in parameters.items()]

    def build_command(self):

        cmd = []

        out_file = os.path.join(self.sim_dir, self.toplevel_module)
        verilator_cpp = os.path.join(
            os.path.dirname(cocotb.__file__),
            "share",
            "lib",
            "verilator",
            "verilator.cpp",
        )

        verilator_exec = shutil.which("verilator")
        if verilator_exec is None:
            raise ValueError("Verilator executable not found.")

        compile_args = self.compile_args + self.verilog_compile_args

        if self.waves:
            compile_args += ["--trace-fst", "--trace-structs"]

        if self.timescale:
            compile_args += ["--timescale", self.timescale]

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
                self.toplevel_module,
                "--vpi",
                "--public-flat-rw",
                "--prefix",
                "Vtop",
                "-o",
                self.toplevel_module,
                "-LDFLAGS",
                "-Wl,-rpath,{LIB_DIR} -L{LIB_DIR} -lcocotbvpi_verilator".format(LIB_DIR=self.lib_dir),
            ]
            + compile_args
            + self.get_define_commands(self.defines)
            + self.get_include_commands(self.includes)
            + self.get_parameter_commands(self.parameters)
            + [verilator_cpp]
            + self.verilog_sources_flat
        )

        cmd.append(["make", "-C", self.sim_dir, "-f", "Vtop.mk"] + self.make_args)

        if not self.compile_only:
            cmd.append([out_file] + self.plus_args)

        return cmd


def run(simulator=None, **kwargs):

    __tracebackhide__ = True  # Hide the traceback when using PyTest.

    sim_env = os.getenv("SIM")

    # priority, highest first, is: env, kwarg, "icarus"
    if sim_env is None:
        sim_env = "icarus" if simulator is None else simulator
    elif simulator is not None:
        logging.warning(f"'SIM={sim_env}' overrides kwarg 'simulator={simulator}'")

    supported_sim = [
        "icarus",
        "questa",
        "modelsim",
        "ius",
        "xcelium",
        "vcs",
        "ghdl",
        "riviera",
        "activehdl",
        "verilator",
    ]

    if sim_env not in supported_sim:
        raise NotImplementedError("Set SIM variable. Supported: " + ", ".join(supported_sim))

    if sim_env == "icarus":
        sim = Icarus(**kwargs)
    elif sim_env == "questa":
        sim = Questa(**kwargs)
    elif sim_env == "modelsim":
        sim = Modelsim(**kwargs)
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
    elif sim_env == "activehdl":
        sim = Activehdl(**kwargs)
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
