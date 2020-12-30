# cocotb-test
[![Build Status](https://dev.azure.com/themperek/themperek/_apis/build/status/themperek.cocotb-test?branchName=master)](https://dev.azure.com/themperek/themperek/_build/latest?definitionId=2&branchName=master)
[![PyPI version](https://badge.fury.io/py/cocotb-test.svg)](https://badge.fury.io/py/cocotb-test)

``cocotb-test`` provides standard python unit testing capabilities for [cocotb](https://github.com/cocotb/cocotb)
- allow the look and feel of Python unit testing
- remove the need for Makefiles (includes Makefile compatibility mode)
- allow easy customization of simulation flow
- allow to use [pytest-xdist](https://pypi.org/project/pytest-xdist/) or [pytest-parallel](https://github.com/browsertron/pytest-parallel) for parallel runs

# Usage:

- Install [cocotb](https://docs.cocotb.org/).

- Install simulator (for Icarus Verilog with conda):
```bash
conda install -c conda-forge iverilog
```
- Install the package via [pip](https://pip.pypa.io/en/stable/user_guide/):
```bash
pip install cocotb-test
```
&emsp;or development version
```bash
pip install -v https://github.com/themperek/cocotb-test/archive/master.zip
```
&emsp;or
```bash
git clone https://github.com/themperek/cocotb-test.git
pip install -v -e cocotb-test
```

- Create a `test_dff.py` file (check [test folder](https://github.com/themperek/cocotb-test/tree/master/tests) for more examples):
```python
from cocotb_test.simulator import run
def test_dff():
    run(
        verilog_sources=["dff.v"], # sources
        toplevel="dff",            # top level HDL
        module="dff_cocotb"        # name of cocotb test module
    )
```

- Run [pytest](https://docs.pytest.org/en/latest/contents.html) (need `dff.v` and `dff_cocotb.py` in same directory where running `pytest`): 
```bash
SIM=icarus pytest -o log_cli=True test_dff.py
```

- To clean (remove all `sim_build` folders): 
```bash
cocotb-clean -r
```
### Arguments for `simulator.run`:

* `toplevel`: Use this to indicate the instance in the hierarchy to use as the DUT.
* `module`: The name of the module(s) to search for test functions (see [MODULE](https://docs.cocotb.org/en/stable/building.html?#envvar-MODULE) ).

* `python_search` : List of additional directoreis to search for python/cocotb modules.
* `verilog_sources`: A list of the Verilog source files to include. 
* `vhdl_sources`: A list of the VHDL source files to include. 
* `toplevel_lang`: see [TOPLEVEL_LANG](https://docs.cocotb.org/en/stable/building.html?#var-TOPLEVEL_LANG). (default: `verilog`)
* `includes`: A list of directories to search for includes. 
* `defines`: A list of the defines. 
* `parameters`: A dictionary of top-level parameters/generics. 
* `compile_args`: Any arguments or flags to pass to the compile stage of the simulation.
* `sim_args`: Any arguments or flags to pass to the execution of the compiled simulation.
* `extra_args`: Passed to both the compile and execute phases of simulators.
* `plus_args`: plusargs arguments passed to simulator.
* `force_compile`: Force compilation even if sources did not change. (default: `False`)
* `compile_only`: Only compile sources. Do not run simulation. (default: `False`)
* `testcase`: The name of the test function(s) to run (see [TESTCASE](https://docs.cocotb.org/en/stable/building.html?#envvar-TESTCASE) ).
* `sim_build`: The directory used to compile the tests. (default: `sim_build`)
* `work_dir`: The directory used to tun the tests. (default: same as `sim_build` argument)
* `seed`: Seed the Python random module to recreate a previous test stimulus (see [RANDOM_SEED](https://docs.cocotb.org/en/stable/building.html?#envvar-RANDOM_SEED) ).
* `extra_env`: A dictionary of extra environment variables set in simulator process.
* `waves`: Enable wave dumps (not all simulators supported).
* `gui`: Starts in gui mode (not all simulators supported).


### Environmental variables:

* `SIM`: Selects which simulator to use. (default: `icarus`)
* `WAVES`: Overwrite enable wave dumps argument. Example use `WAVES=1 pytest test_dff.py`.

### pytest arguments

* `cocotbxml`: Combines and saves junitxml reports from cocotb tests.  Example use `pytest --cocotbxml=test-cocotb.xml`.

### Tips and tricks:

* List all available test:
```bash
pytest --collect-only
```

* Run only selected test:
```bash
pytest -k test_dff_verilog_param[3]
```

* Test parameterization (for more see: [test_parameters.py](https://github.com/themperek/cocotb-test/blob/master/tests/test_parameters.py) )

```python
@pytest.mark.parametrize("width", [{"WIDTH_IN": "8"}, {"WIDTH_IN": "16"}])
def test_dff_verilog_testcase(width):
    run(
        ...
        parameters=width,
        sim_build="sim_build/" + "_".join(("{}={}".format(*i) for i in width.items())),
    )
```

*  Run test in parallel (after installing  [pytest-xdist](https://pypi.org/project/pytest-xdist/) )
```bash
pytest -n NUMCPUS
```

# Running (some) tests and examples from cocotb
For cocotb tests/examples install cocotb in editable mode  
```bash
git clone https://github.com/potentialventures/cocotb.git
pip install -e cocotb
SIM=icarus pytest -o log_cli=True --junitxml=test-results.xml --cocotbxml=test-cocotb.xml tests
```

# Related resources
- [pytest logging](https://docs.pytest.org/en/stable/logging.html) - pytest logging documentation 
- [pytest-xdist](https://pypi.org/project/pytest-xdist/) - test run parallelization (see [test_parallel](https://github.com/themperek/cocotb-test/blob/master/tests/test_parallel.py))
- [pytest-parallel](https://github.com/browsertron/pytest-parallel) - parallel and concurrent testing  (see [test_parallel](https://github.com/themperek/cocotb-test/blob/master/tests/test_parallel.py))
- [pytest-html](https://github.com/pytest-dev/pytest-html) - generates a HTML report for the test results
- [pytest-sugar](https://github.com/Teemu/pytest-sugar/) - sugar
