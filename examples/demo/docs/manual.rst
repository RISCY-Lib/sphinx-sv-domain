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

Namespaces group related objects and give cross-references a prefix.

.. sv:namespace:: soc

.. sv:module:: dma

   A scatter-gather DMA engine living in the ``soc`` namespace.

.. sv:namespace::

The DMA engine is reachable as :sv:module:`soc::dma`, and the manually
documented timer is :sv:module:`timer`.
