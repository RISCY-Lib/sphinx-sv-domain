// Utility package for the counter design.
package counter_pkg;
  // Operating state of the counter FSM.
  typedef enum logic [1:0] {IDLE, COUNTING, DONE} state_t;

  // A saturating add of two counts.
  function automatic int sat_add(int a, int b);
    return a + b;
  endfunction
endpackage

// A parameterisable up-counter.
//
// Counts on every rising clock edge while enabled and wraps at ``2**WIDTH``.
module counter #(
    parameter int WIDTH = 8  // Counter width in bits.
) (
    input  logic             clk,    // The counter clock.
    input  logic             rst_n,  // Active-low synchronous reset.
    input  logic             en,     // Count enable.
    output logic [WIDTH-1:0] count   // Current count value.
);
endmodule
