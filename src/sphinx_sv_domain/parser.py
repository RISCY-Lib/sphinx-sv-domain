"""pyslang-backed SystemVerilog parsing layer.

This module isolates the :mod:`pyslang` dependency from the Sphinx-facing code.
It turns SystemVerilog source (whole files or single-declaration signature
snippets) into plain :class:`SVDecl` dataclasses that the domain, directives and
autodoc code consume.  Nothing outside this module should import ``pyslang``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from pyslang.parsing import Token
from pyslang.syntax import SyntaxKind, SyntaxTree

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

__all__ = [
    "ParseResult",
    "SVArg",
    "SVDecl",
    "SVEnumerator",
    "SVMember",
    "SVParam",
    "SVPort",
    "parse_file",
    "parse_signature",
    "parse_source",
]

# Object kinds this parser understands, mapped from pyslang ``SyntaxKind``.
_KIND_BY_SYNTAX = {
    SyntaxKind.ModuleDeclaration: "module",
    SyntaxKind.InterfaceDeclaration: "interface",
    SyntaxKind.ProgramDeclaration: "program",
    SyntaxKind.PackageDeclaration: "package",
    SyntaxKind.ClassDeclaration: "class",
    SyntaxKind.FunctionDeclaration: "function",
    SyntaxKind.TaskDeclaration: "task",
    SyntaxKind.TypedefDeclaration: "typedef",
    SyntaxKind.CovergroupDeclaration: "covergroup",
}

# Container kinds whose bodies we descend into, and the attribute holding the
# child list (``ModuleDeclarationSyntax`` uses ``members``; classes use ``items``).
_MEMBER_ATTR = {
    "module": "members",
    "interface": "members",
    "program": "members",
    "package": "members",
    "class": "items",
    "covergroup": "members",
}

# SystemVerilog keywords used to wrap bare manual-directive signatures so that
# pyslang can parse them as complete constructs.
_SIGNATURE_WRAP = {
    "module": ("module", "endmodule"),
    "interface": ("interface", "endinterface"),
    "program": ("program", "endprogram"),
    "package": ("package", "endpackage"),
    "class": ("class", "endclass"),
    "function": ("function", "endfunction"),
    "task": ("task", "endtask"),
    "typedef": ("typedef", ""),
}

_IDENT_RE = re.compile(r"[A-Za-z_]\w*")
_LEADING_KW_RE = re.compile(
    r"^\s*(?:module|interface|program|package|class|function|task|typedef|"
    r"struct|union|enum|covergroup)\b"
)
# A double-quoted string literal (with escapes), used to blank out strings before
# hunting for trailing ``//`` comments so a ``//`` inside a string is ignored.
_STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"')
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/")


@dataclass
class SVParam:
    """A ``parameter`` / ``localparam`` of a module, interface or program."""

    name: str
    type: str = ""
    default: str | None = None
    doc: str = ""


@dataclass
class SVPort:
    """A port of a module, interface or program."""

    name: str
    direction: str = ""
    type: str = ""
    doc: str = ""


@dataclass
class SVArg:
    """A formal argument of a function or task."""

    name: str
    direction: str = ""
    type: str = ""


@dataclass
class SVMember:
    """A struct/union field or a class property."""

    name: str
    type: str = ""
    doc: str = ""


@dataclass
class SVEnumerator:
    """A single member of an ``enum``."""

    name: str
    value: str | None = None
    doc: str = ""


@dataclass
class SVDecl:
    """A single documented SystemVerilog declaration.

    A flat, self-contained description produced by the parser.  ``parent`` links
    a declaration to its enclosing scope (e.g. a function inside a package) so
    autodoc can render nested members.
    """

    kind: str
    name: str
    line: int = 0
    column: int = 0
    doc: str = ""
    parent: str | None = None
    params: list[SVParam] = field(default_factory=list)
    ports: list[SVPort] = field(default_factory=list)
    args: list[SVArg] = field(default_factory=list)
    members: list[SVMember] = field(default_factory=list)
    enumerators: list[SVEnumerator] = field(default_factory=list)
    return_type: str | None = None
    base: str | None = None
    underlying: str | None = None
    # Set for leaf declarations parsed from a manual signature (port/parameter/
    # enumerator): the data type and (for ports) the direction.
    datatype: str = ""
    direction: str = ""
    default: str | None = None


@dataclass
class ParseResult:
    """The declarations and diagnostics produced by parsing some source."""

    declarations: list[SVDecl] = field(default_factory=list)
    diagnostics: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class _Ctx:
    """Shared parsing context threaded through the tree walk.

    ``trailing`` maps a 1-based source line number to the cleaned text of any
    comment that trails code on that line, so ports and parameters can adopt the
    comment written beside them as their description.
    """

    sm: object
    trailing: dict[int, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------
def parse_source(text: str) -> ParseResult:
    """Parse a block of SystemVerilog *text* into a :class:`ParseResult`."""
    tree = SyntaxTree.fromText(text)
    return _parse_tree(tree, text)


def parse_file(path: str | Path) -> ParseResult:
    """Parse the SystemVerilog file at *path* into a :class:`ParseResult`."""
    tree = SyntaxTree.fromFile(str(path))
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        text = ""
    return _parse_tree(tree, text)


def parse_signature(sig: str, objtype: str) -> SVDecl:
    """Parse a single manual-directive *signature* for the given *objtype*.

    Signatures are hand-written fragments such as ``counter #(WIDTH) (clk, q)``
    or ``int add(int a, int b)``.  The fragment is wrapped into a complete
    construct and parsed with pyslang; on any failure the leading identifier is
    used as the name so the directive still renders something useful.
    """
    sig = sig.strip()
    if not sig:
        raise ValueError("empty signature")

    if objtype in ("port", "parameter", "enumerator"):
        member = _parse_member_signature(sig, objtype)
        if member is not None:
            return member
        return _fallback_decl(sig, objtype)

    wrapped = _wrap_signature(sig, objtype)
    if wrapped is not None:
        try:
            result = parse_source(wrapped)
        except Exception:
            result = ParseResult()
        for decl in result.declarations:
            if decl.kind == objtype and decl.name:
                return decl
        if result.declarations and result.declarations[0].name:
            return result.declarations[0]

    return _fallback_decl(sig, objtype)


# ---------------------------------------------------------------------------
# Tree walking
# ---------------------------------------------------------------------------
def _parse_tree(tree: SyntaxTree, text: str) -> ParseResult:
    result = ParseResult()
    sm = tree.sourceManager
    for diag in tree.diagnostics:
        try:
            line = sm.getLineNumber(diag.location)
        except Exception:
            line = 0
        result.diagnostics.append((line, str(diag.code)))

    ctx = _Ctx(sm=sm, trailing=_trailing_comments_by_line(text))
    root = tree.root
    for node in _top_level_nodes(root):
        _walk(node, None, ctx, result.declarations)
    return result


def _top_level_nodes(root: object) -> Iterator[object]:
    """Yield the top-level declaration nodes of a parsed tree.

    ``tree.root`` is a ``CompilationUnitSyntax`` for multi-item source but the
    bare item itself for single-item source, so both shapes are handled.
    """
    if getattr(root, "kind", None) == SyntaxKind.CompilationUnit:
        yield from _iter_nodes(getattr(root, "members", []))
    else:
        yield root


def _walk(node: object, parent: str | None, ctx: _Ctx, out: list[SVDecl]) -> None:
    kind = getattr(node, "kind", None)
    objtype = _KIND_BY_SYNTAX.get(kind)
    if objtype is None:
        return

    decl = _build_decl(node, objtype, parent, ctx)
    out.append(decl)

    member_attr = _MEMBER_ATTR.get(objtype)
    if member_attr:
        for child in _iter_nodes(getattr(node, member_attr, []) or []):
            _walk(child, decl.name, ctx, out)


def _build_decl(node: object, objtype: str, parent: str | None, ctx: _Ctx) -> SVDecl:
    line, column = _location(node, ctx.sm)
    decl = SVDecl(
        kind=objtype,
        name="",
        line=line,
        column=column,
        parent=parent,
        doc=_extract_doc(node),
    )

    if objtype in ("module", "interface", "program", "package"):
        _fill_header(node, decl, ctx)
    elif objtype == "class":
        _fill_class(node, decl)
    elif objtype in ("function", "task"):
        _fill_subroutine(node, decl)
    elif objtype == "typedef":
        _fill_typedef(node, decl)
    elif objtype == "covergroup":
        decl.name = _token_text(getattr(node, "name", None))

    if not decl.name:
        decl.name = "<anonymous>"
    return decl


# ---------------------------------------------------------------------------
# Per-construct extraction
# ---------------------------------------------------------------------------
def _fill_header(node: object, decl: SVDecl, ctx: _Ctx) -> None:
    header = getattr(node, "header", None)
    if header is None:
        return
    decl.name = _token_text(getattr(header, "name", None))

    parameters = getattr(header, "parameters", None)
    if parameters is not None:
        for pdecl in _iter_nodes(getattr(parameters, "declarations", [])):
            ptype = _str(getattr(pdecl, "type", None))
            for declarator in _iter_nodes(getattr(pdecl, "declarators", [])):
                default = None
                init = getattr(declarator, "initializer", None)
                if init is not None:
                    default = _str(getattr(init, "expr", None)) or None
                decl.params.append(
                    SVParam(
                        name=_token_text(getattr(declarator, "name", None)),
                        type=ptype,
                        default=default,
                        doc=_trailing_doc(declarator, ctx),
                    )
                )

    ports = getattr(header, "ports", None)
    if ports is not None:
        for port in _iter_nodes(getattr(ports, "ports", [])):
            declarator = getattr(port, "declarator", None)
            if declarator is None:
                continue
            phdr = getattr(port, "header", None)
            # ``direction`` (and a bare ``netType`` such as ``wire``) are read from
            # the token's clean value text: str() would include leading trivia, which
            # is where pyslang parks the *previous* line's trailing comment.
            ptype = _str(getattr(phdr, "dataType", None)) or _token_text(
                getattr(phdr, "netType", None)
            )
            decl.ports.append(
                SVPort(
                    name=_token_text(getattr(declarator, "name", None)),
                    direction=_token_text(getattr(phdr, "direction", None)),
                    type=ptype,
                    doc=_trailing_doc(declarator, ctx),
                )
            )


def _fill_class(node: object, decl: SVDecl) -> None:
    decl.name = _token_text(getattr(node, "name", None))
    extends = getattr(node, "extendsClause", None)
    if extends is not None:
        base = _str(extends)
        decl.base = re.sub(r"^\s*extends\s+", "", base).strip() or None


def _fill_subroutine(node: object, decl: SVDecl) -> None:
    proto = getattr(node, "prototype", None)
    if proto is None:
        return
    decl.name = _str(getattr(proto, "name", None))
    ret = _str(getattr(proto, "returnType", None))
    decl.return_type = ret or ("void" if decl.kind == "function" else None)
    port_list = getattr(proto, "portList", None)
    if port_list is not None:
        for fport in _iter_nodes(getattr(port_list, "ports", [])):
            fdecl = getattr(fport, "declarator", None)
            decl.args.append(
                SVArg(
                    name=_token_text(getattr(fdecl, "name", None)),
                    direction=_token_text(getattr(fport, "direction", None)),
                    type=_str(getattr(fport, "dataType", None)),
                )
            )


def _fill_typedef(node: object, decl: SVDecl) -> None:
    decl.name = _token_text(getattr(node, "name", None))
    dtype = getattr(node, "type", None)
    dkind = getattr(dtype, "kind", None)
    if dkind == SyntaxKind.EnumType:
        decl.underlying = "enum"
        for member in _iter_nodes(getattr(dtype, "members", [])):
            init = getattr(member, "initializer", None)
            value = _str(getattr(init, "expr", None)) if init is not None else None
            decl.enumerators.append(
                SVEnumerator(name=_token_text(getattr(member, "name", None)), value=value or None)
            )
    elif dkind in (SyntaxKind.StructType, SyntaxKind.UnionType):
        decl.underlying = "union" if dkind == SyntaxKind.UnionType else "struct"
        for member in _iter_nodes(getattr(dtype, "members", [])):
            mtype = _str(getattr(member, "type", None))
            for mdecl in _iter_nodes(getattr(member, "declarators", [])):
                decl.members.append(
                    SVMember(name=_token_text(getattr(mdecl, "name", None)), type=mtype)
                )
    elif dtype is not None:
        decl.underlying = _str(dtype) or None


# ---------------------------------------------------------------------------
# Signature-wrapping helpers (manual directives)
# ---------------------------------------------------------------------------
def _wrap_signature(sig: str, objtype: str) -> str | None:
    """Build complete SystemVerilog text from a manual-directive fragment."""
    if objtype in _SIGNATURE_WRAP:
        keyword, end = _SIGNATURE_WRAP[objtype]
        has_keyword = re.match(rf"^\s*{keyword}\b", sig) is not None
        body = sig if has_keyword else f"{keyword} {sig}"
        if end and re.search(rf"\b{end}\b", body):
            return body
        text = body.rstrip(";") + ";"
        return f"{text} {end}" if end else text
    return None


def _parse_member_signature(sig: str, objtype: str) -> SVDecl | None:
    """Parse a leaf signature (port / parameter / enumerator) into an SVDecl."""
    if objtype == "port":
        wrapped = f"module __sig__({sig}); endmodule"
    elif objtype == "parameter":
        wrapped = f"module __sig__ #({sig}) (); endmodule"
    else:  # enumerator
        wrapped = f"typedef enum {{ {sig} }} __sig__;"

    try:
        result = parse_source(wrapped)
    except Exception:
        return None
    if not result.declarations:
        return None
    container = result.declarations[0]

    if objtype == "port" and container.ports:
        port = container.ports[0]
        return SVDecl(kind="port", name=port.name, direction=port.direction, datatype=port.type)
    if objtype == "parameter" and container.params:
        param = container.params[0]
        return SVDecl(kind="parameter", name=param.name, datatype=param.type, default=param.default)
    if objtype == "enumerator" and container.enumerators:
        enum = container.enumerators[0]
        return SVDecl(kind="enumerator", name=enum.name, default=enum.value)
    return None


def _fallback_decl(sig: str, objtype: str) -> SVDecl:
    """Best-effort name extraction when pyslang cannot parse the fragment."""
    stripped = _LEADING_KW_RE.sub("", sig, count=1).strip()
    match = _IDENT_RE.match(stripped)
    name = match.group(0) if match else sig
    return SVDecl(kind=objtype, name=name)


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------
def _iter_nodes(seplist: Iterable[object]) -> Iterator[object]:
    """Yield real nodes from a (possibly comma-separated) pyslang list."""
    try:
        items = list(seplist)
    except TypeError:
        return
    for item in items:
        if not isinstance(item, Token):
            yield item


def _token_text(token: object) -> str:
    if token is None:
        return ""
    value = getattr(token, "valueText", None)
    if value:
        return str(value)
    return _str(token)


def _str(node: object) -> str:
    if node is None:
        return ""
    return str(node).strip()


def _location(node: object, sm: object) -> tuple[int, int]:
    rng = getattr(node, "sourceRange", None)
    if rng is None:
        return (0, 0)
    try:
        return (sm.getLineNumber(rng.start), sm.getColumnNumber(rng.start))  # type: ignore[attr-defined]
    except Exception:
        return (0, 0)


def _extract_doc(node: object) -> str:
    """Return the reST doc-comment block immediately preceding *node*.

    Reads the leading trivia of the declaration's first token and collects the
    contiguous run of ``//`` / ``/* */`` comments, stopping at a blank line.
    """
    try:
        token = node.getFirstToken()  # type: ignore[attr-defined]
    except Exception:
        return ""
    trivia = list(getattr(token, "trivia", []) or [])

    lines: list[str] = []
    newline_run = 0
    for triv in reversed(trivia):
        kind = str(getattr(triv, "kind", ""))
        if "LineComment" in kind or "BlockComment" in kind:
            lines.append(_clean_comment(_raw_text(triv)))
            newline_run = 0
        elif "EndOfLine" in kind:
            newline_run += 1
            if newline_run >= 2 and lines:
                break
        elif "Whitespace" in kind:
            continue
        else:
            break
    lines.reverse()
    return "\n".join(line for line in lines if line is not None).strip()


def _raw_text(triv: object) -> str:
    getter = getattr(triv, "getRawText", None)
    if callable(getter):
        return str(getter())
    return str(getattr(triv, "rawText", ""))


def _clean_comment(text: str) -> str:
    """Strip comment markers from a single trivia comment, preserving reST."""
    text = text.strip()
    if text.startswith("//"):
        # Drop the '//' marker (and any doxygen '/' or '!'), then one space.
        body = text[2:].lstrip("/!")
        if body.startswith(" "):
            body = body[1:]
        return body.rstrip()
    if text.startswith("/*"):
        text = text[2:]
        if text.endswith("*/"):
            text = text[:-2]
        cleaned = []
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith("*"):
                line = line[1:]
            cleaned.append(line.rstrip())
        # Drop leading/trailing blank lines from block comments.
        while cleaned and not cleaned[0].strip():
            cleaned.pop(0)
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()
        return "\n".join(cleaned)
    return text


def _trailing_comments_by_line(text: str) -> dict[int, str]:
    """Map each 1-based line number to the comment trailing code on that line.

    A comment counts as *trailing* only when non-whitespace code precedes it, so
    stand-alone doc-comment lines are ignored.  String literals are blanked
    (preserving column positions) so a ``//`` inside a string default value is not
    mistaken for a comment.
    """
    out: dict[int, str] = {}
    for lineno, raw in enumerate(text.splitlines(), start=1):
        code = _STRING_RE.sub(lambda m: " " * (m.end() - m.start()), raw)
        line_pos = code.find("//")
        if line_pos != -1:
            # A ``//`` comment always runs to end of line, so it is the trailing
            # one even if an inline ``/* */`` (e.g. a width annotation) precedes it.
            start, end = line_pos, len(raw)
        else:
            # Otherwise accept a block comment only when it genuinely trails the
            # code; an embedded ``/* */`` with code after it is part of the type.
            block = None
            for match in _BLOCK_COMMENT_RE.finditer(code):
                block = match
            if block is None or code[block.end() :].strip():
                continue
            start, end = block.start(), block.end()
        if not code[:start].strip():
            continue  # nothing but the comment on this line
        comment = _clean_comment(raw[start:end])
        if comment:
            out[lineno] = comment
    return out


def _trailing_doc(node: object, ctx: _Ctx) -> str:
    """Return the trailing comment on the source line where *node* begins."""
    if not ctx.trailing:
        return ""
    rng = getattr(node, "sourceRange", None)
    if rng is None:
        return ""
    try:
        line = ctx.sm.getLineNumber(rng.start)  # type: ignore[attr-defined]
    except Exception:
        return ""
    return ctx.trailing.get(line, "")
