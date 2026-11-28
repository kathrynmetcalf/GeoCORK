Schema
======


Core Sample-Analyses Hierarchy
--------------

.. code-block:: text

   Samples
   └── Aliquots
       └── Spots (── Grains)
           ├── UPbAnalyses (see below)
           └── GeoChemicalAnalyses (see below)

Core Sample Metadata
--------------
All sample metadata is a many-to-many relationship to contextual data categories.

.. code-block:: text

   Samples
   └── Sample Contexts (tags)
   └── Units
   └── Rock Types
   └── GPS Locations
   └── Sample Ages
   └── Age Constraints
   └── Age Interpretation
   └── Regions
   └── Settings
   └── Columns

Other metadata like references, instruments, or method data are stored lower in the hierarchy.
However, through the hierarchy these data are accessible and summarized at the sample level.

Sample-Aliquot-Spot-Grain Schema
""""

.. code-block:: text

   Samples
   └── Aliquots (tree-like structure for nested aliquots)
       └── Aliquot Contexts (tags)

       └── Spots
           └── Spot Contexts (tags) (m:n) (optional)
                  Recommended use is to store Rim/Core contexts
           └── Spot Composition (tags) (1:m) (optional)
                  Recommended use is to store mineral data
           └── Grains (1:m) (optional)
                  Allows a single grain to be associated with multiple spots.

           ├── UPbAnalyses (see below)
           └── GeoChemicalAnalyses (see below)


U-Pb Analysis Schema
""""

.. code-block:: text

   UPbAnalyses
   └── References
   └── Lab Facilities
   └── Instruments
   └── U-Pb Analysis Methods
   └── U-Pb Analysis Contexts (tags)
   └── Rejection Reasons

GeoChemical Analysis Schema
""""

.. code-block:: text

   GeoChemicalAnalyses
   └── References
   └── Lab Facilities
   └── Instruments
   └── Geochemical Analysis Methods
   └── Geochemical Analysis Contexts (tags)
   └── Rejection Reasons

See :mod:`util.database.create.Create_database` for how a new database is created and
:mod:`Functions.SQLUtils` for the shared table and column constants.
