// A transaction object exercising class data-member (property) autodoc.
class txn_item;
  // Number of beats in the burst.
  rand int unsigned burst_len;

  // Internal routing tag.  A blank line separates this documented, unqualified
  // member from the one above, so its type must render intact -- a regression
  // guard for the leading-trivia handling in the parser.
  bit [7:0] tag;

  string label;

  // Human-readable one-line summary.
  function automatic string convert2string();
    return label;
  endfunction
endclass
