// A parameterisable up-counter with enable and synchronous reset.
//
// Counts on every rising ``clk`` edge while ``en`` is high and wraps back to
// zero at ``2**WIDTH``.  Pulling ``rst_n`` low clears the count on the next
// edge.
module counter #(
    parameter int WIDTH = 8  // Width of the count in bits.
) (
    input  logic             clk,    // Clock; counter advances on the rising edge.
    input  logic             rst_n,  // Active-low synchronous reset.
    input  logic             en,     // Count enable.
    output logic [WIDTH-1:0] count,  // Current count value.
    output logic             wrap    // High for one cycle when the count wraps.
);

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      count <= '0;
      wrap  <= 1'b0;
    end else if (en) begin
      {wrap, count} <= count + 1'b1;
    end else begin
      wrap <= 1'b0;
    end
  end

endmodule
