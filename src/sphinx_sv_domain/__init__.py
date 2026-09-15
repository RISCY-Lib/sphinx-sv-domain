"""A SystemVerilog language domain for Sphinx.

Enable it in ``conf.py`` with::

    extensions = ["sphinx_sv_domain"]

and, for the ``sv:auto*`` directives, point it at your sources::

    sv_autodoc_source_path = ["../rtl", "../verif"]
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata

__version__ = "0.1.0"

__all__ = ["__version__", "setup"]

#: Bundled static assets (stylesheet for grouped ports/parameters, etc.).
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
_CSS_FILE = "sv-domain.css"


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register the SystemVerilog domain with Sphinx."""
    # Imported lazily so that importing this package never eagerly imports
    # pyslang (e.g. for ``sphinx_sv_domain.__version__``).
    from sphinx_sv_domain.domain import SVDomain

    app.add_config_value("sv_autodoc_source_path", None, "env", types=(str, list))
    # When true, nested members repeat their enclosing scope in the displayed
    # signature (e.g. ``fifo::clk``); off by default so members read as ``clk``.
    app.add_config_value("sv_qualify_nested_names", False, "env", types=(bool,))
    # When true, symmetric banner comments (``// --- Title ---``) in a source
    # port/parameter list open member groups; ``@group`` tags always do.  Turn
    # off if a project's decorative banners are misread as group titles.
    app.add_config_value("sv_autodoc_group_banners", True, "env", types=(bool,))
    app.add_domain(SVDomain)

    # Ship a small stylesheet so grouped ports/parameters read as nested blocks
    # even in themes that leave definition-list terms unstyled.
    app.add_css_file(_CSS_FILE)
    app.connect("build-finished", _copy_static_assets)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def _copy_static_assets(app: Sphinx, exc: Exception | None) -> None:
    """Copy the bundled CSS into the HTML output's ``_static`` directory."""
    if exc is not None or app.builder.format != "html":
        return
    from sphinx.util.fileutil import copy_asset_file

    copy_asset_file(os.path.join(_STATIC_DIR, _CSS_FILE), os.path.join(app.outdir, "_static"))
