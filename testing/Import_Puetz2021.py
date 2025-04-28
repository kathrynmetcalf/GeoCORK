import pandas as pd
import numpy as np
import openpyxl
import sqlite3
import re

def import_rock_type(cursor, name, parent_id, parent_row):
    """
    Import a rock type into the database.
    :param name: The name of the rock type
    :param parent_id: The ID of the parent rock type
    :param parent_row: The row of the parent rock type
    """
    try:
        cursor.execute(f'INSERT INTO RockTypes (RockTypeName, ParentRockTypeID, RockTypeParentRow) VALUES (?, ?, ?)',
                       (name, parent_id, parent_row))
        conn = cursor.connection()
        conn.commit()
        cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ?', (name,))
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
    Method to import the data from Puetz et al. (2021) and convert it into a format
    that can be used by the model.
    """
    full_data = '/Users/kametcalf/Zotero/storage/GILLMCCW/Supplement0_DB0.xlsx'
    db = '/Users/kametcalf/Documents/Research/GeoChron_non_git/Puetz_et_al_2021.db'
    igneous_dict = {}
    reference_dict = {}
    ref_sample_dict = {}
    sample_analysis_tags_dict = {}

    # --------------------
    # Import the references from Puetz et al. (2021) into the database file.
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
    # Import the regions from Puetz et al. (2021) into the database file.
    # --------------------
    sheet_name = 'Countries'
    try:
        region_df = pd.read_excel(full_data, header=None, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        print(f"Failed to parse sheet with pandas:\n{e}")
        return
    while not region_df.empty and region_df.iloc[0].isna().all():
        region_df = region_df.iloc[1:].reset_index(drop=True)

    rows, cols = region_df.shape

    # add each country to the database
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for i in range(1, rows):
            # check if continent is in the database
            region_name = region_df.iloc[i, 2]
            if pd.isna(region_name):
                continue
            cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ?', (region_df.iloc[i, 2],))
            continent_id = cursor.fetchone()
            if continent_id is None:
                # if not, add it to the database
                cursor.execute(f'INSERT INTO Regions (RegionName, RegionParentRow) VALUES (?, ?)',
                               (region_df.iloc[i, 2], i-1))
                conn.commit()
                cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ?', (region_df.iloc[i, 2],))
                continent_id = cursor.fetchone()
                if continent_id is None:
                    print(f"Failed to add region {region_df.iloc[i, 2]} to the database")
                    return
            continent_id = continent_id[0]
            # check if geographic region is in the database
            if pd.isna(region_df.iloc[i, 1]):
                continue
            cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ?', (region_df.iloc[i, 1],))
            region_id = cursor.fetchone()
            if region_id is None:
                # if not, add it to the database
                # get the largest value for RegionParentRow of the continent_id
                cursor.execute(f'SELECT MAX(RegionParentRow) FROM Regions WHERE ParentRegionID = ?',
                               (continent_id,))
                parent_row = cursor.fetchone()
                if parent_row[0] is None:
                    parent_row = 0
                else:
                    parent_row = parent_row[0] + 1
                cursor.execute(f'INSERT INTO Regions (RegionName, ParentRegionID, RegionParentRow) VALUES (?,?,?)', 
                               (region_df.iloc[i, 1], continent_id, parent_row))
                conn.commit()
                cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ?', (region_df.iloc[i, 1],))
                region_id = cursor.fetchone()
                if region_id is None:
                    print(f"Failed to add region {region_df.iloc[i, 1]} to the database")
                    return
            region_id = region_id[0]
            # check if country/state is in the database
            if pd.isna(region_df.iloc[i, 0]):
                continue
            cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ?', (region_df.iloc[i, 0],))
            country_id = cursor.fetchone()
            if country_id is None:
                # if not, add it to the database
                # get the largest value for RegionParentRow of the region_id
                cursor.execute(f'SELECT MAX(RegionParentRow) FROM Regions WHERE ParentRegionID = ?', (region_id,))
                parent_row = cursor.fetchone()
                if parent_row [0] is None:
                    parent_row = 0
                else:
                    parent_row = parent_row[0] + 1
                cursor.execute(f'INSERT INTO Regions (RegionName, ParentRegionID, RegionParentRow) VALUES (?,?,?)',
                               (region_df.iloc[i, 0], region_id, parent_row))
                conn.commit()
                cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ?', (region_df.iloc[i, 0],))
                country_id = cursor.fetchone()
                if country_id is None:
                    print(f"Failed to add region {region_df.iloc[i, 0]} to the database")
                    return
            country_id = country_id[0]
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    sheet_name = 'Samples'
    try:
        sample_df = pd.read_excel(full_data, header=None, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        print(f"Failed to parse sheet with pandas:\n{e}")
        return
    while not sample_df.empty and sample_df.iloc[0].isna().all():
        sample_df = sample_df.iloc[1:].reset_index(drop=True)
    rows, cols = sample_df.shape

    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for i in range(1, rows):
            # check if sample is in the database
            if pd.isna(sample_df.iloc[i, 10]):
                continue
            print(f'importing {sample_df.iloc[i, 10]}')
            cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ?', (sample_df.iloc[i, 10],))
            region_id = cursor.fetchone()
            if region_id is None:
                # if not, add it to the database
                # get the parent region id and parent row
                cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ?', (sample_df.iloc[i, 5],))
                parent_region_id = cursor.fetchone()
                if parent_region_id is None:
                    print(f"Could not find region {sample_df.iloc[i, 5]} in the database")
                    return
                parent_region_id = parent_region_id[0]
                cursor.execute(f'SELECT MAX(RegionParentRow) FROM Regions WHERE ParentRegionID = ?', (parent_region_id,))
                parent_row = cursor.fetchone()
                if parent_row [0] is None:
                    parent_row = 0
                else:
                    parent_row = parent_row[0] + 1
                cursor.execute(f'INSERT INTO Regions (RegionName, ParentRegionID, RegionParentRow) VALUES (?,?,?)',
                                  (sample_df.iloc[i, 10], parent_region_id, parent_row))
                conn.commit()
                cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ?', (sample_df.iloc[i, 10],))
                region_id = cursor.fetchone()
                if region_id is None:
                    print(f"Failed to add region {sample_df.iloc[i, 10]} to the database")
                    return
            region_id = region_id[0]
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        print(f"Failed to add region {sample_df.iloc[i, 10]} to the database")
        return

    # --------------------
    # Import the rock types from Puetz et al. (2021) into the database file.
    # --------------------
    sheet_name = 'Rock_Types'
    try:
        rock_df = pd.read_excel(full_data, header=None, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        print(f"Failed to parse sheet with pandas:\n{e}")
        return
    while not rock_df.empty and rock_df.iloc[0].isna().all():
        rock_df = rock_df.iloc[1:].reset_index(drop=True)

    # get only the first column and import those rows into the database
    df1 = rock_df.iloc[:, 0]
    df1 = df1.dropna()
    df1 = df1.reset_index(drop=True)

    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for i1 in range(1, len(df1)):
            # check if rock type is in the database
            if pd.isna(df1[i1]):
                continue
            print(f'importing {df1[i1]}')
            cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ?', (df1.iloc[i1],))
            rock_type_id1 = cursor.fetchone()
            if rock_type_id1 is None:
                # if not, add it to the database
                rock_type_id1 = import_rock_type(cursor, df1.iloc[i1], '', '')
                if rock_type_id1 is None:
                    print(f"Failed to add rock type {df1.iloc[i1]} to the database")
                    return
            rock_type_id1 = rock_type_id1[0]
            df2 = rock_df.iloc[:, 3+i1]
            df2 = df2.dropna()
            df2 = df2.reset_index(drop=True)
            for i2 in range(1, len(df2)):
                if pd.isna(df2[i2]):
                    continue
                # check if rock type is in the database
                cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ?', (df2.iloc[i2],))
                rock_type_id2 = cursor.fetchone()
                if rock_type_id2 is None:
                    # if not, add it to the database
                    rock_type_id2 = import_rock_type(cursor, df2.iloc[i2], rock_type_id1, i2)
                    if rock_type_id2 is None:
                        print(f"Failed to add rock type {df2.iloc[i2]} to the database")
                        return
                rock_type_id2 = rock_type_id2[0]
                df3 = rock_df.iloc[:, 8+i2+(2*i1)]
                df3 = df3.dropna()
                df3 = df3.reset_index(drop=True)
                mf_names = ['ultramafic', 'mafic', 'felsic']
                for mf in mf_names:
                    # check if rock type is in the database
                    cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ?', (mf,))
                    rock_type_idmf = cursor.fetchone()
                    if rock_type_idmf is None:
                        # if not, add it to the database
                        rock_type_idmf = import_rock_type(cursor, mf, rock_type_id2, mf_names.index(mf))
                        if rock_type_idmf is None:
                            print(f"Failed to add rock type {mf} to the database")
                            return
                    rock_type_idmf = rock_type_idmf[0]
                for i3 in range(1, len(df3)):
                    if pd.isna(df3.iloc[i3]):
                        continue
                    # check if rock type is in the database
                    cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ?', (df3.iloc[i3],))
                    rock_type_id3 = cursor.fetchone()
                    if rock_type_id3 is None:
                        # if not, add it to the database
                        rock_type_id3 = import_rock_type(cursor, df3.iloc[i3]+len(mf_names), rock_type_id2, i3)
                        if rock_type_id3 is None:
                            print(f"Failed to add rock type {df3.iloc[i3]} to the database")
                            return
                    rock_type_id3 = rock_type_id3[0]
                    if i1 == 0:
                        # if the rock type is igneous, add composition classification
                        mf_name = rock_df.iloc[i3, 4 + i1]
                        if mf_name == 'N.A.':
                            rock_type_idmf = None
                        else:
                            cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ?', (mf_name,))
                            rock_type_idmf = cursor.fetchone()
                            if rock_type_idmf is None:
                                # if not, add it to the database
                                rock_type_idmf = import_rock_type(cursor, mf_name, rock_type_id3, 0)
                                if rock_type_idmf is None:
                                    print(f"Failed to add rock type {mf_name} to the database")
                                    return
                            rock_type_idmf = rock_type_idmf[0]
                        igneous_dict[rock_type_id3] = rock_type_idmf
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        print(f"Failed to add rock type {df1.iloc[i1]} to the database")
        return

    # --------------------
    # Import the analysis methods from Puetz et al. (2021) into the database file.
    # --------------------
    sheet_name = 'Spectrometers'
    try:
        spectrometer_df = pd.read_excel(full_data, header=None, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        print(f"Failed to parse sheet with pandas:\n{e}")
        return
    while not spectrometer_df.empty and spectrometer_df.iloc[0].isna().all():
        spectrometer_df = spectrometer_df.iloc[1:].reset_index(drop=True)

    # get only the first column and import those rows into the database
    df1 = spectrometer_df.iloc[:, 0]
    df1 = df1.dropna()
    df1 = df1.reset_index(drop=True)
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for i1 in range(1, len(df1)+1):
            if pd.isna(df1[i1]):
                continue
            # check if method is in the database
            cursor.execute(f'SELECT UPbAnalysisMethodID FROM UPbAnalysisMethods WHERE UPbAnalysisMethodName = ?',
                           (df1.iloc[i1],))
            method_id1 = cursor.fetchone()
            if method_id1 is None:
                # if not, add it to the database
                cursor.execute(f'INSERT INTO UPbAnalysisMethods (UPbAnalysisMethodName) VALUES (?)',
                               (df1.iloc[i1],))
                conn.commit()
                cursor.execute(f'SELECT UPbAnalysisMethodID FROM UPbAnalysisMethods WHERE UPbAnalysisMethodName = ?',
                               (df1.iloc[i1],))
                method_id1 = cursor.fetchone()
                if method_id1 is None:
                    print(f"Failed to add method {df1.iloc[i1]} to the database")
                    return
            method_id1 = method_id1[0]
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    # --------------------
    # Import the lab facilities from Puetz et al. (2021) into the database file.
    # --------------------
    df_shrimp_sims = spectrometer_df.iloc[:, 3:4]
    df_shrimp_sims = df_shrimp_sims.dropna()
    df_shrimp_sims = df_shrimp_sims.reset_index(drop=True)
    row, col = df_shrimp_sims.shape
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for i in range(1, row):
            facility_name = df_shrimp_sims.iloc[i, 0]
            facility_description = df_shrimp_sims.iloc[i, 1]
            if pd.isna(facility_name):
                continue
            # check if facility is in the database
            cursor.execute(f'SELECT LabFacilityID FROM LabFacilities WHERE LabFacilityName = ?', (facility_name,))
            facility_id = cursor.fetchone()
            if facility_id is None:
                # if not, add it to the database
                cursor.execute(f'INSERT INTO LabFacilities (LabFacilityName, LabFacilityDescription) VALUES (?, ?)',
                               (facility_name, facility_description))
                conn.commit()
                cursor.execute(f'SELECT LabFacilityID FROM LabFacilities WHERE LabFacilityName = ?', (facility_name,))
                facility_id = cursor.fetchone()
                if facility_id is None:
                    print(f"Failed to add facility {facility_name} to the database")
                    return
            facility_id = facility_id[0]
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return
    df_laicpms = spectrometer_df.iloc[:, 10:11]
    df_laicpms = df_laicpms.dropna()
    df_laicpms = df_laicpms.reset_index(drop=True)
    row, col = df_laicpms.shape
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for i in range(1, row):
            facility_name = df_laicpms.iloc[i, 0]
            facility_description = df_laicpms.iloc[i, 1]
            if pd.isna(facility_name):
                continue
            # check if facility is in the database
            cursor.execute(f'SELECT LabFacilityID FROM LabFacilities WHERE LabFacilityName = ?', (facility_name,))
            facility_id = cursor.fetchone()
            if facility_id is None:
                # if not, add it to the database
                cursor.execute(f'INSERT INTO LabFacilities (LabFacilityName, LabFacilityDescription) VALUES (?, ?)',
                               (facility_name, facility_description))
                conn.commit()
                cursor.execute(f'SELECT LabFacilityID FROM LabFacilities WHERE LabFacilityName = ?', (facility_name,))
                facility_id = cursor.fetchone()
                if facility_id is None:
                    print(f"Failed to add facility {facility_name} to the database")
                    return
            facility_id = facility_id[0]
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    # --------------------
    # Import the instruments from Puetz et al. (2021) into the database file.
    # --------------------
    df_shrimp_sims = spectrometer_df.iloc[:, 5]
    df_shrimp_sims = df_shrimp_sims.dropna()
    df_shrimp_sims = df_shrimp_sims.reset_index(drop=True)
    row, col = df_shrimp_sims.shape
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for i in range(1, row):
            instrument_name = df_shrimp_sims.iloc[i, 0]
            if pd.isna(instrument_name):
                continue
            # check if instrument is in the database
            cursor.execute(f'SELECT InstrumentID FROM Instruments WHERE InstrumentName = ?', (instrument_name,))
            instrument_id = cursor.fetchone()
            if instrument_id is None:
                # if not, add it to the database
                cursor.execute(f'INSERT INTO Instruments (InstrumentName) VALUES (?)', instrument_name)
                conn.commit()
                cursor.execute(f'SELECT InstrumentID FROM Instruments WHERE InstrumentName = ?', (instrument_name,))
                instrument_id = cursor.fetchone()
                if instrument_id is None:
                    print(f"Failed to add instrument {instrument_name} to the database")
                    return
            instrument_id = instrument_id[0]
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    df_laicpms = spectrometer_df.iloc[:, 12:13]
    df_laicpms = df_laicpms.dropna()
    df_laicpms = df_laicpms.reset_index(drop=True)
    row, col = df_laicpms.shape
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for i in range(1, row):
            instrument_name = df_laicpms.iloc[i, 0]
            instrument_description = df_laicpms.iloc[i, 1]
            if pd.isna(instrument_name):
                continue
            # check if instrument is in the database
            cursor.execute(f'SELECT InstrumentID FROM Instruments WHERE InstrumentName = ?', (instrument_name,))
            instrument_id = cursor.fetchone()
            if instrument_id is None:
                # if not, add it to the database
                cursor.execute(f'INSERT INTO Instruments (InstrumentName, InstrumentDescription) VALUES (?, ?)',
                               (instrument_name, instrument_description))
                conn.commit()
                cursor.execute(f'SELECT InstrumentID FROM Instruments WHERE InstrumentName = ?', (instrument_name,))
                instrument_id = cursor.fetchone()
                if instrument_id is None:
                    print(f"Failed to add instrument {instrument_name} to the database")
                    return
            instrument_id = instrument_id[0]
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    df_laser = spectrometer_df.iloc[:, 14:15]
    df_laser = df_laser.dropna()
    df_laser = df_laser.reset_index(drop=True)
    row, col = df_laser.shape
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for i in range(1, row):
            instrument_name = df_laser.iloc[i, 0]
            instrument_description = df_laser.iloc[i, 1]
            if pd.isna(instrument_name):
                continue
            # check if instrument is in the database
            cursor.execute(f'SELECT InstrumentID FROM Instruments WHERE InstrumentName = ?', (instrument_name,))
            instrument_id = cursor.fetchone()
            if instrument_id is None:
                # if not, add it to the database
                cursor.execute(f'INSERT INTO Instruments (InstrumentName, InstrumentDescription) VALUES (?, ?)',
                               (instrument_name, instrument_description))
                conn.commit()
                cursor.execute(f'SELECT InstrumentID FROM Instruments WHERE InstrumentName = ?', (instrument_name,))
                instrument_id = cursor.fetchone()
                if instrument_id is None:
                    print(f"Failed to add instrument {instrument_name} to the database")
                    return
            instrument_id = instrument_id[0]
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    # --------------------
    # Import the units from Puetz et al. (2021) into the database file.
    # --------------------
    df_units = sample_df.iloc[:, 8:9]
    df_units = df_units.dropna()
    df_units = df_units.reset_index(drop=True)
    row, col = df_units.shape
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for i in range(1, row):
            unit_name1 = df_units.iloc[i, 0]
            if pd.isna(unit_name1):
                continue
            # check if unit is in the database
            cursor.execute(f'SELECT UnitID FROM Units WHERE UnitName = ?', (unit_name1,))
            unit_id1 = cursor.fetchone()
            if unit_id1 is None:
                # if not, add it to the database
                cursor.execute(f'INSERT INTO Units (UnitName) VALUES (?)', (unit_name1,))
                conn.commit()
                cursor.execute(f'SELECT UnitID FROM Units WHERE UnitName = ?', (unit_name1,))
                unit_id1 = cursor.fetchone()
                if unit_id1 is None:
                    print(f"Failed to add unit {unit_name1} to the database")
                    return
            unit_id1 = unit_id1[0]
            # Find the last parent row
            cursor.execute(f'SELECT MAX(UnitParentRow) FROM Units WHERE ParentUnitID = ?', (unit_id1,))
            parent_row = cursor.fetchone()
            if parent_row [0] is None:
                parent_row = 0
            else:
                parent_row = parent_row[0] + 1
            unit_name2 = df_units.iloc[i, 1]
            if pd.isna(unit_name2):
                continue
            # check if unit is in the database
            cursor.execute(f'SELECT UnitID FROM Units WHERE UnitName = ?', (unit_name2,))
            unit_id2 = cursor.fetchone()
            if unit_id2 is None:
                # if not, add it to the database
                cursor.execute(f'INSERT INTO Units (UnitName, ParentUnitID, UnitParentRow) VALUES (?, ?, ?)',
                               (unit_name2, unit_id1, parent_row))
                conn.commit()
                cursor.execute(f'SELECT UnitID FROM Units WHERE UnitName = ?', (unit_name2,))
                unit_id2 = cursor.fetchone()
                if unit_id2 is None:
                    print(f"Failed to add unit {unit_name2} to the database")
                    return
            unit_id2 = unit_id2[0]
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

    # --------------------
    # Import the spot compositions from Puetz et al. (2021) into the database file.
    # --------------------
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        spot_composition_name = 'zircon'
        cursor.execute(f'SELECT SpotCompositionID FROM SpotCompositions WHERE SpotCompositionName = ?', (spot_composition_name,))
        spot_composition_id = cursor.fetchone()
        if spot_composition_id is None:
            # if not, add it to the database
            cursor.execute(f'INSERT INTO SpotCompositions (SpotCompositionName) VALUES (?)', spot_composition_name)
            conn.commit()
            cursor.execute(f'SELECT SpotCompositionID FROM SpotCompositions WHERE SpotCompositionName = ?', (spot_composition_name,))
            spot_composition_id = cursor.fetchone()
            if spot_composition_id is None:
                print(f"Failed to add mineral {spot_composition_name} to the database")
                return
        spot_composition_id = spot_composition_id[0]
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return


    # --------------------
    # Import the samples from Puetz et al. (2021) into the database file.
    # --------------------
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

            # add the sample name and reference key to the dictionary
            sample_name = sample_df.iloc[i, 4]
            if pd.isna(sample_name):
                continue
            ref_sample_key = sample_df.iloc[i, 3]
            ref_sample_dict[ref_sample_key] = sample_name

            # Regions
            region_ids = []
            columns = [5, 6, 7, 10]
            for column in columns:
                region_name = sample_df.iloc[i, column]
                cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ?', (region_name,))
                region_id = cursor.fetchone()
                if region_id is None:
                    print(f"Failed to find region {region_name} in the database")
                    return
                region_id = region_id[0]
                region_ids.append(region_id)

            # Units
            unit_ids = []
            columns = [8, 9]
            for column in columns:
                unit_name = sample_df.iloc[i, column]
                cursor.execute(f'SELECT UnitID FROM Units WHERE UnitName = ?', (unit_name,))
                unit_id = cursor.fetchone()
                if unit_id is None:
                    print(f"Failed to find unit {unit_name} in the database")
                    return
                unit_id = unit_id[0]
                unit_ids.append(unit_id)

            # GPS location
            gps_lat = sample_df.iloc[i, 11]
            gps_lon = sample_df.iloc[i, 12]
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
            sample_age_max = sample_df.iloc[i, 13]
            sample_age_est = sample_df.iloc[i, 14]
            sample_age_min = sample_df.iloc[i, 15]
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

            # Rock types
            rock_type_ids = []
            columns = [21, 22, 23]
            for column in columns:
                rock_type_name = sample_df.iloc[i, column]
                if pd.isna(rock_type_name):
                    pass
                else:
                    cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ?', (rock_type_name,))
                    rock_type_id = cursor.fetchone()
                    if rock_type_id is None:
                        print(f"Failed to find rock type {rock_type_name} in the database")
                        return
                    rock_type_id = rock_type_id[0]
                    rock_type_ids.append(rock_type_id)

            # Sample
            cursor.execute(f'SELECT SampleID FROM Samples WHERE SampleName = ?', (sample_name,))
            sample_id = cursor.fetchone()
            if sample_id is None:
                # if not, add it to the database
                cursor.execute(f'INSERT INTO Samples (SampleName, SampleGPSLocationID) Values (?, ?)',
                               (sample_name, gps_id))
                conn.commit()
                cursor.execute(f'SELECT SampleID FROM Samples WHERE SampleName = ?', (sample_name,))
                sample_id = cursor.fetchone()
                if sample_id is None:
                    print(f"Failed to add sample {sample_name} to the database")
                    return
            sample_id = sample_id[0]

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

            # Method
            method_name = sample_df.iloc[i, 17]
            if pd.isna(method_name):
                method_id = None
            else:
                cursor.execute(f'SELECT UPbAnalysisMethodID FROM UPbAnalysisMethods WHERE UPbAnalysisMethodName = ?',
                               (method_name,))
                method_id = cursor.fetchone()
                if method_id is None:
                    print(f"Failed to find method {method_name} in the database")
                    return
                method_id = method_id[0]

            # Lab facility
            lab_facility_name = sample_df.iloc[i, 18]
            if pd.isna(lab_facility_name):
                lab_facility_id = None
            else:
                cursor.execute(f'SELECT LabFacilityID FROM LabFacilities WHERE LabFacilityName = ?', (lab_facility_name,))
                lab_facility_id = cursor.fetchone()
                if lab_facility_id is None:
                    print(f"Failed to find lab facility {lab_facility_name} in the database")
                    return
                lab_facility_id = lab_facility_id[0]

            # Instrument
            instrument_name = sample_df.iloc[i, 20]
            if pd.isna(instrument_name):
                instrument_id = None
            else:
                cursor.execute(f'SELECT InstrumentID FROM Instruments WHERE InstrumentName = ?', (instrument_name,))
                instrument_id = cursor.fetchone()
                if instrument_id is None:
                    print(f"Failed to find instrument {instrument_name} in the database")
                    return
                instrument_id = instrument_id[0]

            sample_analysis_tags_dict[sample_id] = [method_id, lab_facility_id, instrument_id]

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    # --------------------
    # Import the spot compositions from Puetz et al. (2021) into the database file.
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

    for i in range(1, rows):
        # get analysis information

        # reference
        ref_sample_key = upb_df.iloc[i, 0]
        if pd.isna(ref_sample_key):
            continue
        pattern = r'(?<=\b[A-Z]0*)[^-]+(?=-)'
        match = re.search(pattern, ref_sample_key)
        if not match:
            print(f"Failed to find reference in {ref_sample_key}")
            return
        ref_id = match.group(0)
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
            sample_name = sample_name[0]
            cursor.execute(f'SELECT AliquotName WHERE SampleID = ?', (sample_id,))
            aliquot_names = cursor.fetchall()
            aliquot_id = None
            if aliquot_names is None or sample_name not in aliquot_names:
                # if not, add it to the database
                aliquot_name = sample_name
                cursor.execute(f'INSERT INTO Aliquots (AliquotName, SampleID) VALUES (?, ?)',
                               (aliquot_name, sample_id))
                conn.commit()
                cursor.execute(f'SELECT AliquotID FROM Aliquots WHERE AliquotName = ?', (aliquot_name,))
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
            cursor.execute(f'SELECT SpotID FROM Spots WHERE SpotName = ?', (spot_name,))
            spot_id = cursor.fetchone()
            if spot_id is None:
                # if not, add it to the database
                cursor.execute(f'INSERT INTO Spots (SpotName, AliquotID) VALUES (?, ?)',
                               (spot_name, aliquot_id))
                conn.commit()
                cursor.execute(f'SELECT SpotID FROM Spots WHERE SpotName = ?', (spot_name,))
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
                cursor.execute(f'SELECT SpotContextID FROM SpotContexts WHERE SpotContextName = ?', (spot_context,))
                spot_context_id = cursor.fetchone()
                if spot_context_id is None:
                    # if not, add it to the database
                    cursor.execute(f'INSERT INTO SpotContexts (SpotContextName) VALUES (?)', spot_context)
                    conn.commit()
                    cursor.execute(f'SELECT SpotContextID FROM SpotContexts WHERE SpotContextName = ?', (spot_context,))
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

        if spot_composition_id is not None:
            try:
                conn = sqlite3.connect(db)
                cursor = conn.cursor()
                cursor.execute(f'SELECT SpotID, SpotCompositionID FROM Spots_SpotCompositions WHERE SpotID = ? AND SpotCompositionID = ?',
                                 (spot_id, spot_composition_id))
                result = cursor.fetchone()
                if result is None:
                    # if not, add it to the database
                    cursor.execute(f'INSERT INTO Spots_SpotCompositions (SpotID, SpotCompositionID) VALUES (?, ?)',
                                   (spot_id, spot_composition_id))
                    conn.commit()
                    cursor.execute(f'SELECT SpotID, SpotCompositionID FROM Spots_SpotCompositions WHERE SpotID = ? AND SpotCompositionID = ?',
                                   (spot_id, spot_composition_id))
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

        # ratios
        pb6_u8 = upb_df.iloc[i, 5]
        pb6_u8_err = upb_df.iloc[i, 6]
        pb7_u5 = upb_df.iloc[i, 8]
        pb7_u5_err = upb_df.iloc[i, 9]
        pb7_pb6 = upb_df.iloc[i, 11]
        pb7_pb6_err = upb_df.iloc[i, 12]
        rho = upb_df.iloc[i, 14]

        # ages
        pb6_u8_age = upb_df.iloc[i, 16]
        pb6_u8_age_err = upb_df.iloc[i, 17]
        pb7_u5_age = upb_df.iloc[i, 18]
        pb7_u5_age_err = upb_df.iloc[i, 19]
        pb7_pb6_age = upb_df.iloc[i, 20]
        pb7_pb6_age_err = upb_df.iloc[i, 21]

        if pd.isna(pb6_u8) and pd.isna(pb6_u8_err) and pd.isna(pb7_u5) and pd.isna(pb7_u5_err) and pd.isna(pb7_pb6) and \
            pd.isna(pb7_pb6_err) and pd.isna(pb6_u8_age) and pd.isna(pb6_u8_age_err) and pd.isna(pb7_u5_age) and \
                pd.isna(pb7_u5_age_err) and pd.isna(pb7_pb6_age) and pd.isna(pb7_pb6_age_err):
            continue
        try: 
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            # check if analysis is in the database
            cursor.execute(f'''SELECT UPbAnalysisID FROM UPbAnalyses WHERE SpotID = ? AND "ReferenceID" = ? AND
                            LabFacilityID = ? AND InstrumentID = ? AND UPbAnalysisMethodID = ? AND "207Pb/206Pb" = ?
                            AND "207Pb/206PbError" = ? AND "207Pb/235U" = ? AND "207Pb/235UError" = ? AND 
                            "206Pb/238U" = ? AND "206Pb/238UError" = ? AND "RatioErrorFormatID" = ? AND "rho" = ? AND 
                            "207Pb/206PbAge" = ? AND "207Pb/206PbAgeError" = ? AND "207Pb/235UAge" = ? AND 
                            "207Pb/235UAgeError" = ? AND "206Pb/238UAge" = ? AND "206Pb/238UAgeError" = ? AND 
                            "AgeErrorFormatID" = ? AND "AgeUnitID" = ? AND "SpotSize" = ? AND "SpotSizeUnitID" = ?''',
                           (spot_id, reference_id, lab_facility_id, instrument_id, method_id, pb7_pb6, 
                            pb7_pb6_err, pb7_u5, pb7_u5_err, pb6_u8, pb6_u8_err, ratio_error_format_id, rho, 
                            pb7_pb6_age, pb7_pb6_age_err, pb7_u5_age, pb7_u5_age_err, pb6_u8_age, pb6_u8_age_err, 
                            age_error_format_id, age_unit_id, spot_size, spot_size_unit_id))
            analysis_id = cursor.fetchone()
            if analysis_id is None:
                # if not, add it to the database
                cursor.execute(f'''INSERT INTO UPbAnalyses (SpotID, "ReferenceID", LabFacilityID, InstrumentID, 
                            UPbAnalysisMethodID, "207Pb/206Pb", "207Pb/206PbError", "207Pb/235U", "207Pb/235UError", 
                            "206Pb/238U", "206Pb/238UError", "RatioErrorFormatID", "rho", "207Pb/206PbAge", 
                            "207Pb/206PbAgeError", "207Pb/235UAge", "207Pb/235UAgeError", "206Pb/238UAge", 
                            "206Pb/238UAgeError", "AgeErrorFormatID", AgeUnitID, SpotSize, SpotSizeUnitID) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (spot_id, reference_id, lab_facility_id, instrument_id, method_id, pb7_pb6,
                                pb7_pb6_err, pb7_u5, pb7_u5_err, pb6_u8, pb6_u8_err, ratio_error_format_id, rho,
                                pb7_pb6_age, pb7_pb6_age_err, pb7_u5_age, pb7_u5_age_err, pb6_u8_age, pb6_u8_age_err,
                                age_error_format_id, age_unit_id, spot_size, spot_size_unit_id))
                conn.commit()
                cursor.execute(f'''SELECT UPbAnalysisID FROM UPbAnalyses WHERE SpotID = ? AND "ReferenceID" = ? AND
                            LabFacilityID = ? AND InstrumentID = ? AND UPbAnalysisMethodID = ? AND "207Pb/206Pb" = ?
                            AND "207Pb/206PbError" = ? AND "207Pb/235U" = ? AND "207Pb/235UError" = ? AND 
                            "206Pb/238U" = ? AND "206Pb/238UError" = ? AND "RatioErrorFormatID" = ? AND "rho" = ? AND 
                            "207Pb/206PbAge" = ? AND "207Pb/206PbAgeError" = ? AND "207Pb/235UAge" = ? AND 
                            "207Pb/235UAgeError" = ? AND "206Pb/238UAge" = ? AND "206Pb/238UAgeError" = ? AND 
                            "AgeErrorFormatID" = ? AND "AgeUnitID" = ? AND "SpotSize" = ? AND "SpotSizeUnitID" = ?''',
                               (spot_id, reference_id, lab_facility_id, instrument_id, method_id, pb7_pb6,
                                pb7_pb6_err, pb7_u5, pb7_u5_err, pb6_u8, pb6_u8_err, ratio_error_format_id, rho,
                                pb7_pb6_age, pb7_pb6_age_err, pb7_u5_age, pb7_u5_age_err, pb6_u8_age, pb6_u8_age_err,
                                age_error_format_id, age_unit_id, spot_size, spot_size_unit_id))
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
