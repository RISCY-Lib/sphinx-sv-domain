Automatic documentation
========================

Each directive below parses a ``.sv`` file from ``../src`` and renders the
declaration together with the reST written in its doc-comment.  Change the RTL
and rebuild - the docs follow.

Design modules
--------------

.. sv:automodule:: counter

The ``fifo`` divides its port list with ``--- banner ---`` comments and its
parameters with a banner too; each becomes a sub-heading under *Ports* /
*Parameters*.  The ``monitor`` below uses ``//! @group`` tags for the same
effect.  Set ``sv_autodoc_group_banners = False`` in ``conf.py`` to ignore
banners (``@group`` tags always apply).

.. sv:automodule:: fifo

The ``monitor`` reuses types from ``counter_pkg`` in its port list.  Because
those types are documented (below), the ``state`` and ``snap`` port types in the
generated *Ports* table are clickable and jump straight to their definitions.

.. sv:automodule:: monitor

Interfaces
----------

.. sv:autointerface:: counter_if

Shared package
--------------

Documenting a package pulls in its members - the enum, struct, function and
task all render underneath it.

.. sv:autopackage:: counter_pkg

Verification classes
--------------------

.. sv:autopackage:: counter_txn_pkg

You can also document a single class on its own and point the directive at a
specific file with the ``:file:`` option:

.. sv:autoclass:: base_txn
   :file: ../src/counter_txn.sv
