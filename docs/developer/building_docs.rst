Building the documentation
==========================

Locally
-------

From the repository root:

.. code-block:: bash

   pip install -r docs/requirements.txt
   sphinx-build -b html docs docs/_build/html
   # or, with live reload while writing:
   pip install sphinx-autobuild
   sphinx-autobuild docs docs/_build/html

Open ``docs/_build/html/index.html``. The API pages under ``docs/api/generated/`` are
regenerated on every build; they are git-ignored and should not be edited by hand.

How imports work during the build
---------------------------------

Autodoc imports every module. ``docs/conf.py`` therefore:

* puts the repository root on ``sys.path``;
* starts a headless ``QApplication`` (``QT_QPA_PLATFORM=offscreen``) so module-level Qt code
  and ``QMessageBox`` calls from the logger do not crash the build;
* uses a separate ``QSettings`` organization (``GeoCORK-docs``) so a build never changes your
  real GeoCORK settings;
* mocks ``detritalPy`` and ``pyrolite``;
* inserts the blank line reST needs between a docstring summary and its ``:param:`` fields, and
  makes ``QMessageBox`` helpers return immediately so nothing waits for a click.

If a module fails to import, Sphinx prints ``autosummary: failed to import ...`` with the
traceback. The usual causes are a new third-party dependency (add it to
``docs/requirements.txt`` or to ``autodoc_mock_imports`` in ``conf.py``) or code that does real
work at import time (move it into a function or behind ``if __name__ == '__main__':``).

Read the Docs
-------------

The build is configured by ``.readthedocs.yaml`` at the repository root (Python 3.12, the
system libraries PyQt6/QtWebEngine need, and ``docs/requirements.txt``).

One-time setup:

1. Sign in at https://app.readthedocs.org with GitHub and choose **Add project** →
   the GeoCORK repository. Pushes to the default branch then rebuild the docs
   automatically; enable *Build pull requests* in the project settings for PR previews.
2. Check the first build at ``https://geocork.readthedocs.io``.

Custom domain (``documentation.geocork.org``):

1. In Read the Docs: **Settings → Domains → Add domain** → ``documentation.geocork.org``,
   and tick *Canonical*.
2. At the DNS provider for ``geocork.org``, add a record:

   ========================  ======  ==============================
   Name                      Type    Value
   ========================  ======  ==============================
   ``documentation``         CNAME   ``geocork.readthedocs.io``
   ========================  ======  ==============================

3. Wait for DNS to propagate; Read the Docs then issues the HTTPS certificate itself (the
   Domains page shows its status). No CNAME file is needed in the repository; that is a
   GitHub Pages convention.

``conf.py`` uses Read the Docs' ``READTHEDOCS_CANONICAL_URL`` for canonical links, falling back to
``https://documentation.geocork.org/`` for local builds.
