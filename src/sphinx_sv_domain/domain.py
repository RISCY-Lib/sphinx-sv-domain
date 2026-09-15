"""The SystemVerilog Sphinx domain."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, NamedTuple

from sphinx.domains import Domain, Index, IndexEntry, ObjType
from sphinx.locale import _
from sphinx.util import logging
from sphinx.util.nodes import make_refnode

from sphinx_sv_domain.autodoc import AUTODOC_DIRECTIVES
from sphinx_sv_domain.directives import (
    SVGroup,
    SVNamespace,
    SVNamespacePop,
    SVNamespacePush,
    SVObject,
)
from sphinx_sv_domain.roles import SVXRefRole

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from collections.abc import Set as AbstractSet

    from docutils.nodes import Element, reference
    from sphinx.addnodes import pending_xref
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import RoleFunction

logger = logging.getLogger(__name__)

__all__ = ["SVDomain", "SVObjectsIndex"]


class ObjectEntry(NamedTuple):
    """A single registered object in the domain's data store."""

    docname: str
    node_id: str
    objtype: str


class SVObjectsIndex(Index):
    """An alphabetical index of every documented SystemVerilog object."""

    name = "objindex"
    localname = _("SystemVerilog Object Index")
    shortname = _("SV objects")

    def generate(
        self,
        docnames: Iterable[str] | None = None,
    ) -> tuple[list[tuple[str, list[IndexEntry]]], bool]:
        content: dict[str, list[IndexEntry]] = {}
        docnames_set = set(docnames) if docnames is not None else None

        domain: SVDomain = self.domain  # type: ignore[assignment]
        for fullname, entry in sorted(domain.objects.items()):
            if docnames_set is not None and entry.docname not in docnames_set:
                continue
            letter = (fullname.lstrip("_")[:1] or "_").upper()
            content.setdefault(letter, []).append(
                IndexEntry(fullname, 0, entry.docname, entry.node_id, entry.objtype, "", "")
            )

        sorted_content = [(letter, entries) for letter, entries in sorted(content.items())]
        return sorted_content, False


