`timescale 1 ns / 1 ps
`include "system.vh"
`include "int_mem.vh"

module system (
               input                clk,
               input                reset,
               output               trap,

`ifdef USE_DDR //AXI MASTER INTERFACE

               //address write
               output [0:0]         m_axi_awid, 
               output [`ADDR_W-1:0] m_axi_awaddr,
               output [7:0]         m_axi_awlen,
               output [2:0]         m_axi_awsize,
               output [1:0]         m_axi_awburst,
               output [0:0]         m_axi_awlock,
               output [3:0]         m_axi_awcache,
               output [2:0]         m_axi_awprot,
               output [3:0]         m_axi_awqos,
               output               m_axi_awvalid,
               input                m_axi_awready,

               //write
               output [`DATA_W-1:0] m_axi_wdata,
               output [3:0]         m_axi_wstrb,
               output               m_axi_wlast,
               output               m_axi_wvalid, 
               input                m_axi_wready,

               //write response
               input [0:0]          m_axi_bid,
               input [1:0]          m_axi_bresp,
               input                m_axi_bvalid,
               output               m_axi_bready,

               //address read
               output [0:0]         m_axi_arid,
               output [`ADDR_W-1:0] m_axi_araddr, 
               output [7:0]         m_axi_arlen,
               output [2:0]         m_axi_arsize,
               output [1:0]         m_axi_arburst,
               output [0:0]         m_axi_arlock,
               output [3:0]         m_axi_arcache,
               output [2:0]         m_axi_arprot,
               output [3:0]         m_axi_arqos,
               output               m_axi_arvalid, 
               input                m_axi_arready,

               //read
               input [0:0]          m_axi_rid,
               input [`DATA_W-1:0]  m_axi_rdata,
               input [1:0]          m_axi_rresp,
               input                m_axi_rlast, 
               input                m_axi_rvalid, 
               output               m_axi_rready,
