// Observes a counter and captures a running sample for the scoreboard.
//
// On every clock the monitor snapshots the counter's
// :sv:type:`counter_pkg::state_t` alongside its value and emits a
// :sv:type:`counter_pkg::sample_t`.  It is meant to sit beside the
// :sv:module:`counter` it watches.
//
// The package types appear in the port list below and link back to their
// definitions in :sv:package:`counter_pkg`.
module monitor #(
    parameter int WIDTH = 8  // Width of the observed count.
) (
    input  logic                 clk,    // Sample clock.
    input  counter_pkg::state_t  state,  // Current FSM state of the counter.
    input  logic [WIDTH-1:0]     count,  // Current count value.
    output counter_pkg::sample_t snap    // Latest captured sample.
);
endmodule
