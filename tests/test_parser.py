"""Unit tests for the pyslang-backed parser layer."""

from __future__ import annotations

import textwrap

import pytest

from sphinx_sv_domain import parser

MIXED_SOURCE = textwrap.dedent(
    """
    // Utility helpers.
    // Second doc line.
    package util_pkg;
      // The FSM state.
      typedef enum logic [1:0] {IDLE, RUN = 2, DONE} state_t;
      typedef struct packed { logic [7:0] a; int b; } word_t;
      // Add two integers.
      function automatic int add(int a, int b);
        return a + b;
      endfunction
      task drive();
      endtask
    endpackage

    // Top counter.
    module counter #(parameter int WIDTH = 8) (
        input  logic             clk,
        output logic [WIDTH-1:0] count
    );
    endmodule

    class Packet extends BaseTxn;
    endclass
    """
)


@pytest.fixture(scope="module")
def decls() -> dict[tuple[str, str], parser.SVDecl]:
    result = parser.parse_source(MIXED_SOURCE)
    assert result.diagnostics == []
    return {(d.kind, d.name): d for d in result.declarations}


def test_all_top_level_kinds_found(decls: dict[tuple[str, str], parser.SVDecl]) -> None:
    kinds = {kind for kind, _ in decls}
    assert {"package", "typedef", "function", "task", "module", "class"} <= kinds


def test_module_ports_and_params(decls: dict[tuple[str, str], parser.SVDecl]) -> None:
    counter = decls[("module", "counter")]
    assert [p.name for p in counter.params] == ["WIDTH"]
    assert counter.params[0].type == "int"
    assert counter.params[0].default == "8"
    assert [p.name for p in counter.ports] == ["clk", "count"]
    assert counter.ports[0].direction == "input"
    assert counter.ports[1].type == "logic [WIDTH-1:0]"


def test_trailing_comments_become_member_docs() -> None:
    src = textwrap.dedent(
        """
        module m #(
            parameter int WIDTH = 8,  // Data width in bits.
            parameter int DEPTH = 16  // Number of entries.
        ) (
            input  logic             clk,   // The clock.
            output logic [WIDTH-1:0] data   // Output data bus.
        );
        endmodule
        """
    )
    (decl,) = parser.parse_source(src).declarations
    assert [(p.name, p.doc) for p in decl.params] == [
        ("WIDTH", "Data width in bits."),
        ("DEPTH", "Number of entries."),
    ]
    # A port's direction stays clean even though the previous line's trailing
    # comment is parked in its leading trivia by pyslang.
    assert [(p.name, p.direction, p.doc) for p in decl.ports] == [
        ("clk", "input", "The clock."),
        ("data", "output", "Output data bus."),
    ]
    assert decl.ports[1].type == "logic [WIDTH-1:0]"


def test_inline_block_comment_does_not_shadow_trailing_line_comment() -> None:
    # A ``//`` doc comment must win over an inline ``/* */`` width annotation.
    src = "module m (\n  output logic [/*MSB*/7:0] data  // Output data bus.\n); endmodule"
    (decl,) = parser.parse_source(src).declarations
    assert decl.ports[0].doc == "Output data bus."


def test_net_type_port_surfaces_net_kind() -> None:
    (decl,) = parser.parse_source("module m (inout wire w, input clk); endmodule").declarations
    types = {p.name: p.type for p in decl.ports}
    assert types["w"] == "wire"
    assert types["clk"] == ""  # no data type and no net type -> empty


def test_double_slash_inside_string_is_not_a_comment() -> None:
    src = 'module m #(parameter string URL = "http://example.com") (); endmodule'
    (decl,) = parser.parse_source(src).declarations
    assert decl.params[0].name == "URL"
    # The ``//`` lives inside a string literal, so it is not a trailing comment.
    assert decl.params[0].doc == ""


def test_function_signature(decls: dict[tuple[str, str], parser.SVDecl]) -> None:
    add = decls[("function", "add")]
    assert add.return_type == "int"
    assert [a.name for a in add.args] == ["a", "b"]
    assert add.parent == "util_pkg"


def test_task_has_no_return(decls: dict[tuple[str, str], parser.SVDecl]) -> None:
    drive = decls[("task", "drive")]
    assert drive.return_type is None
    assert drive.parent == "util_pkg"


