# README #

# iob-regfileif

## What is this repository for? ##

The IObundle REGFILEIF is a RISC-V-based Peripheral written in Verilog, which users can download, modify, simulate and implement in FPGA or ASIC.  
This peripheral contains registers to buffer communication between two systems using their respective peripheral buses.
It has the internal native interface that connects to the peripheral bus of the system that uses this REGFILEIF as a peripheral.
It also has an external native interface that connects to the native peripheral bus of an external system.

## Integrate in SoC ##

* Check out [IOb-SoC](https://github.com/IObundle/iob-soc)

## Usage

This peripheral need a register configuration file to determine how many registers it contains and the type of those registers.
This configuration file must be named "sut\_swreg.vh" and is placed in the root directory of the system that is using this component as a peripheral.

The "sut\_swreg.vh" file is based on a group of \`IOB\_SWREG_ macros from IOb-Lib. An example configuration is:
```
`IOB\_SWREG_W(REGFILEIF_REG1, 8, 0) // Write register: 8 bit
`IOB\_SWREG_R(REGFILEIF_REG3, 8, 0) // Read register: 8 bit
```

When the system is built, the values from the configuration file are automatically read, and the peripheral is created according to the configuration.
The internal native interface connects automatically to the peripheral bus, while the external native interface is available to be used externally.

### Connecting peripheral buses of SUT and Tester systems

When using two systems, such as SUT and Tester, the REGFILEIF is a peripheral of the SUT.

The connection between the REGFILEIF's external native interface and the peripheral bus of the Tester can be made using the peripheral\_portmap.txt

However, to connect using the portmap, the native bus signals of the Tester must be externally accessible (the portmap configuration can only map signals that can be accessed externally).
To do this, we use the peripheral **IOBNATIVEBRIDGEIF**. This peripheral also has two native interfaces, one internal and one external, however, unlike REGFILEIF, the external interface of this peripheral is made to be connected to the native interface of another peripheral. The IOBNATIVEBRIDGEIF, allows the peripheral bus signals of the system to be accessed externally.

We use the IOBNATIVEBRIDGEIF as a peripheral of the Tester to allows its peripheral bus signals to be accessed externally (and therefore be portmapped).
To create the IOBNATIVEBRIDGEIF we use the `software/python/iobnativebridge.py` script. We call this script along with the path to the directory in which the peripheral will be created.
For example, if we are in the root directory of the system, we use:
```
./submodules/REGFILEIF/software/python/iobnativebridge.py submodules/
```
The command above creates the IOBNATIVEBRIDGEIF peripheral inside de submodules folder.

We then change the PERIPHERALS and TESTER\_PERIPHERALS lists in config.mk to contain REGFILEIF and IOBNATIVEBRIDGEIF, respectively.

Using the tester-portmap target, we generate a template for the portmap configuration file:
```
make tester-portmap
```

In the portmap file, we connect the regfileif signals and nativebridgeif signals together, and then the complete system is ready to be built!
Example connection if peripheral\_portmap.txt file:
```
SUT.REGFILEIF[0].REGFILEIF_valid : Tester.IOBNATIVEBRIDGEIF[0].IOBNATIVEBRIDGEIF_valid
SUT.REGFILEIF[0].REGFILEIF_address : Tester.IOBNATIVEBRIDGEIF[0].IOBNATIVEBRIDGEIF_address
SUT.REGFILEIF[0].REGFILEIF_wdata : Tester.IOBNATIVEBRIDGEIF[0].IOBNATIVEBRIDGEIF_wdata
SUT.REGFILEIF[0].REGFILEIF_wstrb : Tester.IOBNATIVEBRIDGEIF[0].IOBNATIVEBRIDGEIF_wstrb
SUT.REGFILEIF[0].REGFILEIF_rdata : Tester.IOBNATIVEBRIDGEIF[0].IOBNATIVEBRIDGEIF_rdata
SUT.REGFILEIF[0].REGFILEIF_ready : Tester.IOBNATIVEBRIDGEIF[0].IOBNATIVEBRIDGEIF_ready
```

---

(Enhancement for the future: allow bidirectional registers if no config file is found)