`endif
               //UART
               output               uart_txd,
               input                uart_rxd,
               output               uart_rts,
               input                uart_cts
               );

   //
   // RESET
   //
   wire                             soft_reset;   
   wire                             reset_int = reset | soft_reset;
   
   //
   //  CPU
   //
   reg 				    m_i_ready, m_d_ready;
   wire [`ADDR_W-1:0] 		    m_i_addr, m_d_addr;
   reg [`DATA_W-1:0] 		    m_i_data, m_d_rdata;
   wire [`DATA_W-1:0] 		    m_d_wdata;
   wire [3:0] 			    m_d_wstrb;
   wire 			    m_d_valid;
   wire 			    HLT;
   
   cpu_wrapper cpu_wrapper (
			    .clk (clk),
			    .rst (reset_int),
      
			    .trap (trap),
			    .HLT (HLT),

			    //memory interface

			    //instruction bus
			    .i_ready (m_i_ready),
			    .i_addr (m_i_addr),
			    .i_data (m_i_data),

			    //data bus
			    .d_ready (m_d_ready),
			    .d_addr (m_d_addr),
			    .d_rdata (m_d_rdata),
			    .d_wdata (m_d_wdata),
			    .d_wstrb (m_d_wstrb),
			    .d_valid (m_d_valid)
			    );   
   
   //select memory  according to addr msb, boot status and ddr use

   reg                              int_mem_valid;
   wire                             int_mem_ready;
   wire [`DATA_W-1:0]               int_mem_rdata;
   
`ifdef USE_DDR
   reg                              ext_mem_valid;
   reg                              ext_mem_ready;
   reg [`DATA_W-1:0]                ext_mem_rdata;
`endif
   
   reg                              p_valid;
   wire                             p_ready;
   wire [`DATA_W-1:0]               p_rdata;
   
   wire                             boot;
   
   always @* begin
      //assume internal memory is being addressed
      int_mem_valid = m_d_valid;
      p_valid = 1'b0;

      m_d_rdata = int_mem_rdata;
      m_d_ready = int_mem_ready;

`ifdef USE_DDR
      ext_mem_valid = 1'b0;
`endif

      if(m_d_addr[`ADDR_W-1]) begin
         //peripherals are being addressed
         int_mem_valid = 1'b0;
         p_valid = m_d_valid;
         m_d_rdata = p_rdata;
         m_d_ready = p_ready;
      end
`ifdef USE_DDR
      //ddr is being addressed
      else if(!boot) begin
         int_mem_valid = 1'b0;
 `ifdef USE_BOOT
         ext_mem_valid = m_valid | s_valid[`DDR_BASE];
 `else
         ext_mem_valid = m_valid;
 `endif
         m_rdata = ext_mem_rdata;
         m_ready = ext_mem_ready;
      end
`endif
   end
   
   
   //
   // INTERNAL SRAM MEMORY
   //
   wire [`DATA_W-1:0]                     s_rdata[`N_SLAVES-1:0];
   wire [`N_SLAVES*`DATA_W-1:0]           s_rdata_concat;
   wire [`N_SLAVES-1:0]                   s_valid;
   wire [`N_SLAVES-1:0]                   s_ready;
   
   int_mem int_mem0 (
	             .clk                (clk ),
                     .rst                (reset_int),
                     .boot               (boot), 
`ifndef USE_DDR
 `ifdef USE_BOOT
                     .pvalid             (s_valid[`SRAM_BASE]),
 `endif
`endif
                     //cpu interface
	             .addr               (m_d_addr[`BOOTRAM_ADDR_W-1:2]),
                     .rdata              (int_mem_rdata),
	             .wdata              (m_d_wdata),
	             .wstrb              (m_d_wstrb),
                     .valid              (int_mem_valid),
                     .ready              (int_mem_ready)
	             );
   
`ifndef USE_DDR
 `ifdef USE_BOOT
   assign s_ready[`SRAM_BASE] = int_mem_ready;
   assign s_rdata[`SRAM_BASE] = int_mem_rdata;
 `endif
`endif

   
   //
   // EXTERNAL DDR MAIN MEMORY
   //

`ifdef USE_DDR
   iob_cache #(
               .ADDR_W(`MAINRAM_ADDR_W),
               .DATA_W(`DATA_W)
               )
   cache (
	  .clk (clk),
	  .reset (reset_int),

          //data interface 
	  .wdata (m_wdata),
	  .addr  (m_addr[`MAINRAM_ADDR_W : 2]),
	  .wstrb (m_wstrb),
	  .rdata (ext_mem_rdata),
	  .valid (ext_mem_valid),
	  .ready (ext_mem_ready),
	  .instr (m_instr),

          //
	  // AXI MASTER INTERFACE TO MAIN MEMORY
          //

          //address write
          .AW_ID(m_axi_awid), 
          .AW_ADDR(m_axi_awaddr[`MAINRAM_ADDR_W-1:0]), 
          .AW_LEN(m_axi_awlen), 
          .AW_SIZE(m_axi_awsize), 
          .AW_BURST(m_axi_awburst), 
          .AW_LOCK(m_axi_awlock), 
          .AW_CACHE(m_axi_awcache), 
          .AW_PROT(m_axi_awprot),
          .AW_QOS(m_axi_awqos), 
          .AW_VALID(m_axi_awvalid), 
          .AW_READY(m_axi_awready), 

          //write
          .W_DATA(m_axi_wdata), 
          .W_STRB(m_axi_wstrb), 
          .W_LAST(m_axi_wlast), 
          .W_VALID(m_axi_wvalid), 
          .W_READY(m_axi_wready), 

          //write response
          .B_ID(m_axi_bid), 
          .B_RESP(m_axi_bresp), 
          .B_VALID(m_axi_bvalid), 
          .B_READY(m_axi_bready), 

          //address read
          .AR_ID(m_axi_arid), 
          .AR_ADDR(m_axi_araddr[`MAINRAM_ADDR_W-1:0]), 
          .AR_LEN(m_axi_arlen), 
          .AR_SIZE(m_axi_arsize), 
          .AR_BURST(m_axi_arburst), 
          .AR_LOCK(m_axi_arlock), 
          .AR_CACHE(m_axi_arcache), 
          .AR_PROT(m_axi_arprot), 
          .AR_QOS(m_axi_arqos), 
          .AR_VALID(m_axi_arvalid), 
          .AR_READY(m_axi_arready), 

          //read 
          .R_ID(m_axi_rid), 
          .R_DATA(m_axi_rdata), 
          .R_RESP(m_axi_rresp), 
          .R_LAST(m_axi_rlast), 
          .R_VALID(m_axi_rvalid),  
          .R_READY(m_axi_rready)  
	  );

   assign m_axi_araddr[`ADDR_W-1:`MAINRAM_ADDR_W] = {(`ADDR_W-`MAINRAM_ADDR_W){1'b0}};
   assign m_axi_awaddr[`ADDR_W-1:`MAINRAM_ADDR_W] = {(`ADDR_W-`MAINRAM_ADDR_W){1'b0}};

 `ifdef USE_BOOT
   assign s_ready[`DDR_BASE] = ext_mem_ready;
   assign s_rdata[`DDR_BASE] = ext_mem_rdata;
 `endif
   
`endif



   //
   // PERIPHERALS
   //

   
   //
   // INTERCONNECT
   //
   
   //concatenate slave read data signals to input in interconnect
   genvar                                 i;
   generate 
      for(i=0; i<`N_SLAVES; i=i+1)
        begin : rdata_concat
	   assign s_rdata_concat[((i+1)*`DATA_W)-1 -: `DATA_W] = s_rdata[i];
        end
   endgenerate



   sm2ms_interconnect intercon
     (
      // master interface
      .m_addr  (m_d_addr[`ADDR_W-2 -: `N_SLAVES_W]),
      .m_rdata (p_rdata),
      .m_valid (p_valid),
      .m_ready (p_ready),
      
      // slaves interface
      .s_rdata (s_rdata_concat),
      .s_valid (s_valid),
      .s_ready (s_ready)
      );

   

   //
   // UART
   //
   iob_uart uart(
		 //cpu interface
		 .clk       (clk),
		 .rst       (reset_int),
                 
		 //cpu i/f
		 .valid     (s_valid[`UART_BASE]),
		 .ready     (s_ready[`UART_BASE]),
		 .address   (m_d_addr[4:2]),
		 .write     (m_d_wstrb != 0),                 
		 .data_in   (m_d_wdata),
		 .data_out  (s_rdata[`UART_BASE]),
                 
		 //serial i/f
		 .txd       (uart_txd),
		 .rxd       (uart_rxd),
                 .rts       (uart_rts),
                 .cts       (uart_cts)
		 );
   
   //
   // RESET CONTROLLER
   //
   rst_ctr rst_ctr0 (
                     .clk(clk),
                     .rst(reset),
                     .soft_rst(soft_reset),
                     .boot(boot),
      
                     .wdata(m_d_wdata[0]),
                     .write(m_d_wstrb != 4'd0),
                     .rdata(s_rdata[`SOFT_RESET_BASE]),
                     .valid(s_valid[`SOFT_RESET_BASE]),
                     .ready(s_ready[`SOFT_RESET_BASE])
                     );
   

endmodule
