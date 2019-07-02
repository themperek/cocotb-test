import subprocess
import os
import sys

if sys.version_info.major >= 3:
    from tkinter import _stringify as as_tcl_value
else:
    from Tkinter import _stringify as as_tcl_value


class Simulator:
    def __init__(
        self,
        run_dir,
        sim_dir,
        lib_dir,
        lib_ext,
        toplevel,
        verilog_sources=[],
        vhdl_sources=[],
        includes=[],
        defines=[],
        extra_compile_args=[],
        extra_simulation_args=[],
        **kwargs
    ):

        self.run_dir = run_dir
        self.sim_dir = sim_dir
        self.lib_dir = lib_dir
        self.lib_ext = lib_ext

        self.toplevel = toplevel
        self.verilog_sources = self.get_abs_paths(verilog_sources)
        self.vhdl_sources = self.get_abs_paths(vhdl_sources)
        self.includes = self.get_abs_paths(includes)

        self.defines = defines
        self.extra_compile_args = extra_compile_args
        self.extra_simulation_args = extra_simulation_args

        for arg in kwargs:
            setattr(self, arg, kwargs[arg])

    def build_command(self):
        pass

    def run(self):
        cmds = self.build_command()
        self.execute(cmds)

    def get_include_commands(self, includes):
        pass

    def get_define_commands(self, defines):
        pass

    def get_abs_paths(self, paths):
        paths_abs = []
        for path in paths:
            if os.path.isabs(path):
                paths_abs.append(path)
            else:
                paths_abs.append(os.path.abspath(os.path.join(self.run_dir, path)))

        return paths_abs

    def execute(self, cmds):
        for cmd in cmds:
            print(" ".join(cmd))
            process = subprocess.check_call(cmd, cwd=self.sim_dir)


class Icarus(Simulator):
    def __init__(self, *argv, **kwargs):
        super(Icarus, self).__init__(*argv, **kwargs)

        if self.vhdl_sources:
            raise ValueError("This simulator does not support VHDL")

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

    def build_command(self):

        sim_compile_file = os.path.join(self.sim_dir, "sim.vvp")

        cmd_compile = (
            [
                "iverilog",
                "-o",
                sim_compile_file,
                "-D",
                "COCOTB_SIM=1",
                "-s",
                self.toplevel,
                "-g2012",
            ]
            + self.get_define_commands(self.defines)
            + self.get_include_commands(self.includes)
            + self.verilog_sources
        )

        cmd_run = ["vvp", "-M", self.lib_dir, "-m", "gpivpi", sim_compile_file]

        return [cmd_compile, cmd_run]