class SVDomain(Domain):
    """A domain for documenting SystemVerilog designs and testbenches."""

    name = "sv"
    label = "SystemVerilog"
    data_version = 1

    object_types: ClassVar[dict[str, ObjType]] = {
        "module": ObjType(_("module"), "module", "mod", "obj"),
        "interface": ObjType(_("interface"), "interface", "iface", "obj"),
        "program": ObjType(_("program"), "program", "obj"),
        "package": ObjType(_("package"), "package", "pkg", "obj"),
        "class": ObjType(_("class"), "class", "obj"),
        "port": ObjType(_("port"), "port", "obj"),
        "parameter": ObjType(_("parameter"), "parameter", "param", "obj"),
        "typedef": ObjType(_("typedef"), "typedef", "type", "obj"),
        "struct": ObjType(_("struct"), "struct", "obj"),
        "enum": ObjType(_("enum"), "enum", "obj"),
        "enumerator": ObjType(_("enumerator"), "enumerator", "obj"),
        "covergroup": ObjType(_("covergroup"), "covergroup", "obj"),
        "function": ObjType(_("function"), "function", "func", "obj"),
        "task": ObjType(_("task"), "task", "obj"),
    }

    directives: ClassVar[dict[str, Any]] = {
        "module": SVObject,
        "interface": SVObject,
        "program": SVObject,
        "package": SVObject,
        "class": SVObject,
        "port": SVObject,
        "parameter": SVObject,
        "typedef": SVObject,
        "struct": SVObject,
        "enum": SVObject,
        "enumerator": SVObject,
        "covergroup": SVObject,
        "function": SVObject,
        "task": SVObject,
        "group": SVGroup,
        "namespace": SVNamespace,
        "namespace-push": SVNamespacePush,
        "namespace-pop": SVNamespacePop,
        **AUTODOC_DIRECTIVES,
    }

    roles: ClassVar[dict[str, RoleFunction | Any]] = {
        "module": SVXRefRole(),
        "mod": SVXRefRole(),
        "interface": SVXRefRole(),
        "iface": SVXRefRole(),
        "program": SVXRefRole(),
        "package": SVXRefRole(),
        "pkg": SVXRefRole(),
        "class": SVXRefRole(),
        "port": SVXRefRole(),
        "parameter": SVXRefRole(),
        "param": SVXRefRole(),
        "typedef": SVXRefRole(),
        "type": SVXRefRole(),
        "struct": SVXRefRole(),
        "enum": SVXRefRole(),
        "enumerator": SVXRefRole(),
        "covergroup": SVXRefRole(),
        "function": SVXRefRole(),
        "func": SVXRefRole(),
        "task": SVXRefRole(),
        "obj": SVXRefRole(),
    }

    initial_data: ClassVar[dict[str, Any]] = {"objects": {}}
    indices: ClassVar[list[type[Index]]] = [SVObjectsIndex]

    @property
    def objects(self) -> dict[str, ObjectEntry]:
        return self.data.setdefault("objects", {})  # type: ignore[no-any-return]

    def note_object(
        self,
        fullname: str,
        objtype: str,
        node_id: str,
        location: Any = None,
    ) -> None:
        """Register a documented object, warning on duplicates."""
        if fullname in self.objects:
            other = self.objects[fullname]
            logger.warning(
                _("duplicate SystemVerilog %s description of %s, other instance in %s"),
                objtype,
                fullname,
                other.docname,
                location=location,
                type="sv",
            )
        self.objects[fullname] = ObjectEntry(self.env.docname, node_id, objtype)

    # -- environment bookkeeping -------------------------------------------
    def clear_doc(self, docname: str) -> None:
        for fullname, entry in list(self.objects.items()):
            if entry.docname == docname:
                del self.objects[fullname]

    def merge_domaindata(self, docnames: AbstractSet[str], otherdata: dict[str, Any]) -> None:
        for fullname, entry in otherdata["objects"].items():
            if entry.docname in docnames:
                self.objects[fullname] = entry

    # -- cross-reference resolution ----------------------------------------
    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        typ: str,
        target: str,
        node: pending_xref,
        contnode: Element,
    ) -> reference | None:
        match = self._lookup(target, node.get("sv:namespace"))
        if match is None:
            return None
        fullname, entry = match
        return make_refnode(builder, fromdocname, entry.docname, entry.node_id, contnode, fullname)

    def resolve_any_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        target: str,
        node: pending_xref,
        contnode: Element,
    ) -> list[tuple[str, reference]]:
        match = self._lookup(target, node.get("sv:namespace"))
        if match is None:
            return []
        fullname, entry = match
        refnode = make_refnode(
            builder, fromdocname, entry.docname, entry.node_id, contnode, fullname
        )
        return [(f"sv:{entry.objtype}", refnode)]

    def get_objects(self) -> Iterator[tuple[str, str, str, str, str, int]]:
        for fullname, entry in self.objects.items():
            yield fullname, fullname, entry.objtype, entry.docname, entry.node_id, 1

    def get_full_qualified_name(self, node: Element) -> str | None:
        target: str | None = node.get("reftarget")
        if target is None:
            return None
        namespace = node.get("sv:namespace")
        if namespace:
            return f"{namespace}::{target}"
        return target

    def _lookup(self, target: str, namespace: str | None) -> tuple[str, ObjectEntry] | None:
        """Resolve *target* to a registered object using SV scoping rules."""
        if target in self.objects:
            return target, self.objects[target]

        if namespace:
            # Try progressively shorter enclosing namespaces.
            parts = namespace.split("::")
            for i in range(len(parts), 0, -1):
                qualified = "::".join((*parts[:i], target))
                if qualified in self.objects:
                    return qualified, self.objects[qualified]

        # Fall back to a unique suffix match on the final name component.
        candidates = [
            (name, entry)
            for name, entry in self.objects.items()
            if _last_component(name) == _last_component(target)
        ]
        if len(candidates) == 1:
            return candidates[0]
        return None


def _last_component(name: str) -> str:
    for sep in ("::", "."):
        if sep in name:
            name = name.rsplit(sep, 1)[-1]
    return name