def test_enum_typedef(decls: dict[tuple[str, str], parser.SVDecl]) -> None:
    state = decls[("typedef", "state_t")]
    assert state.underlying == "enum"
    assert [(e.name, e.value) for e in state.enumerators] == [
        ("IDLE", None),
        ("RUN", "2"),
        ("DONE", None),
    ]


def test_struct_typedef(decls: dict[tuple[str, str], parser.SVDecl]) -> None:
    word = decls[("typedef", "word_t")]
    assert word.underlying == "struct"
    assert [(m.name, m.type) for m in word.members] == [("a", "logic [7:0]"), ("b", "int")]


def test_class_extends(decls: dict[tuple[str, str], parser.SVDecl]) -> None:
    packet = decls[("class", "Packet")]
    assert packet.base == "BaseTxn"


def test_doc_comment_extraction(decls: dict[tuple[str, str], parser.SVDecl]) -> None:
    assert decls[("package", "util_pkg")].doc == "Utility helpers.\nSecond doc line."
    assert decls[("function", "add")].doc == "Add two integers."
    # A declaration with no preceding comment has an empty doc string.
    assert decls[("class", "Packet")].doc == ""


def test_block_comment_extraction() -> None:
    src = textwrap.dedent(
        """
        /* A block-commented module.
           Spanning two lines. */
        module m; endmodule
        """
    )
    (decl,) = parser.parse_source(src).declarations
    assert decl.doc == "A block-commented module.\nSpanning two lines."


def test_source_locations_are_recorded() -> None:
    result = parser.parse_source("module a; endmodule\nmodule b; endmodule\n")
    lines = {d.name: d.line for d in result.declarations}
    assert lines == {"a": 1, "b": 2}


def test_diagnostics_are_surfaced() -> None:
    result = parser.parse_source("module broken (input logic ; endmodule")
    assert result.diagnostics
    assert all(isinstance(line, int) for line, _ in result.diagnostics)


@pytest.mark.parametrize(
    ("sig", "objtype", "expected_name"),
    [
        ("counter #(parameter int W = 8) (input clk, output q)", "module", "counter"),
        ("module counter; endmodule", "module", "counter"),
        ("int add(int a, int b)", "function", "add"),
        ("run()", "task", "run"),
        ("enum {A, B, C} color_t", "typedef", "color_t"),
        ("MyBareName", "module", "MyBareName"),
    ],
)
def test_parse_signature_names(sig: str, objtype: str, expected_name: str) -> None:
    assert parser.parse_signature(sig, objtype).name == expected_name


def test_parse_signature_module_details() -> None:
    decl = parser.parse_signature("m #(parameter int W=4) (input clk, output q)", "module")
    assert [p.name for p in decl.params] == ["W"]
    assert [p.name for p in decl.ports] == ["clk", "q"]


def test_parse_signature_leaf_port() -> None:
    decl = parser.parse_signature("input logic [7:0] data", "port")
    assert decl.name == "data"
    assert decl.direction == "input"
    assert decl.datatype == "logic [7:0]"


def test_parse_signature_leaf_parameter() -> None:
    decl = parser.parse_signature("int WIDTH = 8", "parameter")
    assert decl.name == "WIDTH"
    assert decl.datatype == "int"
    assert decl.default == "8"


def test_parse_signature_leaf_enumerator() -> None:
    decl = parser.parse_signature("DONE = 3", "enumerator")
    assert decl.name == "DONE"
    assert decl.default == "3"


def test_parse_signature_empty_raises() -> None:
    with pytest.raises(ValueError, match="empty signature"):
        parser.parse_signature("   ", "module")


def test_interface_program_covergroup() -> None:
    src = textwrap.dedent(
        """
        interface my_if #(parameter int N = 4) (input logic clk);
          modport mp (input clk);
        endinterface
        program tb (input logic clk);
        endprogram
        module m;
          covergroup cg;
          endgroup
        endmodule
        """
    )
    decls = {(d.kind, d.name): d for d in parser.parse_source(src).declarations}
    assert decls[("interface", "my_if")].params[0].name == "N"
    assert decls[("interface", "my_if")].ports[0].name == "clk"
    assert decls[("program", "tb")].ports[0].name == "clk"
    assert decls[("covergroup", "cg")].parent == "m"


def test_parse_file(tmp_path: object) -> None:
    from pathlib import Path

    path = Path(str(tmp_path)) / "m.sv"
    path.write_text("// A file module.\nmodule filemod; endmodule\n")
    result = parser.parse_file(path)
    (decl,) = result.declarations
    assert decl.name == "filemod"
    assert decl.doc == "A file module."
