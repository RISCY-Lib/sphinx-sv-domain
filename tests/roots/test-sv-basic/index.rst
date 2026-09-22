SystemVerilog Domain Test
=========================

Manual directives
-----------------

.. sv:module:: fifo #(parameter int DEPTH = 16) (input logic clk, output logic full)

   A synchronous FIFO with configurable depth.

   .. sv:port:: input logic clk

      The clock.

.. sv:package:: my_pkg

   .. sv:function:: int clog2(int value)

      Ceiling log base 2.

   .. sv:typedef:: enum {RED, GREEN, BLUE} color_t

      A colour.

Manual grouping
---------------

.. sv:module:: gpio #(parameter int N = 8) (input logic clk, output logic [7:0] pins)

   A general-purpose IO block documented by hand.

   .. sv:group:: Clock & Reset

      The single synchronous clock domain.

      .. sv:port:: input logic clk

         Bus clock.

   .. sv:group:: Pads

      .. sv:port:: output logic [7:0] pins

         Bidirectional pad drivers.

Signature type links
---------------------

.. sv:module:: sampler #(parameter int N = 4) (input my_pkg::color_t tint, output logic done)

   A module whose header port type links to its typedef.

.. sv:module:: bridge (input :sv:type:`my_pkg::color_t` din, output logic valid)

   An explicit cross-reference role written inside the signature.

Namespaces
----------

.. sv:namespace:: chip_top

.. sv:module:: alu

   Arithmetic logic unit inside ``chip_top``.

.. sv:namespace-push:: sub

.. sv:task:: reset

   A task nested two scopes deep.

Relative reference while scoped: :sv:task:`reset`.

.. sv:namespace-pop::

.. sv:namespace::

Cross references
----------------

See :sv:module:`fifo` and :sv:func:`my_pkg::clog2` and :sv:obj:`color_t`.
The namespaced ALU is :sv:module:`chip_top::alu` and the deep task is
:sv:task:`chip_top::sub::reset`.
Abbreviated display: :sv:module:`~chip_top::alu`.
Generic any-role: :any:`fifo`.

Autodoc
-------

.. sv:automodule:: counter

.. sv:automodule:: router

.. sv:autopackage:: counter_pkg

.. sv:autoclass:: txn_item

Index
-----

* :ref:`genindex`
