Troubleshooting and common issues
=================================

Navigation and names
--------------------

Hovering over buttons, table headers and drop-down items often shows a tooltip with more
information. For database items, the item's description is used as its tooltip. If you
find places where more tooltips would help, let us know on the `GeoCORK GitHub`_.

Video tutorials are coming, and on-screen tutorials are planned for future releases.

Problems opening views
----------------------

As GeoCORK gains features and its internals change, some stored settings may stop working
for some users. We try hard to prevent this, but occasionally settings need to be reset.

If tables display strangely, or column selections or database views cause errors, use
**Restore Defaults** in :doc:`settings`. This fixes many of the most obscure problems.

Fixing an import
----------------

If data were imported incorrectly or columns were missed, the fix is easy as long as the
sample names were imported correctly:

* re-import the whole file with the **Overwrite** conflict mode, or
* import only the missing data with the **Add to** conflict mode.

See :doc:`importing`.

If data were imported by mistake, sort the samples by newest created in the main window
and delete them. Deleting a sample also deletes all its aliquots, grains, spots and U-Pb
analyses. Remove other imported metadata the same way in the other tables. Trees cannot
be sorted, but newly imported items are added as top-level items at the end.

Opening and reading log files
-----------------------------

In settings, the **About Database** tab has two buttons at the bottom: **Open Logs
Folder** and **Open Backups Folder**. Each opens a file browser at that folder.

GeoCORK writes a new log each time it starts. Log files describe what GeoCORK was doing in
detail, including fuller error messages, which makes them very useful for debugging. While
GeoCORK is open, the newest log file is the current session.

Reporting bugs, features, ideas and suggestions
-----------------------------------------------

We welcome all feedback on the `GeoCORK GitHub`_. Please open a detailed issue for each
bug, feature, idea or suggestion. For bugs, include all diagnostic information, including
the log file from the time the problem happened.
