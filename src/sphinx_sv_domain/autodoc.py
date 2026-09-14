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

from sphinx_sv_domain.parser import ParseResult, SVDecl, parse_file

if TYPE_CHECKING:
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

# Per-process parse cache keyed by (path, mtime); pyslang parsing is pure so
# this is safe under Sphinx's process-based parallel builds.
_PARSE_CACHE: dict[tuple[str, float], ParseResult] = {}


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
    }

    def run(self) -> list[Node]:
        base_kind = self.name.split(":")[-1].removeprefix("auto")
        name = self.arguments[0].strip()

        result = self._resolve(name, base_kind)
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
    ) -> tuple[str, SVDecl, list[SVDecl]] | None:
        for path in self._candidate_files():
            parsed = _parse_cached(path)
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

        for param in decl.params:
            lines.append(f"{pad}.. sv:parameter:: {_param_signature(param)}")
            lines.append("")
        for port in decl.ports:
            lines.append(f"{pad}.. sv:port:: {_port_signature(port)}")
            lines.append("")
        for enum in decl.enumerators:
            sig = enum.name if enum.value is None else f"{enum.name} = {enum.value}"
            lines.append(f"{pad}.. sv:enumerator:: {sig}")
            lines.append("")
        if decl.members:
            for member in decl.members:
                lines.append(f"{pad}* ``{member.type} {member.name}``")
            lines.append("")

        for child in by_parent.get(decl.name, []):
            lines.extend(self._render(child, by_parent, indent))
        return lines

    # -- helpers ------------------------------------------------------------
    def _warn(self, message: str) -> nodes.system_message:
        logger.warning(message, location=(self.env.docname, self.lineno), type="sv")
        return self.state.document.reporter.warning(message, line=self.lineno)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------
def _parse_cached(path: str) -> ParseResult:
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return parse_file(path)
    key = (path, mtime)
    cached = _PARSE_CACHE.get(key)
    if cached is None:
        cached = parse_file(path)
        _PARSE_CACHE[key] = cached
    return cached


def _group_by_parent(decls: list[SVDecl]) -> dict[str, list[SVDecl]]:
    grouped: dict[str, list[SVDecl]] = {}
    for decl in decls:
        if decl.parent:
            grouped.setdefault(decl.parent, []).append(decl)
    return grouped


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
