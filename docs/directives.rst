Manual directives
=================

Manual directives take a signature you write by hand and render a documented
SystemVerilog object.  Every object type has one; the directive name is
``sv:<type>`` and its argument is the object's signature.  Nesting a member
directive inside its container (a ``sv:port`` inside a ``sv:module``, a
``sv:function`` inside a ``sv:package``) both scopes the member's name and lets
you cross-reference it.

The ``sv:auto*`` directives (:doc:`autodoc`) build exactly these directives from
source, so anything below applies to autodoc output too.

Common options
--------------

Every object directive accepts the standard Sphinx object-description options:

.. rst:directive:option:: no-index
   :type: flag

   Do not register the object; render it without a cross-reference target or
   index entry.  Handy for illustrative examples.

.. rst:directive:option:: no-index-entry
   :type: flag

   Register the target but omit it from the general index.

.. rst:directive:option:: no-contents-entry
   :type: flag

   Omit the object from the table-of-contents entries.

.. rst:directive:option:: no-typesetting
   :type: flag

   Create the target and index entry but do not render the signature.

Design units
------------

.. rst:directive:: .. sv:module:: signature

   A hardware module.  The signature is a header: an optional ``#( ... )``
   parameter list and an optional ``( ... )`` port list.

   .. code-block:: rst

      .. sv:module:: fifo #(parameter int DEPTH = 16) (input logic clk, output logic full)

         A synchronous FIFO.

   Parameters and ports render as sections beneath the module; document each one
   with a nested :rst:dir:`sv:parameter` / :rst:dir:`sv:port`, or let
   :doc:`autodoc <autodoc>` fill them in from source.  Long lists can be split
   into titled :doc:`groups <grouping>`.

.. rst:directive:: .. sv:interface:: signature
                   .. sv:program:: signature

   An ``interface`` or ``program``.  Both take the same header form as
   :rst:dir:`sv:module`.

Containers
----------

.. rst:directive:: .. sv:package:: name

   A ``package``.  Nest the package's typedefs, functions and tasks inside it so
   they are scoped under ``name::``.

.. rst:directive:: .. sv:class:: name

   A ``class``.  Its base class is shown after ``extends``.

   .. rst:directive:option:: extends
      :type: class name

      The base class, when you are not parsing it from source:

      .. code-block:: rst

         .. sv:class:: reset_txn
            :extends: base_txn

Subroutines
-----------

.. rst:directive:: .. sv:function:: signature
                   .. sv:task:: signature

   A ``function`` (with a return type) or ``task``.  The signature is the
   prototype:

   .. code-block:: rst

      .. sv:function:: int clog2_ceil(int value)

         Ceiling log base 2 of ``value``.

Types
-----

.. rst:directive:: .. sv:typedef:: signature

   A ``typedef``.  An ``enum`` / ``struct`` / ``union`` underlying type renders
   its members.

   .. code-block:: rst

      .. sv:typedef:: enum {IDLE, COUNTING, DONE} state_t

.. rst:directive:: .. sv:struct:: name
                   .. sv:enum:: name
                   .. sv:enumerator:: name

   A standalone ``struct``/``enum``, or a single enumerator.  ``sv:enumerator``
   accepts an optional ``= value``.

Coverage
--------

.. rst:directive:: .. sv:covergroup:: name

   A ``covergroup``.

Members
-------

.. rst:directive:: .. sv:port:: signature

   A single port, e.g. ``input logic [7:0] data``.  The direction becomes a
   keyword and the data type links like any signature type.

.. rst:directive:: .. sv:parameter:: signature

   A single ``parameter``, e.g. ``int WIDTH = 8``.

   .. rst:directive:option:: localparam
      :type: flag

      Render the keyword as ``localparam`` instead of ``parameter``.

Grouping
--------

.. rst:directive:: .. sv:group:: title

   Group the nested ``sv:port`` / ``sv:parameter`` directives under *title*.
   See :doc:`grouping` for the full story, including the source-comment markers
   that produce groups automatically.

Namespaces
----------

Namespaces give cross-references a prefix and group related objects, mirroring
SystemVerilog's package / ``$unit`` scopes.

.. rst:directive:: .. sv:namespace:: name

   Set the current namespace absolutely.  An empty argument (or ``$unit`` /
   ``$root`` / ``none``) returns to the root scope.

.. rst:directive:: .. sv:namespace-push:: name

   Push *name* onto the current namespace.

.. rst:directive:: .. sv:namespace-pop::

   Undo the most recent :rst:dir:`sv:namespace-push`.

.. code-block:: rst

   .. sv:namespace:: soc

   .. sv:module:: dma        # documented as soc::dma

   .. sv:namespace::         # back to the root
