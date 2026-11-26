Introduction
============

GeoCORK's intended use is deliberately left open, because different geoscience
disciplines have different use cases. Its tables, attributes and options are largely
left to the interpretation of each researcher and their needs. This guide covers tips,
tricks, and how to get the most out of GeoCORK.

Main widgets
------------

GeoCORK is built around a few main widgets:

Data Viewer
   The primary way to view all data in a database. A drop-down switches quickly between
   tables. Tables are paged and can be sorted by clicking column headers. Trees are not
   paged, and their item order is stored in the database. See :doc:`browsing_editing`.

Filters tab
   Filters all data in the database with multivariate, nested logical operators. Results
   can be shown as Samples, Aliquots, Grains, Spots, or U-Pb Analyses. See :doc:`filters`.

Export tab
   Saves any data, selected by hand or through a filter, as an Excel, CSV, or database
   file, in predefined or custom formats. See :doc:`exporting`.

Import Wizard
   Imports data from an Excel workbook (``.xlsx`` only). Multiple sheets are supported.
   Column mapping, row removal or rejection, and metadata selection make importing quick,
   and mappings can be saved for one-click reuse. See :doc:`importing`.

Filtered Data View
   A high-level overview of the Samples, Aliquots, Grains, Spots, or U-Pb Analyses in the
   whole database that pass the current filter.

Data View tab
   A tab showing the Aliquots, Grains, Spots, or U-Pb Analyses of one parent Sample,
   Aliquot, Grain, or Spot. Viewing every analysis in a database at once is impractical,
   so these tabs are opened by right-clicking a parent item.

Edit Table dialog
   Edits fields by double-clicking a cell, or by selecting several cells in a column and
   right-clicking. Some fields, such as GPS, open an extra dialog to keep related fields
   consistent. Tree items can be moved by drag and drop.

Add Item dialog
   Adds new items to a table. In trees, an item can be added as a parent, as a child,
   before or after a sibling, or at the end.

Sample Edit dialog
   Edits metadata for one or more samples with text boxes, drop-down menus and check
   boxes. This is the primary way to change sample metadata. See
   :doc:`sample_information`.

Unique names
------------

Every item name must be unique within its table. That way, whenever GeoCORK offers a
list of choices (especially in filters), you never see two options with the same name,
such as *Basalt* and *Basalt*, and have to guess which is which.

GeoCORK has 59 tables in total. Most are used internally and are not shown to users.
All of them are described in :doc:`/database/tables`.
