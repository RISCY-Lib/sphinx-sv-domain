// A synchronous FIFO with configurable depth and data width.
//
// Single clock domain; ``full`` and ``empty`` are combinational flags derived
// from the read and write pointers.
module fifo #(
    parameter int WIDTH = 8,   // Data width in bits.
    parameter int DEPTH = 16   // Number of entries; should be a power of two.
) (
    input  logic             clk,      // Write and read clock.
    input  logic             rst_n,    // Active-low synchronous reset.
    input  logic             push,     // Enqueue ``din`` when not full.
    input  logic             pop,      // Dequeue into ``dout`` when not empty.
    input  logic [WIDTH-1:0] din,      // Data to enqueue.
    output logic [WIDTH-1:0] dout,     // Data at the front of the queue.
    output logic             full,     // High when no more entries fit.
    output logic             empty     // High when the queue holds nothing.
);
endmodule
