
all: test

export VERILOG_SOURCES
export VHDL_SOURCES
export TOPLEVEL_LANG
export TOPLEVEL
export MODULE
export SIM_ARGS

PYTHONPATH += $(dir $(realpath $(firstword $(MAKEFILE_LIST))))
export PYTHONPATH

test:
	cocotb-run --env

clean:
	cocotb-clean
