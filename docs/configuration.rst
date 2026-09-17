Configuration
=============

The extension adds three configuration values, all set in your project's
``conf.py``.

.. _config-source-path:

``sv_autodoc_source_path``
--------------------------

:Type: ``str`` or ``list[str]``
:Default: ``None``

Where the ``sv:auto*`` directives (:doc:`autodoc`) look for SystemVerilog
sources.  Entries may be individual ``.sv`` / ``.svh`` files or directories,
which are searched recursively.  Paths are resolved relative to the
documentation source directory (the folder containing ``conf.py``); absolute
paths are used as-is.

.. code-block:: python

   sv_autodoc_source_path = ["../rtl", "../verif/env"]

When it is unset, ``sv:auto*`` directives can still be pointed at a specific file
with their ``:file:`` option (see :doc:`autodoc`).

.. _config-qualify-nested:

``sv_qualify_nested_names``
---------------------------

:Type: ``bool``
:Default: ``False``

Whether a nested member repeats its enclosing scope in the *displayed*
signature.  By default a module's port renders as ``clk``; enabling this shows
the fully-qualified ``fifo::clk`` instead.  It affects display only -- the
cross-reference target is the fully-qualified name either way.

.. code-block:: python

   sv_qualify_nested_names = True

.. _config-group-banners:

``sv_autodoc_group_banners``
----------------------------

:Type: ``bool``
:Default: ``True``

Whether symmetric *banner* comments (``// --- Clock & Reset ---``) in a source
port/parameter list open a member group (:doc:`grouping`).  ``@group`` tags are
always honoured; set this to ``False`` if a project's decorative banner comments
would otherwise be misread as group titles.

.. code-block:: python

   sv_autodoc_group_banners = False  # opt out of banner detection
