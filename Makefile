# SPDX-FileCopyrightText: 2025 IObundle
#
# SPDX-License-Identifier: MIT

CORE := iob_soc

SIMULATOR ?= xcelium
SYNTHESIZER ?= yosys
LINTER ?= spyglass
BOARD ?= cyclonev_gt_dk

BUILD_DIR ?= $(shell nix-shell --run "py2hwsw $(CORE) print_build_dir")

USE_INTMEM ?= 1
USE_EXTMEM ?= 0
INIT_MEM ?= 1

# TMR config generation parameters
# for fatori-v usage
TMR_SCRIPT   		?= select_tmr.py
TMR_WRAP_FILE     	?= wrapped_registers.json
TMR_PERCENT 		?= 50
TMR_SEED     		?=
TMR_FORCED_FILE   	?= forced_enabled_files.json         	# JSON with forced-enable registers/files
TMR_FILE_INCLUDE  	?= 1        							# set to 1 to include forced regs in percentage
TMR_DIS_FLAGS     	?= dis_flags.json         				# JSON with disable flags
VERBOSE           	?= 1        							# set to 1 for debug output

VERSION ?=$(shell cat iob_soc.py | grep version | cut -d '"' -f 4)

ifneq ($(DEBUG),)
EXTRA_ARGS +=--debug_level $(DEBUG)
endif

setup:
	nix-shell --run "py2hwsw $(CORE) setup --no_verilog_lint --py_params 'use_intmem=$(USE_INTMEM):use_extmem=$(USE_EXTMEM):init_mem=$(INIT_MEM)' $(EXTRA_ARGS)"

ibex-setup:
	@echo "=== Generating Ibex RTL files ==="
	$(MAKE) -C submodules/iob_ibex generate-ibex

	@echo "=== Copying Ibex files to build directory ==="
	$(MAKE) -C submodules/iob_ibex copy-ibex COPY_DIR=../../../$(CORE)_V$(VERSION)/hardware/src/

	@echo "=== Generating TMR configuration ==="
	$(MAKE) -C submodules/iob_ibex tmr-config \
		TMR_FINAL_FOLDER=../../../$(CORE)_V$(VERSION)/hardware/src \
		TMR_SCRIPT=$(TMR_SCRIPT) \
		TMR_WRAP_FILE=$(TMR_WRAP_FILE) \
		TMR_FORCED_FILE=$(TMR_FORCED_FILE) \
		TMR_FILE_INCLUDE=$(TMR_FILE_INCLUDE) \
		TMR_DIS_FLAGS=$(TMR_DIS_FLAGS) \
		TMR_PERCENT=$(TMR_PERCENT) \
		TMR_SEED=$(TMR_SEED) \
		VERBOSE=$(VERBOSE)

	@echo "=== Cleaning temporary Ibex build files ==="
	$(MAKE) -C submodules/iob_ibex clean-ibex


pc-emul-run:
	nix-shell --run "make clean setup"
	make ibex-setup
	nix-shell --run "make -C ../$(CORE)_V$(VERSION)/ pc-emul-run"

pc-emul-test:
	nix-shell --run "make clean setup"
	make ibex-setup
	nix-shell --run "make -C ../$(CORE)_V$(VERSION)/ pc-emul-run"

sim-run:
	nix-shell --run "make clean setup"
	make ibex-setup
	nix-shell --run "make -C ../$(CORE)_V$(VERSION)/ sim-run SIMULATOR=$(SIMULATOR)"

sim-test:
	nix-shell --run "make clean setup USE_INTMEM=1 USE_EXTMEM=0 INIT_MEM=1"
	make ibex-setup
	nix-shell --run "make -C ../$(CORE)_V$(VERSION)/ sim-run SIMULATOR=icarus"
	nix-shell --run "make clean setup USE_INTMEM=1 USE_EXTMEM=0 INIT_MEM=0"
	make ibex-setup
	nix-shell --run "make -C ../$(CORE)_V$(VERSION)/ sim-run SIMULATOR=verilator"
	nix-shell --run "make clean setup USE_INTMEM=1 USE_EXTMEM=1 INIT_MEM=0"
	make ibex-setup
	nix-shell --run "make -C ../$(CORE)_V$(VERSION)/ sim-run SIMULATOR=verilator"
	nix-shell --run "make clean setup USE_INTMEM=0 USE_EXTMEM=1 INIT_MEM=0"
	make ibex-setup
	nix-shell --run "make -C ../$(CORE)_V$(VERSION)/ sim-run SIMULATOR=verilator"

fpga-run:
	nix-shell --run "make clean setup"
	make ibex-setup 
	nix-shell "make -C ../$(CORE)_V$(VERSION)/ fpga-fw-build BOARD=$(BOARD)"
	make -C ../$(CORE)_V$(VERSION)/ fpga-run BOARD=$(BOARD)

fpga-test:
	make clean setup fpga-run BOARD=iob_cyclonev_gt_dk USE_INTMEM=1 USE_EXTMEM=0 INIT_MEM=1 
	make clean setup fpga-run BOARD=iob_cyclonev_gt_dk USE_INTMEM=0 USE_EXTMEM=1 INIT_MEM=0 
	make clean setup fpga-run BOARD=iob_aes_ku040_db_g USE_INTMEM=1 USE_EXTMEM=0 INIT_MEM=1 
	make clean setup fpga-run BOARD=iob_aes_ku040_db_g USE_INTMEM=0 USE_EXTMEM=1 INIT_MEM=0 

syn-build: clean
	nix-shell --run "make clean setup"
	make ibex-setup
	nix-shell --run " make -C ../$(CORE)_V$(VERSION)/ syn-build SYNTHESIZER=$(SYNTHESIZER)"

lint-run: clean
	nix-shell --run "make clean setup"
	make ibex-setup
	nix-shell --run "make -C ../$(CORE)_V$(VERSION)/ lint-run LINTER=$(LINTER)"

doc-build:
	nix-shell --run "make clean setup"
	make ibex-setup
	nix-shell --run "make -C ../$(CORE)_V$(VERSION)/ doc-build"

doc-test:
	nix-shell --run "make clean setup"
	make ibex-setup
	nix-shell --run "make -C ../$(CORE)_V$(VERSION)/ doc-test"


test-all: pc-emul-test sim-test fpga-test syn-build lint-run doc-build doc-test



# Install board server and client
board_server_install:
	make -C lib board_server_install

board_server_uninstall:
	make -C lib board_server_uninstall

board_server_status:
	systemctl status board_server

.PHONY: setup ibex-setup sim-test fpga-test doc-test test-all board_server_install board_server_uninstall board_server_status


clean:
	nix-shell --run "py2hwsw $(CORE) clean --build_dir '$(BUILD_DIR)'"
	@rm -rf ../*.summary ../*.rpt
	@find . -name \*~ -delete

# Remove all __pycache__ folders with python bytecode
python-cache-clean:
	find . -name "*__pycache__" -exec rm -rf {} \; -prune

.PHONY: clean python-cache-clean

# Tester

tester-sim-run:
	nix-shell --run "make clean setup"
	make ibex-setup
	nix-shell --run "make -C ../$(CORE)_V$(VERSION)/tester/ sim-run SIMULATOR=$(SIMULATOR)"

tester-fpga-run:
	nix-shell --run "make clean setup"
	make ibex-setup
	nix-shell --run " make -C ../$(CORE)_V$(VERSION)/tester/ fpga-fw-build BOARD=$(BOARD)"
	make -C ../$(CORE)_V$(VERSION)/tester/ fpga-run BOARD=$(BOARD)

.PHONY: tester-sim-run tester-fpga-run