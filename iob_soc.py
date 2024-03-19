#!/usr/bin/env python3

import sys

from iob_module import iob_module
from iob_soc_utils import pre_setup_iob_soc, post_setup_iob_soc

# Submodules
from iob_picorv32 import iob_picorv32
from iob_cache import iob_cache
from iob_uart import iob_uart
from iob_timer import iob_timer
from iob_utils import iob_utils
from iob_merge import iob_merge
from iob_split import iob_split
from iob_rom_sp import iob_rom_sp
from iob_ram_dp_be import iob_ram_dp_be
from iob_ram_dp_be_xil import iob_ram_dp_be_xil
from iob_pulse_gen import iob_pulse_gen
from iob_counter import iob_counter
from iob_reg import iob_reg
from iob_reg_re import iob_reg_re
from iob_ram_sp_be import iob_ram_sp_be
from iob_ram_dp import iob_ram_dp
from iob_reset_sync import iob_reset_sync
from axi_ram import axi_ram
from iob_tasks import iob_tasks
from printf import printf
from iob_ctls import iob_ctls
from iob_ram_2p import iob_ram_2p
from iob_ram_sp import iob_ram_sp
from axi_interconnect import axi_interconnect


class iob_soc(iob_module):
    def __init__(self, *args, **kwargs):
        self.version = "V0.70"
        self.rw_overlap = True
        self.is_system = True
        self.board_list = ["CYCLONEV-GT-DK", "AES-KU040-DB-G"]

        # macros
        # This method creates a macro and adds it to the local module's `confs` list
        self.create_conf(
            name="INIT_MEM",
            type="M",
            val="INIT_MEM" in sys.argv,
            min="0",
            max="1",
            descr="Enable MUL and DIV CPU instructions",
        ),
        self.create_conf(
            name="USE_EXTMEM",
            type="M",
            val="USE_EXTMEM" in sys.argv,
            min="0",
            max="1",
            descr="Enable MUL and DIV CPU instructions",
        ),
        self.create_conf(
            name="USE_MUL_DIV",
            type="M",
            val="1",
            min="0",
            max="1",
            descr="Enable MUL and DIV CPU instructions",
        ),
        self.create_conf(
            name="USE_COMPRESSED",
            type="M",
            val="1",
            min="0",
            max="1",
            descr="Use compressed CPU instructions",
        ),
        self.create_conf(
            name="E",
            type="M",
            val="31",
            min="1",
            max="32",
            descr="Address selection bit for external memory",
        ),
        self.create_conf(
            name="B",
            type="M",
            val="20",
            min="1",
            max="32",
            descr="Address selection bit for boot ROM",
        ),
        # parameters
        self.create_conf(
            name="BOOTROM_ADDR_W",
            type="P",
            val="12",
            min="1",
            max="32",
            descr="Boot ROM address width",
        ),
        self.create_conf(
            name="SRAM_ADDR_W",
            type="P",
            val="15",
            min="1",
            max="32",
            descr="SRAM address width",
        ),
        self.create_conf(
            name="MEM_ADDR_W",
            type="P",
            val="24",
            min="1",
            max="32",
            descr="Memory bus address width",
        ),
        # mandatory parameters (do not change them!)
        self.create_conf(
            name="ADDR_W",
            type="F",
            val="32",
            min="1",
            max="32",
            descr="Address bus width",
        ),
        self.create_conf(
            name="DATA_W",
            type="F",
            val="32",
            min="1",
            max="32",
            descr="Data bus width",
        ),
        self.create_conf(
            name="AXI_ID_W",
            type="F",
            val="0",
            min="1",
            max="32",
            descr="AXI ID bus width",
        ),
        self.create_conf(
            name="AXI_ADDR_W",
            type="F",
            val="`IOB_SOC_MEM_ADDR_W",
            min="1",
            max="32",
            descr="AXI address bus width",
        ),
        self.create_conf(
            name="AXI_DATA_W",
            type="F",
            val="`IOB_SOC_DATA_W",
            min="1",
            max="32",
            descr="AXI data bus width",
        ),
        self.create_conf(
            name="AXI_LEN_W",
            type="F",
            val="4",
            min="1",
            max="4",
            descr="AXI burst length width",
        ),
        self.create_conf(
            name="MEM_ADDR_OFFSET",
            type="F",
            val="0",
            min="0",
            max="NA",
            descr="Offset of memory address",
        ),

        # Create system ports (and wires) for them

        # This method creates a bus port local module's `port_bus_list`, and connects it to a newly created wire bus from the local wire list: `wire_bus_list`.
        self.create_bus_port(
            name="clk_en_rst",
            type="slave",
            wire_prefix="",
            port_prefix="",
            descr="Clock, enable, and reset",
        )

        self.create_bus_port(
            name="axi",
            type="master",
            wire_prefix="",
            port_prefix="",
            mult="",  # Will be filled automatically
            widths={
                "ID_W": "AXI_ID_W",
                "ADDR_W": "AXI_ADDR_W",
                "DATA_W": "AXI_DATA_W",
                "LEN_W": "AXI_LEN_W",
            },
            descr="Bus of AXI master interfaces for external memory. One interface for this system and others optionally for peripherals.",
            if_defined="USE_EXTMEM",
        )

        self.create_bus_port(
            name="rs232",
            type="",  # Neutral type. Neither master nor slave.
            wire_prefix="",
            port_prefix="",
            descr="iob-soc uart interface",
        ),

        # Example method for creating a single wire port
        # This method creates a port in the local module's `port_bus_list`, and assigns a bus to it. It also connects the port to a newly created wire from the local wire list.
        # self.create_wire_port(
        #     name="trap",
        #     direction="output",
        #     width=1,
        #     descr="CPU trap signal",
        # )

        #######################################
        # IOb-SoC modules, wires, and instances
        #######################################

        # TODO: Find a way to include verilog headers at the top of the generated module 

        #
        # SYSTEM RESET
        #

        # Create single wires, and automatically assign them to single wire groups
        self.create_wire("boot", width=1)
        self.create_wire("cpu_reset", width=1)

        #
        # CPU
        #

        self.create_bus(
            name="cpu_i_bus",
            descr="Cpu instruction bus",
            wires=[
                {"name": "cpu_i_req", "width": REQ_W},
                {"name": "cpu_i_resp", "width": RESP_W}
            ],
        )
        ### Alternative way to create wires and assign them to a group
        # self.create_wire(
        #     name="cpu_i_req",
        #     width=REQ_W,
        #     group="cpu_i_bus"
        # )
        # self.create_wire(
        #     name="cpu_i_resp",
        #     width=RESP_W,
        #     group="cpu_i_bus"
        # )

        self.create_bus(
            name="cpu_d_bus",
            descr="Cpu data bus",
            wires=[
                {"name": "cpu_d_req", "width": REQ_W},
                {"name": "cpu_d_resp", "width": RESP_W}
            ],
        )

        self.create_bus(
            name="cpu_clk_en_rst",
            descr="Cpu clock, enable, and reset",
            wires=[
                get_wire_from_bus("clk_en_rst", "clk"),
                get_wire("cpu_reset"),
                get_wire_from_bus("clk_en_rst", "cke"),

            ],
        )

        # This method creates a new module instance and adds it to the local module's `blocks` list
        self.create_instance(
            iob_picorv32,
            "cpu",
            parameters={
                "ADDR_W": "ADDR_W",
                "DATA_W": "DATA_W",
                "USE_COMPRESSED":  USE_COMPRESSED,
                "USE_MUL_DIV": USE_MUL_DIV,
                "USE_EXTMEM": USE_EXTMEM
            },
            # Connect port groups to wire groups
            connect={
                "clk_en_rst": "cpu_clk_en_rst",
                "boot": "boot",
                # instruction bus
                "i_bus": "cpu_i_bus",
                # data bus
                "d_bus": "cpu_d_bus",
            },
        )

        # ###########################################################################
        # TODO: Update lines below with new connections from local wires and groups.
        #       Also remove `_i` and `_o` suffixes.
        # ###########################################################################

        #
        # SPLIT CPU BUSES TO ACCESS INTERNAL OR EXTERNAL MEMORY
        #

        # internal memory instruction bus
        int_mem_i_bus = wire_group(
            "int_mem_i_bus",
            descr="Internal memory instruction bus",
            wires=[
                wire("int_mem_i_req", width=REQ_W),
                wire("int_mem_i_resp", width=RESP_W),
            ],
        )
        # external memory instruction bus
        ext_mem_i_bus = wire_group(
            "ext_mem_i_bus",
            descr="External memory instruction bus",
            wires=[
                wire("ext_mem_i_req", width=REQ_W),
                wire("ext_mem_i_resp", width=RESP_W),
            ],
        )

        if USE_EXTMEM:
            ibus_split = iob_split(
                "ibus_split",
                parameters={
                    "ADDR_W": "ADDR_W",
                    "DATA_W": "DATA_W",
                    "N_SLAVES": "2",
                    "P_SLAVES": str(REQ_W - 2),
                },
                connect={
                    "clk_i": clk,
                    "arst_i": cpu_reset,
                    # master interface
                    "m_bus": cpu_i_bus,
                    # slaves interface
                    "s_bus": [ext_mem_i_bus, int_mem_i_bus],
                },
            )
        else:  # no extmem
            int_mem_i_bus = cpu_i_bus

        # DATA BUS

        # internal data bus
        int_d_bus = wire_group(
            "int_d_bus",
            descr="Internal data bus",
            wires=[
                wire("int_d_req", width=REQ_W),
                wire("int_d_resp", width=RESP_W)
            ],
        )
        # external memory data bus
        ext_mem_d_bus = wire_group(
            "ext_mem_d_bus",
            descr="External memory data bus",
            wires=[
                wire("ext_mem_d_req", width=REQ_W),
                wire("ext_mem_d_resp", width=RESP_W),
            ],
        )

        if USE_EXTMEM:
            dbus_split = iob_split(
                "dbus_split",
                parameters={
                    "ADDR_W": "ADDR_W",
                    "DATA_W": "DATA_W",
                    "N_SLAVES": "2",  # E,{P,I}
                    "P_SLAVES": str(REQ_W - 2),
                },
                connect={
                    "clk_i": clk,
                    "arst_i": cpu_reset,
                    # master interface
                    "m_bus": cpu_d_bus,
                    # slaves interface
                    "s_bus": [ext_mem_d_bus, int_d_bus],
                },
            )
        else:  # no extmem
            int_d_bus = cpu_d_bus

        #
        # SPLIT INTERNAL MEMORY AND PERIPHERALS BUS
        #

        # slaves bus (includes internal memory + periphrals)
        slaves_bus = wire_group(
            "slaves_bus",
            descr="Slaves bus",
            wires=[
                wire("slaves_req", width=N_SLAVES*REQ_W),
                wire("slaves_resp", width=N_SLAVES*RESP_W)
            ],
        )

        pbus_split = iob_split(
           "pbus_split",
           parameters={
              "ADDR_W": "ADDR_W",
              "DATA_W": "DATA_W",
              "N_SLAVES": str(N_SLAVES),
              "P_SLAVES": str(REQ_W - 3),
           },
           connect={
              "clk_i": clk,
              "arst_i": cpu_reset,
              # master interface
              "m_bus": int_d_bus,
              # slaves interface
              "s_bus": slaves_bus,
           },
        )

        #
        # INTERNAL SRAM MEMORY
        #

        int_mem = iob_soc_int_mem(
            "int_mem",
            parameters={
                "ADDR_W": "ADDR_W",
                "DATA_W": "DATA_W",
                "HEXFILE": "iob_soc_firmware",
                "BOOT_HEXFILE": "iob_soc_boot",
                "SRAM_ADDR_W": "SRAM_ADDR_W",
                "BOOTROM_ADDR_W": "BOOTROM_ADDR_W",
                "B_BIT": f"{REQ_W} - (ADDR_W-`IOB_SOC_B+1)",
            },
            connect={
                "clk_en_rst": clk_en_rst,
                "boot": boot,
                "cpu_reset": cpu_reset,
                # instruction bus
                "i_bus": int_mem_i_bus,
                # data bus
                "d_bus": slaves_bus.part_sel(0, REQ_W or RESP_W?),  # .part(<part index>, <part width>)
            },
        )

        #
        # EXTERNAL DDR MEMORY
        #

        # TODO: Find a way to merge these into buses?
        ext_mem0_i_req = wire("ext_mem0_i_req", width=1+MEM_ADDR_W-2+DATA_W+DATA_W/8)
        ext_mem0_d_req = wire("ext_mem0_d_req", width=1+MEM_ADDR_W+1-2+DATA_W+DATA_W/8)

        # TODO: find a way to replace this. We don't to connect a wire to another.
        # Either inject verilog, or use module
        ext_mem_i_req.connect_to = [valid(ext_mem_i_req, 0), address(ext_mem_i_req, 0, MEM_ADDR_W, -2), write(ext_mem_i_req, 0)]
        ext_mem_d_req.connect_to = [valid(ext_mem_d_req, 0), address(ext_mem_d_req, 0, MEM_ADDR_W+1, -2), write(ext_mem_d_req, 0)]

        internal_axi_awaddr_o = wire("internal_axi_awaddr_o", width=AXI_ADDR_W)
        internal_axi_araddr_o = wire("internal_axi_araddr_o", width=AXI_ADDR_W)

        ext_mem = iob_soc_ext_mem(
            "ext_mem",
            parameters={
                "ADDR_W": "ADDR_W",
                "DATA_W": "DATA_W",
                "FIRM_ADDR_W": "MEM_ADDR_W",
                "MEM_ADDR_W": "MEM_ADDR_W",
                "DDR_ADDR_W": "`DDR_ADDR_W",
                "DDR_DATA_W": "`DDR_DATA_W",
                "AXI_ID_W": "AXI_ID_W",
                "AXI_LEN_W": "AXI_LEN_W",
                "AXI_ADDR_W": "AXI_ADDR_W",
                "AXI_DATA_W": "AXI_DATA_W"
            },
            connect={
                # instruction bus
                "i_req_i": ext_mem0_i_req,
                "i_resp_o": ext_mem_i_bus.wires.ext_mem_i_resp,

                # data bus
                "d_req_i": ext_mem0_d_req,
                "d_resp_o": ext_mem_d_bus.wires.ext_mem_d_resp,

                # AXI INTERFACE
                # address write
                "axi_awid_o": axi.wires.axi_awid_o.part_sel(0, AXI_ID_W),
                "axi_awaddr_o": internal_axi_awaddr_o.part_sel(0, AXI_ADDR_W),
                "axi_awlen_o": axi.wires.axi_awlen_o.part_sel(0, AXI_LEN_W),
                "axi_awsize_o": axi.wires.axi_awsize_o.part_sel(0, 3),
                "axi_awburst_o": axi.wires.axi_awburst_o.part_sel(0, 2),
                "axi_awlock_o": axi.wires.axi_awlock_o.part_sel(0, 2),
                "axi_awcache_o": axi.wires.axi_awcache_o.part_sel(0, 4),
                "axi_awprot_o": axi.wires.axi_awprot_o.part_sel(0, 3),
                "axi_awqos_o": axi.wires.axi_awqos_o.part_sel(0, 4),
                "axi_awvalid_o": axi.wires.axi_awvalid_o.part_sel(0, 1),
                "axi_awready_i": axi.wires.axi_awready_i.part_sel(0, 1),
                # write
                "axi_wdata_o": axi.wires.axi_wdata_o.part_sel(0, AXI_DATA_W),
                "axi_wstrb_o": axi.wires.axi_wstrb_o.part_sel(0, (AXI_DATA_W/8)),
                "axi_wlast_o": axi.wires.axi_wlast_o.part_sel(0, 1),
                "axi_wvalid_o": axi.wires.axi_wvalid_o.part_sel(0, 1),
                "axi_wready_i": axi.wires.axi_wready_i.part_sel(0, 1),
                # write response
                "axi_bid_i": axi.wires.axi_bid_i.part_sel(0, AXI_ID_W),
                "axi_bresp_i": axi.wires.axi_bresp_i.part_sel(0, 2),
                "axi_bvalid_i": axi.wires.axi_bvalid_i.part_sel(0, 1),
                "axi_bready_o": axi.wires.axi_bready_o.part_sel(0, 1),
                # address read
                "axi_arid_o": axi.wires.axi_arid_o.part_sel(0, AXI_ID_W),
                "axi_araddr_o": internal_axi_araddr_o.part_sel(0, AXI_ADDR_W),
                "axi_arlen_o": axi.wires.axi_arlen_o.part_sel(0, AXI_LEN_W),
                "axi_arsize_o": axi.wires.axi_arsize_o.part_sel(0, 3),
                "axi_arburst_o": axi.wires.axi_arburst_o.part_sel(0, 2),
                "axi_arlock_o": axi.wires.axi_arlock_o.part_sel(0, 2),
                "axi_arcache_o": axi.wires.axi_arcache_o.part_sel(0, 4),
                "axi_arprot_o": axi.wires.axi_arprot_o.part_sel(0, 3),
                "axi_arqos_o": axi.wires.axi_arqos_o.part_sel(0, 4),
                "axi_arvalid_o": axi.wires.axi_arvalid_o.part_sel(0, 1),
                "axi_arready_i": axi.wires.axi_arready_i.part_sel(0, 1),
                # read
                "axi_rid_i": axi.wires.axi_rid_i.part_sel(0, AXI_ID_W),
                "axi_rdata_i": axi.wires.axi_rdata_i.part_sel(0, AXI_DATA_W),
                "axi_rresp_i": axi.wires.axi_rresp_i.part_sel(0, 2),
                "axi_rlast_i": axi.wires.axi_rlast_i.part_sel(0, 1),
                "axi_rvalid_i": axi.wires.axi_rvalid_i.part_sel(0, 1),
                "axi_rready_o": axi.wires.axi_rready_o.part_sel(0, 1),

                "clk_i": clk,
                "cke_i": cke,
                "arst_i": cpu_reset,
            },
        )

        # TODO: find a way to replace this. We don't to connect a wire to another.
        # Either inject verilog, or use module
        axi.wires.axi_awaddr_o.part_sel(0, AXI_ADDR_W).connect_to = internal_axi_awaddr_o + MEM_ADDR_OFFSET
        axi.wires.axi_araddr_o.part_sel(0, AXI_ADDR_W).connect_to = internal_axi_araddr_o + MEM_ADDR_OFFSET

        # TODO: Replace below with a script to auto-create and connect peripherals
        UART0 = iob_uart(
            "UART0",
            parameters={
                "DATA_W": "UART0_DATA_W",
                "ADDR_W": "UART0_ADDR_W",
                "UART_DATA_W": "UART0_UART_DATA_W",
            },
            connect={
                "rs232": rs232,
                "clk_en_rst": clk_en_rst,
                "iob_interface": slaves_bus.part_sel(0, REQ_W or RESP_W?),  # .part(<part index>, <part width>)
            },
        )
        TIMER0 = iob_timer(
            "TIMER0",
            parameters={
                "DATA_W": "TIMER0_DATA_W",
                "ADDR_W": "TIMER0_ADDR_W",
                "TIMER_DATA_W": "TIMER0_WDATA_W",
            },
            connect={
                "clk_en_rst": clk_en_rst,
                "iob_interface": slaves_bus.part_sel(0, REQ_W or RESP_W?),  # .part(<part index>, <part width>)
            },
        )


        #######################################
        # End of IOb-SoC module
        #######################################

        # Modules that need to be setup, but are not instantiated inside iob_soc Verilog module
        iob_utils("utils")
        iob_merge("merge")
        iob_cache("cache")
        iob_rom_sp("rom_sp")
        iob_ram_dp_be("ram_dp_be")
        iob_ram_dp_be_xil("ram_dp_be_xil")
        iob_pulse_gen("pulse_gen")
        # iob_counter("counter")
        iob_reg("reg")
        iob_reg_re("reg_re")
        iob_ram_sp_be("ram_sp_be")
        # iob_ram_dp("ram_dp")
        # iob_ctls("ctls")
        axi_interconnect("interconnect")
        # Simulation headers & modules
        axi_ram("ram", purpose="simulation")
        iob_tasks("tasks", purpose="simulation")
        # Software modules
        printf()
        # Modules required for CACHE
        iob_ram_2p("ram_2p", purpose="simulation")
        iob_ram_2p("ram_2p", purpose="fpga")
        iob_ram_sp("ram_sp", purpose="simulation")
        iob_ram_sp("ram_sp", purpose="fpga")
        # FPGA modules
        iob_reset_sync("reset_sync", purpose="fpga")

        # Peripherals
        self.peripherals = [UART0, TIMER0]

        # Fill blocks list with modules that need to be instantiated inside the iob_soc Verilog module
        # TODO: Remove this list. We no longer need it, since the `self.create_instance` method manages it.
        self.blocks = [
            cpu,
            pbus_split,
            int_mem,
        ] + peripherals
        if USE_EXTMEM:
            blocks += [
                ibus_split,
                dbus_split,
                ext_mem,
                ]

        # Number of external memory connections (will be filled automatically)
        self.num_extmem_connections = -1

        # Pre-setup specialized IOb-SoC functions
        pre_setup_iob_soc(self)
        # Call the superclass setup
        super().__init__(*args, **kwargs)
        # Post-setup specialized IOb-SoC functions
        post_setup_iob_soc(self)


if __name__ == "__main__":
    # Create an iob-soc ip core
    iob_soc_core = iob_soc()
    if "clean" in sys.argv:
        iob_soc_core.clean_build_dir()
    elif "print" in sys.argv:
        iob_soc_core.print_build_dir()
    else:
        iob_soc_core()
