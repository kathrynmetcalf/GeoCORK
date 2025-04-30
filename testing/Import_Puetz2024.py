import pandas as pd
import openpyxl
import sqlite3
import re

def import_rock_type(conn, name, parent_id, parent_row):
    """
    Import a rock type into the database.
    :param name: The name of the rock type
    :param parent_id: The ID of the parent rock type
    :param parent_row: The row of the parent rock type
    """
    try:
        cursor = conn.cursor()
        cursor.execute(f'INSERT INTO RockTypes (RockTypeName, ParentRockTypeID, RockTypeParentRow) VALUES (?, ?, ?)',
                       (name, parent_id, parent_row))
        conn.commit()
        cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ? COLLATE NOCASE', (name,))
        rock_type_id = cursor.fetchone()
        if rock_type_id is None:
            print(f"Failed to add rock type {name} to the database")
            return
        return rock_type_id
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return


def Puetz_importer():
    """
    Method to import the data from Puetz et al. (2024) and convert it into a format
    that can be used by the model.
    """
    full_data = '/Users/kametcalf/Zotero/storage/9M4KJZG4/DB1_2019.xlsx'
    db = '/Users/kametcalf/Documents/Research/GeoChron_non_git/Puetz_et_al_2024.db'
    reference_dict = {}
    ref_sample_dict = {}
    sample_analysis_tags_dict = {}

    # --------------------
    # Import the references from Puetz et al. (2024) into the database file.
    # --------------------
    sheet_name = 'References'
    try:
        reference_df = pd.read_excel(full_data, header=None, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        print(f"Failed to parse sheet with pandas:\n{e}")
        return
    while not reference_df.empty and reference_df.iloc[0].isna().all():
        reference_df = reference_df.iloc[1:].reset_index(drop=True)

    rows, cols = reference_df.shape

    # create dictionary for reference number and reference fields
    # add each reference to the database
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for i in range(1, rows):
            lead_author = reference_df.iloc[i, 1]
            year = reference_df.iloc[i, 2]
            journal = reference_df.iloc[i, 3]
            vol = reference_df.iloc[i, 4]
            pages = reference_df.iloc[i, 5]
            title = reference_df.iloc[i, 6]
            web_link = reference_df.iloc[i, 7]
            doi = ''
            if isinstance(web_link, str):
                if 'doi.org' in web_link:
                    doi = web_link.split('doi.org/')[1]
            if (pd.isna(lead_author) and pd.isna(year) and pd.isna(journal) and pd.isna(vol) and pd.isna(pages)
                    and pd.isna(title)):
                continue
            print(f'importing {lead_author} {year} {journal} {vol} {pages} {title}')
            cursor.execute(f'''SELECT ReferenceID FROM "References" WHERE Authors = ? AND Year = ? AND 
                                    Title = ? AND Source = ? AND DOI = ?''', (lead_author, year, title, journal, doi))
            reference_id = cursor.fetchone()
            if reference_id is None:
                # if not, add it to the database
                cursor.execute(f'INSERT INTO "References" (Authors, Year, Title, Source, DOI) VALUES (?, ?, ?, ?, ?)',
                               (lead_author, year, title, journal, doi))
                conn.commit()
                cursor.execute(f'''SELECT ReferenceID FROM "References" WHERE Authors = ? AND Year = ? AND 
                                    Title = ? AND Source = ? AND DOI = ?''', (lead_author, year, title, journal, doi))
                reference_id = cursor.fetchone()
                if reference_id is None:
                    print(f"Failed to add reference {lead_author} {year} to the database")
                    return
            reference_id = reference_id[0]
            reference_dict[reference_df.iloc[i, 0]] = reference_id
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return


    # --------------------
    # Import the samples from Puetz et al. (2024) into the database file.
    # --------------------
    sheet_name = 'Samples'
    try:
        sample_df = pd.read_excel(full_data, header=None, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        print(f"Failed to parse sheet with pandas:\n{e}")
        return
    while not sample_df.empty and sample_df.iloc[0].isna().all():
        sample_df = sample_df.iloc[1:].reset_index(drop=True)
    rows, cols = sample_df.shape

    gps_format_id = 1
    age_unit_id = 2

    # create dictionary for sample number and sample fields
    # add each sample to the database
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for i in range(1, rows):
            # get sample information

            sample_name = sample_df.iloc[i, 1]
            if pd.isna(sample_name):
                continue
            print(f'importing {sample_name}')

            # Regions
            # add each continent, large region, country/small region, and locality to the database
            # check if continent is in the database
            continent_name = sample_df.iloc[i, 4]
            large_region_name = sample_df.iloc[i, 3]
            country_name = sample_df.iloc[i, 2]
            locality_name = sample_df.iloc[i, 7]
            if pd.isna(continent_name) and pd.isna(large_region_name) and pd.isna(country_name) and pd.isna(locality_name):
                continent_id = None
                region_id = None
                country_id = None
                locality_id = None
                region_ids = []
            else:
                cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
                               (continent_name,))
                continent_id = cursor.fetchone()
                if continent_id is None:
                    # if not, add it to the database
                    # get the largest value for RegionParentRow of the continent_id
                    print(f'importing {continent_name}')
                    cursor.execute(f'SELECT MAX(RegionParentRow) FROM Regions WHERE ParentRegionID IS NULL')
                    parent_row = cursor.fetchone()
                    if parent_row[0] is None:
                        parent_row = 0
                    else:
                        parent_row = parent_row[0] + 1
                    cursor.execute(f'INSERT INTO Regions (RegionName, RegionParentRow) VALUES (?, ?)',
                                   (continent_name, parent_row))
                    conn.commit()
                    cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
                                   (continent_name,))
                    continent_id = cursor.fetchone()
                    if continent_id is None:
                        print(f"Failed to add region {continent_name} to the database")
                        return
                continent_id = continent_id[0]
                # check if large region is in the database
                cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
                               (large_region_name,))
                region_id = cursor.fetchone()
                if region_id is None:
                    # if not, add it to the database
                    # get the largest value for RegionParentRow of the continent_id
                    print(f'importing {large_region_name}')
                    cursor.execute(f'SELECT MAX(RegionParentRow) FROM Regions WHERE ParentRegionID = ?',
                                   (continent_id,))
                    parent_row = cursor.fetchone()
                    if parent_row[0] is None:
                        parent_row = 0
                    else:
                        parent_row = parent_row[0] + 1
                    cursor.execute(
                        f'INSERT INTO Regions (RegionName, ParentRegionID, RegionParentRow) VALUES (?,?,?)',
                        (large_region_name, continent_id, parent_row))
                    conn.commit()
                    cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
                                   (large_region_name,))
                    region_id = cursor.fetchone()
                    if region_id is None:
                        print(f"Failed to add region {large_region_name} to the database")
                        return
                region_id = region_id[0]
                cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
                               (country_name,))
                country_id = cursor.fetchone()
                if country_id is None:
                    # if not, add it to the database
                    # get the largest value for RegionParentRow of the region_id
                    cursor.execute(f'SELECT MAX(RegionParentRow) FROM Regions WHERE ParentRegionID = ?',
                                   (region_id,))
                    parent_row = cursor.fetchone()
                    if parent_row[0] is None:
                        parent_row = 0
                    else:
                        parent_row = parent_row[0] + 1
                    cursor.execute(
                        f'INSERT INTO Regions (RegionName, ParentRegionID, RegionParentRow) VALUES (?,?,?)',
                        (country_name, region_id, parent_row))
                    conn.commit()
                    cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
                                   (country_name,))
                    country_id = cursor.fetchone()
                    if country_id is None:
                        print(f"Failed to add region {country_name} to the database")
                        return
                country_id = country_id[0]
                # check if locality is in the database
                cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
                               (locality_name,))
                locality_id = cursor.fetchone()
                if locality_id is None:
                    # if not, add it to the database
                    # get the largest value for RegionParentRow of the region_id
                    print(f'importing {locality_name}')
                    cursor.execute(f'SELECT MAX(RegionParentRow) FROM Regions WHERE ParentRegionID = ?',
                                   (country_id,))
                    parent_row = cursor.fetchone()
                    if parent_row[0] is None:
                        parent_row = 0
                    else:
                        parent_row = parent_row[0] + 1
                    cursor.execute(f'INSERT INTO Regions (RegionName, ParentRegionID, RegionParentRow) VALUES (?,?,?)',
                                   (locality_name, country_id, parent_row))
                    conn.commit()
                    cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
                                   (locality_name,))
                    locality_id = cursor.fetchone()
                    if locality_id is None:
                        print(f"Failed to add region {locality_name} to the database")
                        return
                locality_id = locality_id[0]
                region_ids = [continent_id, region_id, country_id, locality_id]

            # Units
            major_unit_name = sample_df.iloc[i, 5]
            minor_unit_name = sample_df.iloc[i, 6]
            if pd.isna(major_unit_name) and pd.isna(minor_unit_name):
                major_unit_id = None
                minor_unit_id = None
                unit_ids = []
            else:
                cursor.execute(f'SELECT UnitID FROM Units WHERE UnitName = ? COLLATE NOCASE', (major_unit_name,))
                major_unit_id = cursor.fetchone()
                if major_unit_id is None:
                    # if not, add it to the database
                    # get the largest value for UnitParentRow of the major_unit_id
                    cursor.execute(f'SELECT MAX(UnitParentRow) FROM Units WHERE ParentUnitID IS NULL')
                    parent_row = cursor.fetchone()
                    if parent_row[0] is None:
                        parent_row = 0
                    else:
                        parent_row = parent_row[0] + 1
                    cursor.execute(f'INSERT INTO Units (UnitName, UnitParentRow) VALUES (?, ?)',
                                     (major_unit_name, parent_row))
                    conn.commit()
                    cursor.execute(f'SELECT UnitID FROM Units WHERE UnitName = ? COLLATE NOCASE', (major_unit_name,))
                    major_unit_id = cursor.fetchone()
                    if major_unit_id is None:
                        print(f"Failed to add unit {major_unit_name} to the database")
                        return
                major_unit_id = major_unit_id[0]
                # check if minor unit is in the database
                cursor.execute(f'SELECT UnitID FROM Units WHERE UnitName = ? COLLATE NOCASE', (minor_unit_name,))
                minor_unit_id = cursor.fetchone()
                if minor_unit_id is None:
                    # if not, add it to the database
                    # get the largest value for UnitParentRow of the minor_unit_id
                    cursor.execute(f'SELECT MAX(UnitParentRow) FROM Units WHERE ParentUnitID = ?',
                                   (major_unit_id,))
                    parent_row = cursor.fetchone()
                    if parent_row[0] is None:
                        parent_row = 0
                    else:
                        parent_row = parent_row[0] + 1
                    cursor.execute(f'INSERT INTO Units (UnitName, ParentUnitID, UnitParentRow) VALUES (?, ?, ?)',
                                   (minor_unit_name, major_unit_id, parent_row))
                    conn.commit()
                    cursor.execute(f'SELECT UnitID FROM Units WHERE UnitName = ? COLLATE NOCASE', (minor_unit_name,))
                    minor_unit_id = cursor.fetchone()
                    if minor_unit_id is None:
                        print(f"Failed to add unit {minor_unit_name} to the database")
                        return
                minor_unit_id = minor_unit_id[0]
                unit_ids = [major_unit_id, minor_unit_id]

            # GPS location
            gps_lat = sample_df.iloc[i, 8]
            gps_lon = sample_df.iloc[i, 9]
            if pd.isna(gps_lat) or pd.isna(gps_lon):
                gps_id = None
            else:
                cursor.execute(f'SELECT GPSLocationID FROM GPSLocations WHERE GPSLatDeg = ? AND GPSLonDeg = ?',
                               (gps_lat, gps_lon))
                gps_id = cursor.fetchone()
                if gps_id is None:
                    # if not, add it to the database
                    cursor.execute(f'INSERT INTO GPSLocations (GPSLatDeg, GPSLonDeg, GPSFormatID) VALUES (?, ?, ?)',
                                   (gps_lat, gps_lon, gps_format_id))
                    conn.commit()
                    cursor.execute(f'SELECT GPSLocationID FROM GPSLocations WHERE GPSLatDeg = ? AND GPSLonDeg = ?',
                                   (gps_lat, gps_lon))
                    gps_id = cursor.fetchone()
                    if gps_id is None:
                        print(f"Failed to add sample {sample_name} to the database")
                        return
                gps_id = gps_id[0]

            # Sample age
            sample_age_max = sample_df.iloc[i, 10]
            sample_age_est = sample_df.iloc[i, 11]
            sample_age_min = sample_df.iloc[i, 12]
            if pd.isna(sample_age_max) and pd.isna(sample_age_est) and pd.isna(sample_age_min):
                sample_age_id = None
            else:
                cursor.execute(f'''SELECT SampleAgeID FROM SampleAges WHERE OldestDirectAge = ? AND 
                                        YoungestDirectAge = ? AND DirectAge = ? AND DirectAgeUnitID = ?''',
                               (sample_age_max, sample_age_min, sample_age_est, age_unit_id))
                sample_age_id = cursor.fetchone()
                if sample_age_id is None:
                    # if not, add it to the database
                    cursor.execute(f'INSERT INTO SampleAges (OldestDirectAge, YoungestDirectAge, DirectAge, DirectAgeUnitID) VALUES (?, ?, ?, ?)',
                                   (sample_age_max, sample_age_min, sample_age_est, age_unit_id))
                    conn.commit()
                    cursor.execute(f'''SELECT SampleAgeID FROM SampleAges WHERE OldestDirectAge = ? AND 
                                        YoungestDirectAge = ? AND DirectAge = ? AND DirectAgeUnitID = ?''',
                                   (sample_age_max, sample_age_min, sample_age_est, age_unit_id))
                    sample_age_id = cursor.fetchone()
                    if sample_age_id is None:
                        print(f"Failed to add sample {sample_name} to the database")
                        return
                sample_age_id = sample_age_id[0]

            # Mineral
            # check if mineral is in the database
            spot_composition_name = sample_df.iloc[i, 13]
            if pd.isna(spot_composition_name):
                spot_composition_id = None
            else:
                cursor.execute(
                    f'SELECT SpotCompositionID FROM SpotCompositions WHERE SpotCompositionName = ? COLLATE NOCASE',
                    (spot_composition_name,))
                spot_composition_id = cursor.fetchone()
                if spot_composition_id is None:
                    # if not, add it to the database
                    # get the largest value for SpotCompositionParentRow of the spot_composition_id
                    cursor.execute(
                        f'SELECT MAX(SpotCompositionParentRow) FROM SpotCompositions WHERE ParentSpotCompositionID IS NULL')
                    parent_row = cursor.fetchone()
                    if parent_row[0] is None:
                        parent_row = 0
                    else:
                        parent_row = parent_row[0] + 1
                    cursor.execute(
                        f'INSERT INTO SpotCompositions (SpotCompositionName, SpotCompositionParentRow) VALUES (?,?)',
                        (spot_composition_name, parent_row))
                    conn.commit()
                    cursor.execute(
                        f'SELECT SpotCompositionID FROM SpotCompositions WHERE SpotCompositionName = ? COLLATE NOCASE',
                        (spot_composition_name,))
                    spot_composition_id = cursor.fetchone()
                    if spot_composition_id is None:
                        print(f"Failed to add mineral {spot_composition_name} to the database")
                        return
                spot_composition_id = spot_composition_id[0]

            # Methods
            method_name = sample_df.iloc[i, 14]
            if pd.isna(method_name):
                method_id = None
            else:
                # check if method is in the database
                cursor.execute(f'SELECT UPbAnalysisMethodID FROM UPbAnalysisMethods WHERE UPbAnalysisMethodName = ? COLLATE NOCASE',
                               (method_name,))
                method_id = cursor.fetchone()
                if method_id is None:
                    # if not, add it to the database
                    # get the largest value for UPbAnalysisMethodParentRow of the method_id
                    print(f'importing {method_name}')
                    cursor.execute(f'SELECT MAX("UPbAnalysisMethodParentRow") FROM UPbAnalysisMethods WHERE "ParentUPbAnalysisMethodID" IS NULL')
                    parent_row = cursor.fetchone()
                    if parent_row[0] is None:
                        parent_row = 0
                    else:
                        parent_row = parent_row[0] + 1
                    cursor.execute(f'INSERT INTO UPbAnalysisMethods (UPbAnalysisMethodName, UPbAnalysisMethodParentRow) VALUES (?, ?)',
                                   (method_name, parent_row))
                    conn.commit()
                    cursor.execute(f'SELECT UPbAnalysisMethodID FROM UPbAnalysisMethods WHERE UPbAnalysisMethodName = ? COLLATE NOCASE',
                                   (method_name,))
                    method_id = cursor.fetchone()
                    if method_id is None:
                        print(f"Failed to add method {method_name} to the database")
                        return
                method_id = method_id[0]

            # Lab facilities
            facility_name = sample_df.iloc[i, 15]
            facility_description = sample_df.iloc[i, 16]
            if pd.isna(facility_name):
                facility_id = None
            else:
                # check if facility is in the database
                cursor.execute(f'SELECT LabFacilityID FROM LabFacilities WHERE LabFacilityName = ? COLLATE NOCASE',
                               (facility_name,))
                facility_id = cursor.fetchone()
                if facility_id is None:
                    # if not, add it to the database
                    print(f'importing {facility_name}')
                    cursor.execute(f'INSERT INTO LabFacilities (LabFacilityName, LabFacilityDescription) VALUES (?, ?)',
                                   (facility_name, facility_description))
                    conn.commit()
                    cursor.execute(f'SELECT LabFacilityID FROM LabFacilities WHERE LabFacilityName = ? COLLATE NOCASE',
                                   (facility_name,))
                    facility_id = cursor.fetchone()
                    if facility_id is None:
                        print(f"Failed to add facility {facility_name} to the database")
                        return
                facility_id = facility_id[0]

            # Instruments
            instrument_name = sample_df.iloc[i, 17]
            if pd.isna(instrument_name):
                instrument_id = None
            else:
                # check if instrument is in the database
                cursor.execute(f'SELECT InstrumentID FROM Instruments WHERE InstrumentName = ? COLLATE NOCASE',
                                 (instrument_name,))
                instrument_id = cursor.fetchone()
                if instrument_id is None:
                    # if not, add it to the database
                    print(f'importing {instrument_name}')
                    cursor.execute(f'INSERT INTO Instruments (InstrumentName) VALUES (?)', (instrument_name,))
                    conn.commit()
                    cursor.execute(f'SELECT InstrumentID FROM Instruments WHERE InstrumentName = ? COLLATE NOCASE',
                                      (instrument_name,))
                    instrument_id = cursor.fetchone()
                    if instrument_id is None:
                        print(f"Failed to add instrument {instrument_name} to the database")
                        return
                instrument_id = instrument_id[0]

            # Rock types
            rock_type1_name = sample_df.iloc[i, 18]
            rock_type2_name = sample_df.iloc[i, 19]
            rock_type3_name = sample_df.iloc[i, 20]
            if pd.isna(rock_type1_name) and pd.isna(rock_type2_name) and pd.isna(rock_type3_name):
                rock_type1_id = None
                rock_type2_id = None
                rock_type3_id = None
                rock_type_ids = []
            else:
                cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ? COLLATE NOCASE',
                               (rock_type1_name,))
                rock_type1_id = cursor.fetchone()
                if rock_type1_id is None:
                    # if not, add it to the database
                    # get the largest value for RockTypeParentRow of the rock_type1_id
                    print(f'importing {rock_type1_name}')
                    cursor.execute(f'SELECT MAX(RockTypeParentRow) FROM RockTypes WHERE ParentRockTypeID IS NULL')
                    parent_row = cursor.fetchone()
                    if parent_row[0] is None:
                        parent_row = 0
                    else:
                        parent_row = parent_row[0] + 1
                    cursor.execute(f'INSERT INTO RockTypes (RockTypeName, RockTypeParentRow) VALUES (?, ?)',
                                      (rock_type1_name, parent_row))
                    conn.commit()
                    cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ? COLLATE NOCASE',
                                      (rock_type1_name,))
                    rock_type1_id = cursor.fetchone()
                    if rock_type1_id is None:
                        print(f"Failed to add rock type {rock_type1_name} to the database")
                        return
                rock_type1_id = rock_type1_id[0]
                # check if rock type 2 is in the database
                cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ? COLLATE NOCASE',
                               (rock_type2_name,))
                rock_type2_id = cursor.fetchone()
                if rock_type2_id is None:
                    # if not, add it to the database
                    # get the largest value for RockTypeParentRow of the rock_type2_id
                    print(f'importing {rock_type2_name}')
                    cursor.execute(f'SELECT MAX(RockTypeParentRow) FROM RockTypes WHERE ParentRockTypeID = ?',
                                   (rock_type1_id,))
                    parent_row = cursor.fetchone()
                    if parent_row[0] is None:
                        parent_row = 0
                    else:
                        parent_row = parent_row[0] + 1
                    cursor.execute(f'INSERT INTO RockTypes (RockTypeName, ParentRockTypeID, RockTypeParentRow) VALUES (?, ?, ?)',
                                   (rock_type2_name, rock_type1_id, parent_row))
                    conn.commit()
                    cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ? COLLATE NOCASE',
                                   (rock_type2_name,))
                    rock_type2_id = cursor.fetchone()
                    if rock_type2_id is None:
                        print(f"Failed to add rock type {rock_type2_name} to the database")
                        return
                rock_type2_id = rock_type2_id[0]
                # check if rock type 3 is in the database
                cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ? COLLATE NOCASE',
                                 (rock_type3_name,))
                rock_type3_id = cursor.fetchone()
                if rock_type3_id is None:
                    # if not, add it to the database
                    # get the largest value for RockTypeParentRow of the rock_type3_id
                    print(f'importing {rock_type3_name}')
                    cursor.execute(f'SELECT MAX(RockTypeParentRow) FROM RockTypes WHERE ParentRockTypeID = ?',
                                   (rock_type2_id,))
                    parent_row = cursor.fetchone()
                    if parent_row[0] is None:
                        parent_row = 0
                    else:
                        parent_row = parent_row[0] + 1
                    cursor.execute(f'INSERT INTO RockTypes (RockTypeName, ParentRockTypeID, RockTypeParentRow) VALUES (?, ?, ?)',
                                   (rock_type3_name, rock_type2_id, parent_row))
                    conn.commit()
                    cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ? COLLATE NOCASE',
                                   (rock_type3_name,))
                    rock_type3_id = cursor.fetchone()
                    if rock_type3_id is None:
                        print(f"Failed to add rock type {rock_type3_name} to the database")
                        return
                rock_type3_id = rock_type3_id[0]
                rock_type_ids = [rock_type1_id, rock_type2_id, rock_type3_id]

            # Sample
            cursor.execute(f'SELECT SampleID FROM Samples WHERE SampleName = ? COLLATE NOCASE', (sample_name,))
            sample_id = cursor.fetchone()
            if sample_id is None:
                # if not, add it to the database
                cursor.execute(f'INSERT INTO Samples (SampleName, SampleGPSLocationID) Values (?, ?)',
                               (sample_name, gps_id))
                conn.commit()
                cursor.execute(f'SELECT SampleID FROM Samples WHERE SampleName = ? COLLATE NOCASE', (sample_name,))
                sample_id = cursor.fetchone()
                if sample_id is None:
                    print(f"Failed to add sample {sample_name} to the database")
                    return
            sample_id = sample_id[0]

            # add the sample name and reference key to the dictionary
            ref_sample_key = sample_df.iloc[i, 0]
            ref_sample_dict[ref_sample_key] = sample_id

            # Many to many
            for region_id in region_ids:
                cursor.execute(f'SELECT SampleID, RegionID FROM Samples_Regions WHERE SampleID = ? AND RegionID = ?',
                               (sample_id, region_id))
                result = cursor.fetchone()
                if result is None:
                    # if not, add it to the database
                    cursor.execute(f'INSERT INTO Samples_Regions (SampleID, RegionID) Values (?, ?)',
                                   (sample_id, region_id))
                    conn.commit()
                    cursor.execute(f'SELECT SampleID, RegionID FROM Samples_Regions WHERE SampleID = ? AND RegionID = ?',
                                    (sample_id, region_id))
                    result = cursor.fetchone()
                    if result is None:
                        print(f"Failed to add sample {sample_name} to the database")
                        return

            for rock_type_id in rock_type_ids:
                cursor.execute(f'SELECT SampleID, RockTypeID FROM Samples_RockTypes WHERE SampleID = ? AND RockTypeID = ?',
                               (sample_id, rock_type_id))
                result = cursor.fetchone()
                if result is None:
                    # if not, add it to the database
                    cursor.execute(f'INSERT INTO Samples_RockTypes (SampleID, RockTypeID) Values (?, ?)',
                                   (sample_id, rock_type_id))
                    conn.commit()
                    cursor.execute(f'SELECT SampleID, RockTypeID FROM Samples_RockTypes WHERE SampleID = ? AND RockTypeID = ?',
                                   (sample_id, rock_type_id))
                    result = cursor.fetchone()
                    if result is None:
                        print(f"Failed to add sample {sample_name} to the database")
                        return

            if sample_age_id is not None:
                cursor.execute(f'SELECT SampleID, SampleAgeID FROM Samples_SampleAges WHERE SampleID = ? AND SampleAgeID = ?',
                               (sample_id, sample_age_id))
                result = cursor.fetchone()
                if result is None:
                    # if not, add it to the database
                    cursor.execute(f'INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) Values (?, ?)',
                                   (sample_id, sample_age_id))
                    conn.commit()
                    cursor.execute(f'SELECT SampleID, SampleAgeID FROM Samples_SampleAges WHERE SampleID = ? AND SampleAgeID = ?',
                                   (sample_id, sample_age_id))
                    result = cursor.fetchone()
                    if result is None:
                        print(f"Failed to add sample {sample_name} to the database")
                        return

            for unit_id in unit_ids:
                cursor.execute(f'SELECT SampleID, UnitID FROM Samples_Units WHERE SampleID = ? AND UnitID = ?',
                               (sample_id, unit_id))
                result = cursor.fetchone()
                if result is None:
                    # if not, add it to the database
                    cursor.execute(f'INSERT INTO Samples_Units (SampleID, UnitID) Values (?, ?)',
                                   (sample_id, unit_id))
                    conn.commit()
                    cursor.execute(f'SELECT SampleID, UnitID FROM Samples_Units WHERE SampleID = ? AND UnitID = ?',
                                   (sample_id, unit_id))
                    result = cursor.fetchone()
                    if result is None:
                        print(f"Failed to add sample {sample_name} to the database")
                        return

            sample_analysis_tags_dict[sample_id] = [method_id, facility_id, instrument_id]

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    # --------------------
    # Import the spot compositions from Puetz et al. (2024) into the database file.
    # --------------------
    sheet_name = 'UPb_Data'
    try:
        upb_df = pd.read_excel(full_data, header=None, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        print(f"Failed to parse sheet with pandas:\n{e}")
        return
    while not upb_df.empty and upb_df.iloc[0].isna().all():
        upb_df = upb_df.iloc[1:].reset_index(drop=True)
    rows, cols = upb_df.shape

    spot_composition_id = 1
    spot_size_unit_id = 5
    ratio_error_format_id = 1
    age_error_format_id = 2
    age_unit_id = 2
    concordance_format_id = 3

    for i in range(1, rows):
        # get analysis information

        # reference
        ref_sample_key = upb_df.iloc[i, 0]
        if pd.isna(ref_sample_key):
            continue
        print(f'importing {ref_sample_key}')
        ref_id = ref_sample_key.split('-')[0]
        if ref_id in reference_dict:
            reference_id = reference_dict[ref_id]
        else:
            print(f"Failed to find reference {ref_id} in the dictionary")
            return

        # Sample
        sample_id = ref_sample_dict[ref_sample_key]

        # Aliquot
        try:
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            cursor.execute(f'SELECT SampleName FROM Samples WHERE SampleID = ?', (sample_id,))
            sample_name = cursor.fetchone()
            if sample_name is None:
                print(f"Failed to find sample {sample_id} in the database")
                return
            new_aliquot = True
            sample_name = sample_name[0]
            cursor.execute(f'SELECT AliquotID FROM Aliquots WHERE SampleID = ?', (sample_id,))
            aliquot_id = cursor.fetchall()
            if len(aliquot_id) > 0:
                # check if the name we want to use exists
                cursor.execute(f'SELECT AliquotID FROM Aliquots WHERE AliquotName = ?', (sample_name,))
                aliquot_id = cursor.fetchone()
            if not aliquot_id:
                # if not, add it to the database
                # get the largest value for AliquotParentRow of the aliquot_id
                cursor.execute(f'SELECT MAX(AliquotParentRow) FROM Aliquots WHERE ParentAliquotID IS NULL AND SampleID = ?',
                               (sample_id,))
                parent_row = cursor.fetchone()
                if parent_row[0] is None:
                    parent_row = 0
                else:
                    parent_row = parent_row[0] + 1
                aliquot_name = sample_name
                cursor.execute(f'INSERT INTO Aliquots (AliquotName, AliquotParentRow, SampleID) VALUES (?, ?, ?)',
                               (aliquot_name, parent_row, sample_id))
                conn.commit()
                cursor.execute(f'SELECT AliquotID FROM Aliquots WHERE AliquotName = ? COLLATE NOCASE', (aliquot_name,))
                aliquot_id = cursor.fetchone()
                if aliquot_id is None:
                    print(f"Failed to add aliquot {aliquot_name} to the database")
                    return
            aliquot_id = aliquot_id[0]
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return


        # Spot
        spot_name = upb_df.iloc[i, 1]
        if pd.isna(spot_name):
            continue
        try:
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            cursor.execute(f'SELECT SpotID FROM Spots WHERE SpotName = ? COLLATE NOCASE', (spot_name,))
            spot_id = cursor.fetchone()
            if spot_id is None:
                # if not, add it to the database
                print(f'importing {spot_name}')
                cursor.execute(f'INSERT INTO Spots (SpotName, AliquotID, SpotCompositionID) VALUES (?, ?, ?)',
                               (spot_name, aliquot_id, spot_composition_id))
                conn.commit()
                cursor.execute(f'SELECT SpotID FROM Spots WHERE SpotName = ? COLLATE NOCASE', (spot_name,))
                spot_id = cursor.fetchone()
                if spot_id is None:
                    print(f"Failed to add spot {spot_name} to the database")
                    return
            spot_id = spot_id[0]
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return

        # spot_context
        spot_context = upb_df.iloc[i, 2]
        if pd.isna(spot_context):
            spot_context_id = None
        else:
            try:
                conn = sqlite3.connect(db)
                cursor = conn.cursor()
                cursor.execute(f'SELECT SpotContextID FROM SpotContexts WHERE SpotContextName = ? COLLATE NOCASE',
                               (spot_context,))
                spot_context_id = cursor.fetchone()
                if spot_context_id is None:
                    # if not, add it to the database
                    # get the largest value for SpotContextParentRow of the spot_context_id
                    cursor.execute(f'SELECT MAX(SpotContextParentRow) FROM SpotContexts WHERE ParentSpotContextID IS NULL')
                    parent_row = cursor.fetchone()
                    if parent_row[0] is None:
                        parent_row = 0
                    else:
                        parent_row = parent_row[0] + 1
                    cursor.execute(f'INSERT INTO SpotContexts (SpotContextName, SpotContextParentRow) VALUES (?,?)',
                                   (spot_context, parent_row))
                    conn.commit()
                    cursor.execute(f'SELECT SpotContextID FROM SpotContexts WHERE SpotContextName = ? COLLATE NOCASE',
                                   (spot_context,))
                    spot_context_id = cursor.fetchone()
                    if spot_context_id is None:
                        print(f"Failed to add spot context {spot_context} to the database")
                        return
                spot_context_id = spot_context_id[0]
                conn.commit()
                conn.close()
            except sqlite3.Error as e:
                print(f"SQLite error: {e}")
                return

        # Spot tags
        if spot_context_id is not None:
            try:
                conn = sqlite3.connect(db)
                cursor = conn.cursor()
                cursor.execute(f'SELECT SpotID FROM Spots_SpotContexts WHERE SpotID = ? AND SpotContextID = ?',
                               (spot_id, spot_context_id))
                result = cursor.fetchone()
                if result is None:
                    # if not, add it to the database
                    cursor.execute(f'INSERT INTO Spots_SpotContexts (SpotID, SpotContextID) VALUES (?, ?)',
                                   (spot_id, spot_context_id))
                    conn.commit()
                    cursor.execute(f'SELECT SpotID FROM Spots_SpotContexts WHERE SpotID = ? AND SpotContextID = ?',
                                   (spot_id, spot_context_id))
                    result = cursor.fetchone()
                    if result is None:
                        print(f"Failed to add spot tags {spot_name} to the database")
                        return
            except sqlite3.Error as e:
                print(f"SQLite error: {e}")
                return

        # Analysis tags
        analysis_tags = sample_analysis_tags_dict[sample_id]
        method_id = analysis_tags[0]
        lab_facility_id = analysis_tags[1]
        instrument_id = analysis_tags[2]

        # Spot size
        spot_size = upb_df.iloc[i, 3]
        if pd.isna(spot_size):
            spot_size = None


        # ratios
        pb6_u8 = upb_df.iloc[i, 5]
        if pd.isna(pb6_u8):
            pb6_u8 = None
        pb6_u8_err = upb_df.iloc[i, 6]
        if pd.isna(pb6_u8_err):
            pb6_u8_err = None
        pb7_u5 = upb_df.iloc[i, 7]  # calculated based on 238U/235U = 137.818
        if pd.isna(pb7_u5):
            pb7_u5 = None
        pb7_u5_err = upb_df.iloc[i, 8]  # calculated based on 238U/235U = 137.818
        if pd.isna(pb7_u5_err):
            pb7_u5_err = None
        pb7_pb6 = upb_df.iloc[i, 9]
        if pd.isna(pb7_pb6):
            pb7_pb6 = None
        pb7_pb6_err = upb_df.iloc[i, 10]
        if pd.isna(pb7_pb6_err):
            pb7_pb6_err = None
        rho = upb_df.iloc[i, 11]
        if pd.isna(rho):
            rho = None

        # ages
        pb6_u8_age = upb_df.iloc[i, 13]
        if pd.isna(pb6_u8_age):
            pb6_u8_age = None
        pb6_u8_age_err = upb_df.iloc[i, 14]
        if pd.isna(pb6_u8_age_err):
            pb6_u8_age_err = None
        pb7_u5_age = upb_df.iloc[i, 15]  # calculated based on 238U/235U = 137.818
        if pd.isna(pb7_u5_age):
            pb7_u5_age = None
        pb7_u5_age_err = upb_df.iloc[i, 16]  # calculated based on 238U/235U = 137.818
        if pd.isna(pb7_u5_age_err):
            pb7_u5_age_err = None
        pb7_pb6_age = upb_df.iloc[i, 17]
        if pd.isna(pb7_pb6_age):
            pb7_pb6_age = None
        pb7_pb6_age_err = upb_df.iloc[i, 18]
        if pd.isna(pb7_pb6_age_err):
            pb7_pb6_age_err = None
        best_age = upb_df.iloc[i, 28]
        if pd.isna(best_age):
            best_age = None
        best_age_err = upb_df.iloc[i, 29]
        if pd.isna(best_age_err):
            best_age_err = None
        concordance = upb_df.iloc[i, 30]
        if pd.isna(concordance):
            concordance = None

        if (pd.isna(pb6_u8) and pd.isna(pb6_u8_err) and pd.isna(pb7_pb6) and pd.isna(pb7_pb6_err) and
                pd.isna(pb6_u8_age) and pd.isna(pb6_u8_age_err) and pd.isna(pb7_u5_age) and pd.isna(pb7_u5_age_err) and
                pd.isna(pb7_pb6_age) and pd.isna(pb7_pb6_age_err) and pd.isna(best_age) and pd.isna(best_age_err)):
            continue
        print(f'importing {spot_name} data')
        try: 
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            # check if analysis is in the database
            cursor.execute(f'''SELECT UPbAnalysisID FROM UPbAnalyses WHERE 
                            iif(:spot_id IS NULL, SpotID IS NULL, SpotID = :spot_id) AND 
                            iif(:reference_id IS NULL, "ReferenceID" IS NULL, "ReferenceID" = :reference_id) AND
                            iif(:lab_facility_id IS NULL, LabFacilityID IS NULL, LabFacilityID = :lab_facility_id) AND
                            iif(:instrument_id IS NULL, InstrumentID IS NULL, InstrumentID = :instrument_id) AND
                            iif(:method_id IS NULL, UPbAnalysisMethodID IS NULL, UPbAnalysisMethodID = :method_id) AND
                            iif(:pb7_pb6 IS NULL, "207Pb/206Pb" IS NULL, "207Pb/206Pb" = :pb7_pb6) AND
                            iif(:pb7_pb6_err IS NULL, "207Pb/206PbError" IS NULL, "207Pb/206PbError" = :pb7_pb6_err) AND
                            iif(:pb7_u5 IS NULL, "207Pb/235U" IS NULL, "207Pb/235U" = :pb7_u5) AND
                            iif(:pb7_u5_err IS NULL, "207Pb/235UError" IS NULL, "207Pb/235UError" = :pb7_u5_err) AND
                            iif(:pb6_u8 IS NULL, "206Pb/238U" IS NULL, "206Pb/238U" = :pb6_u8) AND
                            iif(:pb6_u8_err IS NULL, "206Pb/238UError" IS NULL, "206Pb/238UError" = :pb6_u8_err) AND
                            iif(:ratio_error_format_id IS NULL, "RatioErrorFormatID" IS NULL, "RatioErrorFormatID" = :ratio_error_format_id) AND
                            iif(:rho IS NULL, "ErrorCorr/Rho" IS NULL, "ErrorCorr/Rho" = :rho) AND
                            iif(:pb7_pb6_age IS NULL, "207Pb/206PbAge" IS NULL, "207Pb/206PbAge" = :pb7_pb6_age) AND
                            iif(:pb7_pb6_age_err IS NULL, "207Pb/206PbAgeError" IS NULL, "207Pb/206PbAgeError" = :pb7_pb6_age_err) AND
                            iif(:pb7_u5_age IS NULL, "207Pb/235UAge" IS NULL, "207Pb/235UAge" = :pb7_u5_age) AND
                            iif(:pb7_u5_age_err IS NULL, "207Pb/235UAgeError" IS NULL, "207Pb/235UAgeError" = :pb7_u5_age_err) AND
                            iif(:pb6_u8_age IS NULL, "206Pb/238UAge" IS NULL, "206Pb/238UAge" = :pb6_u8_age) AND
                            iif(:pb6_u8_age_err IS NULL, "206Pb/238UAgeError" IS NULL, "206Pb/238UAgeError" = :pb6_u8_age_err) AND
                            iif(:best_age IS NULL, "BestAge" IS NULL, "BestAge" = :best_age) AND
                            iif(:best_age_err IS NULL, "BestAgeError" IS NULL, "BestAgeError" = :best_age_err) AND
                            iif(:age_error_format_id IS NULL, "AgeErrorFormatID" IS NULL, "AgeErrorFormatID" = :age_error_format_id) AND
                            iif(:concordance IS NULL, "Concordance" IS NULL, "Concordance" = :concordance) AND
                            iif(:concordance_format_id IS NULL, "ConcordanceFormatID" IS NULL, "ConcordanceFormatID" = :concordance_format_id) AND
                            iif(:spot_size IS NULL, "SpotSize" IS NULL, "SpotSize" = :spot_size) AND
                            iif(:spot_size_unit_id IS NULL, "SpotSizeUnitID" IS NULL, "SpotSizeUnitID" = :spot_size_unit_id)''',
                           {'spot_id': spot_id, 'reference_id': reference_id, 'lab_facility_id': lab_facility_id,
                            'instrument_id': instrument_id, 'method_id': method_id, 'pb7_pb6': pb7_pb6,
                            'pb7_pb6_err': pb7_pb6_err,
                            'pb7_u5': pb7_u5, 'pb7_u5_err': pb7_u5_err, 'pb6_u8': pb6_u8, 'pb6_u8_err': pb6_u8_err,
                            'ratio_error_format_id': ratio_error_format_id, 'rho': rho, 'pb7_pb6_age': pb7_pb6_age,
                            'pb7_pb6_age_err': pb7_pb6_age_err, 'pb7_u5_age': pb7_u5_age,
                            'pb7_u5_age_err': pb7_u5_age_err,
                            'pb6_u8_age': pb6_u8_age, 'pb6_u8_age_err': pb6_u8_age_err, 'best_age': best_age,
                            'best_age_err': best_age_err, 'age_error_format_id': age_error_format_id,
                            'concordance': concordance,
                            'concordance_format_id': concordance_format_id, 'spot_size': spot_size,
                            'spot_size_unit_id': spot_size_unit_id})
            analysis_id = cursor.fetchone()
            if analysis_id is None:
                # if not, add it to the database
                print(f'Adding {spot_name} analysis to the database')
                cursor.execute(f'''INSERT INTO UPbAnalyses (SpotID, "ReferenceID", LabFacilityID, InstrumentID, 
                            UPbAnalysisMethodID, "207Pb/206Pb", "207Pb/206PbError", "207Pb/235U", "207Pb/235UError", 
                            "206Pb/238U", "206Pb/238UError", "RatioErrorFormatID", "ErrorCorr/Rho", "207Pb/206PbAge", 
                            "207Pb/206PbAgeError", "207Pb/235UAge", "207Pb/235UAgeError", "206Pb/238UAge", 
                            "206Pb/238UAgeError", "BestAge", "BestAgeError", "AgeErrorFormatID", AgeUnitID, 
                            "Concordance", "ConcordanceFormatID", SpotSize, SpotSizeUnitID) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (spot_id, reference_id, lab_facility_id, instrument_id, method_id, pb7_pb6,
                            pb7_pb6_err, pb7_u5, pb7_u5_err, pb6_u8, pb6_u8_err, ratio_error_format_id, rho,
                            pb7_pb6_age, pb7_pb6_age_err, pb7_u5_age, pb7_u5_age_err, pb6_u8_age, pb6_u8_age_err,
                            best_age, best_age_err, age_error_format_id, age_unit_id, concordance,
                            concordance_format_id, spot_size, spot_size_unit_id))
                conn.commit()
                cursor.execute(f'''SELECT UPbAnalysisID FROM UPbAnalyses WHERE 
                            iif(:spot_id IS NULL, SpotID IS NULL, SpotID = :spot_id) AND 
                            iif(:reference_id IS NULL, "ReferenceID" IS NULL, "ReferenceID" = :reference_id) AND
                            iif(:lab_facility_id IS NULL, LabFacilityID IS NULL, LabFacilityID = :lab_facility_id) AND
                            iif(:instrument_id IS NULL, InstrumentID IS NULL, InstrumentID = :instrument_id) AND
                            iif(:method_id IS NULL, UPbAnalysisMethodID IS NULL, UPbAnalysisMethodID = :method_id) AND
                            iif(:pb7_pb6 IS NULL, "207Pb/206Pb" IS NULL, "207Pb/206Pb" = :pb7_pb6) AND
                            iif(:pb7_pb6_err IS NULL, "207Pb/206PbError" IS NULL, "207Pb/206PbError" = :pb7_pb6_err) AND
                            iif(:pb7_u5 IS NULL, "207Pb/235U" IS NULL, "207Pb/235U" = :pb7_u5) AND
                            iif(:pb7_u5_err IS NULL, "207Pb/235UError" IS NULL, "207Pb/235UError" = :pb7_u5_err) AND
                            iif(:pb6_u8 IS NULL, "206Pb/238U" IS NULL, "206Pb/238U" = :pb6_u8) AND
                            iif(:pb6_u8_err IS NULL, "206Pb/238UError" IS NULL, "206Pb/238UError" = :pb6_u8_err) AND
                            iif(:ratio_error_format_id IS NULL, "RatioErrorFormatID" IS NULL, "RatioErrorFormatID" = :ratio_error_format_id) AND
                            iif(:rho IS NULL, "ErrorCorr/Rho" IS NULL, "ErrorCorr/Rho" = :rho) AND
                            iif(:pb7_pb6_age IS NULL, "207Pb/206PbAge" IS NULL, "207Pb/206PbAge" = :pb7_pb6_age) AND
                            iif(:pb7_pb6_age_err IS NULL, "207Pb/206PbAgeError" IS NULL, "207Pb/206PbAgeError" = :pb7_pb6_age_err) AND
                            iif(:pb7_u5_age IS NULL, "207Pb/235UAge" IS NULL, "207Pb/235UAge" = :pb7_u5_age) AND
                            iif(:pb7_u5_age_err IS NULL, "207Pb/235UAgeError" IS NULL, "207Pb/235UAgeError" = :pb7_u5_age_err) AND
                            iif(:pb6_u8_age IS NULL, "206Pb/238UAge" IS NULL, "206Pb/238UAge" = :pb6_u8_age) AND
                            iif(:pb6_u8_age_err IS NULL, "206Pb/238UAgeError" IS NULL, "206Pb/238UAgeError" = :pb6_u8_age_err) AND
                            iif(:best_age IS NULL, "BestAge" IS NULL, "BestAge" = :best_age) AND
                            iif(:best_age_err IS NULL, "BestAgeError" IS NULL, "BestAgeError" = :best_age_err) AND
                            iif(:age_error_format_id IS NULL, "AgeErrorFormatID" IS NULL, "AgeErrorFormatID" = :age_error_format_id) AND
                            iif(:concordance IS NULL, "Concordance" IS NULL, "Concordance" = :concordance) AND
                            iif(:concordance_format_id IS NULL, "ConcordanceFormatID" IS NULL, "ConcordanceFormatID" = :concordance_format_id) AND
                            iif(:spot_size IS NULL, "SpotSize" IS NULL, "SpotSize" = :spot_size) AND
                            iif(:spot_size_unit_id IS NULL, "SpotSizeUnitID" IS NULL, "SpotSizeUnitID" = :spot_size_unit_id)''',
                           {'spot_id': spot_id, 'reference_id': reference_id, 'lab_facility_id': lab_facility_id,
                             'instrument_id': instrument_id, 'method_id': method_id, 'pb7_pb6': pb7_pb6, 'pb7_pb6_err': pb7_pb6_err,
                             'pb7_u5': pb7_u5, 'pb7_u5_err': pb7_u5_err, 'pb6_u8': pb6_u8, 'pb6_u8_err': pb6_u8_err,
                             'ratio_error_format_id': ratio_error_format_id, 'rho': rho, 'pb7_pb6_age': pb7_pb6_age,
                             'pb7_pb6_age_err': pb7_pb6_age_err, 'pb7_u5_age': pb7_u5_age, 'pb7_u5_age_err': pb7_u5_age_err,
                             'pb6_u8_age': pb6_u8_age, 'pb6_u8_age_err': pb6_u8_age_err, 'best_age': best_age,
                             'best_age_err': best_age_err, 'age_error_format_id': age_error_format_id, 'concordance': concordance,
                             'concordance_format_id': concordance_format_id, 'spot_size': spot_size, 'spot_size_unit_id': spot_size_unit_id})
                analysis_id = cursor.fetchone()
                if analysis_id is None:
                    print(f"Failed to add analysis {spot_name} to the database")
                    return
            analysis_id = analysis_id[0]
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return

if __name__ == "__main__":
    Puetz_importer()
