"""Integration tests that build real Sphinx projects using the domain."""

from __future__ import annotations

import re
from html import unescape
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from io import StringIO

    from sphinx.application import Sphinx


def _text(html: str) -> str:
    """Collapse an HTML fragment to its visible text."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def _signatures(html: str) -> dict[str, str]:
    """Map each ``desc_signature`` id to its rendered text."""
    out: dict[str, str] = {}
    for match in re.finditer(r'<dt class="sig[^"]*"[^>]*id="([^"]*)"[^>]*>(.*?)</dt>', html, re.S):
        out[match.group(1)] = _text(match.group(2)).rstrip("¶").strip()
    return out


def _group_titles(html: str) -> list[str]:
    """Return the rendered title of every ``sv:group`` on the page, in order."""
    return [
        unescape(_text(m.group(1)))
        for m in re.finditer(r'<dt class="[^"]*sv-group-title[^"]*">(.*?)</dt>', html, re.S)
    ]


def _sig_links(html: str, sig_id: str) -> dict[str, str]:
    """Map link text to href for the internal references inside one signature."""
    match = re.search(rf'<dt class="sig[^"]*"[^>]*id="{sig_id}"[^>]*>(.*?)</dt>', html, re.S)
    if match is None:
        return {}
    return {
        _text(m.group(2)): m.group(1)
        for m in re.finditer(
            r'<a class="reference internal" href="([^"]*)"[^>]*>(.*?)</a>', match.group(1), re.S
        )
    }


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_build_succeeds_without_warnings(app: Sphinx, warning: StringIO) -> None:
    app.build()
    assert warning.getvalue() == ""


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_objects_registered(app: Sphinx) -> None:
    app.build()
    objects = app.env.get_domain("sv").objects  # type: ignore[attr-defined]
    assert objects["fifo"].objtype == "module"
    assert objects["my_pkg::clog2"].objtype == "function"
    assert objects["counter"].objtype == "module"
    assert objects["counter_pkg::sat_add"].objtype == "function"
    assert objects["counter_pkg::state_t"].objtype == "typedef"
    # Namespaced objects use their fully qualified names.
    assert objects["chip_top::alu"].objtype == "module"
    assert objects["chip_top::sub::reset"].objtype == "task"


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_manual_signature_rendering(app: Sphinx) -> None:
    app.build()
    sigs = _signatures((app.outdir / "index.html").read_text())
    assert (
        sigs["module-fifo"] == "module fifo #(int DEPTH = 16)(input logic clk, output logic full)"
    )
    # A member nested in a package drops the redundant enclosing-scope prefix.
    assert sigs["function-my_pkg-clog2"].startswith("function clog2(int value)")
    assert "int" in sigs["function-my_pkg-clog2"]


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_autodoc_module_expands_ports_and_params(app: Sphinx) -> None:
    app.build()
    html = (app.outdir / "index.html").read_text()
    sigs = _signatures(html)
    assert sigs["module-counter"] == "module counter"
    # Members show their direction and drop the redundant ``counter::`` prefix.
    assert sigs["parameter-counter-WIDTH"] == "parameter WIDTH: int = 8"
    assert sigs["port-counter-clk"] == "input clk: logic"
    assert sigs["port-counter-count"] == "output count: logic [WIDTH-1:0]"
    # Parameters and ports are grouped under rubric headings...
    assert '<p class="rubric">Parameters</p>' in html
    assert '<p class="rubric">Ports</p>' in html
    # ...and each signal's trailing comment becomes its description.
    assert "The counter clock." in _text(html)
    assert "Counter width in bits." in _text(html)


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_autodoc_groups_ports_and_params(app: Sphinx) -> None:
    app.build()
    html = (app.outdir / "index.html").read_text()
    sigs = _signatures(html)
    # Ungrouped ports still render (before any group), and grouped members keep
    # their own signatures and ids.
    assert sigs["port-router-clk"] == "input clk: logic"
    assert sigs["port-router-in_data"] == "input in_data: logic [WIDTH-1:0]"
    assert sigs["parameter-router-WIDTH"] == "parameter WIDTH: int = 32"
    # The parameter banner and the port @group / banner become group headings...
    assert set(_group_titles(html)) >= {"Sizing", "Ingress", "Egress"}
    # ...inside the existing section rubrics, which are unchanged.
    assert '<p class="rubric">Parameters</p>' in html
    assert '<p class="rubric">Ports</p>' in html
    # A group's continuation-comment description renders under its heading.
    assert "The inbound payload channel." in _text(html)


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_group_stylesheet_is_bundled_and_linked(app: Sphinx) -> None:
    app.build()
    css = app.outdir / "_static" / "sv-domain.css"
    assert css.exists()
    assert "sv-group-title" in css.read_text()
    assert "sv-domain.css" in (app.outdir / "index.html").read_text()


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_group_renders_as_nested_definition_list(app: Sphinx) -> None:
    app.build()
    html = (app.outdir / "index.html").read_text()
    # Each group is a definition list wrapping its members in the definition body.
    assert '<dl class="sv-group' in html
    # The ungrouped port renders before the first group; a grouped port renders
    # after its group title -> the section reads Ports > ungrouped > group > member.
    pos_clk = html.index('id="port-router-clk"')
    pos_group = re.search(r'<dt class="[^"]*sv-group-title[^"]*">\s*Ingress', html)
    pos_in_data = html.index('id="port-router-in_data"')
    assert pos_group is not None
    assert pos_clk < pos_group.start() < pos_in_data


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_manual_group_directive(app: Sphinx) -> None:
    app.build()
    html = (app.outdir / "index.html").read_text()
    sigs = _signatures(html)
    # A hand-written sv:group renders its title and holds its nested ports, which
    # register under the enclosing module's namespace.
    assert {"Clock & Reset", "Pads"} <= set(_group_titles(html))
    assert sigs["port-gpio-clk"] == "input clk: logic"
    assert sigs["port-gpio-pins"] == "output pins: logic [7:0]"
    assert "The single synchronous clock domain." in _text(html)


@pytest.mark.sphinx(
    "html",
    testroot="sv-basic",
    freshenv=True,
    confoverrides={"sv_autodoc_group_banners": False},
)
def test_group_banners_config_disables_banner_markers(app: Sphinx) -> None:
    app.build()
    html = (app.outdir / "index.html").read_text()
    titles = _group_titles(html)
    # Banner-declared groups disappear; the @group tag and the manual sv:group
    # directive are unaffected.
    assert "Sizing" not in titles
    assert "Egress" not in titles
    assert "Ingress" in titles
    assert {"Clock & Reset", "Pads"} <= set(titles)


@pytest.mark.sphinx(
    "html",
    testroot="sv-basic",
    freshenv=True,
    confoverrides={"sv_qualify_nested_names": True},
)
def test_qualify_nested_names_restores_scope_prefix(app: Sphinx) -> None:
    app.build()
    sigs = _signatures((app.outdir / "index.html").read_text())
    assert sigs["parameter-counter-WIDTH"] == "parameter counter::WIDTH: int = 8"
    assert sigs["port-counter-clk"] == "input counter::clk: logic"


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_autodoc_package_recurses_into_members(app: Sphinx) -> None:
    app.build()
    sigs = _signatures((app.outdir / "index.html").read_text())
    assert "package-counter_pkg" in sigs
    assert sigs["enumerator-counter_pkg-IDLE"] == "IDLE"
    assert sigs["function-counter_pkg-sat_add"].startswith("function sat_add")


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_cross_references_resolve(app: Sphinx) -> None:
    app.build()
    html = (app.outdir / "index.html").read_text()
    hrefs = {
        _text(m.group(2)): m.group(1)
        for m in re.finditer(
            r'<a class="reference internal" href="([^"]*)"[^>]*>(.*?)</a>', html, re.S
        )
    }
    assert hrefs.get("fifo") == "#module-fifo"
    assert hrefs.get("my_pkg::clog2") == "#function-my_pkg-clog2"
    # The generic :sv:obj: role resolves by unique suffix match.
    assert hrefs.get("color_t") == "#typedef-my_pkg-color_t"
    # Namespaced references resolve to the fully qualified target.
    assert hrefs.get("chip_top::alu") == "#module-chip_top-alu"
    assert hrefs.get("chip_top::sub::reset") == "#task-chip_top-sub-reset"
    # A namespace-relative reference resolves against the enclosing scope.
    assert hrefs.get("reset") == "#task-chip_top-sub-reset"
    # A leading '~' shows only the final component but still resolves.
    assert hrefs.get("alu") == "#module-chip_top-alu"
    # The generic :any: role dispatches through resolve_any_xref.
    assert "fifo" in hrefs


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_signature_type_links(app: Sphinx) -> None:
    app.build()
    html = (app.outdir / "index.html").read_text()
    # A user-defined type in a module header auto-links to its definition, while
    # built-in types (``logic``) and port names stay plain text.
    assert _sig_links(html, "module-sampler") == {
        "my_pkg::color_t": "#typedef-my_pkg-color_t",
    }
    # An explicit :sv:type: role written inside the signature links the same way.
    assert _sig_links(html, "module-bridge") == {
        "my_pkg::color_t": "#typedef-my_pkg-color_t",
    }
    # The linked type does not change the visible signature text.
    sigs = _signatures(html)
    assert sigs["module-sampler"] == (
        "module sampler #(int N = 4)(input my_pkg::color_t tint, output logic done)"
    )


@pytest.mark.sphinx("html", testroot="sv-basic", freshenv=True)
def test_object_index_generated(app: Sphinx) -> None:
    app.build()
    index_html = (app.outdir / "sv-objindex.html").read_text()
    assert "SystemVerilog Object Index" in index_html
    assert "fifo" in _text(index_html)


@pytest.mark.sphinx("html", testroot="sv-warnings", freshenv=True)
def test_warning_cases(app: Sphinx, warning: StringIO) -> None:
    app.build()
    warnings = warning.getvalue()
    assert "duplicate SystemVerilog module description of dup_mod" in warnings
    assert "does_not_exist" in warnings
    assert "could not find SystemVerilog module 'nonexistent_module'" in warnings
