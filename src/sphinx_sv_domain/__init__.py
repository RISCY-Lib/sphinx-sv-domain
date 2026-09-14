"""A SystemVerilog language domain for Sphinx.

Enable it in ``conf.py`` with::

    extensions = ["sphinx_sv_domain"]

and, for the ``sv:auto*`` directives, point it at your sources::

    sv_autodoc_source_path = ["../rtl", "../verif"]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata

__version__ = "0.1.0"

__all__ = ["__version__", "setup"]


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register the SystemVerilog domain with Sphinx."""
    # Imported lazily so that importing this package never eagerly imports
    # pyslang (e.g. for ``sphinx_sv_domain.__version__``).
    from sphinx_sv_domain.domain import SVDomain

    app.add_config_value("sv_autodoc_source_path", None, "env", types=(str, list))
    app.add_domain(SVDomain)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
