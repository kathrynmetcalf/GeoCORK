Architecture
============

.. todo:: Expand with diagrams.

Package layout
--------------

``Functions/``
   Core SQL building blocks: :mod:`Functions.SQLUtils` (static table/column constants used
   throughout the app), :mod:`Functions.Database_views` (``ViewQuery``, which builds the
   view SQL and supports both analysis leaf tables), triggers, and indexes.

``util/``
   Non-UI helpers: database creation, import, export, merge, backup and conversion
   (:mod:`util.database`), plotting data providers and plot types (:mod:`util.plotting`),
   reusable widgets, models and views (:mod:`util.widgets`), settings, logging and
   coordinate conversion.

``ui/``
   Windows, dialogs, and tabs that create the GeoCORK user's see.

Conventions
-----------

* Absolute imports from the repository root (``from util.database import ...``).
* Singletons for shared state: :class:`util.settings_manager.SettingsManager`,
  :class:`util.database.savepoint_manager.SavepointManager`, the loading-dialog manager.
* Database changes are wrapped in savepoints (``create_savepoint`` /
  ``release_savepoint`` / ``rollback_savepoint``).
