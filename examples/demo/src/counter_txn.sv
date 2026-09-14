// Transaction objects used by the counter's UVM-style testbench.
package counter_txn_pkg;

  // Base sequence item carrying a single stimulus step.
  //
  // Subclasses specialise how ``randomize`` fills the fields.
  class base_txn;
    // Number of cycles to hold ``en`` high.
    int unsigned burst_len;

    // Human-readable one-line summary for logging.
    function automatic string convert2string();
      return $sformatf("burst_len=%0d", burst_len);
    endfunction
  endclass

  // A stimulus item that also drives a reset before counting.
  class reset_txn extends base_txn;
    // Cycles to hold ``rst_n`` low before releasing.
    int unsigned reset_len;
  endclass

endpackage
