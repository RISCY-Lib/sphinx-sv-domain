# sphinx-sv-domain: A SystemVerilog language domain for the Sphinx documentation tooling.
# Copyright (C) 2026 RISCY-Lib Contributors
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; If not, see <https://www.gnu.org/licenses/>.

"""Cross-referencing roles for the SystemVerilog domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.roles import XRefRole

if TYPE_CHECKING:
    from docutils.nodes import Element
    from sphinx.environment import BuildEnvironment

__all__ = ["SVXRefRole"]


class SVXRefRole(XRefRole):
    """A cross-reference role that records the active SystemVerilog namespace.

    The current namespace (set by the ``sv:namespace`` family of directives) is
    stored on the reference node so that :meth:`SVDomain.resolve_xref` can
    resolve relative names against the enclosing scope.
    """

    def process_link(
        self,
        env: BuildEnvironment,
        refnode: Element,
        has_explicit_title: bool,
        title: str,
        target: str,
    ) -> tuple[str, str]:
        refnode["sv:namespace"] = env.ref_context.get("sv:namespace")
        # A leading '~' displays only the final scope component of the name.
        if not has_explicit_title and target.startswith("~"):
            target = target[1:]
            title = _last_component(target)
        return title, target


def _last_component(name: str) -> str:
    """Return the final ``::``- or ``.``-separated component of *name*."""
    for sep in ("::", "."):
        if sep in name:
            name = name.rsplit(sep, 1)[-1]
    return name
