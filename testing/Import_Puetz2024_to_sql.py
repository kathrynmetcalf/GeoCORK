import pandas as pd
import numpy as np
import openpyxl
import sqlite3
import re
import time
from testing.Additional_units_Puetz2024 import additional_unit_tags_dict

def strip_strings(x):
    """
    Remove excess white space from strings. Returns the data unchanged if not a string.
    :param x: value from a DataFrame
    :return: stripped value if string, unchanged if another data type
    """
    if isinstance(x, str):
        return x.strip()
    return x

def shift_left(row):
    """
    Shift the values in a row to the left, filling empty spaces with NaN
    :param row: data frame row
    :return: shifted row
    """
    non_null = [value for value in row if pd.notnull(value)]
    shifted_row = non_null + [np.nan] * (len(row) - len(non_null))
    return pd.Series(shifted_row, index=row.index)

def edit_duplicate_sample_name(sample_df, reference_dict_df, reference_sql_df):
    """
    Edit the sample names in the sample_df to remove ambiguity for duplicate sample names. This will be used for
    linking other fields to samples, aliquots, spots, and UPb analyses.
    :param sample_df: DataFrame with sample names and Ref-Sample Key
    :param reference_dict_df: reference dictionary data frame with columns ReferenceNumber and ReferenceID
    :param reference_sql_df: reference sql data frame, the Reference table in the sql database
    """

    # Identify duplicate sample name and Ref-Sample Key pairs, case insensitive
    sample_df['lower_Sample_ID'] = sample_df['Sample_ID'].str.lower()
    sample_df['Ref Key'] = sample_df['Ref-Sample Key'].apply(lambda x: x.split('-')[0])
    counts = sample_df[['Ref Key', 'lower_Sample_ID']].value_counts()
    duplicates = counts[counts > 1]
    if duplicates.any():
        print(f'Duplicate sample names and references found: {duplicates.sum()}')
        print(duplicates.index.tolist())
        print('Please check the sample names in the sample sheet.')
        return
    counts = sample_df['lower_Sample_ID'].value_counts()
    duplicates = counts[counts > 1]
    if not duplicates.any():
        sample_df.drop(columns=['lower_Sample_ID'], inplace=True)
        sample_df.drop(columns=['Ref Key'], inplace=True)
        return sample_df
    duplicates_df = sample_df['lower_Sample_ID'].duplicated(keep=False)
    print(f'Duplicate sample names found: {duplicates.sum()}')

    def edit_name(row):
        """
        If it is a duplicate, edit the sample name based on the Ref-Sample Key column to return a sample name in the format
        sample_name: Authors_Year
        :param row: data frame row
        :return: edited, non-ambiguous sample name
        """
        ref_sample_key = row['Ref-Sample Key']
        sample_name = row['Sample_ID']
        # Split the reference number from the sample number
        if isinstance(ref_sample_key, str):
            reference_number = ref_sample_key.split('-')[0]
        else:
            print(f"Invalid reference number format for {sample_name}: {ref_sample_key}")
            return
        # Get the reference ID from the reference_dict_df
        reference_id = reference_dict_df[reference_number]
        # Get the Author and Year from the reference_sql_df
        author = reference_sql_df[reference_sql_df['ReferenceID'] == reference_id]['Authors']
        author = list(author)[0]
        year = reference_sql_df[reference_sql_df['ReferenceID'] == reference_id]['Year']
        year = int(list(year)[0])
        edited_sample_name = f'{sample_name}: {author}, {year}'
        return edited_sample_name

    # Apply the edit_name function to the sample_df
    sample_df.loc[duplicates_df, 'Sample_ID'] = sample_df.loc[duplicates_df].apply(edit_name, axis=1)
    # Refresh the lower_Sample_ID column
    sample_df['lower_Sample_ID'] = sample_df['Sample_ID'].str.lower()
    duplicates_df = sample_df['lower_Sample_ID'].duplicated(keep=False)
    # If there are still duplicates, print a message
    if duplicates_df.any():
        print(f'Warning: {duplicates_df.sum()} duplicate sample names found after editing')
        print(list(sample_df.loc[duplicates_df]['lower_Sample_ID']))
        print('Please check the sample names in the sample sheet.')
        return
    # Drop the lower_Sample_ID column
    sample_df.drop(columns=['lower_Sample_ID'], inplace=True)
    sample_df.drop(columns=['Ref Key'], inplace=True)
    return sample_df

def edit_duplicate_grain_name(upb_analysis_df):
    """
    Edit the grain names in the UPbAnalysis table to remove ambiguity for duplicate grain names. This will be used for
    linking other fields to samples, aliquots, spots, and UPb analyses.
    :param upb_analysis_df: DataFrame with UPbAnalysis data from excel sheet
    :return:
    """
    # Identify duplicate grain ame and Ref-Sample Key pairs, case insensitive
    upb_analysis_df['lower_Sample&Grain'] = upb_analysis_df['Sample&Grain'].str.lower()
    counts = upb_analysis_df['lower_Sample&Grain'].value_counts()
    duplicates = counts[counts > 1]
    if not duplicates.any():
        upb_analysis_df.drop(columns=['lower_Sample&Grain'], inplace=True)
        return upb_analysis_df
    print(f'Duplicate grain names found: {duplicates.sum()}')
    duplicates_df = upb_analysis_df['lower_Sample&Grain'].duplicated(keep=False)
    name_count = {}

    def edit_name(row):
        grain_name = row['Sample&Grain']
        # Compare case insensitive
        lower_grain_name = grain_name.lower()
        if lower_grain_name in name_count:
            name_count[lower_grain_name] += 1
        else:
            name_count[lower_grain_name] = 1
        # Display case-sensitive name
        edited_name = f"{grain_name}: {name_count[lower_grain_name]}"

        return edited_name

    # Apply the edit_name function to the upb_analysis_df
    upb_analysis_df.loc[duplicates_df, 'Sample&Grain'] = upb_analysis_df.loc[duplicates_df].apply(edit_name, axis=1)
    # Refresh the lower_Sample&Grain column
    upb_analysis_df['lower_Sample&Grain'] = upb_analysis_df['Sample&Grain'].str.lower()
    duplicates_df = upb_analysis_df['lower_Sample&Grain'].duplicated(keep=False)
    # If there are still duplicates, print a message
    if duplicates_df.any():
        print(f'Warning: {duplicates_df.sum()} duplicate grain names found after editing')
        print(list(upb_analysis_df.loc[duplicates_df]['lower_Sample&Grain']))
        print('Please check the grain names in the UPb_Data sheet.')
        return
    # Drop the lower_Sample&Grain column
    upb_analysis_df.drop(columns=['lower_Sample&Grain'], inplace=True)

    return upb_analysis_df

def edit_duplicate_recalculated_name(upb_analysis_df):
    counts = upb_analysis_df['Sample&Grain'].value_counts()
    duplicates = counts[counts > 1]
    if not duplicates.any():
        return upb_analysis_df
    print(f'Duplicate grain names found: {duplicates.sum()}')
    duplicates_df = upb_analysis_df['Sample&Grain'].duplicated(keep=False)
    name_count = {}

    def edit_name(row):
        grain_name = row['Sample&Grain']
        if grain_name in name_count:
            name_count[grain_name] += 1
        else:
            name_count[grain_name] = 1
        if grain_name in duplicates_df:
            edited_name = f"{grain_name}: recalculated{name_count[grain_name]}"
        else:
            edited_name = f"{grain_name}: recalculated"
        return edited_name

    # Apply the edit_name function to the upb_analysis_df
    upb_analysis_df.loc[duplicates_df, 'Sample&Grain'] = upb_analysis_df.loc[duplicates_df].apply(edit_name, axis=1)

    return upb_analysis_df


