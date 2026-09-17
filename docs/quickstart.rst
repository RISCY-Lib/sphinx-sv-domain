Quickstart
==========

This page walks through documenting a small design from scratch.  It assumes you
have :doc:`installed and enabled <installation>` the extension.

1. Point autodoc at your RTL
----------------------------

In ``conf.py``:

.. code-block:: python

   extensions = ["sphinx_sv_domain"]
   sv_autodoc_source_path = ["../rtl"]

Paths are resolved relative to the documentation source directory (the folder
containing ``conf.py``).

2. Document a comment straight from source
------------------------------------------

Given ``../rtl/fifo.sv``:

.. code-block:: systemverilog

   // A synchronous FIFO with configurable depth and width.
   module fifo #(
       parameter int WIDTH = 8,   // Data width in bits.
       parameter int DEPTH = 16   // Number of entries.
   ) (
       input  logic             clk,   // Write and read clock.
       input  logic [WIDTH-1:0] din,   // Data to enqueue.
       output logic             full   // High when no more entries fit.
   );
   endmodule

a single directive renders the module, its parameters and ports, and the reST in
each doc-comment:

.. code-block:: rst

   .. sv:automodule:: fifo

The trailing comment on each port/parameter becomes its description, so the
generated *Ports* and *Parameters* sections are filled in for you.

3. Or write it by hand
----------------------

When there is no source file -- or you just want prose -- the manual directives
take a signature and render the same way:

.. sv:module:: spi_master #(parameter int CLK_DIV = 4) (input logic clk, output logic sclk)

   A simple SPI master.

   .. sv:port:: input logic clk

      The system clock.

4. Cross-reference it anywhere
------------------------------

Refer to documented objects with the domain roles:

.. code-block:: rst

   The design is :sv:module:`spi_master`; its clock is :sv:port:`spi_master::clk`.

which renders as: the design is :sv:module:`spi_master`; its clock is
:sv:port:`spi_master::clk`.

Where to go next
----------------

- :doc:`directives` -- every manual directive and its options.
- :doc:`autodoc` -- the ``sv:auto*`` directives in depth.
- :doc:`cross-references` -- roles, automatic type links and namespaces.
- :doc:`grouping` -- organise long port/parameter lists into titled groups.
