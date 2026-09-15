// A tiny packet router used to exercise port and parameter grouping.
module router #(
    // === Sizing ===
    parameter int WIDTH = 32,           // Payload width in bits.
    parameter int PORTS = 4             // Number of egress ports.
) (
    input  logic clk,                   // Core clock (ungrouped).
    input  logic rst_n,                 // Active-low reset (ungrouped).
    //! @group Ingress
    //! The inbound payload channel.
    input  logic [WIDTH-1:0] in_data,   // Inbound payload.
    input  logic             in_valid,  // Inbound payload valid.
    // --- Egress ---
    output logic [WIDTH-1:0] out_data,  // Outbound payload.
    output logic             out_valid  // Outbound payload valid.
);
endmodule
