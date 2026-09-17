"""Sphinx configuration for the ``sphinx-sv-domain`` documentation.

Build from the repository root with::

    uv run --group docs sphinx-build -b html docs docs/_build/html

or from this directory with ``make html`` (see the bundled ``Makefile``).
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

# -- Project information -----------------------------------------------------
project = "sphinx-sv-domain"
author = "RISCY-Lib Contributors"
copyright = "RISCY-Lib Contributors"  # noqa: A001

try:
    release = version("sphinx-sv-domain")
except PackageNotFoundError:  # pragma: no cover - source checkout without install
    release = "0.0.0"
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------
extensions = [
    # The extension documenting itself: every ``sv:*`` directive and role on
    # these pages is provided by the package described here.
    "sphinx_sv_domain",
    "sphinx.ext.intersphinx",
]

# The ``sv:auto*`` directives on the autodoc/grouping pages parse this RTL.  It
# is the same SystemVerilog that ships in ``examples/demo/src`` -- reused rather
# than duplicated -- and already exercises every feature, grouping included.
sv_autodoc_source_path = ["../examples/demo/src"]

intersphinx_mapping = {
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
    "python": ("https://docs.python.org/3", None),
}

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- HTML output -------------------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_title = f"{project} {release}"
