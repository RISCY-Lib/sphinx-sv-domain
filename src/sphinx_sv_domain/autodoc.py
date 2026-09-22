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

"""Autodoc-style directives that document SystemVerilog straight from source.

Each ``sv:auto*`` directive parses a ``.sv``/``.svh`` file with pyslang, finds
the requested declaration, and synthesises the equivalent manual directive
(plus any reST written in the declaration's doc-comment).  Routing autodoc
through the same manual directives means the two paths always render, index and
cross-reference identically.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, ClassVar

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

from sphinx_sv_domain.parser import ParseResult, SVDecl, SVGroup, parse_file

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from docutils.nodes import Node
    from sphinx.util.typing import OptionSpec

logger = logging.getLogger(__name__)

__all__ = ["AUTODOC_DIRECTIVES", "SVAutoObject"]

#: Object kinds that ``sv:auto*`` directives can document.
_AUTO_KINDS = (
    "module",
    "interface",
    "program",
    "package",
    "class",
    "function",
    "task",
    "typedef",
    "covergroup",
)

_SV_SUFFIXES = (".sv", ".svh")
_INDENT = "   "

# Per-process parse cache keyed by (path, mtime, group_banners); pyslang parsing
# is pure so this is safe under Sphinx's process-based parallel builds.
_PARSE_CACHE: dict[tuple[str, float, bool], ParseResult] = {}


class SVAutoObject(SphinxDirective):
    """Document a SystemVerilog declaration parsed from a source file."""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True
    option_spec: ClassVar[OptionSpec] = {
        "file": directives.unchanged,
        "no-index": directives.flag,
        "no-index-entry": directives.flag,
        "members": directives.flag,
        "no-members": directives.flag,
        "no-functions": directives.flag,
    }

    def run(self) -> list[Node]:
        base_kind = self.name.split(":")[-1].removeprefix("auto")
        name = self.arguments[0].strip()

        result = self._resolve(name, base_kind, self.config.sv_autodoc_group_banners)
        if result is None:
            return [self._warn(f"could not find SystemVerilog {base_kind} '{name}'")]
        path, decl, all_decls = result
        self.env.note_dependency(path)

        by_parent = _group_by_parent(all_decls)
        rst = "\n".join(self._render(decl, by_parent, indent=0))
        parsed = self.parse_text_to_nodes(rst, offset=self.content_offset)

        # Append any hand-written directive content after the generated body.
        if self.content:
            parsed += self.parse_content_to_nodes()
        return parsed

    # -- source resolution --------------------------------------------------
    def _resolve(
        self,
        name: str,
        kind: str,
        group_banners: bool,
    ) -> tuple[str, SVDecl, list[SVDecl]] | None:
        for path in self._candidate_files():
            parsed = _parse_cached(path, group_banners)
            for decl in parsed.declarations:
                if decl.kind == kind and decl.name == name:
                    return path, decl, parsed.declarations
        return None

    def _candidate_files(self) -> list[str]:
        explicit = self.options.get("file")
        if explicit:
            return [self.env.relfn2path(explicit)[1]]

        configured = self.config.sv_autodoc_source_path
        if not configured:
            return []
        roots = [configured] if isinstance(configured, str) else list(configured)

        files: list[str] = []
        for root in roots:
            abs_root = root if os.path.isabs(root) else os.path.join(self.env.srcdir, root)
            if os.path.isfile(abs_root):
                files.append(abs_root)
            elif os.path.isdir(abs_root):
                for dirpath, _dirs, filenames in os.walk(abs_root):
                    files.extend(
                        os.path.join(dirpath, fn)
                        for fn in sorted(filenames)
                        if fn.endswith(_SV_SUFFIXES)
                    )
        return files

    # -- reST synthesis -----------------------------------------------------
    def _render(
        self,
        decl: SVDecl,
        by_parent: dict[str, list[SVDecl]],
        indent: int,
    ) -> list[str]:
        pad = _INDENT * indent
        body = _INDENT * (indent + 1)
        lines = [f"{pad}.. sv:{decl.kind}:: {_signature_for(decl)}"]

        if decl.kind == "class" and decl.base:
            lines.append(f"{body}:extends: {decl.base}")
        if "no-index" in self.options:
            lines.append(f"{body}:no-index:")
        lines.append("")

        for doc_line in decl.doc.splitlines():
            lines.append(body + doc_line if doc_line else "")
        if decl.doc:
            lines.append("")

        want_members = "no-members" not in self.options
        if want_members:
            lines.extend(self._render_members(decl, by_parent, indent + 1))
        return lines

    def _render_members(
        self,
        decl: SVDecl,
        by_parent: dict[str, list[SVDecl]],
        indent: int,
    ) -> list[str]:
        pad = _INDENT * indent
        lines: list[str] = []

        if decl.params:
            lines += [f"{pad}.. rubric:: Parameters", ""]
            lines += _group_section_lines(
                pad, "parameter", decl.params, decl.param_groups, _param_signature
            )
        if decl.ports:
            lines += [f"{pad}.. rubric:: Ports", ""]
            lines += _group_section_lines(
                pad, "port", decl.ports, decl.port_groups, _port_signature
            )
        for enum in decl.enumerators:
            sig = enum.name if enum.value is None else f"{enum.name} = {enum.value}"
            lines += _member_lines(pad, "enumerator", sig, enum.doc)
        if decl.members:
            if decl.kind == "class":
                lines += [f"{pad}.. rubric:: Properties", ""]
            for member in decl.members:
                signature = f"{member.type} {member.name}".strip()
                lines.append(f"{pad}* ``{signature}``")
                doc = getattr(member, "doc", "")
                if doc:
                    lines.append("")
                    body = pad + "  "
                    lines += [body + line if line else "" for line in doc.splitlines()]
                    lines.append("")
            lines.append("")

        skip_kinds = {"function", "task"} if "no-functions" in self.options else set()
        for child in by_parent.get(decl.name, []):
            if child.kind not in skip_kinds:
                lines.extend(self._render(child, by_parent, indent))
        return lines

    # -- helpers ------------------------------------------------------------
    def _warn(self, message: str) -> nodes.system_message:
        logger.warning(message, location=(self.env.docname, self.lineno), type="sv")
        return self.state.document.reporter.warning(message, line=self.lineno)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------
def _parse_cached(path: str, group_banners: bool) -> ParseResult:
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return parse_file(path, group_banners=group_banners)
    key = (path, mtime, group_banners)
    cached = _PARSE_CACHE.get(key)
    if cached is None:
        cached = parse_file(path, group_banners=group_banners)
        _PARSE_CACHE[key] = cached
    return cached


def _group_by_parent(decls: list[SVDecl]) -> dict[str, list[SVDecl]]:
    grouped: dict[str, list[SVDecl]] = {}
    for decl in decls:
        if decl.parent:
            grouped.setdefault(decl.parent, []).append(decl)
    return grouped


def _member_lines(pad: str, kind: str, signature: str, doc: str) -> list[str]:
    """Emit an ``sv:<kind>`` directive for a member, with its doc as content."""
    lines = [f"{pad}.. sv:{kind}:: {signature}", ""]
    if doc:
        body = pad + _INDENT
        lines += [body + line if line else "" for line in doc.splitlines()]
        lines.append("")
    return lines


def _group_section_lines(
    pad: str,
    kind: str,
    members: Sequence[object],
    groups: list[SVGroup],
    signature: Callable[[object], str],
) -> list[str]:
    """Emit the members of one section, ungrouped first then per ``sv:group``.

    Members carry the ``title`` of the group they belong to; because markers are
    sticky, members of a group are contiguous, so the ordered *groups* are filled
    by walking the member list once.
    """
    lines: list[str] = []
    i, n = 0, len(members)

    def _emit(at: str, member: object) -> None:
        lines.extend(_member_lines(at, kind, signature(member), getattr(member, "doc", "")))

    while i < n and getattr(members[i], "group", None) is None:
        _emit(pad, members[i])
        i += 1

    body = pad + _INDENT
    for group in groups:
        lines += [f"{pad}.. sv:group:: {group.title}", ""]
        if group.desc:
            lines += [body + line if line else "" for line in group.desc.splitlines()]
            lines.append("")
        while i < n and getattr(members[i], "group", None) == group.title:
            _emit(body, members[i])
            i += 1

    # Defensive: emit any members left unclaimed (e.g. an unregistered group).
    while i < n:
        _emit(pad, members[i])
        i += 1
    return lines


def _signature_for(decl: SVDecl) -> str:
    if decl.kind in ("function", "task"):
        args = ", ".join(_arg_text(a) for a in decl.args)
        prefix = f"{decl.return_type} " if decl.kind == "function" and decl.return_type else ""
        return f"{prefix}{decl.name}({args})"
    return decl.name


def _arg_text(arg: object) -> str:
    parts = [
        p
        for p in (getattr(arg, "direction", ""), getattr(arg, "type", ""), getattr(arg, "name", ""))
        if p
    ]
    return " ".join(parts)


def _param_signature(param: object) -> str:
    text = getattr(param, "name", "")
    ptype = getattr(param, "type", "")
    if ptype:
        text = f"{ptype} {text}"
    default = getattr(param, "default", None)
    if default is not None:
        text = f"{text} = {default}"
    return text


def _port_signature(port: object) -> str:
    parts = [
        p
        for p in (
            getattr(port, "direction", ""),
            getattr(port, "type", ""),
            getattr(port, "name", ""),
        )
        if p
    ]
    return " ".join(parts)


#: Mapping of ``auto<kind>`` directive names to the single autodoc directive.
AUTODOC_DIRECTIVES: dict[str, type[SVAutoObject]] = {
    f"auto{kind}": SVAutoObject for kind in _AUTO_KINDS
}
