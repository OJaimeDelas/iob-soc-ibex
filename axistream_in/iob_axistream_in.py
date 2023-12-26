#!/usr/bin/env python3

import os

from iob_module import iob_module

# Submodules
from iob_reg_re import iob_reg_re
from iob_ram_t2p import iob_ram_t2p
from iob_fifo_async import iob_fifo_async
from iob_sync import iob_sync
from iob_counter import iob_counter


class iob_axistream_in(iob_module):
    name = 'iob_axistream_in'
    version = "V0.30"
    setup_dir = os.path.dirname(__file__)

    @classmethod
    def _create_submodules_list(cls):
        ''' Create submodules list with dependencies of this module
        '''
        super()._create_submodules_list([
            {"interface": "iob_s_port"},
            {"interface": "iob_s_portmap"},
            iob_fifo_async,
            iob_reg_re,
            iob_ram_t2p,
            iob_sync
        ])

    @classmethod
    def _setup_confs(cls):
        super()._setup_confs([
            # Macros
            # Parameters
            {
                "name": "DATA_W",
                "type": "P",
                "val": "32",
                "min": "32",
                "max": "32",
                "descr": "CPU data bus width",
            },
            {
                "name": "ADDR_W",
                "type": "P",
                "val": "`IOB_AXISTREAM_IN_SWREG_ADDR_W",
                "min": "NA",
                "max": "NA",
                "descr": "Address bus width",
            },
            {
                "name": "TDATA_W",
                "type": "P",
                "val": "8",
                "min": "1",
                "max": "DATA_W",
                "descr": "AXI stream data width",
            },
            {
                "name": "FIFO_ADDR_W",
                "type": "P",
                "val": "4",
                "min": "NA",
                "max": "16",
                "descr": "FIFO depth (log2)",
            },
        ])
   
    @classmethod
    def _setup_ios(cls):
        cls.ios += [
            {"name": "iob_s_port", "descr": "CPU native interface", "ports": []},
            {
                "name": "general",
                "descr": "System general interface signals",
                "ports": [
                    {
                        "name": "clk_i",
                        "type": "I",
                        "n_bits": "1",
                        "descr": "System clock input",
                    },
                    {
                        "name": "arst_i",
                        "type": "I",
                        "n_bits": "1",
                        "descr": "System reset, asynchronous and active high",
                    },
                    {
                        "name": "cke_i",
                        "type": "I",
                        "n_bits": "1",
                        "descr": "System clock enable signal.",
                    },
                    {
                        "name": "interrupt_o",
                        "type": "O",
                        "n_bits": "1",
                        "descr": "FIFO threshold interrupt signal",
                    },
                ],
            },
            {
                "name": "axistream",
                "descr": "Axistream interface signals",
                "ports": [
                    {
                        "name": "axis_clk_i",
                        "type": "I",
                        "n_bits": "1",
                        "descr": "Axistream clock input",
                    },
                    {
                        "name": "axis_cke_i",
                        "type": "I",
                        "n_bits": "1",
                        "descr": "Axistream clock enable signal.",
                    },
                    {
                        "name": "axis_arst_i",
                        "type": "I",
                        "n_bits": "1",
                        "descr": "Axistream reset, asynchronous and active high",
                    },
                    {
                        "name": "axis_tdata_i",
                        "type": "I",
                        "n_bits": "TDATA_W",
                        "descr": "Axistream data input interface",
                    },
                    {
                        "name": "axis_tvalid_i",
                        "type": "I",
                        "n_bits": "1",
                        "descr": "Axistream valid input interface",
                    },
                    {
                        "name": "axis_tready_o",
                        "type": "O",
                        "n_bits": "1",
                        "descr": "Axistream ready output interface",
                    },
                    {
                        "name": "axis_tlast_i",
                        "type": "I",
                        "n_bits": "1",
                        "descr": "Axistream last input interface",
                    },
                ],
            },
            {
                "name": "dma",
                "descr": "Direct Memory Access via dedicated AXI Stream interface.",
                "ports": [
                    {
                        "name": "dma_tdata_o",
                        "type": "O",
                        "n_bits": "DATA_W",
                        "descr": "TData output interface",
                    },
                    {
                        "name": "dma_tvalid_o",
                        "type": "O",
                        "n_bits": "1",
                        "descr": "TValid output interface",
                    },
                    {
                        "name": "dma_tready_i",
                        "type": "I",
                        "n_bits": "1",
                        "descr": "TReady input interface",
                    },
                ],
            },
        ]

    @classmethod
    def _setup_regs(cls):
        cls.regs += [
            {
                "name": "axistream",
                "descr": "Axistream software accessible registers.",
                "regs": [
                    {
                        "name": "SOFT_RESET",
                        "type": "W",
                        "n_bits": 1,
                        "rst_val": 0,
                        "log2n_items": 0,
                        "autoreg": True,
                        "descr": "Soft reset.",
                    },
                    {
                        "name": "ENABLE",
                        "type": "W",
                        "n_bits": 1,
                        "rst_val": 0,
                        "log2n_items": 0,
                        "autoreg": True,
                        "descr": "Enable peripheral.",
                    },
                    {
                        "name": "DATA",
                        "type": "R",
                        "n_bits": 32,
                        "rst_val": 0,
                        "log2n_items": 0,
                        "autoreg": False,
                        "descr": "Data output (reading from this register sets the RSTRB and LAST registers).",
                    },
                    {
                        "name": "NWORDS",
                        "type": "R",
                        "n_bits": "DATA_W",
                        "rst_val": 0,
                        "log2n_items": 0,
                        "autoreg": True,
                        "descr": "Read the number of words (with TDATA_W bits) written to the FIFO.",
                    },
                    {
                        "name": "TLAST_DETECTED",
                        "type": "R",
                        "n_bits": 1,
                        "rst_val": 0,
                        "log2n_items": 0,
                        "autoreg": True,
                        "descr": "Read the TLAST detected status.",
                    },
                ],
            },
            {
                "name": "fifo",
                "descr": "FIFO related registers",
                "regs": [
                    {
                        "name": "FIFO_FULL",
                        "type": "R",
                        "n_bits": 1,
                        "rst_val": 0,
                        "log2n_items": 0,
                        "autoreg": True,
                        "descr": "Full (1), or non-full (0).",
                    },
                    {
                        "name": "FIFO_EMPTY",
                        "type": "R",
                        "n_bits": 1,
                        "rst_val": 0,
                        "log2n_items": 0,
                        "autoreg": True,
                        "descr": "Full (1), or non-full (0).",
                    },
                    {
                        "name": "FIFO_THRESHOLD",
                        "type": "W",
                        "n_bits": 32,
                        "rst_val": 4,
                        "log2n_items": 0,
                        "autoreg": True,
                        "descr": "FIFO threshold level for interrupt signal",
                    },
                    {
                        "name": "FIFO_LEVEL",
                        "type": "R",
                        "n_bits": 32,
                        "rst_val": 0,
                        "log2n_items": 0,
                        "autoreg": True,
                        "descr": "Current FIFO level",
                    },
                ],
            }
        ]

    @classmethod
    def _setup_block_groups(cls):
        cls.block_groups += []
