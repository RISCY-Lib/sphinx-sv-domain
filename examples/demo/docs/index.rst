sphinx-sv-domain demo
=====================

This small project shows how to document SystemVerilog with
``sphinx-sv-domain``.  The RTL lives in ``../src`` and the pages below pull
documentation straight out of those files with the ``sv:auto*`` directives.

.. toctree::
   :maxdepth: 2

   autodoc
   manual

Cross references work across pages: the counter is :sv:module:`counter`, its
shared types live in :sv:package:`counter_pkg`, and the FSM state type is
:sv:type:`counter_pkg::state_t`.

Index
-----

* :ref:`genindex`
