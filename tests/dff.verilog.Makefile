#

CWD=$(shell pwd)

TOPLEVEL_LANG=verilog
VERILOG_SOURCES =$(CWD)/dff.sv

TOPLEVEL=dff_test
MODULE=dff_cocotb

ifeq ($(SIM),questa)
SIM_ARGS=-t 1ps
endif

include $(shell cocotb --inc-makefile)

