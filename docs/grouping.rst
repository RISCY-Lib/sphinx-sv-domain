Grouping ports and parameters
=============================

Long port and parameter lists read better in named groups -- *Clock & Reset*,
*AXI*, *Status*, and so on.  The extension can build these groups automatically
from markers in your source, or you can write them by hand.  Grouping is purely
additive: a module with no markers renders exactly as before, and ungrouped
members appear first, before any named group.

Ports and parameters are grouped independently, and the module's one-line header
signature is left flat -- grouping only shapes the *Ports* / *Parameters*
sections beneath it.

Source markers
--------------

Put a marker on its own line inside the ``#( ... )`` parameter list or the port
list.  A marker is **sticky**: it applies to every following member until the
next marker.

There are two marker styles:

``@group`` tags
   A doc tag ``@group Title`` (or ``@defgroup Title``).  Always recognised.

Banner comments
   A symmetric banner such as ``// --- Title ---`` or ``//=== Title ===`` (a run
   of three or more of the same character fencing both sides of the title).
   Recognised unless you disable :ref:`sv_autodoc_group_banners
   <config-group-banners>`.

Comment lines immediately after a marker (before the first member) become the
group's description:

.. code-block:: systemverilog

   module fifo #(
       // === Sizing ===
       parameter int WIDTH = 8,
       parameter int DEPTH = 16
   ) (
       // --- Clock & Reset ---
       input logic clk,
       input logic rst_n,
       //! @group Data
       //! The payload path; widths track WIDTH.
       input  logic [WIDTH-1:0] din,
       output logic [WIDTH-1:0] dout
   );

Rendered from source
~~~~~~~~~~~~~~~~~~~~~

``fifo`` uses banner comments to divide its ports and parameters:

.. sv:automodule:: fifo

``monitor`` uses ``@group`` tags for the same effect:

.. sv:automodule:: monitor

Disabling banners
~~~~~~~~~~~~~~~~~

If a project's decorative banner comments would be misread as group titles, set:

.. code-block:: python

   sv_autodoc_group_banners = False

``@group`` tags still apply; only banner detection is turned off.

By hand
-------

In hand-written docs, wrap the members in a :rst:dir:`sv:group` block.  The
argument is the title and the content is an optional description followed by the
nested :rst:dir:`sv:port` / :rst:dir:`sv:parameter` directives:

.. sv:module:: gpio #(parameter int N = 8) (input logic clk, output logic [7:0] pins)

   A general-purpose IO block.

   .. sv:group:: Clock & Reset

      The single synchronous clock domain.

      .. sv:port:: input logic clk

         Bus clock.

   .. sv:group:: Pads

      .. sv:port:: output logic [7:0] pins

         Bidirectional pad drivers.

How it renders
--------------

Each group is a definition list: the title is the term and its members are the
indented definition body, so the section reads *Ports* -> *group* -> *members*.
The extension injects a small stylesheet automatically, so the nesting is visible
in any theme -- no configuration required.
