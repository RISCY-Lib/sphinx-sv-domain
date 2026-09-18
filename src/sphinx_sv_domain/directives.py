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

"""Object-description and namespace directives for the SystemVerilog domain."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_id

from sphinx_sv_domain.parser import SVDecl, parse_signature
from sphinx_sv_domain.roles import _last_component

if TYPE_CHECKING:
    from docutils.nodes import Node
    from sphinx.addnodes import desc_signature
    from sphinx.util.typing import OptionSpec

    from sphinx_sv_domain.domain import SVDomain

__all__ = [
    "SVGroup",
    "SVNamespace",
    "SVNamespacePop",
    "SVNamespacePush",
    "SVObject",
]

#: Object types that open a new naming scope for the objects nested inside them.
SCOPE_TYPES = frozenset(
    {"module", "interface", "program", "package", "class", "covergroup", "enum"}
)

#: SystemVerilog keyword rendered before the name of each object type.
_KEYWORDS = {
    "module": "module",
    "interface": "interface",
    "program": "program",
    "package": "package",
    "class": "class",
    "function": "function",
    "task": "task",
    "typedef": "typedef",
    "struct": "struct",
    "enum": "enum",
    "covergroup": "covergroup",
    "port": "",
    "parameter": "parameter",
    "enumerator": "",
}

#: Built-in data types, net types and qualifiers that are never linked as the
#: base type of a signature (a port typed ``logic`` should not become a
#: cross-reference).  Anything *not* here is treated as a user-defined type name.
_TYPE_KEYWORDS = frozenset(
    {
        # integral / real / string data types
        "logic", "bit", "reg", "int", "integer", "byte", "shortint", "longint",
        "time", "real", "shortreal", "realtime", "string", "void", "chandle", "event",
        # net types (a typeless net port carries one of these)
        "wire", "supply0", "supply1", "tri", "triand", "trior", "trireg",
        "wand", "wor", "uwire",
        # signedness / lifetime / storage qualifiers that precede the base type
        "signed", "unsigned", "var", "const", "virtual", "static", "automatic",
        "local", "protected", "rand", "randc", "type",
        # aggregate keywords
        "struct", "union", "enum", "packed", "tagged",
        # port directions (may lead a port type string)
        "input", "output", "inout", "ref",
    }
)  # fmt: skip

#: A ``::``-qualified SystemVerilog identifier chain (e.g. ``pkg::sub::type_t``).
_TYPE_CHAIN_RE = re.compile(r"[A-Za-z_]\w*(?:\s*::\s*[A-Za-z_]\w*)*")

#: A reST cross-reference role embedded in a signature, e.g.
#: ``:sv:type:`pkg::foo_t``` or ``:sv:module:`Nice name <pkg::bar>```.  Real
#: SystemVerilog signatures never contain backticks, so this never matches one.
_SIG_ROLE_RE = re.compile(r":(?P<role>[\w:.+-]+):`(?P<content>[^`]+)`")

#: Template for the identifier that stands in for an explicit-role reference
#: while the signature is parsed by pyslang; substituted back to a link after.
_PLACEHOLDER = "__sv_xref_{}__"

#: Matches any placeholder token produced by :data:`_PLACEHOLDER`.
_PLACEHOLDER_RE = re.compile(r"__sv_xref_\d+__")


def _join(namespace: str | None, name: str) -> str:
    """Build a fully-qualified object name from *namespace* and *name*."""
    if namespace and not name.startswith(namespace + "::"):
        return f"{namespace}::{name}"
    return name


def _extract_sig_roles(sig: str) -> tuple[str, dict[str, tuple[str, str, str]]]:
    """Swap embedded reST cross-reference roles for parse-safe placeholders.

    Returns the cleaned signature (each ``:role:`content``` replaced by a
    ``__sv_xref_N__`` identifier that pyslang parses as an ordinary type name)
    and a map from placeholder to ``(reftype, target, title)``.  Ordinary
    signatures contain no backticks, so they come back unchanged with an empty
    map and never pay for this.
    """
    xrefs: dict[str, tuple[str, str, str]] = {}

    def _sub(match: re.Match[str]) -> str:
        reftype = match.group("role").rsplit(":", 1)[-1]
        title, target = _split_xref_content(match.group("content"))
        placeholder = _PLACEHOLDER.format(len(xrefs))
        xrefs[placeholder] = (reftype, target, title)
        return placeholder

    return _SIG_ROLE_RE.sub(_sub, sig), xrefs


def _split_xref_content(content: str) -> tuple[str, str]:
    """Split reST cross-reference *content* into ``(title, target)``.

    Handles the explicit ``Title <target>`` form and the leading ``~`` that
    shows only the final ``::`` component, mirroring
    :meth:`~sphinx_sv_domain.roles.SVXRefRole.process_link`.
    """
    content = content.strip()
    explicit = re.match(r"^(?P<title>.*?)\s*<(?P<target>[^>]+)>$", content)
    if explicit:
        return explicit.group("title").strip(), explicit.group("target").strip()
    if content.startswith("~"):
        target = content[1:].strip()
        return _last_component(target), target
    return content, content


class SVObject(ObjectDescription[str]):
    """Base directive for a documented SystemVerilog object.

    A single class serves every object directive; ``self.objtype`` (derived from
    the directive name by Sphinx) selects the rendering and scoping behaviour.
    """

    option_spec: ClassVar[OptionSpec] = {
        "no-index": directives.flag,
        "no-index-entry": directives.flag,
        "no-contents-entry": directives.flag,
        "no-typesetting": directives.flag,
        "localparam": directives.flag,
        "extends": directives.unchanged,
    }

    def handle_signature(self, sig: str, signode: desc_signature) -> str:
        # Explicit reST cross-reference roles written in the signature (e.g. an
        # ``:sv:type:`pkg::foo_t``` port type) are swapped for parse-safe
        # placeholders here, then rendered back as links in _type_nodes.
        clean_sig, sig_xrefs = _extract_sig_roles(sig)
        try:
            decl = parse_signature(clean_sig, self.objtype)
        except ValueError:
            decl = SVDecl(kind=self.objtype, name=clean_sig.strip())

        namespace = self.env.ref_context.get("sv:namespace")
        fullname = _join(namespace, decl.name)
        signode["sv:namespace"] = namespace
        signode["fullname"] = fullname
        signode["sv:objtype"] = self.objtype

        keyword = _KEYWORDS.get(self.objtype, "")
        if self.objtype == "parameter" and "localparam" in self.options:
            keyword = "localparam"
        elif self.objtype == "port" and decl.direction:
            keyword = decl.direction
        if keyword:
            signode += addnodes.desc_sig_keyword(keyword, keyword)
            signode += addnodes.desc_sig_space()

        if self._show_scope_prefix(namespace):
            prefix = namespace + "::"  # type: ignore[operator]
            signode += addnodes.desc_addname(prefix, prefix)
        signode += addnodes.desc_name(decl.name, decl.name)

        self._render_details(signode, decl, namespace, sig_xrefs)
        return fullname

    def _show_scope_prefix(self, namespace: str | None) -> bool:
        """Whether to display the *namespace* prefix on this object's signature.

        A namespace introduced by an ``sv:namespace`` directive is always shown,
        but the prefix that merely repeats the enclosing documented object (e.g. a
        module's name on each of its ports) is redundant and suppressed unless the
        ``sv_qualify_nested_names`` config opts back into it.
        """
        if not namespace:
            return False
        if self.config.sv_qualify_nested_names:
            return True
        return namespace != self.env.ref_context.get("sv:enclosing_object")

    # -- per-type rendering -------------------------------------------------
    def _render_details(
        self,
        signode: desc_signature,
        decl: SVDecl,
        namespace: str | None,
        sig_xrefs: dict[str, tuple[str, str, str]],
    ) -> None:
        objtype = self.objtype
        if objtype in ("module", "interface", "program"):
            self._render_params(signode, decl, namespace, sig_xrefs)
            self._render_ports(signode, decl, namespace, sig_xrefs)
        elif objtype in ("function", "task"):
            self._render_args(signode, decl, namespace, sig_xrefs)
            if objtype == "function":
                self._render_return(signode, decl, namespace, sig_xrefs)
        elif objtype == "class":
            self._render_extends(signode, decl, namespace, sig_xrefs)
        elif objtype in ("port", "parameter", "enumerator"):
            self._render_typed_leaf(signode, decl, namespace, sig_xrefs)
        elif objtype == "typedef":
            if decl.underlying:
                self._append_typed_annotation(signode, ": ", decl.underlying, namespace, sig_xrefs)

    def _render_params(
        self,
        signode: desc_signature,
        decl: SVDecl,
        namespace: str | None,
        sig_xrefs: dict[str, tuple[str, str, str]],
    ) -> None:
        if not decl.params:
            return
        signode += addnodes.desc_sig_space()
        signode += addnodes.desc_sig_punctuation("#", "#")
        plist = addnodes.desc_parameterlist()
        for param in decl.params:
            node = addnodes.desc_parameter()
            self._extend_spaced(
                node,
                self._type_nodes(param.type, namespace, sig_xrefs),
                [nodes.Text(param.name)] if param.name else [],
            )
            if param.default is not None:
                node += nodes.Text(f" = {param.default}")
            plist += node
        signode += plist

    def _render_ports(
        self,
        signode: desc_signature,
        decl: SVDecl,
        namespace: str | None,
        sig_xrefs: dict[str, tuple[str, str, str]],
    ) -> None:
        if not decl.ports:
            return
        plist = addnodes.desc_parameterlist()
        for port in decl.ports:
            node = addnodes.desc_parameter()
            self._extend_spaced(
                node,
                [nodes.Text(port.direction)] if port.direction else [],
                self._type_nodes(port.type, namespace, sig_xrefs),
                [nodes.Text(port.name)] if port.name else [],
            )
            plist += node
        signode += plist

    def _render_return(
        self,
        signode: desc_signature,
        decl: SVDecl,
        namespace: str | None,
        sig_xrefs: dict[str, tuple[str, str, str]],
    ) -> None:
        ret = decl.return_type or "void"
        returns = addnodes.desc_returns()
        for node in self._type_nodes(ret, namespace, sig_xrefs):
            returns += node
        signode += returns

    def _render_args(
        self,
        signode: desc_signature,
        decl: SVDecl,
        namespace: str | None,
        sig_xrefs: dict[str, tuple[str, str, str]],
    ) -> None:
        plist = addnodes.desc_parameterlist()
        for arg in decl.args:
            node = addnodes.desc_parameter()
            self._extend_spaced(
                node,
                [nodes.Text(arg.direction)] if arg.direction else [],
                self._type_nodes(arg.type, namespace, sig_xrefs),
                [nodes.Text(arg.name)] if arg.name else [],
            )
            plist += node
        signode += plist

    def _render_extends(
        self,
        signode: desc_signature,
        decl: SVDecl,
        namespace: str | None,
        sig_xrefs: dict[str, tuple[str, str, str]],
    ) -> None:
        base = decl.base or self.options.get("extends")
        if base:
            self._append_typed_annotation(signode, " extends ", base, namespace, sig_xrefs)

    def _render_typed_leaf(
        self,
        signode: desc_signature,
        decl: SVDecl,
        namespace: str | None,
        sig_xrefs: dict[str, tuple[str, str, str]],
    ) -> None:
        if decl.datatype:
            self._append_typed_annotation(signode, ": ", decl.datatype, namespace, sig_xrefs)
        if decl.default is not None:
            self._append_annotation(signode, f" = {decl.default}")

    def _append_annotation(self, signode: desc_signature, text: str) -> None:
        signode += addnodes.desc_annotation(text, text)

    def _append_typed_annotation(
        self,
        signode: desc_signature,
        prefix: str,
        type_str: str,
        namespace: str | None,
        sig_xrefs: dict[str, tuple[str, str, str]],
    ) -> None:
        """Append ``prefix`` + a (possibly linked) type as a ``desc_annotation``."""
        ann = addnodes.desc_annotation()
        ann += nodes.Text(prefix)
        for node in self._type_nodes(type_str, namespace, sig_xrefs):
            ann += node
        signode += ann

    # -- type cross-referencing --------------------------------------------
    @staticmethod
    def _extend_spaced(container: nodes.Element, *parts: list[Node]) -> None:
        """Append node-list *parts* to *container*, single-spacing between them.

        Empty parts are skipped so a missing direction or type does not leave a
        stray space, reproducing the ``" ".join(...)`` spacing of plain text.
        """
        first = True
        for part in parts:
            if not part:
                continue
            if not first:
                container += nodes.Text(" ")
            container.extend(part)
            first = False

    def _type_nodes(
        self,
        text: str,
        namespace: str | None,
        sig_xrefs: dict[str, tuple[str, str, str]],
    ) -> list[Node]:
        """Render a type string as inline nodes, cross-referencing type names.

        A string carrying an explicit-role placeholder is rendered from the
        author's own references; otherwise the leading user-defined type name is
        auto-linked.  Names that do not resolve fall back to plain text (Sphinx
        does not warn on xrefs created without ``refwarn``).
        """
        if not text:
            return []
        if _PLACEHOLDER_RE.search(text):
            return self._explicit_type_nodes(text, namespace, sig_xrefs)
        return self._autolink_type(text, namespace)

    def _explicit_type_nodes(
        self,
        text: str,
        namespace: str | None,
        sig_xrefs: dict[str, tuple[str, str, str]],
    ) -> list[Node]:
        out: list[Node] = []
        pos = 0
        for match in _PLACEHOLDER_RE.finditer(text):
            if match.start() > pos:
                out.append(nodes.Text(text[pos : match.start()]))
            reftype, target, title = sig_xrefs.get(
                match.group(0), ("type", match.group(0), match.group(0))
            )
            out.append(self._make_xref(target, title, namespace, reftype))
            pos = match.end()
        if pos < len(text):
            out.append(nodes.Text(text[pos:]))
        return out

    def _autolink_type(self, text: str, namespace: str | None) -> list[Node]:
        # The base type is the leading run before any packed dimension ('[') or
        # interface-modport selector ('.'); the remainder stays plain text.
        cut = len(text)
        for sep in ("[", "."):
            idx = text.find(sep)
            if idx != -1:
                cut = min(cut, idx)
        head, tail = text[:cut], text[cut:]

        chosen: re.Match[str] | None = None
        for match in _TYPE_CHAIN_RE.finditer(head):
            first = match.group(0).split("::", 1)[0].strip()
            if first not in _TYPE_KEYWORDS:
                chosen = match
        if chosen is None:
            return [nodes.Text(text)]

        out: list[Node] = []
        before = head[: chosen.start()]
        after = head[chosen.end() :] + tail
        if before:
            out.append(nodes.Text(before))
        target = re.sub(r"\s+", "", chosen.group(0))
        out.append(self._make_xref(target, chosen.group(0), namespace, "type"))
        if after:
            out.append(nodes.Text(after))
        return out

    def _make_xref(
        self,
        target: str,
        title: str,
        namespace: str | None,
        reftype: str,
    ) -> addnodes.pending_xref:
        """Build a domain cross-reference node for a type name in a signature."""
        ref = addnodes.pending_xref(
            "",
            refdomain="sv",
            reftype=reftype,
            reftarget=target,
        )
        ref["sv:namespace"] = namespace
        ref += nodes.Text(title)
        return ref

    # -- target registration ------------------------------------------------
    def add_target_and_index(self, name: str, sig: str, signode: desc_signature) -> None:
        node_id = make_id(self.env, self.state.document, self.objtype, name)
        signode["ids"].append(node_id)
        self.state.document.note_explicit_target(signode)

        domain: SVDomain = self.env.get_domain("sv")  # type: ignore[assignment]
        domain.note_object(name, self.objtype, node_id, location=signode)

        if "no-index-entry" not in self.options:
            index_text = f"{name} (SystemVerilog {self.objtype})"
            self.indexnode["entries"].append(("single", index_text, node_id, "", None))

    # -- scope management ---------------------------------------------------
    def before_content(self) -> None:
        if self.objtype in SCOPE_TYPES and self.names:
            stack = self.env.ref_context.setdefault("sv:namespace_stack", [])
            stack.append(self.env.ref_context.get("sv:namespace"))
            self.env.ref_context["sv:namespace"] = self.names[-1]
            # Remember the object opening this scope so its members can drop the
            # redundant ``<object>::`` prefix from their own signatures.
            obj_stack = self.env.ref_context.setdefault("sv:enclosing_object_stack", [])
            obj_stack.append(self.env.ref_context.get("sv:enclosing_object"))
            self.env.ref_context["sv:enclosing_object"] = self.names[-1]

    def after_content(self) -> None:
        if self.objtype in SCOPE_TYPES:
            stack = self.env.ref_context.get("sv:namespace_stack", [])
            self.env.ref_context["sv:namespace"] = stack.pop() if stack else None
            obj_stack = self.env.ref_context.get("sv:enclosing_object_stack", [])
            self.env.ref_context["sv:enclosing_object"] = obj_stack.pop() if obj_stack else None


# ---------------------------------------------------------------------------
# Member grouping
# ---------------------------------------------------------------------------
class SVGroup(SphinxDirective):
    """A titled group of ports or parameters inside a module/interface/program.

    Renders as a single-item definition list: the argument is the term and the
    directive content -- an optional description followed by the nested
    ``sv:port`` / ``sv:parameter`` directives -- is the (indented) definition.
    Nesting the members in the definition body gives a clear ``Ports > group >
    members`` hierarchy in every theme without a heading level.  Purely
    presentational: it registers no object and creates no cross-reference
    target, and (unlike a section) never enters the table of contents.  Autodoc
    emits the same directive so grouped source and hand-written docs render alike.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec: ClassVar[OptionSpec] = {}

    def run(self) -> list[Node]:
        title = self.arguments[0].strip()
        term = nodes.term("", title, classes=["sv-group-title"])
        definition = nodes.definition("", *self.parse_content_to_nodes())
        item = nodes.definition_list_item("", term, definition)
        return [nodes.definition_list("", item, classes=["sv-group"])]


# ---------------------------------------------------------------------------
# Namespace directives
# ---------------------------------------------------------------------------
_ROOT_TOKENS = frozenset({"", "$unit", "$root", "none", "None"})


class SVNamespace(SphinxDirective):
    """Set the current SystemVerilog namespace (absolute)."""

    has_content = False
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    def run(self) -> list[Node]:
        arg = self.arguments[0].strip() if self.arguments else ""
        self.env.ref_context["sv:namespace_stack"] = []
        self.env.ref_context["sv:namespace"] = None if arg in _ROOT_TOKENS else arg
        # An absolute namespace is not an enclosing object, so its prefix stays.
        self.env.ref_context["sv:enclosing_object_stack"] = []
        self.env.ref_context["sv:enclosing_object"] = None
        return []


class SVNamespacePush(SphinxDirective):
    """Push a nested namespace component onto the current namespace."""

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self) -> list[Node]:
        arg = self.arguments[0].strip()
        stack = self.env.ref_context.setdefault("sv:namespace_stack", [])
        current = self.env.ref_context.get("sv:namespace")
        stack.append(current)
        self.env.ref_context["sv:namespace"] = _join(current, arg)
        return []


class SVNamespacePop(SphinxDirective):
    """Undo the most recent :rst:dir:`sv:namespace-push`."""

    has_content = False
    required_arguments = 0
    optional_arguments = 0

    def run(self) -> list[Node]:
        stack = self.env.ref_context.get("sv:namespace_stack", [])
        self.env.ref_context["sv:namespace"] = stack.pop() if stack else None
        return []
