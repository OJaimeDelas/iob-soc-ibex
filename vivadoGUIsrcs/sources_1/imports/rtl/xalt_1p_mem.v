`timescale 1ns / 1ps

module xalt_1p_mem #(
		      parameter MEM_INIT_FILE=0,
		      parameter DATA_W=8,
		      parameter ADDR_W=12
		      )
   (
    input [(DATA_W-1):0]      data_a,
    input [(ADDR_W-1):0]      addr_a,
    input                     we_a, clk,
    output reg [(DATA_W-1):0] q_a
    );

   // Declare the RAM
   reg [DATA_W-1:0] 			       ram[2**ADDR_W-1:0];


   // Initialize the RAM
   initial $readmemh(MEM_INIT_FILE, ram, 0, 2**ADDR_W - 1);

   // Operate the RAM
   always @ (posedge clk)
     begin // Port A
	if (we_a)
	  begin
	     ram[addr_a] <= data_a;
	     //q_a <= data_a;
	  end
	else
	  q_a <= ram[addr_a];
     end

 endmodule
