sphinx-sv-domain
================

``sphinx-sv-domain`` adds a **SystemVerilog language domain** to `Sphinx
<https://www.sphinx-doc.org/>`_.  It gives you first-class directives and
cross-references for SystemVerilog designs and testbenches -- the same way
Sphinx's built-in domains cover Python, C or C++ -- and it can pull
documentation straight out of your ``.sv`` / ``.svh`` sources.

Two ways to document
--------------------

- **Manual** directives (:rst:dir:`sv:module`, :rst:dir:`sv:function`, ...) take
  a signature you write by hand.
- **Autodoc** directives (:rst:dir:`sv:automodule`, ...) parse a source file with
  `pyslang <https://github.com/MikePopoloski/slang>`_ and render the declaration
  together with the reST written in its doc-comment.

Both paths render, index and cross-reference identically -- autodoc simply
synthesises the manual directives for you.

Highlights
----------

- Modules, interfaces, programs, packages, classes, functions, tasks, typedefs,
  structs, enums, covergroups, ports and parameters.
- Type names in a signature link automatically to their definition, just like
  ``:py:class:`` annotations in the Python domain.
- Namespaces (``$unit`` / package scopes) with relative and absolute references.
- Grouping of a module's ports and parameters into titled sections.

A five-line taste
-----------------

.. code-block:: rst

   .. sv:module:: fifo #(parameter int DEPTH = 16) (input logic clk, output logic full)

      A synchronous FIFO.  Its clock is :sv:port:`clk`.

renders a linkable ``fifo`` module, and elsewhere ``:sv:module:`fifo``` jumps
straight to it.

.. toctree::
   :maxdepth: 2
   :caption: Getting started

   installation
   quickstart
   configuration

.. toctree::
   :maxdepth: 2
   :caption: Reference

   directives
   autodoc
   cross-references
   grouping

Indices
-------

* :ref:`genindex`
* :ref:`SystemVerilog Object Index <sv-objindex>`
