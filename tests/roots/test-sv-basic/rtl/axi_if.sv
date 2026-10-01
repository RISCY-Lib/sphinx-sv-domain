// A minimal AXI-like interface for testing.
interface axi_if #(parameter int W = 32) (input logic clk);
  // Data bus width ``W`` bits.
  logic [W-1:0] data;  // The data payload.
  logic valid;         // Data valid flag.
  logic ready;         // Downstream ready.

  // Master modport for initiating transfers.
  modport master (output data, output valid, input ready);
  // Slave modport for accepting transfers.
  modport slave  (input data, input valid, output ready);
endinterface
