Autodoc
=======

The ``sv:auto*`` directives parse a ``.sv`` / ``.svh`` file with `pyslang
<https://github.com/MikePopoloski/slang>`_, find the requested declaration, and
render it together with the reST written in its doc-comment.  Under the hood they
synthesise the equivalent :doc:`manual directive <directives>`, so autodoc and
hand-written docs render, index and cross-reference identically.

Doc-comments are the ``//`` or ``/* */`` comments immediately preceding a
declaration; their body is treated as reST.  A trailing comment on a port or
parameter line becomes that member's description.

Pointing at sources
-------------------

Set :ref:`sv_autodoc_source_path <config-source-path>` in ``conf.py`` to the
files or directories to search:

.. code-block:: python

   sv_autodoc_source_path = ["../rtl", "../verif"]

The directives
--------------

.. rst:directive:: .. sv:automodule:: name

   Document the module *name* found in the configured sources.  There is one
   ``sv:auto*`` directive per documentable type:

   ``sv:automodule``, ``sv:autointerface``, ``sv:autoprogram``,
   ``sv:autopackage``, ``sv:autoclass``, ``sv:autofunction``, ``sv:autotask``,
   ``sv:autotypedef``, ``sv:autocovergroup``.

   Documenting a container (a package or class) pulls in its members.

   .. rst:directive:option:: file
      :type: path

      Parse this specific file instead of searching
      :ref:`sv_autodoc_source_path <config-source-path>`.  The path is relative
      to the current document.

      .. code-block:: rst

         .. sv:autoclass:: base_txn
            :file: ../rtl/counter_txn.sv

   .. rst:directive:option:: members
      :type: flag

      Render nested members (the default).

   .. rst:directive:option:: no-members
      :type: flag

      Document only the declaration itself, skipping its members.

   .. rst:directive:option:: no-functions
      :type: flag

      Render a class without documenting the functions and tasks it contains.
      Properties, parameters, and nested types are still included.

   .. rst:directive:option:: no-index
      :type: flag

      Render without registering a cross-reference target or index entry.

Examples
--------

The remainder of this page is generated from the SystemVerilog that ships in the
project's ``examples/demo/src`` directory.  Change the RTL and rebuild -- the
docs follow.

A module
~~~~~~~~

.. code-block:: rst

   .. sv:automodule:: counter

.. sv:automodule:: counter

An interface
~~~~~~~~~~~~

.. sv:autointerface:: counter_if

A package and its members
~~~~~~~~~~~~~~~~~~~~~~~~~~

Documenting a package renders the enum, struct and functions declared inside it:

.. sv:autopackage:: counter_pkg

Classes
~~~~~~~

.. sv:autopackage:: counter_txn_pkg
