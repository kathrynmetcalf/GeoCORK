Schema versions and upgrades
============================

Known schema versions: v1.0.0, v1.0.1, v1.0.2, v1.0.3, v1.0.4, v1.0.5, v1.1.0.

All notable changes to the GeoCORK database schema and the automatic migration
path are documented here. When GeoCORK opens a database whose version is older
than the application's, it asks the user to confirm, creates an automatic
backup, and then applies each migration step in order (see :mod:`util.database.create.Create_database`).

[1.1.0] — Unreleased
^^^^

.. note::
    - No schema migration has been defined yet for v1.0.5 → v1.1.0.
    - *(Add v1.1.0 schema changes here)*

[1.0.5]
^^^^^

- No schema changes. The migration only sets the database version to `v1.0.5`.

[1.0.4]
^^^^

Added
""""

- **UPbAnalyses**: new columns

  - `ErrorCorr/Rho_68v76` (REAL): error correlation for 206Pb/238U vs 207Pb/206Pb
  - `ErrorCorr/Rho_68v75` (REAL): error correlation for 206Pb/238U vs 207Pb/235U
  - `MinimumSegmentedDiscordance` (REAL)
  - `Pbppm` (TEXT)
  - `UPbAnalysisDescription` (TEXT)

- **Aliquots**: new column

  - `AliquotDescription` (TEXT) column.

- **Spots**: new column

  - `SpotDescription` (TEXT) column.

- New setting `show_items_missing_data` (set to its default if missing).

  - Note: this setting will improve performance if left off
- Progress dialogs are shown during each migration stage.

Changed
""""

- **Error correlation split**: the single `ErrorCorr/Rho` value is copied into
  `ErrorCorr/Rho_68v76` for analyses that have a 206Pb/238U–207Pb/206Pb
  concordance, and into `ErrorCorr/Rho_68v75` for analyses that have a
  206Pb/238U–207Pb/235U concordance. An analysis with both gets both.
- **Minimum segmented discordance moved to its own column**: v1.0.3 stored these
  values in the concordance columns (`ConcordanceFormatID = 5`). They are moved
  to `MinimumSegmentedDiscordance`, and the concordance columns and
  `ConcordanceFormatID` are set to NULL for those analyses.
- `UPbAnalyses`, `Spots`, and `Aliquots` are rebuilt using the current table
  definitions.
- **All view/edit column settings are reset to defaults** (UPb analyses, spots,
  grains, aliquots, samples). Any custom column layouts are replaced.

Removed
""""

- The `MinSegDis` concordance format (from `ConcordanceFormats`).
- Minimum-segmented-discordance conversions (rows in
  `ConcordanceFormatConversions` whose calculation is `-`).
- The old single `ErrorCorr/Rho` column (dropped by the table rebuild).

Fixed
""""

- `Spots.GrainID` values containing the literal text `"GrainID"`, left over
  from the v1.0.1 migration, are set to NULL.

[1.0.3]
^^^^^

Added
""""

- **Ages**: new `Color` (TEXT) column, filled from `GeologicTime_Ages.xml` by
  matching age names case-insensitively.
- **UPbAnalyses**: two concordance columns replace the single one:
  - `Concordance_206Pb/238Uv207Pb/206Pb` (REAL)
  - `Concordance_206Pb/238Uv207Pb/235U` (REAL)

Changed
""""

- Existing `Concordance` values are copied into
  `Concordance_206Pb/238Uv207Pb/206Pb`. This assumes all earlier values used
  that definition. (v1.0.4 later moves minimum segmented discordance values out.)
- `UPbAnalyses` is rebuilt with the new table definition.
- UPb analysis view/edit column settings: `Concordance` and
  `CalculatedConcordance` are removed and the new concordance columns are added.

Removed
""""

- The single `Concordance` column in `UPbAnalyses`.

[1.0.2]
^^^^^

- No schema changes. v1.0.2 databases migrate through the same path as v1.0.1
  (straight to v1.0.3).

[1.0.1]
^^^^^

Added
""""

- **Grains**: grain tables, created automatically on open (`Create_database.py`).
- **Spots**: new `GrainID` (INTEGER) column, a foreign key to `Grains(GrainID)`
  (`ON UPDATE CASCADE`, `ON DELETE SET NULL`).
- **UPbAnalyses**: new `UPbAnalysisName` (TEXT) column, filled from the linked
  spot's `SpotName`.
- Grain columns and `UPbAnalysisName` are added to the view/edit column
  settings. Existing custom layouts are kept.

Changed
""""

- `Spots` is rebuilt with:
  - `UNIQUE (SpotName COLLATE NOCASE, AliquotID)`
  - foreign keys to `Aliquots` (cascade), `SpotCompositions` (set null), and `Grains` (set null)
- `UPbAnalyses` is rebuilt using the v1.0.1 table definition.
- **Data correction**: spot names starting with `km001` (case-sensitive) are
  prefixed with `16` (e.g. `km001-…` → `16km001-…`).

Removed
""""

- **Orphaned U-Pb analyses**: analyses whose `SpotID` has no matching spot are
  deleted. Each deletion is logged.

[1.0.0]
""""

- Initial schema release.

---
