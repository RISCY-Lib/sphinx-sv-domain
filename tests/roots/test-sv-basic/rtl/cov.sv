// A module that samples a bus.
module cov_mod (input logic clk, input logic [3:0] addr);
  // Address and mode coverage.
  covergroup addr_cg @(posedge clk);
    // Which address was hit.
    cp_addr: coverpoint addr { bins lo = {[0:7]}; }
    coverpoint addr[0];
    x_addr: cross cp_addr, addr[0];
  endgroup
endmodule