'''
def _run_vcs(
    toplevel, libs_dir, verilog_sources_abs, sim_build_dir, ext_name, include_dir_abs
):

    pli_cmd = "acc+=rw,wn:*"

    inculde_dir_cmd = []
    for dir in include_dir_abs:
        inculde_dir_cmd.append("+incdir+" + dir)

    do_file_path = os.path.join(sim_build_dir, "pli.tab")
    with open(do_file_path, "w") as pli_file:
        pli_file.write(pli_cmd)

    comp_cmd = (
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
            os.path.join(libs_dir, "libvpi." + ext_name),
        ]
        + inculde_dir_cmd
        + verilog_sources_abs
    )
    print(" ".join(comp_cmd))
    process = subprocess.check_call(comp_cmd, cwd=sim_build_dir)

    cmd = [os.path.join(sim_build_dir, "simv"), "+define+COCOTB_SIM=1"]
    print(" ".join(cmd))
    process = subprocess.check_call(cmd, cwd=sim_build_dir)


def _run_ius(
    toplevel,
    libs_dir,
    verilog_sources_abs,
    vhdl_sources_abs,
    sim_build_dir,
    ext_name,
    include_dir_abs,
):

    os.environ["GPI_EXTRA"] = "vhpi"

    include_dir_cmd = []
    for dir in include_dir_abs:
        include_dir_cmd.append("+incdir+" + dir)

    cmd = (
        [
            "irun",
            "-64",
            "-define",
            "COCOTB_SIM=1",
            "-v93",
            "-loadpli1",
            os.path.join(libs_dir, "libvpi." + ext_name)
            + ":vlog_startup_routines_bootstrap",
            "-plinowarn",
            "+access+rwc",
            "-top",
            toplevel,
        ]
        + include_dir_cmd
        + vhdl_sources_abs
        + verilog_sources_abs
    )

    print(" ".join(cmd))
    process = subprocess.check_call(cmd, cwd=sim_build_dir)


def _run_icarus(
    toplevel, libs_dir, verilog_sources_abs, sim_build_dir, include_dir_abs
):

    sim_compile_file = os.path.join(sim_build_dir, "sim.vvp")

    inculde_dir_cmd = []
    for dir in include_dir_abs:
        inculde_dir_cmd.append("-I")
        inculde_dir_cmd.append(dir)

    comp_cmd = (
        [
            "iverilog",
            "-o",
            sim_compile_file,
            "-D",
            "COCOTB_SIM=1",
            "-s",
            toplevel,
            "-g2012",
        ]
        + inculde_dir_cmd
        + verilog_sources_abs
    )
    print(" ".join(comp_cmd))
    process = subprocess.check_call(comp_cmd)

    cmd = ["vvp", "-M", libs_dir, "-m", "gpivpi", sim_compile_file]
    print(" ".join(cmd))
    process = subprocess.check_call(cmd, cwd=sim_build_dir)


def _run_ghdl(
    toplevel, libs_dir, vhdl_sources_abs, sim_build_dir, include_dir_abs, ext_name
):

    inculde_dir_cmd = []
    for dir in include_dir_abs:
        inculde_dir_cmd.append("-I")
        inculde_dir_cmd.append(dir)

    for source_file in vhdl_sources_abs:
        comp_cmd = ["ghdl", "-a", source_file]
        print(" ".join(comp_cmd))
        process = subprocess.check_call(comp_cmd, cwd=sim_build_dir)

    comp_cmd = ["ghdl", "-e", toplevel]
    print(" ".join(comp_cmd))
    process = subprocess.check_call(comp_cmd, cwd=sim_build_dir)

    cmd = [
        "ghdl",
        "-r",
        toplevel,
        "--vpi=" + os.path.join(libs_dir, "libvpi." + ext_name),
    ]
    print(" ".join(cmd))
    process = subprocess.check_call(cmd, cwd=sim_build_dir)


def _run_questa(
    toplevel,
    libs_dir,
    verilog_sources_abs,
    vhdl_sources_abs,
    sim_build_dir,
    ext_name,
    toplevel_lang,
    include_dir_abs,
):

    inculde_dir_cmd = []
    for dir in include_dir_abs:
        inculde_dir_cmd.append("+incdir+" + dir)

    do_script = """# Autogenerated file
    onerror {
        quit -f -code 1
    }
    """

    if vhdl_sources_abs:
        do_script += "vcom -mixedsvvh +define+COCOTB_SIM {INCDIR} {VHDL_SOURCES}\n".format(
            VHDL_SOURCES=" ".join(as_tcl_value(v) for v in vhdl_sources_abs),
            INCDIR=" ".join(as_tcl_value(v) for v in inculde_dir_cmd),
        )
        os.environ["GPI_EXTRA"] = "fli"

    if verilog_sources_abs:
        do_script += "vlog -mixedsvvh +define+COCOTB_SIM -sv {INCDIR} {VERILOG_SOURCES}\n".format(
            VERILOG_SOURCES=" ".join(as_tcl_value(v) for v in verilog_sources_abs),
            INCDIR=" ".join(as_tcl_value(v) for v in inculde_dir_cmd),
        )

    if toplevel_lang == "vhdl":
        do_script += "vsim -onfinish exit -foreign {EXT_NAME} {TOPLEVEL}\n".format(
            TOPLEVEL=as_tcl_value(toplevel),
            EXT_NAME=as_tcl_value(
                "cocotb_init {}".format(os.path.join(libs_dir, "libfli." + ext_name))
            ),
        )
    else:
        do_script += "vsim -onfinish exit -pli {EXT_NAME} {TOPLEVEL}\n".format(
            TOPLEVEL=as_tcl_value(toplevel),
            EXT_NAME=as_tcl_value(os.path.join(libs_dir, "libvpi." + ext_name)),
        )

    do_script += """log -recursive /*
    onbreak resume
    run -all
    quit
    """

    do_file_path = os.path.join(sim_build_dir, "runsim.do")
    with open(do_file_path, "w") as do_file:
        do_file.write(do_script)

    cmd = ["vsim", "-c", "-do", "runsim.do"]
    print(" ".join(cmd))
    process = subprocess.check_call(cmd, cwd=sim_build_dir)
'''
