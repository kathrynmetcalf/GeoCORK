Installation
============

To install GeoCORK first download the desired Windows or MacOS packaged release below.
Installation for Windows and MacOS are similar as they are standalone executables.
The MacOS version is unsigned and requires the user to approve in settings after the first time opening GeoCORK.

Packaged releases
-----------------

The latest release can be found on `GeoCORK's GitHub
<https://github.com/kathrynmetcalf/GeoCORK/releases>`_.

Running from source
-------------------
Want the latest features? Run GeoCORK from source and choose the desired branch.

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
