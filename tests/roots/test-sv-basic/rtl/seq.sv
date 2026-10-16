// A parameterized sequence class exercising class parameters and method qualifiers.
class seq #(type REQ = int, int N = 4) extends base;
  // Runs the sequence.
  protected virtual task run();
  endtask

  // Returns the burst count.
  static function int count();
    return N;
  endfunction
endclass
