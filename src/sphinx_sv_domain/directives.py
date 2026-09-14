"""Object-description and namespace directives for the SystemVerilog domain."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_id

from sphinx_sv_domain.parser import SVDecl, parse_signature

if TYPE_CHECKING:
    from docutils.nodes import Node
    from sphinx.addnodes import desc_signature
    from sphinx.util.typing import OptionSpec

    from sphinx_sv_domain.domain import SVDomain

__all__ = [
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


def _join(namespace: str | None, name: str) -> str:
    """Build a fully-qualified object name from *namespace* and *name*."""
    if namespace and not name.startswith(namespace + "::"):
        return f"{namespace}::{name}"
    return name


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
        try:
            decl = parse_signature(sig, self.objtype)
        except ValueError:
            decl = SVDecl(kind=self.objtype, name=sig.strip())

        namespace = self.env.ref_context.get("sv:namespace")
        fullname = _join(namespace, decl.name)
        signode["sv:namespace"] = namespace
        signode["fullname"] = fullname
        signode["sv:objtype"] = self.objtype

        keyword = _KEYWORDS.get(self.objtype, "")
        if self.objtype == "parameter" and "localparam" in self.options:
            keyword = "localparam"
        if keyword:
            signode += addnodes.desc_sig_keyword(keyword, keyword)
            signode += addnodes.desc_sig_space()

        if namespace:
            prefix = namespace + "::"
            signode += addnodes.desc_addname(prefix, prefix)
        signode += addnodes.desc_name(decl.name, decl.name)

        self._render_details(signode, decl)
        return fullname

    # -- per-type rendering -------------------------------------------------
    def _render_details(self, signode: desc_signature, decl: SVDecl) -> None:
        objtype = self.objtype
        if objtype in ("module", "interface", "program"):
            self._render_params(signode, decl)
            self._render_ports(signode, decl)
        elif objtype in ("function", "task"):
            self._render_args(signode, decl)
            if objtype == "function":
                self._render_return(signode, decl)
        elif objtype == "class":
            self._render_extends(signode, decl)
        elif objtype in ("port", "parameter", "enumerator"):
            self._render_typed_leaf(signode, decl)
        elif objtype == "typedef":
            if decl.underlying:
                self._append_annotation(signode, f": {decl.underlying}")

    def _render_params(self, signode: desc_signature, decl: SVDecl) -> None:
        if not decl.params:
            return
        signode += addnodes.desc_sig_space()
        signode += addnodes.desc_sig_punctuation("#", "#")
        plist = addnodes.desc_parameterlist()
        for param in decl.params:
            text = param.name
            if param.type:
                text = f"{param.type} {param.name}"
            if param.default is not None:
                text = f"{text} = {param.default}"
            plist += addnodes.desc_parameter(text, text)
        signode += plist

    def _render_ports(self, signode: desc_signature, decl: SVDecl) -> None:
        if not decl.ports:
            return
        plist = addnodes.desc_parameterlist()
        for port in decl.ports:
            parts = [p for p in (port.direction, port.type, port.name) if p]
            text = " ".join(parts)
            plist += addnodes.desc_parameter(text, text)
        signode += plist

    def _render_return(self, signode: desc_signature, decl: SVDecl) -> None:
        ret = decl.return_type or "void"
        signode += addnodes.desc_returns(ret, ret)

    def _render_args(self, signode: desc_signature, decl: SVDecl) -> None:
        plist = addnodes.desc_parameterlist()
        for arg in decl.args:
            parts = [p for p in (arg.direction, arg.type, arg.name) if p]
            text = " ".join(parts)
            plist += addnodes.desc_parameter(text, text)
        signode += plist

    def _render_extends(self, signode: desc_signature, decl: SVDecl) -> None:
        base = decl.base or self.options.get("extends")
        if base:
            self._append_annotation(signode, f" extends {base}")

    def _render_typed_leaf(self, signode: desc_signature, decl: SVDecl) -> None:
        if decl.datatype:
            self._append_annotation(signode, f": {decl.datatype}")
        if decl.default is not None:
            self._append_annotation(signode, f" = {decl.default}")

    def _append_annotation(self, signode: desc_signature, text: str) -> None:
        signode += addnodes.desc_annotation(text, text)

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

    def after_content(self) -> None:
        if self.objtype in SCOPE_TYPES:
            stack = self.env.ref_context.get("sv:namespace_stack", [])
            self.env.ref_context["sv:namespace"] = stack.pop() if stack else None


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
