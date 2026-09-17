Cross-references
================

Every documented object can be linked from anywhere in your documentation with a
domain role, and type names written in a signature link themselves.

Roles
-----

Each object type has a role, most with a short alias.  Use them inline:
``:sv:module:`fifo``` renders as :sv:module:`fifo`.

============  ==================  ============================================
Type          Role (and alias)    Example target
============  ==================  ============================================
module        ``mod``             :sv:module:`counter`
interface     ``iface``           ``:sv:interface:`counter_if```
program       --                  ``:sv:program:`...```
package       ``pkg``             :sv:package:`counter_pkg`
class         --                  ``:sv:class:`base_txn```
function      ``func``            :sv:func:`counter_pkg::sat_add`
task          --                  ``:sv:task:`...```
typedef       ``type``            :sv:type:`counter_pkg::state_t`
struct        --                  ``:sv:struct:`...```
enum          --                  ``:sv:enum:`...```
enumerator    --                  ``:sv:enumerator:`...```
covergroup    --                  ``:sv:covergroup:`...```
port          --                  :sv:port:`counter::clk`
parameter     ``param``           :sv:parameter:`counter::WIDTH`
============  ==================  ============================================

A generic ``:sv:obj:`` role resolves to an object of any type by a unique name.

Reference styles
~~~~~~~~~~~~~~~~~

The roles follow the usual Sphinx conventions:

- **Qualified**: ``:sv:type:`counter_pkg::state_t``` targets the exact name.
- **Relative**: inside a namespace, a bare name resolves against the enclosing
  scope, then outward.
- **Custom title**: ``:sv:module:`the counter <counter>``` shows *the counter*.
- **Abbreviated**: a leading ``~`` shows only the last component, so
  ``:sv:module:`~chip_top::alu``` displays *alu*.

Automatic type links in signatures
-----------------------------------

A user-defined type used in a signature links to its definition automatically --
the same way ``:py:class:`` annotations do in the Python domain.  Built-in types
(``logic``, ``int``, ...) stay plain text.

Here ``counter_pkg::state_t`` and ``counter_pkg::sample_t`` (defined by
:sv:package:`counter_pkg` on the :doc:`autodoc` page) become links right in the
module header:

.. sv:module:: sampler #(parameter int N = 4) (input counter_pkg::state_t st, output counter_pkg::sample_t snap)

   Samples the counter FSM state into a packed record.

To be explicit -- or to give the link a nicer label -- write an ordinary
cross-reference role inside the signature:

.. sv:module:: bridge (input :sv:type:`counter_pkg::sample_t` din, output logic valid)

   Forwards a captured :sv:type:`counter_pkg::sample_t` downstream.

Unresolved type names fall back to plain text rather than emitting a warning, so
partially-documented designs stay quiet.

Namespaces
----------

Namespaces prefix the objects declared under them and let references resolve
relative to a scope.  Set one absolutely with :rst:dir:`sv:namespace`, nest with
:rst:dir:`sv:namespace-push`, and reset with an empty :rst:dir:`sv:namespace`.

.. sv:namespace:: soc

.. sv:module:: dma

   A scatter-gather DMA engine living in the ``soc`` namespace.

.. sv:namespace::

The engine above is reachable as :sv:module:`soc::dma`.  Cross-references work
across pages too: the counter is :sv:module:`counter`, the FIFO is
:sv:module:`fifo`, and the FSM state type is :sv:type:`counter_pkg::state_t`.
