Installation
============

Requirements
------------

- Python 3.12 or newer
- Sphinx 8.0 or newer
- `pyslang <https://github.com/MikePopoloski/slang>`_ 11.x (installed
  automatically as a dependency)

Install the package
-------------------

With ``pip``:

.. code-block:: console

   $ pip install sphinx-sv-domain

or with `uv <https://docs.astral.sh/uv/>`_:

.. code-block:: console

   $ uv add sphinx-sv-domain

Enable the extension
--------------------

Add the package to ``extensions`` in your project's ``conf.py``:

.. code-block:: python

   extensions = [
       "sphinx_sv_domain",
   ]

That is enough for the manual directives (:doc:`directives`) and the
cross-referencing roles (:doc:`cross-references`).  To document ``.sv`` files
directly with the ``sv:auto*`` directives, also tell the extension where your
sources live -- see :doc:`configuration`:

.. code-block:: python

   sv_autodoc_source_path = ["../rtl", "../verif"]

The extension ships a small stylesheet that it injects automatically, so grouped
ports and parameters (:doc:`grouping`) render as nested blocks in any theme with
no further setup.

Next steps
----------

Head to the :doc:`quickstart` for a minimal end-to-end example.
