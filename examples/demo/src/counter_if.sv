// Bundles the counter's control and status signals for connection to a
// testbench or a higher-level block.
interface counter_if #(
    parameter int WIDTH = 8
) (
    input logic clk  // Shared clock for the bundled signals.
);

  logic             rst_n;  // Active-low synchronous reset.
  logic             en;     // Count enable.
  logic [WIDTH-1:0] count;  // Current count value.
  logic             wrap;   // Wrap strobe.

endinterface
