// A simple bus interface with body signals and modports.
interface bus_if #(parameter int W = 32) (input logic clk);
  // The data bus.
  logic [W-1:0] data;
  logic valid;   // Transfer valid.
  logic ready;   // Receiver ready.

  // Master modport: drives data and valid, samples ready.
  modport master (output data, output valid, input ready, input clk);
  // Slave modport: samples data and valid, drives ready.
  modport slave  (input data, input valid, output ready, input clk);
endinterface
