"""Sphinx configuration for the sphinx-sv-domain demo.

Run ``sphinx-build -b html . _build/html`` from this directory (with the
``sphinx-sv-domain`` package installed) to build the demo docs.
"""

project = "sphinx-sv-domain demo"
author = "RISCY-Lib Contributors"

extensions = ["sphinx_sv_domain"]

# Where the ``sv:auto*`` directives look for SystemVerilog sources.  Paths are
# resolved relative to this ``docs/`` directory, so ``../src`` points at the
# example RTL that ships alongside these docs.
sv_autodoc_source_path = ["../src"]

master_doc = "index"
exclude_patterns = ["_build"]

html_theme = "alabaster"
