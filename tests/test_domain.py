"""Unit tests for domain bookkeeping (parallel-build correctness hooks)."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from sphinx_sv_domain.domain import ObjectEntry, SVDomain

if TYPE_CHECKING:
    from sphinx.application import Sphinx


def _domain(app: Sphinx) -> SVDomain:
    return cast(SVDomain, app.env.get_domain("sv"))


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_clear_doc_removes_only_that_document(app: Sphinx) -> None:
    app.build()
    domain = _domain(app)
    assert domain.objects  # populated by the build
    domain.clear_doc("index")
    assert domain.objects == {}


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_merge_domaindata_merges_matching_docnames(app: Sphinx) -> None:
    app.build()
    domain = _domain(app)
    other = {"objects": {"other::thing": ObjectEntry("other", "id-1", "module")}}
    domain.merge_domaindata({"other"}, other)
    assert domain.objects["other::thing"].objtype == "module"
    # A docname absent from the merge set is ignored.
    domain.merge_domaindata(set(), {"objects": {"skip::me": ObjectEntry("skip", "i", "task")}})
    assert "skip::me" not in domain.objects


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_get_objects_yields_registered_entries(app: Sphinx) -> None:
    app.build()
    domain = _domain(app)
    names = {row[0] for row in domain.get_objects()}
    assert "fifo" in names
    assert "counter_pkg::sat_add" in names


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_lookup_unique_suffix_and_ambiguity(app: Sphinx) -> None:
    app.build()
    domain = _domain(app)
    # Unique final component resolves even without the namespace prefix.
    match = domain._lookup("sat_add", None)
    assert match is not None
    assert match[0] == "counter_pkg::sat_add"
    # An unknown target does not resolve.
    assert domain._lookup("no_such_object", None) is None
