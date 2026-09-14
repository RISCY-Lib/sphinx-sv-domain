Automatic documentation
========================

Each directive below parses a ``.sv`` file from ``../src`` and renders the
declaration together with the reST written in its doc-comment.  Change the RTL
and rebuild - the docs follow.

Design modules
--------------

.. sv:automodule:: counter

.. sv:automodule:: fifo

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
