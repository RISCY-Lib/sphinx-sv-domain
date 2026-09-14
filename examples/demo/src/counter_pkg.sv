// Shared types and helpers for the counter design.
//
// Everything the counter and its testbench need to agree on lives here so the
// RTL and verification code share a single source of truth.
package counter_pkg;

  // Operating state of the counter FSM.
  //
  // The counter powers up in ``IDLE`` and only advances while ``en`` is
  // asserted.
  typedef enum logic [1:0] {
    IDLE,      // Holding the current value.
    COUNTING,  // Incrementing on every clock edge.
    DONE       // Terminal count reached and latched.
  } state_t;

  // A snapshot of the counter for scoreboard comparison: the current count
  // paired with the FSM state at capture time.
  typedef struct packed {
    logic [31:0] value;
    state_t      state;
  } sample_t;

  // Ceiling of log base 2 of ``value``.
  //
  // Used to size the counter's storage from a depth parameter.
  function automatic int clog2_ceil(int value);
    int result;
    result = 0;
    for (int v = value - 1; v > 0; v = v >> 1) begin
      result++;
    end
    return result;
  endfunction

  // Saturating add of two counts that never wraps past ``max``.
  function automatic int sat_add(int a, int b, int max);
    int sum;
    sum = a + b;
    return (sum > max) ? max : sum;
  endfunction

endpackage
