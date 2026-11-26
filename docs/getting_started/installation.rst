Installation
============

.. todo:: Add download links for packaged releases (Windows / macOS) once they are published.

Packaged releases
-----------------

*To do:* describe where to download the installer for each platform and how to run it.

Running from source
-------------------

GeoCORK requires Python 3.12 or newer.

.. code-block:: bash

   git clone https://github.com/kathrynmetcalf/GeoCORK.git
   cd GeoCORK
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   python mainAppEngine.py

Where GeoCORK keeps its files
-----------------------------

* **Settings** are stored with ``QSettings`` under the organization/application name ``GeoCORK``.
  Each database file also gets its own settings group (``GeoCORK : <database file>``).
* **Logs** are written to the application data folder
  (``QStandardPaths.AppDataLocation``) under ``logs/``, one file per session.
* **Import column mappings** are saved as ``column_mappings.json`` in the same folder.
