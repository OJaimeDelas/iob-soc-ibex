# SPDX-FileCopyrightText: 2025 IObundle
#
# SPDX-License-Identifier: MIT


def setup(py_params_dict):
    # Py2hwsw dictionary describing current core
    core_dict = {
        "version": "0.8",
        "parent": {
            # IOb-SoC is a child core of iob_system: https://github.com/IObundle/py2hwsw/tree/main/py2hwsw/lib/hardware/iob_system
            # IOb-SoC will inherit all attributes/files from the iob_system core.
            "core_name": "iob_system",
            # Every parameter in the lines below will be passed to the iob_system parent core.
            **py_params_dict,
            "cpu": "iob_ibex",
            # Memory address width
            "mem_addr_w": 15,  # the default 18 are not visible in xcelium
            "data_w": 39, # 32bits data + 7 parity
            "system_attributes": {
                # Every attribute in this dictionary will override/append to the ones of the iob_system parent core.
                "board_list": [
                    "iob_aes_ku040_db_g",
                    "iob_cyclonev_gt_dk",
                    "iob_zybo_z7",
                ],
                "ports": [
                    {
                        # Add new rs232 port for uart
                        "name": "rs232_m",
                        "descr": "iob-system uart interface",
                        "signals": {
                            "type": "rs232",
                        },
                    },
                    # NOTE: Add other ports here.
                ],
                "subblocks": [
                    {
                        # Instantiate a UART core from: https://github.com/IObundle/py2hwsw/tree/main/py2hwsw/lib/hardware/iob_uart
                        "core_name": "iob_uart",
                        "instance_name": "UART0",
                        "instance_description": "UART peripheral",
                        "is_peripheral": True,
                        "parameters": {},
                        "connect": {
                            "clk_en_rst_s": "clk_en_rst_s",
                            # Cbus connected automatically
                            "rs232_m": "rs232_m",
                        },
                    },
                    {
                        # Instantiate a TIMER core from: https://github.com/IObundle/py2hwsw/tree/main/py2hwsw/lib/hardware/iob_timer
                        "core_name": "iob_timer",
                        "instance_name": "TIMER0",
                        "instance_description": "Timer peripheral",
                        "is_peripheral": True,
                        "parameters": {},
                        "connect": {
                            "clk_en_rst_s": "clk_en_rst_s",
                            # Cbus connected automatically
                        },
                    },
                    # NOTE: Add other components/peripherals here.
                ],
            },
        },
    }

    return core_dict
