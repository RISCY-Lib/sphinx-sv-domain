`include "defs.svh"

`ifdef WITH_GATED
// Only visible when WITH_GATED is defined.
module gated_mod #(
    parameter int DEPTH = `DEPTH
) (
    input logic [`DATA_WIDTH-1:0] data
);
endmodule
`endif

`ifdef NOT_DEFINED
module hidden_mod;
endmodule
`endif
