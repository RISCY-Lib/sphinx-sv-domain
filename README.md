# sphinx-sv-domain

A SystemVerilog language domain for the [Sphinx](https://www.sphinx-doc.org/)
documentation tooling.

It adds first-class directives and cross-references for SystemVerilog designs and
testbenches -- the way Sphinx's built-in domains cover Python, C or C++ -- and can
pull documentation straight out of your `.sv` / `.svh` sources with
[pyslang](https://github.com/MikePopoloski/slang).

- **Manual** directives (`sv:module`, `sv:function`, ...) take a signature you write.
- **Autodoc** directives (`sv:automodule`, ...) parse a source file and render the
  declaration plus the reST in its doc-comment.
- Modules, interfaces, programs, packages, classes, functions, tasks, typedefs,
  structs, enums, covergroups, ports and parameters.
- Type names in a signature link automatically to their definition.
- Namespaces, and grouping of a module's ports/parameters into titled sections.

## Install

```console
pip install sphinx-sv-domain
```

Then enable it in your `conf.py`:

```python
extensions = ["sphinx_sv_domain"]

# For the sv:auto* directives, point at your sources:
sv_autodoc_source_path = ["../rtl", "../verif"]
```

## Documentation

Full documentation lives in [`docs/`](docs/).  Build it locally with:

```console
uv run --group docs sphinx-build -b html docs docs/_build/html
```

A runnable example project is in [`examples/demo/`](examples/demo/).

## License

LGPL-2.1 (see [`LICENSE`](LICENSE)).
