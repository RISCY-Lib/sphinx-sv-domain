# sphinx-sv-domain demo

A minimal, self-contained project showing how to document SystemVerilog with
[`sphinx-sv-domain`](../../).

```
examples/demo/
├── src/     example SystemVerilog RTL and verification code
└── docs/    a Sphinx project that documents src/ automatically
```

## Building

From the repository root, install the package (and Sphinx) and build the docs:

```bash
uv sync                       # or: pip install -e . sphinx
cd examples/demo/docs
sphinx-build -b html . _build/html
```

Open `examples/demo/docs/_build/html/index.html` in a browser.

## What to look at

- `src/*.sv` — modules, an interface, packages, typedefs, a function/task and
  classes, each with reST doc-comments.
- `docs/conf.py` — enables the extension and sets `sv_autodoc_source_path` to
  `../src`.
- `docs/autodoc.rst` — `sv:auto*` directives that document `src/` from source.
- `docs/manual.rst` — hand-written `sv:*` directives and namespaces.
