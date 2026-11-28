Database
========

GeoCORK stores everything in a single SQLite (.db) file.

.. toctree::
   :maxdepth: 1

   schema
   versions

Design principles
-----------------
GeoCORK’s database was designed with five guiding principles as they relate to geochronological workflows:

1. All data entered should be in the format given by the laboratory (e.g, U/Th vs Th/U).
2. Internal IDs should be hidden to the researcher as they are unreadable and cause confusion.
3. All tables with internal IDs must have a secondary unique alternate ID in the form of a user-viewable name easily recognizable by researchers.
4. Any future geochemical and geochronological methods or data should be easily integrated with minimal changes to ensure backwards compatibility.
5. All data needed for searching, filtering, and database-specific customization mustbe stored inside the database to allow easier sharing of results with other researchers.

* **Calculated Columns** Are used to convert stored values into inverse ratios or different units
  (e.g., Th/U vs. U/Th, 207Pb/235U Age in ka or ma)
  are derived from whatever is stored and converted to the user's unit and
  format settings. Users mainly see the calculated columns; the stored values stay in the background.

* **Analyses hang off a hierarchy.** Samples → aliquots → spots (and grains) → analyses.
  ``UPbAnalyses`` and ``GeoChemicalAnalyses`` are separate leaf tables.
    This enables a single spot or grain to have
    multiple U-Pb analyses or Geochemical analyses, thus allowing split stream methodologies.

