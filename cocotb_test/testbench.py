import argparse
import cocotb_test


class Testbench:
    def __init__(self):
        self.template_parameter_list = []
        self.template_parameters = {}

        self.simulator = None
        self.toplevel = None
        self.module = None
        self.work_dir = None
        self.python_search = None
        self.toplevel_lang = "verilog"
        self.verilog_sources = None
        self.vhdl_sources = None
        self.includes = None
        self.defines = None
        self.parameters = {}
        self.compile_args = None
        self.vhdl_compile_args = None
        self.verilog_compile_args = None
        self.sim_args = None
        self.extra_args = None
        self.plus_args = None
        self.force_compile = False
        self.testcase = None
        self.sim_build = "sim_build"
        self.seed = None
        self.extra_env = None
        self.compile_only = False
        self.waves = None
        self.timescale = None
        self.gui = False
        self.simulation_args = None
        self.simulator_kwargs = {}

    def add_template_parameter(self, name, val):
        self.template_parameter_list.append(name)
        self.template_parameters[name] = val

    def main(self):
        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser.add_argument("--simulator", default=None, help="specify simulator")
        parser.add_argument("--waves", default=False, action="store_true", help="enable waveform dumping")

        for name, val in self.template_parameters.items():
            parser.add_argument(f"--param_{name.lower()}", default=str(val), metavar=name, help=f"set module parameter {name}")

        args = parser.parse_args()

        if args.simulator:
            self.simulator = args.simulator

        if args.waves:
            self.waves = True

        parameters = {}

        for name, val in self.template_parameters.items():
            arg_val = getattr(args, f"param_{name.lower()}")
            if arg_val is not None:
                parameters[name] = arg_val

        self.run(parameters=parameters)

    def run(self, parameters=None):

        sim_parameters = {}

        for name in self.template_parameters:
            if name in parameters:
                val = parameters[name]
            else:
                val = self.template_parameters[name]

            sim_parameters[name] = eval(str(val), {'__builtins__': None}, sim_parameters)

        cocotb_test.simulator.run(
            simulator=self.simulator,
            toplevel=self.toplevel,
            module=self.module,
            work_dir=self.work_dir,
            python_search=self.python_search,
            toplevel_lang=self.toplevel_lang,
            verilog_sources=self.verilog_sources,
            vhdl_sources=self.vhdl_sources,
            includes=self.includes,
            defines=self.defines,
            parameters=sim_parameters,
            compile_args=self.compile_args,
            vhdl_compile_args=self.vhdl_compile_args,
            verilog_compile_args=self.verilog_compile_args,
            sim_args=self.sim_args,
            extra_args=self.extra_args,
            plus_args=self.plus_args,
            force_compile=self.force_compile,
            testcase=self.testcase,
            sim_build=self.sim_build,
            seed=self.seed,
            extra_env=self.extra_env,
            compile_only=self.compile_only,
            waves=self.waves,
            timescale=self.timescale,
            gui=self.gui,
            simulation_args=self.simulation_args
        )