def Puetz_importer():
    """
    Method to import the data from Puetz et al. (2024) and convert it into a format
    that can be used by the model.
    """
    # full_data = '/Users/kametcalf/Downloads/DB1_2019_edited.xlsx'
    # full_data = '/Users/kametcalf/Downloads/DB2_2021_edited.xlsx'
    # full_data = '/Users/kametcalf/Downloads/DB3_2023_edited.xlsx'
    # db = '/Users/kametcalf/Documents/Research/GeoChron_non_git/Puetz_et_al_2024_1.db'
    # db = '/Users/kametcalf/Documents/Research/GeoChron_non_git/Puetz_et_al_2024_2.db'
    # db = '/Users/kametcalf/Documents/Research/GeoChron_non_git/Puetz_et_al_2024_3.db'
    ref_sample_dict = {}
    sample_analysis_tags_dict = {}
    data_files = ['/Users/kametcalf/Downloads/DB1_2019_edited.xlsx',
                  '/Users/kametcalf/Downloads/DB2_2021_edited.xlsx',
                  '/Users/kametcalf/Downloads/DB3_2023_edited.xlsx']
    db = '/Users/kametcalf/Documents/Research/GeoChron_non_git/Puetz_et_al_2024_all.db'

    # --------------------
    # Get the headers for the tables to import into the database
    tables = ['"References"', 'Samples', 'Aliquots', 'Spots', 'UPbAnalyses', 'UPbAnalysisMethods', 'LabFacilities',
              'Instruments', 'UPbAnalysisContexts', 'SpotContexts', 'Units', 'Regions', 'RockTypes', 'SpotCompositions',
              'SampleAges', 'GPSLocations', 'Columns', 'Samples_Regions', 'Samples_RockTypes', 'Samples_SampleAges',
              'Samples_Units', 'Spots_SpotContexts', 'UPbAnalyses_UPbAnalysisContexts']
    table_properties = {}
    print(f'Gathering headers for {len(tables)} tables')
    # get the headers for each table
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for table in tables:
            cursor.execute(f'SELECT * FROM {table}')
            columns = [column[0] for column in cursor.description]
            table_properties[table] = columns
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    # --------------------
    # Import the references from Puetz et al. (2024) into the database file.
    # --------------------
    print('Importing references')
    start_time = time.time()
    sheet_name = 'References'
    # try:
    #     reference_df = pd.read_excel(full_data, sheet_name=sheet_name, engine="openpyxl")
    # except Exception as e:
    #     print(f"Failed to parse sheet with pandas:\n{e}")
    #     return
    reference_dfs = []
    for file in data_files:
        print(f'Loading {file}')
        try:
            data_df = pd.read_excel(file, sheet_name=sheet_name, engine="openpyxl")
        except Exception as e:
            print(f"Failed to parse sheet with pandas:\n{e}")
            return
        reference_dfs.append(data_df)
        print(f'Loaded {file}')
    # Concatenate all the data frames into one
    reference_df = pd.concat(reference_dfs, ignore_index=True)
    # Drop empty rows and remove excess white space
    while not reference_df.empty and reference_df.iloc[0].isna().all():
        reference_df = reference_df.iloc[1:].reset_index(drop=True)
    reference_df = reference_df.map(strip_strings)
    print(f'Loaded References in {time.time() - start_time} seconds')

    reference_sql_df = pd.DataFrame(columns=table_properties['"References"'])
    reference_sql_df['Authors'] = reference_df['Lead_Author']
    reference_sql_df['Year'] = reference_df['Year']
    reference_sql_df['Title'] = reference_df['Title']
    reference_sql_df['Source'] = reference_df['Journal']
    reference_sql_df['DOI'] = reference_df['Web Link'].apply(lambda x: x.split('doi.org/')[1] if isinstance(x, str) and 'doi.org' in x else np.nan)
    # drop all rows without reference info, although some may still have a Ref No.
    reference_sql_df.dropna(subset=['Authors', 'Title', 'Source', 'DOI'], axis=0, how='all', inplace=True)
    # set all rows to the current time stamp for ReferenceCreated and ReferenceModified
    reference_sql_df['ReferenceCreated'] = pd.to_datetime('now')
    reference_sql_df['ReferenceModified'] = pd.to_datetime('now')
    # create a list of values from 1 to the number of rows
    reference_sql_df['ReferenceID'] = list(range(1, reference_sql_df.shape[0]+1))

    merged_reference_id_df = reference_df.merge(reference_sql_df, left_on=['Lead_Author', 'Year', 'Title', 'Journal'],
                                                right_on=['Authors', 'Year', 'Title', 'Source'], how='left', indicator=True)

    # create dictionary for reference number and reference id
    reference_dict_df = dict(zip(reference_df['Ref No.'], reference_sql_df['ReferenceID']))

    # add the reference_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        reference_sql_df.to_sql('References', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {reference_sql_df.shape[0]} references')

    # --------------------
    # Import the samples from Puetz et al. (2024) into the database file.
    # --------------------
    print('Loading sample sheet')
    start_time = time.time()
    sheet_name = 'Samples'
    sample_dfs = []
    for file in data_files:
        print(f'Loading {file}')
        try:
            data_df = pd.read_excel(file, sheet_name=sheet_name, engine="openpyxl", dtype={'Sample_ID': str})
        except Exception as e:
            print(f"Failed to parse sheet with pandas:\n{e}")
            return
        sample_dfs.append(data_df)
        print(f'Loaded {file}')
    # Concatenate all the data frames into one
    sample_df = pd.concat(sample_dfs, ignore_index=True)
    # Drop empty rows and remove excess white space
    sample_df.dropna(axis=0, how='all', inplace=True)
    sample_df.drop_duplicates(inplace=True)
    sample_df.reset_index(drop=True, inplace=True)
    sample_df = sample_df.map(strip_strings)
    print(f'Loaded Samples in {time.time() - start_time} seconds')

    gps_format_id = 1
    age_unit_id = 2

    print('Checking for sample duplicates')
    # Identify duplicate sample names
    sample_sql_df = pd.DataFrame(columns=table_properties['Samples'])

    sample_df = edit_duplicate_sample_name(sample_df, reference_dict_df, reference_sql_df)
    try:
        if sample_df.empty:
            return
    except Exception as e:
        return

    sample_sql_df['SampleName'] = sample_df['Sample_ID']
    sample_sql_df['SampleID'] = pd.Series(list(range(1, sample_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    merged_sample_id_df = sample_df.merge(sample_sql_df, left_on='Sample_ID', right_on='SampleName', how='left', indicator=True)

    print(f'{sample_sql_df.shape[0]} unique samples to import')


    print('Importing GPS')
    gps_sql_df = pd.DataFrame(columns=table_properties['GPSLocations'])

    # Check for duplicate GPS coordinate pairs
    gps_sql_df['GPSLatDeg'] = sample_df['Latitude']
    gps_sql_df['GPSLonDeg'] = sample_df['Longitude']
    gps_sql_df.dropna(subset=['GPSLatDeg', 'GPSLonDeg'], axis=0, how='all', inplace=True)
    gps_sql_df.drop_duplicates(inplace=True)
    gps_sql_df.reset_index(drop=True, inplace=True)

    gps_sql_df['GPSLocationID'] = pd.Series(list(range(1, gps_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    gps_sql_df['GPSFormatID'] = pd.Series([gps_format_id]*gps_sql_df.shape[0], dtype=pd.Int64Dtype())
    gps_sql_df['GPSLocationCreated'] = pd.to_datetime('now')
    gps_sql_df['GPSLocationModified'] = pd.to_datetime('now')

    # Add the GPSLocationID as a foreign key to samples_sql_df
    merged_gps_df = merged_sample_id_df.merge(gps_sql_df, left_on=['Latitude', 'Longitude'], right_on=['GPSLatDeg', 'GPSLonDeg'], how='left', indicator='_merge_indicator')
    sample_sql_df['SampleGPSLocationID'] = pd.Series(merged_gps_df['GPSLocationID'], dtype=pd.Int64Dtype())

    # Add the gps_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        gps_sql_df.to_sql('GPSLocations', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {gps_sql_df.shape[0]} GPS coordinates')


    print('Importing Columns')

    # Column name, height/depth, and height/depth unit are all in the same cell, so need to parse
    # For each Column, the name is the whole thing or comes before ' at '
    column_sql_df = pd.DataFrame(columns=table_properties['Columns'])
    column_dict = {}
    columns = sample_df['Column']
    column_names = set()

    # Remove nan float values from each list
    columns = [column for column in columns if pd.notnull(column)]
    for column in columns:
        if ' at ' in column:
            # If the column name contains ' at ', split it into two parts
            column_name = column.split(' at ')[0]
            hd_info = column.split(' at ')[1]
            # Check if the second part contains an above, below, or depth phrase
            if 'bsf' in hd_info:
                column_name = f'{column_name} bsf'
                hd_info = hd_info.replace('bsf', '')
            if ' above ' in hd_info:
                column_name = f'{column_name} above {hd_info.split(' above ')[1]}'
                hd_info = hd_info.split(' above ')[0]
            if ' below ' in hd_info:
                column_name = f'{column_name} below {hd_info.split(' below ')[1]}'
                hd_info = hd_info.split(' below ')[0]
            if ' depth' in hd_info:
                hd_info = hd_info.split(' depth')[0]
            # Check if the second part contains a unit
            if 'cm' in hd_info:
                unit = 'cm'
                unit_id = 3
            elif 'm' in hd_info:
                unit = 'm'
                unit_id = 2
            elif 'feet' in hd_info:
                unit = 'feet'
                unit_id = 8
            elif 'ft' in hd_info:
                unit = 'ft'
                unit_id = 8
            elif "'" in hd_info:
                unit = "'"
                unit_id = 8
            else:
                print(f"Unknown unit in {hd_info} for column {column_name}")
                return
            hd_info = hd_info.replace(unit, '')
            if '-' in hd_info:
                # If there is a range, split it into two parts
                hd1 = hd_info.split('-')[0]
                hd2 = hd_info.split('-')[1]
                height_depth = (float(hd1) + float(hd2)) / 2
                height_depth_error = abs(float(hd1) - float(hd2)) / 2
            else:
                # If there is no range, just use the value
                height_depth = float(hd_info)
                height_depth_error = None
        else:
            # If the pattern doesn't match, just use the column name and set depth to None
            column_name = column
            height_depth = None
            height_depth_error = None
            unit_id = None
        # Check if the column name is already in the dictionary
        if column_name not in column_names:
            column_names.add(column_name)
        # Add the column name, height/depth, and unit ID to the dictionary
        column_dict[column] = (column_name, height_depth, height_depth_error, unit_id)

    column_sql_df['ColumnName'] = list(column_names)
    column_sql_df['ColumnID'] = pd.Series(list(range(1, len(column_names) + 1)), dtype=pd.Int64Dtype())
    column_sql_df['ColumnCreated'] = pd.to_datetime('now')
    column_sql_df['ColumnModified'] = pd.to_datetime('now')

    # Add the column_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        column_sql_df.to_sql('Columns', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    # Add the column information to sample_sql_df
    column_names_df = pd.DataFrame.from_dict(column_dict, orient='index')
    column_names_df.reset_index(inplace=True)
    column_names_df.rename(columns={'index': 'OriginalColumnName', 0: 'ColumnName', 1: 'Height_Depth', 2: 'Height_Depth_Error', 3: 'Height_Depth_UnitID'}, inplace=True)

    merged_columns_df = sample_df.merge(column_names_df, left_on=['Column'], right_on=['OriginalColumnName'], how='left')
    merged_columns_df = merged_columns_df.merge(column_sql_df, left_on=['ColumnName'], right_on=['ColumnName'], how='left')

    sample_sql_df['SampleColumnID'] = pd.Series(merged_columns_df['ColumnID'], dtype=pd.Int64Dtype())
    sample_sql_df['HeightDepth'] = merged_columns_df['Height_Depth']
    sample_sql_df['HeightDepthError'] = merged_columns_df['Height_Depth_Error']
    sample_sql_df['HeightDepthUnitID'] = pd.Series(merged_columns_df['Height_Depth_UnitID'], dtype=pd.Int64Dtype())

    print(f'Imported {column_sql_df.shape[0]} columns')

    print('Importing sample ages')

    sample_ages_sql_df = pd.DataFrame(columns=table_properties['SampleAges'])

    # Look for unique sample ages
    sample_ages_sql_df['OldestDirectAge'] = sample_df['Max. Stratigraphic Age (Ma)']
    sample_ages_sql_df['YoungestDirectAge'] = sample_df['Min. Stratigraphic Age (Ma)']
    sample_ages_sql_df['DirectAge'] = sample_df['Est. Stratigraphic Age (Ma)']
    sample_ages_sql_df.dropna(axis=0, how='all', inplace=True)
    sample_ages_sql_df.drop_duplicates(inplace=True)
    sample_ages_sql_df.reset_index(drop=True, inplace=True)

    sample_ages_sql_df['SampleAgeID'] = pd.Series(list(range(1, sample_ages_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    sample_ages_sql_df['DirectAgeUnitID'] = pd.Series([age_unit_id]*sample_ages_sql_df.shape[0], dtype=pd.Int64Dtype())
    sample_ages_sql_df['SampleAgeCreated'] = pd.to_datetime('now')
    sample_ages_sql_df['SampleAgeModified'] = pd.to_datetime('now')

    merged_age_df = merged_sample_id_df.merge(sample_ages_sql_df,
                                left_on=['Max. Stratigraphic Age (Ma)', 'Min. Stratigraphic Age (Ma)',
                                         'Est. Stratigraphic Age (Ma)'],
                                right_on=['OldestDirectAge', 'YoungestDirectAge', 'DirectAge'], how='left')

    samples_sample_ages_sql_df = pd.DataFrame(columns=table_properties['Samples_SampleAges'])
    samples_sample_ages_sql_df['SampleID'] = pd.Series(merged_age_df['SampleID'], dtype=pd.Int64Dtype())
    samples_sample_ages_sql_df['SampleAgeID'] = pd.Series(merged_age_df['SampleAgeID'], dtype=pd.Int64Dtype())
    samples_sample_ages_sql_df['Samples_SampleAgesCreated'] = pd.to_datetime('now')
    samples_sample_ages_sql_df['Samples_SampleAgesModified'] = pd.to_datetime('now')
    samples_sample_ages_sql_df.dropna(axis=0, how='any', inplace=True)
    samples_sample_ages_sql_df.drop_duplicates(inplace=True)
    samples_sample_ages_sql_df.reset_index(drop=True, inplace=True)

    # Add the sample_ages_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        sample_ages_sql_df.to_sql('SampleAges', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {sample_ages_sql_df.shape[0]} sample ages')


    # Set default age for samples
    # Check if they have the same number of rows and can be just dropped into the database, they should
    if samples_sample_ages_sql_df.shape[0] == sample_sql_df.shape[0]:
        sample_sql_df['DefaultSampleAgeID'] = pd.Series(samples_sample_ages_sql_df['SampleAgeID'], dtype=pd.Int64Dtype())
    else:
        print(f'Samples table has {sample_sql_df.shape[0]} samples and Samples_SampleAge table has {samples_sample_ages_sql_df.shape[0]} samples')
        return

    # Everything should now be in the Samples table, so it is ready for import
    sample_sql_df['SampleCreated'] = pd.to_datetime('now')
    sample_sql_df['SampleModified'] = pd.to_datetime('now')
    try:
        conn = sqlite3.connect(db)
        sample_sql_df.to_sql('Samples', conn, if_exists='replace', index=False)
        samples_sample_ages_sql_df.to_sql('Samples_SampleAges', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {sample_sql_df.shape[0]} samples')


    print('Importing regions')
    region_sql_df = pd.DataFrame(columns=table_properties['Regions'])

    # Find any instances where a region name is in multiple columns
    duplicates_df = sample_df.map(lambda x: x.lower() if isinstance(x, str) else x)
    duplicates = set()
    region_columns = ['Continent', 'Large Region', 'Country/Small Region', 'Locality']
    for i in range(len(region_columns)):
        for j in range(i + 1, len(region_columns)):
            col1, col2 = region_columns[i], region_columns[j]
            duplicates.update(duplicates_df[col1] [duplicates_df[col1].isin(duplicates_df[col2])])
    if len(list(duplicates)) > 0:
        # If there is only one duplicate of nan, continue
        if len(list(duplicates)) == 1 and pd.isna(list(duplicates)[0]):
            duplicates = set()
        else:
            print('Duplicate region names found:')
            print(list(duplicates))
            print('Please check the region names in the sample sheet.')
            return

    # If any region column is blank, fill with the value from the next one
    shifted_region_df = sample_df[region_columns].apply(shift_left, axis=1)

    # append 'Continent', 'Large Region', and 'Country/Small Region' into one 'RegionName' column
    continent_names = list(shifted_region_df['Continent'].unique())
    large_region_names = list(shifted_region_df['Large Region'].unique())
    country_names = list(sample_df['Country/Small Region'].unique())
    locality_names = list(sample_df['Locality'].unique())
    # Remove nan float values from each list
    continent_names = [region for region in continent_names if pd.notnull(region)]
    large_region_names = [region for region in large_region_names if pd.notnull(region)]
    country_names = [region for region in country_names if pd.notnull(region)]
    locality_names = [region for region in locality_names if pd.notnull(region)]
    region_names = continent_names + large_region_names + country_names + locality_names
    duplicates = []
    distinct_names = set()
    for region_name in region_names:
        if region_name in distinct_names:
            duplicates.append(region_name)
        else:
            distinct_names.add(region_name)
    if len(list(duplicates)) > 0:
        # If there is only one duplicate of nan, continue
        if len(list(duplicates)) == 1 and pd.isna(list(duplicates)[0]):
            pass
        else:
            print('Duplicate region names found:')
            print(duplicates)
            print('Please check the region names in the sample sheet.')
            return

    # Check for children with multiple parents
    multiple_parents = []
    for large_region_name in large_region_names:
        if pd.isnull(large_region_name):
            continue
        # Get the continent values for the region name
        continent_values = shifted_region_df[shifted_region_df['Large Region'] == large_region_name]['Continent'].unique()
        if len(continent_values) > 1:
            multiple_parents.append(large_region_name)
    for country_name in country_names:
        if pd.isnull(country_name):
            continue
        # Get the large region values for the country
        large_region_values = shifted_region_df[shifted_region_df['Country/Small Region'] == country_name]['Large Region'].unique()
        if len(large_region_values) > 1:
            multiple_parents.append(country_name)
    for locality_name in locality_names:
        if pd.isnull(locality_name):
            continue
        # Get the country values for the locality
        country_values = shifted_region_df[shifted_region_df['Locality'] == locality_name]['Country/Small Region'].unique()
        if len(country_values) > 1:
            multiple_parents.append(locality_name)
    if multiple_parents != []:
        print('Regions with multiple parents found:')
        print(multiple_parents)
        print('Please check the region names in the sample sheet.')
        return

    region_sql_df['RegionName'] = region_names
    # Remove null region name rows
    region_sql_df.dropna(subset=['RegionName'], axis=0, how='all', inplace=True)
    region_sql_df['RegionID'] = pd.Series(list(range(1, len(region_names) + 1)), dtype=pd.Int64Dtype())
    region_dict_df = pd.DataFrame(columns=['RegionName', 'RegionID'])
    region_dict_df['RegionName'] = region_sql_df['RegionName']
    region_dict_df['RegionID'] = pd.Series(region_sql_df['RegionID'], dtype=pd.Int64Dtype())

    # Create dictionaries for the region names and their corresponding IDs
    region_parent_id_dictionary = {}
    region_parent_row_dictionary = {}

    shifted_region_df = sample_df[region_columns].apply(shift_left, axis=1)

    # For each unique 'Continent', find all the unique 'Large Region' values
    continents = list(shifted_region_df['Continent'].unique())
    continents = sorted([region for region in continents if pd.notnull(region)])
    for continent in continents:
        large_region_parent_id = region_sql_df.loc[region_sql_df['RegionName'] == continent, 'RegionID'].values[0]
        continent_parent_row = continents.index(continent)
        # Parent ID for top level is empty
        region_parent_id_dictionary[continent] = None
        region_parent_row_dictionary[continent] = continent_parent_row
        child_large_regions = list(shifted_region_df[shifted_region_df['Continent'] ==
                                                            continent]['Large Region'].unique())
        child_large_regions = sorted([region for region in child_large_regions if pd.notnull(region)])
        for large_region in child_large_regions:
            if pd.isnull(large_region):
                continue
            country_small_region_parent_id = \
                region_sql_df.loc[region_sql_df['RegionName'] == large_region, 'RegionID'].values[0]
            if large_region != continent:
                large_region_parent_row = child_large_regions.index(large_region)
                region_parent_id_dictionary[large_region] = int(large_region_parent_id)
                region_parent_row_dictionary[large_region] = large_region_parent_row
            child_country_small_regions = list(
                shifted_region_df[(shifted_region_df['Continent'] == continent) & (shifted_region_df['Large Region'] ==
                   large_region)]['Country/Small Region'].unique())
            child_country_small_regions = sorted([region for region in child_country_small_regions if pd.notnull(region)])
            for country_small_region in child_country_small_regions:
                if pd.isnull(country_small_region):
                    continue
                locality_parent_id = \
                    region_sql_df.loc[region_sql_df['RegionName'] == country_small_region, 'RegionID'].values[0]
                if country_small_region != large_region:
                    country_small_region_parent_row = child_country_small_regions.index(country_small_region)
                    region_parent_id_dictionary[country_small_region] = int(country_small_region_parent_id)
                    region_parent_row_dictionary[country_small_region] = country_small_region_parent_row
                child_locality_regions = list(shifted_region_df[(shifted_region_df['Continent'] == continent) & (
                        shifted_region_df['Large Region'] == large_region) & (shifted_region_df['Country/Small Region']
                                                                       == country_small_region)]['Locality'].unique())
                child_locality_regions = sorted([region for region in child_locality_regions if pd.notnull(region)])
                for locality_region in child_locality_regions:
                    if pd.isnull(locality_region):
                        continue
                    if locality_region != country_small_region:
                        locality_parent_row = child_locality_regions.index(locality_region)
                        region_parent_id_dictionary[locality_region] = int(locality_parent_id)
                        region_parent_row_dictionary[locality_region] = locality_parent_row

    # Add each dictionary to the appropriate column in regions_sql_df
    region_sql_df['ParentRegionID'] = pd.Series(region_sql_df['RegionName'].map(region_parent_id_dictionary),dtype=pd.Int64Dtype())
    region_sql_df['RegionParentRow'] = pd.Series(region_sql_df['RegionName'].map(region_parent_row_dictionary),dtype=pd.Int64Dtype())

    # Add the time stamps
    region_sql_df['RegionCreated'] = pd.to_datetime('now')
    region_sql_df['RegionModified'] = pd.to_datetime('now')

    # Add the region_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        region_sql_df.to_sql('Regions', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {region_sql_df.shape[0]} regions')

    # Create the Samples_Regions table
    sample_region_sql_df = pd.DataFrame(columns=table_properties['Samples_Regions'])

    merged_continent_df = merged_sample_id_df.merge(region_sql_df, left_on=['Continent'], right_on=['RegionName'], how='left')
    merged_large_region_df = merged_sample_id_df.merge(region_sql_df, left_on=['Large Region'], right_on=['RegionName'], how='left')
    merged_country_df = merged_sample_id_df.merge(region_sql_df, left_on=['Country/Small Region'], right_on=['RegionName'], how='left')
    merged_locality_df = merged_sample_id_df.merge(region_sql_df, left_on=['Locality'], right_on=['RegionName'], how='left')
    continents_selected = merged_continent_df[['SampleID', 'RegionID']]
    large_regions_selected = merged_large_region_df[['SampleID', 'RegionID']]
    countries_selected = merged_country_df[['SampleID', 'RegionID']]
    localities_selected = merged_locality_df[['SampleID', 'RegionID']]
    regions_combined_df = pd.concat([continents_selected, large_regions_selected, countries_selected, localities_selected], ignore_index=True)

    sample_region_sql_df['SampleID'] = pd.Series(regions_combined_df['SampleID'], dtype=pd.Int64Dtype())
    sample_region_sql_df['RegionID'] = pd.Series(regions_combined_df['RegionID'], dtype=pd.Int64Dtype())
    sample_region_sql_df['Samples_RegionsCreated'] = pd.to_datetime('now')
    sample_region_sql_df['Samples_RegionsModified'] = pd.to_datetime('now')
    sample_region_sql_df.dropna(axis=0, how='any', inplace=True)
    sample_region_sql_df.drop_duplicates(inplace=True)
    sample_region_sql_df.reset_index(drop=True, inplace=True)

    # Add the sample_region_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        sample_region_sql_df.to_sql('Samples_Regions', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {sample_region_sql_df.shape[0]} sample-region links')


    print('Importing units')
    unit_sql_df = pd.DataFrame(columns=table_properties['Units'])

    # Check for duplicate unit names
    duplicates_df = sample_df.map(lambda x: x.lower() if isinstance(x, str) else x)
    duplicates = set()
    unit_columns = ['Major Geographic-Geologic Description', 'Sub-Major Geographic-Geologic Description',
                    'Intermediate Geologic-Geographic Unit', 'Minor Geologic-Geographic Unit',
                    'Sub-Minor Geologic-Geographic Unit']
    for i in range(len(unit_columns)):
        for j in range(i + 1, len(unit_columns)):
            col1, col2 = unit_columns[i], unit_columns[j]
            duplicates.update(duplicates_df[col1] [duplicates_df[col1].isin(duplicates_df[col2])])
    if len(list(duplicates)) > 0:
        # If there is only one duplicate of nan, continue
        if len(list(duplicates)) == 1 and pd.isna(list(duplicates)[0]):
            pass
        else:
            print('Duplicate unit names found:')
            print(duplicates)
            print('Please check the unit names in the sample sheet.')
            return

    # If any unit column is blank, fill with the value from the next one
    shifted_unit_df = sample_df[unit_columns].apply(shift_left, axis=1)

    # append 'Major Unit' and 'Minor Unit' into one 'UnitName' column
    major_unit_names = list(shifted_unit_df['Major Geographic-Geologic Description'].unique())
    sub_major_unit_names = list(shifted_unit_df['Sub-Major Geographic-Geologic Description'].unique())
    intermediate_unit_names = list(shifted_unit_df['Intermediate Geologic-Geographic Unit'].unique())
    minor_unit_names = list(shifted_unit_df['Minor Geologic-Geographic Unit'].unique())
    sub_minor_unit_names = list(shifted_unit_df['Sub-Minor Geologic-Geographic Unit'].unique())
    # Add any additional tags not already in units
    for key in additional_unit_tags_dict.keys():
        if key not in sub_minor_unit_names:
            if key not in minor_unit_names:
                if key not in intermediate_unit_names:
                    if key not in sub_major_unit_names:
                        if key not in major_unit_names:
                            major_unit_names.append(key)
    # Remove nan float values from each list
    major_unit_names = [name for name in major_unit_names if pd.notnull(name)]
    sub_major_unit_names = [name for name in sub_major_unit_names if pd.notnull(name)]
    intermediate_unit_names = [name for name in intermediate_unit_names if pd.notnull(name)]
    minor_unit_names = [name for name in minor_unit_names if pd.notnull(name)]
    sub_minor_unit_names = [name for name in sub_minor_unit_names if pd.notnull(name)]

    unit_names = major_unit_names + sub_major_unit_names + intermediate_unit_names + minor_unit_names + sub_minor_unit_names
    duplicates = []
    distinct_names = set()
    for unit_name in unit_names:
        if unit_name in distinct_names:
            duplicates.append(unit_name)
        else:
            distinct_names.add(unit_name)
    if len(list(duplicates)) > 0:
        # If there is only one duplicate of nan, continue
        if len(list(duplicates)) == 1 and pd.isna(list(duplicates)[0]):
            pass
        else:
            print('Duplicate unit names found:')
            print(list(duplicates))
            print('Please check the unit names in the sample sheet.')
            return

    # Check for children with multiple parents
    multiple_parents = []
    for sub_major_unit_name in sub_major_unit_names:
        if pd.isnull(sub_major_unit_name):
            continue
        # Get the major unit values for the sub-major unit
        major_unit_values = shifted_unit_df[shifted_unit_df['Sub-Major Geographic-Geologic Description'] == sub_major_unit_name]['Major Geographic-Geologic Description'].unique()
        if len(major_unit_values) > 1:
            multiple_parents.append(sub_major_unit_name)
    for intermediate_unit_name in intermediate_unit_names:
        if pd.isnull(intermediate_unit_name):
            continue
        # Get the sub-major unit values for the intermediate unit
        major_unit_values = shifted_unit_df[shifted_unit_df['Intermediate Geologic-Geographic Unit'] == intermediate_unit_name]['Sub-Major Geographic-Geologic Description'].unique()
        if len(major_unit_values) > 1:
            multiple_parents.append(intermediate_unit_name)
    for minor_unit_name in minor_unit_names:
        if pd.isnull(minor_unit_name):
            continue
        # Get the intermediate unit values for the minor unit
        intermediate_unit_values = shifted_unit_df[shifted_unit_df['Minor Geologic-Geographic Unit'] == minor_unit_name]['Intermediate Geologic-Geographic Unit'].unique()
        if len(intermediate_unit_values) > 1:
            multiple_parents.append(minor_unit_name)
    for sub_minor_unit_name in sub_minor_unit_names:
        if pd.isnull(sub_minor_unit_name):
            continue
        # Get the minor unit values for the sub-minor unit
        minor_unit_values = shifted_unit_df[shifted_unit_df['Sub-Minor Geologic-Geographic Unit'] == sub_minor_unit_name]['Minor Geologic-Geographic Unit'].unique()
        if len(minor_unit_values) > 1:
            multiple_parents.append(sub_minor_unit_name)
    if multiple_parents != []:
        print('Units with multiple parents found:')
        print(multiple_parents)
        print('Please check the unit names in the sample sheet.')
        return

    unit_sql_df['UnitName'] = unit_names
    # Remove null unit name rows
    unit_sql_df.dropna(subset=['UnitName'], axis=0, how='all', inplace=True)
    unit_sql_df['UnitID'] = pd.Series(list(range(1, len(unit_names) + 1)), dtype=pd.Int64Dtype())
    unit_dict_df = pd.DataFrame(columns=['UnitName', 'UnitID'])
    unit_dict_df['UnitName'] = unit_sql_df['UnitName']
    unit_dict_df['UnitID'] = pd.Series(unit_sql_df['UnitID'], dtype=pd.Int64Dtype())

    # Create dictionaries for the unit names and their corresponding IDs
    unit_parent_id_dictionary = {}
    unit_parent_row_dictionary = {}

    # For each unique unit, find all the unique child unit values
    major_units = list(shifted_unit_df['Major Geographic-Geologic Description'].unique())
    major_units = sorted([unit for unit in major_units if pd.notnull(unit)])
    for major_unit in major_units:
        sub_major_unit_parent_id = unit_sql_df.loc[unit_sql_df['UnitName'] == major_unit, 'UnitID'].values[0]
        major_unit_parent_row = major_units.index(major_unit)
        # Check if the major unit is a key in the dictionary
        if major_unit not in unit_parent_id_dictionary:
            # Parent ID for top level is empty
            unit_parent_id_dictionary[major_unit] = None
            unit_parent_row_dictionary[major_unit] = major_unit_parent_row
        child_sub_major_units = list(shifted_unit_df[shifted_unit_df['Major Geographic-Geologic Description']
                                                   == major_unit]['Sub-Major Geographic-Geologic Description'].unique())
        child_sub_major_units = sorted([unit for unit in child_sub_major_units if pd.notnull(unit)])
        for sub_major_unit in child_sub_major_units:
            if pd.isnull(sub_major_unit):
                continue
            intermediate_unit_parent_id = unit_sql_df.loc[unit_sql_df['UnitName'] == sub_major_unit, 'UnitID'].values[0]
            if sub_major_unit != major_unit:
                if sub_major_unit not in unit_parent_id_dictionary:
                    sub_major_unit_parent_row = child_sub_major_units.index(sub_major_unit)
                    unit_parent_id_dictionary[sub_major_unit] = sub_major_unit_parent_id
                    unit_parent_row_dictionary[sub_major_unit] = sub_major_unit_parent_row
            child_intermediate_units = list(shifted_unit_df[(shifted_unit_df['Major Geographic-Geologic Description']
                                         == major_unit) & (shifted_unit_df['Sub-Major Geographic-Geologic Description']
                                            == sub_major_unit)]['Intermediate Geologic-Geographic Unit'].unique())
            child_intermediate_units = sorted([unit for unit in child_intermediate_units if pd.notnull(unit)])
            for intermediate_unit in child_intermediate_units:
                if pd.isnull(intermediate_unit):
                    continue
                minor_unit_parent_id = unit_sql_df.loc[unit_sql_df['UnitName'] == intermediate_unit, 'UnitID'].values[0]
                if intermediate_unit != sub_major_unit:
                    if intermediate_unit not in unit_parent_id_dictionary:
                        intermediate_unit_parent_row = child_intermediate_units.index(intermediate_unit)
                        unit_parent_id_dictionary[intermediate_unit] = intermediate_unit_parent_id
                        unit_parent_row_dictionary[intermediate_unit] = intermediate_unit_parent_row
                child_minor_units = list(
                    shifted_unit_df[(shifted_unit_df['Major Geographic-Geologic Description'] == major_unit) & (
                    shifted_unit_df['Sub-Major Geographic-Geologic Description'] == sub_major_unit) & (
                    shifted_unit_df['Intermediate Geologic-Geographic Unit'] == intermediate_unit)
                    ]['Minor Geologic-Geographic Unit'].unique())
                child_minor_units = sorted([unit for unit in child_minor_units if pd.notnull(unit)])
                for minor_unit in child_minor_units:
                    if pd.isnull(minor_unit):
                        continue
                    sub_minor_unit_parent_id = \
                    unit_sql_df.loc[unit_sql_df['UnitName'] == minor_unit, 'UnitID'].values[0]
                    if minor_unit != intermediate_unit:
                        if minor_unit not in unit_parent_id_dictionary:
                            minor_unit_parent_row = child_minor_units.index(minor_unit)
                            unit_parent_id_dictionary[minor_unit] = minor_unit_parent_id
                            unit_parent_row_dictionary[minor_unit] = minor_unit_parent_row
                    child_sub_minor_units = list(shifted_unit_df[
                                     (shifted_unit_df['Major Geographic-Geologic Description'] == major_unit) &
                                     (shifted_unit_df['Sub-Major Geographic-Geologic Description'] == sub_major_unit) &
                                     (shifted_unit_df['Intermediate Geologic-Geographic Unit'] == intermediate_unit) &
                                     (shifted_unit_df['Minor Geologic-Geographic Unit'] == minor_unit)
                                                 ]['Sub-Minor Geologic-Geographic Unit'].unique())
                    child_sub_minor_units = sorted([unit for unit in child_sub_minor_units if pd.notnull(unit)])
                    for sub_minor_unit in child_sub_minor_units:
                        if pd.isnull(sub_minor_unit):
                            continue
                        if sub_minor_unit != minor_unit:
                            if sub_minor_unit not in unit_parent_id_dictionary:
                                sub_minor_unit_parent_row = child_sub_minor_units.index(sub_minor_unit)
                                unit_parent_id_dictionary[sub_minor_unit] = sub_minor_unit_parent_id
                                unit_parent_row_dictionary[sub_minor_unit] = sub_minor_unit_parent_row

    # Add each dictionary to the appropriate column in unit_sql_df
    unit_sql_df['ParentUnitID'] = pd.Series(unit_sql_df['UnitName'].map(unit_parent_id_dictionary),dtype=pd.Int64Dtype())
    unit_sql_df['UnitParentRow'] = pd.Series(unit_sql_df['UnitName'].map(unit_parent_row_dictionary),dtype=pd.Int64Dtype())

    # Add the time stamps
    unit_sql_df['UnitCreated'] = pd.to_datetime('now')
    unit_sql_df['UnitModified'] = pd.to_datetime('now')

    # Add the unit_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        unit_sql_df.to_sql('Units', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return
    print(f'Imported {unit_sql_df.shape[0]} units')

    # Create the Samples_Units table
    sample_unit_sql_df = pd.DataFrame(columns=table_properties['Samples_Units'])

    merged_major_unit_df = merged_sample_id_df.merge(unit_sql_df,
                             left_on=['Major Geographic-Geologic Description'], right_on=['UnitName'], how='left')
    merged_sub_major_unit_df = merged_sample_id_df.merge(unit_sql_df,
                             left_on=['Sub-Major Geographic-Geologic Description'], right_on=['UnitName'], how='left')
    merged_intermediate_unit_df = merged_sample_id_df.merge(unit_sql_df,
                             left_on=['Intermediate Geologic-Geographic Unit'], right_on=['UnitName'], how='left')
    merged_minor_unit_df = merged_sample_id_df.merge(unit_sql_df,
                             left_on=['Minor Geologic-Geographic Unit'], right_on=['UnitName'], how='left')
    merged_sub_minor_unit_df = merged_sample_id_df.merge(unit_sql_df,
                             left_on=['Sub-Minor Geologic-Geographic Unit'], right_on=['UnitName'], how='left')
    # Include additional units
    missing_sample_names = {}
    additional_units_selected = pd.DataFrame(columns=['SampleID', 'UnitID'])
    for key, value in additional_unit_tags_dict.items():
        # Get the unit ID for the unit key
        unit_id = unit_sql_df.loc[unit_sql_df['UnitName'] == key, 'UnitID'].values[0]
        for sample_name in value:
            # Check if the sample name is in the merged_sample_id_df
            if sample_name not in merged_sample_id_df['Sample_ID'].values:
                # Look for sample names that contain the sample name and a colon
                sample_name_matches = merged_sample_id_df[merged_sample_id_df['Sample_ID'].str.contains(f'{sample_name}: ', na=False)]
                if sample_name_matches.empty:
                    # If no matches are found, add the sample name to the missing_sample_names dictionary
                    if sample_name not in missing_sample_names:
                        missing_sample_names[sample_name] = []
                else:
                    # If matches are found, add a list of matching sample names to the missing_sample_names dictionary
                    missing_sample_names[sample_name] = sample_name_matches['Sample_ID'].tolist()
                continue
            else:
                # Get the sample ID for the sample name
                sample_id = merged_sample_id_df.loc[merged_sample_id_df['Sample_ID'] == sample_name,
                            'SampleID'].values[0]
                # Add the sample ID and unit ID to the additional_units_selected data frame
                new_row = pd.DataFrame({'SampleID': [sample_id], 'UnitID': [unit_id]})
                additional_units_selected = pd.concat([additional_units_selected, new_row], ignore_index=True)
    # If any sample names are missing, print a message
    if missing_sample_names:
        print('The following sample names were not found, but these are close matches:')
        for key, value in missing_sample_names.items():
            print(f'{key}: {value}')
        print('Please check the sample names in the sample additional units dictionary.')
        return

    major_units_selected = merged_major_unit_df[['SampleID', 'UnitID']]
    sub_major_units_selected = merged_sub_major_unit_df[['SampleID', 'UnitID']]
    intermediate_units_selected = merged_intermediate_unit_df[['SampleID', 'UnitID']]
    minor_units_selected = merged_minor_unit_df[['SampleID', 'UnitID']]
    sub_minor_units_selected = merged_sub_minor_unit_df[['SampleID', 'UnitID']]
    units_combined_df = pd.concat([major_units_selected, sub_major_units_selected, intermediate_units_selected,
                                   minor_units_selected, sub_minor_units_selected], ignore_index=True)

    sample_unit_sql_df['SampleID'] = pd.Series(units_combined_df['SampleID'], dtype=pd.Int64Dtype())
    sample_unit_sql_df['UnitID'] = pd.Series(units_combined_df['UnitID'], dtype=pd.Int64Dtype())
    sample_unit_sql_df['Samples_UnitsCreated'] = pd.to_datetime('now')
    sample_unit_sql_df['Samples_UnitsModified'] = pd.to_datetime('now')
    sample_unit_sql_df.dropna(axis=0, how='any', inplace=True)
    sample_unit_sql_df.drop_duplicates(inplace=True)
    sample_unit_sql_df.reset_index(drop=True, inplace=True)

    # Add the sample_unit_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        sample_unit_sql_df.to_sql('Samples_Units', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {sample_unit_sql_df.shape[0]} sample-unit links')


    print('Importing rock types')

    rock_type_sql_df = pd.DataFrame(columns=table_properties['RockTypes'])
    # Check for duplicate rock type names
    duplicates_df = sample_df.map(lambda x: x.lower() if isinstance(x, str) else x)
    duplicates = set()
    rock_type_columns = ['Class-1 Rock Type', 'Class-2 Rock Type', 'Class-3 Rock Type', 'Class-4 Rock Type']
    for i in range(len(rock_type_columns)):
        for j in range(i + 1, len(rock_type_columns)):
            col1, col2 = rock_type_columns[i], rock_type_columns[j]
            duplicates.update(duplicates_df[col1] [duplicates_df[col1].isin(duplicates_df[col2])])
    if len(list(duplicates)) > 0:
        # If there is only one duplicate of nan, continue
        if len(list(duplicates)) == 1 and pd.isna(list(duplicates)[0]):
            pass
        else:
            print('Duplicate rock type names found:')
            print(list(duplicates))
            print('Please check the rock type names in the sample sheet.')
            return

    # If any rock type column is blank, fill with the value from the next one
    shifted_rock_type_df = sample_df[rock_type_columns].apply(shift_left, axis=1)

    # append columns into one 'RockTypeName' column
    class1_names = list(shifted_rock_type_df['Class-1 Rock Type'].unique())
    class2_names = list(shifted_rock_type_df['Class-2 Rock Type'].unique())
    class3_names = list(shifted_rock_type_df['Class-3 Rock Type'].unique())
    class4_names = list(shifted_rock_type_df['Class-4 Rock Type'].unique())
    # Remove nan float values from each list
    class1_names = [name for name in class1_names if pd.notnull(name)]
    class2_names = [name for name in class2_names if pd.notnull(name)]
    class3_names = [name for name in class3_names if pd.notnull(name)]
    class4_names = [name for name in class4_names if pd.notnull(name)]
    rock_type_names = class1_names + class2_names + class3_names + class4_names
    duplicates = []
    distinct_names = set()
    for rock_type_name in rock_type_names:
        if rock_type_name in distinct_names:
            duplicates.append(rock_type_name)
        else:
            distinct_names.add(rock_type_name)
    if len(list(duplicates)) > 0:
        # If there is only one duplicate of nan, continue
        if len(list(duplicates)) == 1 and pd.isna(list(duplicates)[0]):
            pass
        else:
            print('Duplicate rock type names found:')
            print(list(duplicates))
            print('Please check the rock type names in the sample sheet.')
            return

    # Check for children with multiple parents
    multiple_parents = []
    for class2_name in class2_names:
        if pd.isna(class2_name):
            continue
        # Get the class1 values for the class2 name
        class1_values = \
        shifted_rock_type_df[shifted_rock_type_df['Class-2 Rock Type'] == class2_name][
            'Class-1 Rock Type'].unique()
        if len(class1_values) > 1:
            multiple_parents.append(class2_name)
    for class3_name in class3_names:
        if pd.isna(class3_name):
            continue
        # Get the class2 values for the class3 name
        class2_values = \
        shifted_rock_type_df[shifted_rock_type_df['Class-3 Rock Type'] == class3_name][
            'Class-2 Rock Type'].unique()
        if len(class2_values) > 1:
            multiple_parents.append(class3_name)
    for class4_name in class4_names:
        if pd.isna(class4_name):
            continue
        # Get the class3 values for the class4 name
        class3_values = \
        shifted_rock_type_df[shifted_rock_type_df['Class-4 Rock Type'] == class4_name][
            'Class-3 Rock Type'].unique()
        if len(class3_values) > 1:
            multiple_parents.append(class4_name)

    if multiple_parents != []:
        print('Rock types with multiple parents found:')
        print(multiple_parents)
        print('Please check the rock type names in the sample sheet.')
        return

    rock_type_sql_df['RockTypeName'] = rock_type_names
    # Remove null rock type name rows
    rock_type_sql_df.dropna(subset=['RockTypeName'], axis=0, how='all', inplace=True)
    rock_type_sql_df['RockTypeID'] = pd.Series(list(range(1, len(rock_type_names) + 1)), dtype=pd.Int64Dtype())
    rock_type_dict_df = pd.DataFrame(columns=['RockTypeName', 'RockTypeID'])
    rock_type_dict_df['RockTypeName'] = rock_type_sql_df['RockTypeName']
    rock_type_dict_df['RockTypeID'] = pd.Series(rock_type_sql_df['RockTypeID'], dtype=pd.Int64Dtype())

    # Create dictionaries for the rock type names and their corresponding IDs
    rock_type_parent_id_dictionary = {}
    rock_type_parent_row_dictionary = {}

    # For each unique 'Class-1 Rock Type', find all the unique 'Class-2 Rock Type' values
    class1_names = list(shifted_rock_type_df['Class-1 Rock Type'].unique())
    class1_names = sorted([name for name in class1_names if pd.notnull(name)])
    for class1_name in class1_names:
        class2_parent_id = rock_type_sql_df.loc[rock_type_sql_df['RockTypeName'] == class1_name, 'RockTypeID'].values[0]
        class1_parent_row = class1_names.index(class1_name)
        # Parent ID for top level is empty
        rock_type_parent_id_dictionary[class1_name] = None
        rock_type_parent_row_dictionary[class1_name] = class1_parent_row
        child_class2_names = list(
            shifted_rock_type_df[shifted_rock_type_df['Class-1 Rock Type'] == class1_name][
                'Class-2 Rock Type'].unique())
        child_class2_names = sorted([name for name in child_class2_names if pd.notnull(name)])
        for class2_name in child_class2_names:
            if pd.isnull(class2_name):
                continue
            class3_parent_id = \
            rock_type_sql_df.loc[rock_type_sql_df['RockTypeName'] == class2_name, 'RockTypeID'].values[0]
            if class2_name != class1_name:
                class2_parent_row = child_class2_names.index(class2_name)
                rock_type_parent_id_dictionary[class2_name] = class2_parent_id
                rock_type_parent_row_dictionary[class2_name] = class2_parent_row
            child_class3_names = list(
                shifted_rock_type_df[(shifted_rock_type_df['Class-1 Rock Type'] == class1_name) & (
                        shifted_rock_type_df['Class-2 Rock Type'] == class2_name)][
                    'Class-3 Rock Type'].unique())
            child_class3_names = sorted([name for name in child_class3_names if pd.notnull(name)])
            for class3_name in child_class3_names:
                if pd.isnull(class3_name):
                    continue
                class4_parent_id = \
                rock_type_sql_df.loc[rock_type_sql_df['RockTypeName'] == class3_name, 'RockTypeID'].values[0]
                if class3_name != class2_name:
                    class3_parent_row = child_class3_names.index(class3_name)
                    rock_type_parent_id_dictionary[class3_name] = class3_parent_id
                    rock_type_parent_row_dictionary[class3_name] = class3_parent_row
                child_class4_names = list(
                    shifted_rock_type_df[(shifted_rock_type_df['Class-1 Rock Type'] == class1_name) & (
                            shifted_rock_type_df['Class-2 Rock Type'] == class2_name) & (
                            shifted_rock_type_df['Class-3 Rock Type'] == class3_name)][
                        'Class-4 Rock Type'].unique())
                child_class4_names = sorted([name for name in child_class4_names if pd.notnull(name)])
                for class4_name in child_class4_names:
                    if pd.isnull(class4_name):
                        continue
                    if class4_name != class3_name:
                        class4_parent_row = child_class4_names.index(class4_name)
                        rock_type_parent_id_dictionary[class4_name] = class4_parent_id
                        rock_type_parent_row_dictionary[class4_name] = class4_parent_row

    # Add each dictionary to the appropriate column in rock_type_sql_df
    rock_type_sql_df['ParentRockTypeID'] = pd.Series(rock_type_sql_df['RockTypeName'].map(rock_type_parent_id_dictionary),dtype=pd.Int64Dtype())
    rock_type_sql_df['RockTypeParentRow'] = pd.Series(rock_type_sql_df['RockTypeName'].map(rock_type_parent_row_dictionary),dtype=pd.Int64Dtype())
    # Add the time stamps
    rock_type_sql_df['RockTypeCreated'] = pd.to_datetime('now')
    rock_type_sql_df['RockTypeModified'] = pd.to_datetime('now')

    # Add the rock_type_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        rock_type_sql_df.to_sql('RockTypes', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {rock_type_sql_df.shape[0]} rock types')


    # Create the Samples_RockTypes table
    sample_rock_type_sql_df = pd.DataFrame(columns=table_properties['Samples_RockTypes'])
    merged_class1_df = merged_sample_id_df.merge(rock_type_sql_df, left_on=['Class-1 Rock Type'], right_on=['RockTypeName'], how='left')
    merged_class2_df = merged_sample_id_df.merge(rock_type_sql_df, left_on=['Class-2 Rock Type'], right_on=['RockTypeName'], how='left')
    merged_class3_df = merged_sample_id_df.merge(rock_type_sql_df, left_on=['Class-3 Rock Type'], right_on=['RockTypeName'], how='left')
    # Temporarily fill nans with empty strings to avoid errors for empty class-4 rock types
    merged_sample_id_df['Class-4 Rock Type'] = merged_sample_id_df['Class-4 Rock Type'].fillna('')
    merged_class4_df = merged_sample_id_df.merge(rock_type_sql_df, left_on=['Class-4 Rock Type'], right_on=['RockTypeName'], how='left')
    # Remove the temporary empty strings
    merged_sample_id_df['Class-4 Rock Type'] = merged_sample_id_df['Class-4 Rock Type'].replace('', np.nan)
    class1_selected = merged_class1_df[['SampleID', 'RockTypeID']]
    class2_selected = merged_class2_df[['SampleID', 'RockTypeID']]
    class3_selected = merged_class3_df[['SampleID', 'RockTypeID']]
    class4_selected = merged_class4_df[['SampleID', 'RockTypeID']]
    rock_types_combined_df = pd.concat([class1_selected, class2_selected, class3_selected, class4_selected], ignore_index=True)

    sample_rock_type_sql_df['SampleID'] = pd.Series(rock_types_combined_df['SampleID'], dtype=pd.Int64Dtype())
    sample_rock_type_sql_df['RockTypeID'] = pd.Series(rock_types_combined_df['RockTypeID'], dtype=pd.Int64Dtype())
    sample_rock_type_sql_df['Samples_RockTypesCreated'] = pd.to_datetime('now')
    sample_rock_type_sql_df['Samples_RockTypesModified'] = pd.to_datetime('now')
    sample_rock_type_sql_df.dropna(axis=0, how='any', inplace=True)
    sample_rock_type_sql_df.drop_duplicates(inplace=True)
    sample_rock_type_sql_df.reset_index(drop=True, inplace=True)

    # Add the sample_rock_type_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        sample_rock_type_sql_df.to_sql('Samples_RockTypes', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {sample_rock_type_sql_df.shape[0]} sample-rock type links')


    print('Creating aliquots')

    # Create the Aliquots table
    aliquot_sql_df = pd.DataFrame(columns=table_properties['Aliquots'])

    # No aliquots on the database, so just repeat the sample names
    aliquot_sql_df['AliquotName'] = sample_sql_df['SampleName']
    aliquot_sql_df['AliquotID'] = pd.Series(list(range(1, sample_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    aliquot_sql_df['SampleID'] = pd.Series(sample_sql_df['SampleID'], dtype=pd.Int64Dtype())

    # No nested aliquots, so parentID is null, just repeat the sample IDs for order in the root
    aliquot_sql_df['AliquotParentRow'] = pd.Series(list(range(1, sample_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    aliquot_sql_df['AliquotCreated'] = pd.to_datetime('now')
    aliquot_sql_df['AliquotModified'] = pd.to_datetime('now')

    # Add the aliquot_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        aliquot_sql_df.to_sql('Aliquots', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return
    print(f'Imported {aliquot_sql_df.shape[0]} aliquots')


    # --------------------
    # Import the spot and analysis tags from Puetz et al. (2024) into the database file.
    # --------------------
    # These are mostly in the Samples sheet as well.

    # Create the Spot Composition table
    spot_composition_sql_df = pd.DataFrame(columns=table_properties['SpotCompositions'])
    spot_composition_sql_df['SpotCompositionName'] = sample_df['Mineral']
    spot_composition_sql_df.dropna(axis=0, how='all', inplace=True)
    spot_composition_sql_df.drop_duplicates(inplace=True)
    spot_composition_sql_df.reset_index(drop=True, inplace=True)
    spot_composition_sql_df['SpotCompositionID'] = pd.Series(list(range(1, spot_composition_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    spot_composition_sql_df['SpotCompositionCreated'] = pd.to_datetime('now')
    spot_composition_sql_df['SpotCompositionModified'] = pd.to_datetime('now')

    # Add the spot_composition_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        spot_composition_sql_df.to_sql('SpotCompositions', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {spot_composition_sql_df.shape[0]} spot compositions')


    print('Importing U-Pb analysis methods')

    # Create the UPbAnalysisMethods table
    analysis_method_sql_df = pd.DataFrame(columns=table_properties['UPbAnalysisMethods'])
    analysis_method_sql_df['UPbAnalysisMethodName'] = sample_df['Mass Spectrometer']
    analysis_method_sql_df.dropna(axis=0, how='all', inplace=True)
    analysis_method_sql_df.drop_duplicates(inplace=True)
    analysis_method_sql_df.reset_index(drop=True, inplace=True)
    analysis_method_sql_df['UPbAnalysisMethodID'] = pd.Series(list(range(1, analysis_method_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    analysis_method_sql_df['UPbAnalysisMethodCreated'] = pd.to_datetime('now')
    analysis_method_sql_df['UPbAnalysisMethodModified'] = pd.to_datetime('now')

    # Add the analysis_method_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        analysis_method_sql_df.to_sql('UPbAnalysisMethods', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {analysis_method_sql_df.shape[0]} analysis methods')


    print('Importing lab facilities')

    # Create the LabFacilities table
    lab_facility_sql_df = pd.DataFrame(columns=table_properties['LabFacilities'])
    lab_facility_sql_df['LabFacilityName'] = sample_df['Spectrometer Location']
    lab_facility_sql_df['LabFacilityDescription'] = sample_df['Institution']
    lab_facility_sql_df.dropna(axis=0, how='all', inplace=True)
    lab_facility_sql_df.drop_duplicates(inplace=True)
    lab_facility_sql_df.reset_index(drop=True, inplace=True)
    lab_facility_sql_df['LabFacilityID'] = pd.Series(list(range(1, lab_facility_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    lab_facility_sql_df['LabFacilityCreated'] = pd.to_datetime('now')
    lab_facility_sql_df['LabFacilityModified'] = pd.to_datetime('now')

    # Add the lab_facility_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        lab_facility_sql_df.to_sql('LabFacilities', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {lab_facility_sql_df.shape[0]} lab facilities')


    print('Importing instruments')

    # Create the Instruments table
    instrument_sql_df = pd.DataFrame(columns=table_properties['Instruments'])
    instrument_sql_df['InstrumentName'] = sample_df['Spectrometer Model']
    instrument_sql_df.dropna(axis=0, how='all', inplace=True)
    instrument_sql_df.drop_duplicates(inplace=True)
    instrument_sql_df.reset_index(drop=True, inplace=True)
    instrument_sql_df['InstrumentID'] = pd.Series(list(range(1, instrument_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    instrument_sql_df['InstrumentCreated'] = pd.to_datetime('now')
    instrument_sql_df['InstrumentModified'] = pd.to_datetime('now')

    # Add the instrument_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        instrument_sql_df.to_sql('Instruments', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {instrument_sql_df.shape[0]} instruments')

    print(f'Importing UPb analysis contexts')
    # Create the UPbAnalysisContexts table
    upb_analysis_context_sql_df = pd.DataFrame(columns=table_properties['UPbAnalysisContexts'])
    # Create a parent "ConcordanceClasses" context and children from "Concordance class 1" to "Concordance class 7"
    # Create a parent "Recalculated" context and children "238U/235U=137.818" and "non-iterative age model"
    # Create metamorphic and non-metamorphic contexts
    upb_context_dict = {'UPbAnalysisContextName': ['Recalculated', '238U/235U=137.818', 'non-iterative age model',
                                                   'ConcordanceClasses', 'Concordance class 1',
                                                   'Concordance class 2', 'Concordance class 3',
                                                   'Concordance class 4', 'Concordance class 5',
                                                   'Concordance class 6', 'Concordance class 7',
                                                   'Metamorphic', 'Non-metamorphic'],
                        'ParentUPbAnalysisContextID': [None, 1, 1, None, 4, 4, 4, 4, 4, 4, 4, None, None],
                        'UPbAnalysisContextParentRow': [0, 0, 1, 1, 0, 1, 2, 3, 4, 5, 6, 2, 3],
                        'UPbAnalysisContextDescription': ['U-Pb data are recalculated from the original reference',
                                                          '207Pb/235U age recalculated using 238U/235U = 137.818',
                                                          'Best age calculated using the non-iterative age model',
                                                          'Concordance classifications for minimum segmented discordance using on quartiles',
                                                          'Most concordant', '', '', '', '', '', 'Least concordant',
                                                          'Analyzed material is determined to be metamorphic',
                                                          'Analyzed material is determined to be non-metamorphic']
                        }
    upb_analysis_context_sql_df['UPbAnalysisContextName'] = upb_context_dict['UPbAnalysisContextName']
    upb_analysis_context_sql_df['ParentUPbAnalysisContextID'] = pd.Series(
        upb_context_dict['ParentUPbAnalysisContextID'], dtype=pd.Int64Dtype())
    upb_analysis_context_sql_df['UPbAnalysisContextParentRow'] = pd.Series(
        upb_context_dict['UPbAnalysisContextParentRow'], dtype=pd.Int64Dtype())
    upb_analysis_context_sql_df['UPbAnalysisContextID'] = pd.Series(
        list(range(1, upb_analysis_context_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    upb_analysis_context_sql_df['UPbAnalysisContextDescription'] = upb_context_dict['UPbAnalysisContextDescription']
    upb_analysis_context_sql_df['UPbAnalysisContextCreated'] = pd.to_datetime('now')
    upb_analysis_context_sql_df['UPbAnalysisContextModified'] = pd.to_datetime('now')

    # Add the upb_analysis_context_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        upb_analysis_context_sql_df.to_sql('UPbAnalysisContexts', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {upb_analysis_context_sql_df.shape[0]} UPb analysis contexts')


    # --------------------
    # Import the U-Pb data from Puetz et al. (2024) into the database file.
    # --------------------
    print('Loading U-Pb data sheet')
    start_time = time.time()
    sheet_name = 'UPb_Data'
    # try:
    #     upb_analysis_df = pd.read_excel(full_data, sheet_name=sheet_name, engine="openpyxl")
    # except Exception as e:
    #     print(f"Failed to parse sheet with pandas:\n{e}")
    #     return
    upb_dfs = []
    for file in data_files:
        print(f'Loading {file}')
        try:
            data_df = pd.read_excel(file, sheet_name=sheet_name, engine="openpyxl", dtype={'Sample&Grain': str})
        except Exception as e:
            print(f"Failed to parse sheet with pandas:\n{e}")
            return
        upb_dfs.append(data_df)
        print(f'Loaded {file}')
    # Concatenate all the data frames into one
    upb_analysis_df = pd.concat(upb_dfs, ignore_index=True)
    # Drop empty rows and remove excess white space
    while not upb_analysis_df.empty and upb_analysis_df.iloc[0].isna().all():
        upb_analysis_df = upb_analysis_df.iloc[1:].reset_index(drop=True)
    upb_analysis_df = upb_analysis_df.map(strip_strings)
    print(f'Loaded U-Pb data in {time.time() - start_time} seconds')

    # Define the constant IDs
    ratio_error_format = 1  # 1σ absolute
    age_error_format = 2  # 2σ absolute
    age_unit_id = 2  # Ma
    spot_composition_id = 1  # zircon
    spot_size_unit_id = 5  # μm
    concordance_format_id = 5

    # Before we change the grain names for duplicate data, merge DB7 (concordant non-metamorphic cores) and
    # DB12 (concordant metamorphic cores) to define non-metamorphic and metamorphic contexts

    db7_data = '/Users/kametcalf/Documents/Research/Geochronology_Code/testing/DB7_nonmetamorphic_cores.xlsx'
    print('Loading DB7 data')
    start_time = time.time()
    sheet_name = 'UPb_Data'
    try:
        upb_db7_df = pd.read_excel(db7_data, sheet_name=sheet_name, engine="openpyxl", dtype={'Sample&Grain': str})
    except Exception as e:
        print(f"Failed to parse sheet with pandas:\n{e}")
        return
    # Drop empty rows and remove excess white space
    while not upb_db7_df.empty and upb_db7_df.iloc[0].isna().all():
        upb_db7_df = upb_db7_df.iloc[1:].reset_index(drop=True)
    upb_db7_df = upb_db7_df.map(strip_strings)
    print(f'Loaded DB7 data in {time.time() - start_time} seconds')

    db12_data = '/Users/kametcalf/Documents/Research/Geochronology_Code/testing/DB12_metamorphic_cores.xlsx'
    print('Loading DB12 data')
    start_time = time.time()
    sheet_name = 'UPb_Data'
    try:
        upb_db12_df = pd.read_excel(db12_data, sheet_name=sheet_name, engine="openpyxl", dtype={'Sample&Grain': str})
    except Exception as e:
        print(f"Failed to parse sheet with pandas:\n{e}")
        return
    # Drop empty rows and remove excess white space
    while not upb_db12_df.empty and upb_db12_df.iloc[0].isna().all():
        upb_db12_df = upb_db12_df.iloc[1:].reset_index(drop=True)
    upb_db12_df = upb_db12_df.map(strip_strings)
    print(f'Loaded DB12 data in {time.time() - start_time} seconds')

    db11_data = '/Users/kametcalf/Documents/Research/Geochronology_Code/testing/DB11_rims.xlsx'
    print('Loading DB11 data')
    start_time = time.time()
    sheet_name = 'UPb_Data'
    try:
        upb_db11_df = pd.read_excel(db11_data, sheet_name=sheet_name, engine="openpyxl", dtype={'Sample&Grain': str})
    except Exception as e:
        print(f"Failed to parse sheet with pandas:\n{e}")
        return
    # Drop empty rows and remove excess white space
    while not upb_db11_df.empty and upb_db11_df.iloc[0].isna().all():
        upb_db11_df = upb_db11_df.iloc[1:].reset_index(drop=True)
    upb_db11_df = upb_db11_df.map(strip_strings)
    print(f'Loaded DB11 data in {time.time() - start_time} seconds')

    nonmetamorphic_df = pd.DataFrame(columns=['Sample&Grain', 'Non-Iter. Probability age (Ma)', 'Metamorphic'])
    nonmetamorphic_df['Sample&Grain'] = upb_db7_df['Sample&Grain']
    nonmetamorphic_df['Non-Iter. Probability age (Ma)'] = upb_db7_df['Non-Iter. Probability age (Ma)']
    nonmetamorphic_df['Metamorphic'] = 'Non-metamorphic'

    metamorphic_df = pd.DataFrame(columns=['Sample&Grain', 'Non-Iter. Probability age (Ma)', 'Metamorphic'])
    metamorphic_df['Sample&Grain'] = upb_db12_df['Sample&Grain']
    metamorphic_df['Non-Iter. Probability age (Ma)'] = upb_db12_df['Non-Iter. Concord age (Ma)']
    metamorphic_df['Metamorphic'] = 'Metamorphic'

    core_df = pd.concat([nonmetamorphic_df, metamorphic_df], ignore_index=True)
    core_df = core_df.reset_index(drop=True)
    core_df.dropna(axis=0, how='all', inplace=True)
    core_df['Core'] = ['core'] * core_df.shape[0]

    rim_df = pd.DataFrame(columns=['Sample&Grain', 'Non-Iter. Probability age (Ma)', 'Rim'])
    rim_df['Sample&Grain'] = upb_db11_df['Sample&Grain']
    rim_df['Non-Iter. Probability age (Ma)'] = upb_db11_df['Non-Iter. Prob. age (Ma)']
    rim_df['Rim'] = ['rim'] * rim_df.shape[0]

    upb_analysis_df = upb_analysis_df.merge(core_df, on=['Sample&Grain', 'Non-Iter. Probability age (Ma)'], how='left')
    upb_analysis_df = upb_analysis_df.merge(rim_df, on=['Sample&Grain', 'Non-Iter. Probability age (Ma)'], how='left')


    print('Checking for grain duplicates')
    # Identify duplicate grain names
    upb_analysis_sql_df = pd.DataFrame(columns=table_properties['UPbAnalyses'])
    spot_sql_df = pd.DataFrame(columns=table_properties['Spots'])
    upb_analysis_df = edit_duplicate_grain_name(upb_analysis_df)
    try:
        if upb_analysis_df.empty:
            return
    except Exception as e:
        return

    # Add basic/constant information to the UPbAnalyses and Spots tables
    spot_sql_df['SpotName'] = upb_analysis_df['Sample&Grain']
    spot_sql_df['SpotID'] = pd.Series(list(range(1, spot_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    upb_analysis_df['SpotID'] = pd.Series(list(range(1, spot_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    upb_analysis_sql_df['SpotID'] = pd.Series(list(range(1, upb_analysis_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    upb_analysis_sql_df['UPbAnalysisID'] = pd.Series(list(range(1, upb_analysis_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    upb_analysis_sql_df['RatioErrorFormatID'] = pd.Series([ratio_error_format]*upb_analysis_df.shape[0], dtype=pd.Int64Dtype())
    upb_analysis_sql_df['AgeErrorFormatID'] = pd.Series([age_error_format]*upb_analysis_df.shape[0], dtype=pd.Int64Dtype())
    upb_analysis_sql_df['AgeUnitID'] = pd.Series([age_unit_id]*upb_analysis_df.shape[0], dtype=pd.Int64Dtype())
    upb_analysis_sql_df['SpotSizeUnitID'] = pd.Series([spot_size_unit_id]*upb_analysis_df.shape[0], dtype=pd.Int64Dtype())
    upb_analysis_sql_df['ConcordanceFormatID'] = pd.Series([concordance_format_id]*upb_analysis_df.shape[0], dtype=pd.Int64Dtype())

    # Map analyses back to samples
    sample_to_analysis = merged_sample_id_df[['Ref-Sample Key', 'Sample_ID', 'SampleID', 'Mass Spectrometer',
                                              'Spectrometer Location', 'Institution', 'Spectrometer Model']]
    merged_sample_analysis_df = upb_analysis_df.merge(sample_to_analysis, on='Ref-Sample Key', how='left')
    spot_sql_df['AliquotID'] = merged_sample_analysis_df['SampleID']
    spot_sql_df['SpotCompositionID'] = spot_composition_id
    spot_sql_df['SpotCreated'] = pd.to_datetime('now')
    spot_sql_df['SpotModified'] = pd.to_datetime('now')

    # Add the spot_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        spot_sql_df.to_sql('Spots', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {spot_sql_df.shape[0]} spots')


    print(f'Importing spot contexts')

    # Create the SpotContext table
    spot_context_sql_df = pd.DataFrame(columns=table_properties['SpotContexts'])
    upb_analysis_df['Spot'] = upb_analysis_df['Spot'].str.lower()
    spot_context_names = upb_analysis_df['Spot'].unique()
    spot_context_sql_df['SpotContextName'] = spot_context_names
    spot_context_sql_df.dropna(axis=0, how='all', inplace=True)
    spot_context_sql_df.drop_duplicates(inplace=True)
    spot_context_sql_df.reset_index(drop=True, inplace=True)
    spot_context_sql_df['SpotContextID'] = pd.Series(list(range(1, spot_context_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    # All are core, rim, or blank, so no nesting. Just count parent row up from zero
    spot_context_sql_df['SpotContextParentRow'] = pd.Series(list(range(spot_context_sql_df.shape[0])))
    spot_context_sql_df['SpotContextCreated'] = pd.to_datetime('now')
    spot_context_sql_df['SpotContextModified'] = pd.to_datetime('now')

    # Add the spot_context_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        spot_context_sql_df.to_sql('SpotContexts', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {spot_context_sql_df.shape[0]} spot contexts')


    print('Connecting spots and spot contexts')

    # Make sure that the values in Spots agree with the values in Cores and Rims
    conflicting_filled_df = upb_analysis_df[((upb_analysis_df['Spot'] == 'core') & (upb_analysis_df['Rim'] == 'rim')) |
                                            ((upb_analysis_df['Spot'] == 'rim') & (upb_analysis_df['Core'] == 'core'))]
    conflicting_null_df = upb_analysis_df[(upb_analysis_df['Spot'].isnull()) & ((upb_analysis_df['Core'].notnull()) |
                                                                              (upb_analysis_df['Rim'].notnull()))]
    if not conflicting_filled_df.empty:
        print('Warning: Cores/Rims in DB7, DB11, DB12 do not match Spots column')
        print(conflicting_filled_df[['Spot', 'Core', 'Rim']])
        return
    if not conflicting_null_df.empty:
        print('Warning: Cores/Rims in DB7, DB11, DB12 but not in Spots column')
        print(conflicting_null_df[['Spot', 'Core', 'Rim']])
        return

    # Create the Spots_SpotContexts table
    spots_spot_contexts_sql_df = pd.DataFrame(columns=table_properties['Spots_SpotContexts'])
    merged_spot_context_df = upb_analysis_df.merge(spot_context_sql_df, left_on=['Spot'], right_on=['SpotContextName'], how='left')
    spots_spot_contexts_sql_df['SpotID'] = pd.Series(merged_spot_context_df['SpotID'], dtype=pd.Int64Dtype())
    spots_spot_contexts_sql_df['SpotContextID'] = pd.Series(merged_spot_context_df['SpotContextID'], dtype=pd.Int64Dtype())
    spots_spot_contexts_sql_df['Spots_SpotContextCreated'] = pd.to_datetime('now')
    spots_spot_contexts_sql_df['Spots_SpotContextModified'] = pd.to_datetime('now')
    spots_spot_contexts_sql_df.dropna(axis=0, how='any', inplace=True)
    spots_spot_contexts_sql_df.drop_duplicates(inplace=True)
    spots_spot_contexts_sql_df.reset_index(drop=True, inplace=True)

    # Add the spots_spot_contexts_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        spots_spot_contexts_sql_df.to_sql('Spots_SpotContexts', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {spots_spot_contexts_sql_df.shape[0]} spot-spot context links')


    print(f'Connecting UPb analyses and contexts')
    # Create the UPbAnalyses_UPbAnalysisContexts table
    upb_analyses_upb_analysis_contexts_sql_df = pd.DataFrame(columns=table_properties['UPbAnalyses_UPbAnalysisContexts'])
    # All analyses get both recalculated tags
    upb_analysis_ids = list(range(1, upb_analysis_df.shape[0] + 1))
    upb_ids =  upb_analysis_ids * 6
    upb_analysis_df['UPbAnalysisContextName'] = upb_analysis_df['Concord Class'].apply(lambda x: f"Concordance class {x}" if x !='' else '')
    merged_concordance_class_df = upb_analysis_df.merge(upb_analysis_context_sql_df, on=['UPbAnalysisContextName'], how='left')
    met_merged_context_df = upb_analysis_df.merge(upb_analysis_context_sql_df, left_on=['Metamorphic'], right_on=['UPbAnalysisContextName'], how='left')
    core_merged_context_df = upb_analysis_df.merge(upb_analysis_context_sql_df, left_on=['Core'], right_on=['UPbAnalysisContextName'], how='left')
    rim_merged_context_df = upb_analysis_df.merge(upb_analysis_context_sql_df, left_on=['Rim'], right_on=['UPbAnalysisContextName'], how='left')
    upb_analysis_df['Rejected'] = upb_analysis_df['Concord Class'].apply(lambda x: 0 if x<4 else 1)
    recalculated_ratio_context_ids = [2]*upb_analysis_df.shape[0]
    recalculated_non_it_context_ids = [3]*upb_analysis_df.shape[0]
    concordance_context_ids = list(merged_concordance_class_df['UPbAnalysisContextID'])
    met_context_ids = list(met_merged_context_df['UPbAnalysisContextID'])
    core_context_ids = list(core_merged_context_df['UPbAnalysisContextID'])
    rim_context_ids = list(rim_merged_context_df['UPbAnalysisContextID'])
    upb_context_ids = (recalculated_ratio_context_ids + recalculated_non_it_context_ids + concordance_context_ids +
                       met_context_ids + core_context_ids + rim_context_ids)
    upb_analyses_upb_analysis_contexts_sql_df['UPbAnalysisID'] = pd.Series(upb_ids, dtype=pd.Int64Dtype())
    upb_analyses_upb_analysis_contexts_sql_df['UPbAnalysisContextID'] = pd.Series(upb_context_ids, dtype=pd.Int64Dtype())
    upb_analyses_upb_analysis_contexts_sql_df['UPbAnalyses_UPbAnalysisContextCreated'] = pd.to_datetime('now')
    upb_analyses_upb_analysis_contexts_sql_df['UPbAnalyses_UPbAnalysisContextModified'] = pd.to_datetime('now')
    upb_analyses_upb_analysis_contexts_sql_df.dropna(axis=0, how='any', inplace=True)
    upb_analyses_upb_analysis_contexts_sql_df.drop_duplicates(inplace=True)
    upb_analyses_upb_analysis_contexts_sql_df.reset_index(drop=True, inplace=True)

    # Add the upb_analyses_upb_analysis_contexts_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        upb_analyses_upb_analysis_contexts_sql_df.to_sql('UPbAnalyses_UPbAnalysisContexts', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {upb_analyses_upb_analysis_contexts_sql_df.shape[0]} UPb analysis-context links')


    print('Set up UPb data')

    # Add the reference
    upb_analysis_df['Ref No.'] = upb_analysis_df['Ref-Sample Key'].apply(lambda x: x.split('-')[0])
    merged_upb_reference_df = upb_analysis_df.merge(merged_reference_id_df, on='Ref No.', how='left')
    upb_analysis_sql_df['ReferenceID'] = pd.Series(merged_upb_reference_df['ReferenceID'], dtype=pd.Int64Dtype())

    # Add the lab facility
    merged_upb_lab_facility_df = merged_sample_analysis_df.merge(lab_facility_sql_df, left_on='Spectrometer Location',
                                                                 right_on='LabFacilityName', how='left')
    upb_analysis_sql_df['LabFacilityID'] = pd.Series(merged_upb_lab_facility_df['LabFacilityID'], dtype=pd.Int64Dtype())

    # Add the instrument
    merged_upb_instrument_df = merged_sample_analysis_df.merge(instrument_sql_df, left_on='Spectrometer Model',
                                                               right_on='InstrumentName', how='left')
    upb_analysis_sql_df['InstrumentID'] = pd.Series(merged_upb_instrument_df['InstrumentID'], dtype=pd.Int64Dtype())

    # Add the analysis method
    merged_analysis_method_df = merged_sample_analysis_df.merge(analysis_method_sql_df, left_on='Mass Spectrometer',
                                                                right_on='UPbAnalysisMethodName', how='left')
    upb_analysis_sql_df['UPbAnalysisMethodID'] = pd.Series(merged_analysis_method_df['UPbAnalysisMethodID'], dtype=pd.Int64Dtype())

    upb_analysis_sql_df['SpotSize'] = upb_analysis_df['Spot diam. (μm)']
    upb_analysis_sql_df['Rejected'] = upb_analysis_df['Rejected']
    upb_analysis_sql_df['206Pb/238U'] = upb_analysis_df['206Pb/238U      ratio']
    upb_analysis_sql_df['206Pb/238UError'] = upb_analysis_df['206Pb/238U            1σ uncert']
    upb_analysis_sql_df['207Pb/235U'] = upb_analysis_df['calculated 207Pb/235U      ratio']
    upb_analysis_sql_df['207Pb/235UError'] = upb_analysis_df['207Pb/235U            1σ uncert']
    upb_analysis_sql_df['207Pb/206Pb'] = upb_analysis_df['207Pb/206Pb      ratio']
    upb_analysis_sql_df['207Pb/206PbError'] = upb_analysis_df['207Pb/206Pb            1σ uncert']
    upb_analysis_sql_df['ErrorCorr/Rho'] = upb_analysis_df['Rho (calc.)']
    upb_analysis_sql_df['206Pb/238UAge'] = upb_analysis_df['Calc 206Pb/238U age (Ma)']
    upb_analysis_sql_df['206Pb/238UAgeError'] = upb_analysis_df['Calc 206Pb/238U             2σ uncert']
    upb_analysis_sql_df['207Pb/235UAge'] = upb_analysis_df['Calc 207Pb/235U age (Ma)']
    upb_analysis_sql_df['207Pb/235UAgeError'] = upb_analysis_df['Calc 207Pb/235U             2σ uncert']
    upb_analysis_sql_df['207Pb/206PbAge'] = upb_analysis_df['Calc 207Pb/206Pb age (Ma)']
    upb_analysis_sql_df['207Pb/206PbAgeError'] = upb_analysis_df['Calc 207Pb/206Pb             2σ uncert']
    upb_analysis_sql_df['BestAge'] = upb_analysis_df['Non-Iter. Probability age (Ma)']
    upb_analysis_sql_df['BestAgeError'] = upb_analysis_df['Non iterative           2σ uncert']
    upb_analysis_sql_df['Concordance'] = upb_analysis_df['Min. Seg. Disc.']
    upb_analysis_sql_df['UPbAnalysisCreated'] = pd.to_datetime('now')
    upb_analysis_sql_df['UPbAnalysisModified'] = pd.to_datetime('now')

    # Should have all the U-Pb analysis data collected now
    # Add the upb_analysis_sql_df to the database
    try:
        conn = sqlite3.connect(db)
        upb_analysis_sql_df.to_sql('UPbAnalyses', conn, if_exists='replace', index=False)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return

    print(f'Imported {upb_analysis_sql_df.shape[0]} U-Pb analyses')



if __name__ == "__main__":
    Puetz_importer()
