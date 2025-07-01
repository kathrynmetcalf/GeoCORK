![GeoCORK Logo](GeoCORK_Logo.png)
---
<h2 align="center"> An improved workflow for geochronology data management</h2>

## Description
GeoCORK is a desktop application for managing U-Pb geochronology data which are stored in a local relational database. Data can be imported from .xlsx files in various formats and exported for use in analysis tools and data sharing. For more information on using GeoCORK, refer to Metcalf and Burges, 2025. For more information on GeoCORK development, refer to Burges and Metcalf, 2025.

## Download
Find the latest release [here]().

## Example Files
Two example databases and supporting files can be found at (zenodo link).
Klamath_literature.db is a partial compilation of data from the Klamath Mountains with a variety of data formats. 
Puetz_etal_2024.db is a global detrital zircon database with 1.8 million U-Pb analyses. All data are in a uniform format. Other supporting files document changes made to meet the GeoCORK schema requirements.
Explore these databases or start your own.

## Manual
Video tutorials and a user manual are forthcoming.

## Capabilities
### Import
Import data from .xlsx files in various formats or another GeoCORK database file.

### View/Edit
Edit data tables and metadata tags.

### Filter
Create and save complex queries to filter your database. View and edit matching data.

### Export
Export a portion of your database or filtered data sets for data analysis and sharing. Select a defined export format or create your own.

## Data Stored
Data are stored in a .db file. GeoCORK can import from .xlsx files and export to .csv, .xlsx, or .db.
### Sample Metadata
- Unique sample name
- [IGSN](https://ev.igsn.org/)
- Description
- GPS and Elevation
- Units
- Rock Types
- Regions
- Settings
- Columns (e.g. stratigraphic columns, cores, etc.)
- Contexts
- Sampling Methods
- Age Signatures 
- Sample Ages (tags for constraints, interpretations, and references)

### Aliquot Metadata
- Parent sample
- Parent aliquot for nested aliquots
- Contexts

### Spot Metadata
- Parent aliquot
- Composition of analyzed material
- Contexts

### U-Pb Data and Metadata
- Parent spot
- References
- Lab Facilities
- Instruments
- Analysis Methods
- Spot size
- Errors (Ratios and Ages)
- Units (ages, errors, concordance formats, spot size)
- Rejected/Accepted
- Rejection Reasons
- Contexts
#### Counts per Second
- <sup>204</sup>Pb
- <sup>206</sup>Pb
- <sup>207</sup>Pb
- <sup>208</sup>Pb
- Pb<sup>*</sup>
- <sup>235</sup>U
- <sup>238</sup>U
- <sup>232</sup>Th
#### Concentrations
- U
- Th
- U/Th or Th/U
#### Ratios with errors
- <sup>206</sup>Pb/<sup>207</sup>Pb or <sup>207</sup>Pb/<sup>206</sup>Pb
- <sup>207</sup>Pb/<sup>235</sup>U or <sup>235</sup>U/<sup>207</sup>Pb
- <sup>206</sup>Pb/<sup>238</sup>U or <sup>238</sup>U/<sup>206</sup>Pb
- <sup>208</sup>Pb/<sup>232</sup>Th or <sup>232</sup>U/<sup>208</sup>Pb
- <sup>238</sup>U/<sup>232</sup>Th or <sup>232</sup>Th/<sup>238</sup>U
- <sup>204</sup>Pb/<sup>238</sup>U or <sup>238</sup>U/<sup>204</sup>Pb
- <sup>206</sup>Pb/<sup>204</sup>Pb or <sup>204</sup>Pb/<sup>206</sup>Pb
- <sup>207</sup>Pb/<sup>204</sup>Pb or <sup>204</sup>Pb/<sup>207</sup>Pb
- <sup>208</sup>Pb/<sup>204</sup>Pb or <sup>204</sup>Pb/<sup>208</sup>Pb
- Error Correlation / Rho
#### Ages with errors
- <sup>207</sup>Pb/<sup>206</sup>Pb
- <sup>207</sup>Pb/<sup>235</sup>U
- <sup>206</sup>Pb/<sup>238</sup>U
- Best Age
- Concordance

## Publications
If you have used GeoCORK in your research, please cite the permanent Zenodo doi:

Metcalf K., and Burges J., 2025, GeoCORK: ....., doi:....

The accompanying published articles are:

## Contributing
Set up a github account and fork the source code over to get started. If you are interested in contributing to GeoCORK releases, contact [Kate Metcalf](kametcalf@fullerton.edu).

Part 1
Part 2

## License
GeoCORK is licensed under [GNU GENERAL PUBLIC LICENSE Version 3](https://github.com/kathrynmetcalf/GeoCORK/blob/master/LICENSE)
