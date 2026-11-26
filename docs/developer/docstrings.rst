Writing docstrings
==================

The API reference is generated from docstrings, so a function without one shows up with
only its signature.

GeoCORK uses the Sphinx (reST field list) style:

.. code-block:: python

   def rollback_savepoint(savepoint_name: str, database: QSqlDatabase = QSqlDatabase()) -> bool:
       """
       Roll back the given database to the provided savepoint name.

       :param str savepoint_name: name of the savepoint to roll back to
       :param QSqlDatabase database: database to roll back; defaults to the default connection
       :return: True for success, False for failure
       :rtype: bool
       """

Tips:

* Keep a blank line between the summary sentence and the field list.
* The name after ``:param`` must match the argument name exactly, or Sphinx shows the
  description under a parameter that does not exist.
* To document a module-level constant or a class attribute, put a string literal directly
  under it (GeoCORK already does this, e.g. ``BASEMAPS`` in ``ui/SampleMap.py``).
* Use ``:class:`ViewQuery``` or ``:func:`util.gps_conversions.convert_dd_to_utm``` to link
  to other parts of the reference.
