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

.. _config-preprocessor:

Preprocessor options
--------------------

Real source trees use ```include`` files and macros. Three values pass this
information to the pyslang preprocessor.

``sv_autodoc_include_dirs``
   :Type: ``str`` or ``list[str]``
   :Default: ``[]``

   Directories that pyslang searches for ```include`` files. A relative path
   starts at the Sphinx source directory.

``sv_autodoc_defines``
   :Type: ``str`` or ``list[str]``
   :Default: ``[]``

   Predefined macros. Write each one as ``NAME`` or ``NAME=VALUE``. A
   declaration inside ```ifdef NAME`` becomes visible when ``NAME`` is defined.

``sv_autodoc_std``
   :Type: ``str`` or ``None``
   :Default: ``None``

   The language standard. The allowed values are ``"1364-2005"``,
   ``"1800-2017"``, and ``"1800-2023"``. ``None`` selects the pyslang default.

``sv_autodoc_warn_on_parse_errors``
   :Type: ``bool``
   :Default: ``False``

   Report each pyslang diagnostic as a Sphinx warning. The warning location is
   the SystemVerilog file and line, for example ``rtl/fifo.sv:12``. Each file is
   reported one time per build. Use this option with the preprocessor options
   above to find which include directory or define is missing.

``sv_warn_unresolved_xrefs``
   :Type: ``bool``
   :Default: ``False``

   Report a reference that does not resolve as a Sphinx warning. This includes
   the type links in signatures, which are quiet by default. Also report an
   ambiguous reference, and list the fully qualified names of the candidates.
   The Sphinx option ``nitpicky`` also enables the ambiguity warning.

.. code-block:: python

   sv_autodoc_include_dirs = ["../rtl/include", "../uvm/src"]
   sv_autodoc_defines = ["SYNTHESIS", "DEPTH=16"]
   sv_autodoc_std = "1800-2017"
