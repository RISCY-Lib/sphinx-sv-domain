Manual documentation
=====================

When there is no source file - or you want to describe something by hand - the
manual directives take a signature and render the same way autodoc does.

.. sv:module:: timer #(parameter int WIDTH = 16) (input logic clk, output logic tick)

   A free-running timer that raises ``tick`` once every ``2**WIDTH`` cycles.

   .. sv:port:: input logic clk

      Counting clock.

   .. sv:parameter:: int WIDTH = 16

      Width of the internal free-running counter.

Linking types from a signature
-------------------------------

Type names in a signature link to their definition automatically - the same way
``:py:class:`` annotations do in the Python domain.  Built-in types such as
``logic`` stay plain; a user-defined type resolves to wherever it is documented.
Here ``counter_pkg::state_t`` and ``counter_pkg::sample_t`` (defined by
:sv:package:`counter_pkg` on the autodoc page) become links right in the header:

.. sv:module:: sampler #(parameter int N = 4) (input counter_pkg::state_t st, output counter_pkg::sample_t snap)

   Samples the counter FSM state into a packed record.

When you want to be explicit - or give the link a nicer label - write an
ordinary cross-reference role inside the signature.  It renders as a link just
like it would in prose:

.. sv:module:: bridge (input :sv:type:`counter_pkg::sample_t` din, output logic valid)

   Forwards a captured :sv:type:`counter_pkg::sample_t` downstream.

Namespaces group related objects and give cross-references a prefix.

.. sv:namespace:: soc

.. sv:module:: dma

   A scatter-gather DMA engine living in the ``soc`` namespace.

.. sv:namespace::

The DMA engine is reachable as :sv:module:`soc::dma`, and the manually
documented timer is :sv:module:`timer`.
