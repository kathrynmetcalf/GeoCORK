import pandas as pd
import numpy as np
import openpyxl
import sqlite3
import re
import time

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
    :param sample_df: data frame with sample names and Ref-Sample Key
    :param reference_dict_df: reference dictionary data frame with columns ReferenceNumber and ReferenceID
    :param reference_sql_df: reference sql data frame, the Reference table in the sql database
    """

    # Identify duplicate sample names\
    counts = sample_df['Sample_ID'].value_counts()
    duplicates = counts[counts > 1]
    if not duplicates.any():
        return sample_df
    print(f'Duplicate sample names found: {duplicates.sum()}')
    duplicates_df = sample_df['Sample_ID'].duplicated(keep=False)

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
        reference_number = ref_sample_key.split('-')[0]
        # Get the reference ID from the reference_dict_df
        reference_id = reference_dict_df[reference_number]
        # Get the Author and Year from the reference_sql_df
        author = reference_sql_df[reference_sql_df['ReferenceID'] == reference_id]['Authors']
        author = list(author)[0]
        year = reference_sql_df[reference_sql_df['ReferenceID'] == reference_id]['Year']
        year = list(year)[0]
        edited_sample_name = f'{sample_name}: {author}, {year}'
        return edited_sample_name

    # Apply the edit_name function to the sample_df
    sample_df.loc[duplicates, 'Sample_ID'] = sample_df.loc[duplicates].apply(edit_name, axis=1)

    return sample_df

def edit_duplicate_grain_name(upb_analysis_df):
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
        edited_name = f"{grain_name}: {name_count[grain_name]}"

        return edited_name

    # Apply the edit_name function to the upb_analysis_df
    upb_analysis_df.loc[duplicates_df, 'Sample&Grain'] = upb_analysis_df.loc[duplicates_df].apply(edit_name, axis=1)

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
    full_data = '/Users/kametcalf/Downloads/DB1_2019_edited.xlsx'
    # full_data = '/Users/kametcalf/Downloads/DB2_2021_edited.xlsx'
    # full_data = '/Users/kametcalf/Downloads/DB3_2023_edited.xlsx'
    db = '/Users/kametcalf/Documents/Research/GeoChron_non_git/Puetz_et_al_2024_1.db'
    # db = '/Users/kametcalf/Documents/Research/GeoChron_non_git/Puetz_et_al_2024_2.db'
    # db = '/Users/kametcalf/Documents/Research/GeoChron_non_git/Puetz_et_al_2024_3.db'
    ref_sample_dict = {}
    sample_analysis_tags_dict = {}

    # --------------------
    # Get the headers for the tables to import into the database
    tables = ['"References"', 'Samples', 'Aliquots', 'Spots', 'UPbAnalyses', 'UPbAnalysisMethods', 'LabFacilities', 'Instruments',
                'Units', 'Regions', 'RockTypes', 'SpotCompositions', 'SampleAges', 'GPSLocations', 'Columns', 'Samples_Regions',
                'Samples_RockTypes', 'Samples_SampleAges', 'Samples_Units', 'Spots_SpotContexts']
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

    # # --------------------
    # # Import the references from Puetz et al. (2024) into the database file.
    # # --------------------
    # print('Importing references')
    # start_time = time.time()
    # sheet_name = 'References'
    # try:
    #     reference_df = pd.read_excel(full_data, sheet_name=sheet_name, engine="openpyxl")
    # except Exception as e:
    #     print(f"Failed to parse sheet with pandas:\n{e}")
    #     return
    # # Drop empty rows and remove excess white space
    # while not reference_df.empty and reference_df.iloc[0].isna().all():
    #     reference_df = reference_df.iloc[1:].reset_index(drop=True)
    # reference_df = reference_df.map(strip_strings)
    # rows, cols = reference_df.shape
    # print(f'Loaded References in {time.time() - start_time} seconds')
    #
    # reference_sql_df = pd.DataFrame(columns=table_properties['"References"'])
    # reference_sql_df['Authors'] = reference_df['Lead_Author']
    # reference_sql_df['Year'] = reference_df['Year']
    # reference_sql_df['Title'] = reference_df['Title']
    # reference_sql_df['Source'] = reference_df['Journal']
    # reference_sql_df['DOI'] = reference_df['Web Link'].apply(lambda x: x.split('doi.org/')[1] if isinstance(x, str) and 'doi.org' in x else '')
    # # set all rows to the current time stamp for ReferenceCreated and ReferenceModified
    # reference_sql_df['ReferenceCreated'] = pd.to_datetime('now')
    # reference_sql_df['ReferenceModified'] = pd.to_datetime('now')
    # # create a list of values from 1 to the number of rows
    # reference_sql_df['ReferenceID'] = list(range(1, rows+1))
    #
    #
    # # create dictionary for reference number and reference id
    # reference_dict_df = dict(zip(reference_df['Ref No.'], reference_sql_df['ReferenceID']))
    #
    # # add the reference_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     reference_sql_df.to_sql('References', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # print(f'Imported {reference_df.shape[0]} references')
    #
    # # --------------------
    # # Import the samples from Puetz et al. (2024) into the database file.
    # # --------------------
    # print('Loading sample sheet')
    start_time = time.time()
    # sheet_name = 'Samples'
    # try:
    #     sample_df = pd.read_excel(full_data, sheet_name=sheet_name, engine="openpyxl")
    # except Exception as e:
    #     print(f"Failed to parse sheet with pandas:\n{e}")
    #     return
    # # Drop empty rows and remove excess white space
    # while not sample_df.empty and sample_df.iloc[0].isna().all():
    #     sample_df = sample_df.iloc[1:].reset_index(drop=True)
    # sample_df = sample_df.map(strip_strings)
    # print(f'Loaded Samples in {time.time() - start_time} seconds')
    #
    # gps_format_id = 1
    # age_unit_id = 2
    #
    # print('Checking for sample duplicates')
    # # Identify duplicate sample names
    # sample_sql_df = pd.DataFrame(columns=table_properties['Samples'])
    # sample_df = edit_duplicate_sample_name(sample_df, reference_dict_df, reference_sql_df)
    #
    # sample_sql_df['SampleName'] = sample_df['Sample_ID']
    # sample_sql_df['SampleID'] = pd.Series(list(range(1, sample_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    # merged_sample_id_df = sample_df.merge(sample_sql_df, left_on='Sample_ID', right_on='SampleName', how='left', indicator=True)
    #
    # print(f'{sample_sql_df.shape[0]} unique samples to import')
    #
    #
    # print('Importing GPS')
    # gps_sql_df = pd.DataFrame(columns=table_properties['GPSLocations'])
    #
    # # Check for duplicate GPS coordinate pairs
    # gps_sql_df['GPSLatDeg'] = sample_df['Latitude']
    # gps_sql_df['GPSLonDeg'] = sample_df['Longitude']
    # gps_sql_df.dropna(axis=0, how='all', inplace=True)
    # gps_sql_df.drop_duplicates(inplace=True)
    # gps_sql_df.reset_index(drop=True, inplace=True)
    #
    # gps_sql_df['GPSLocationID'] = pd.Series(list(range(1, gps_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    # gps_sql_df['GPSFormatID'] = pd.Series(gps_format_id, dtype=pd.Int64Dtype())
    # gps_sql_df['GPSLocationCreated'] = pd.to_datetime('now')
    # gps_sql_df['GPSLocationModified'] = pd.to_datetime('now')
    #
    # # Add the GPSLocationID as a foreign key to samples_sql_df
    # merged_gps_df = merged_sample_id_df.merge(gps_sql_df, left_on=['Latitude', 'Longitude'], right_on=['GPSLatDeg', 'GPSLonDeg'], how='left')
    # if merged_gps_df['GPSLocationID'].isnull().any():
    #     duplicates = merged_gps_df[merged_sample_id_df['_merge'] == 'left_only']['Latitude', 'Longitude'].unique()
    #     expanded_gps_df = pd.concat([gps_sql_df[gps_sql_df['GPSLatDeg', 'GPSLonDeg'].isin(duplicates)] for _ in range(len(merged_sample_id_df))])
    #     merged_gps_df = merged_sample_id_df.merge(expanded_gps_df, left_on=['Latitude', 'Longitude'], right_on=['GPSLatDeg', 'GPSLonDeg'], how='left')
    # sample_sql_df['SampleGPSLocationID'] = pd.Series(merged_gps_df['GPSLocationID'], dtype=pd.Int64Dtype())
    #
    # # Add the gps_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     gps_sql_df.to_sql('GPSLocations', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # print(f'Imported {gps_sql_df.shape[0]} GPS coordinates')
    #
    #
    # print('Importing Columns')
    #
    # # Column name, height/depth, and height/depth unit are all in the same cell, so need to parse
    # # For each Column, the name is the whole thing or comes before ' at '
    # column_sql_df = pd.DataFrame(columns=table_properties['Columns'])
    # column_dict = {}
    # columns = sample_df['Column']
    # column_names = set()
    #
    # # Remove nan float values from each list
    # columns = [column for column in columns if pd.notnull(column)]
    # for column in columns:
    #     # Check if it ends with the pattern " at [0-9]+ m" or " at [0-9]+ ft" with or without a space
    #     pattern = r'(.*) at (\d+(?:-\d+)?) ?(m|ft)$'
    #     match = re.search(pattern, column)
    #     if match:
    #         # Extract the column, height/depth, and unit
    #         column_name = match.group(1)
    #         height_depth = float(match.group(2))
    #         unit = match.group(3)
    #         # Convert units to unit IDs
    #         if unit == 'm':
    #             unit_id = 2
    #         elif unit == 'ft':
    #             unit_id = 8
    #         else:
    #             print(f"Unknown unit: {unit} for column {column_name}")
    #             continue
    #     else:
    #         # If the pattern doesn't match, just use the column name and set depth to None
    #         column_name = column
    #         height_depth = None
    #         unit_id = None
    #     # Check if the column name is already in the dictionary
    #     if column_name not in column_names:
    #         column_names.add(column_name)
    #         # Add the column name, height/depth, and unit ID to the dictionary
    #         column_dict[column] = (column_name, height_depth, unit_id)
    #
    # column_sql_df['ColumnName'] = list(column_names)
    # column_sql_df['ColumnID'] = pd.Series(list(range(1, len(column_names) + 1)), dtype=pd.Int64Dtype())
    # column_sql_df['ColumnCreated'] = pd.to_datetime('now')
    # column_sql_df['ColumnModified'] = pd.to_datetime('now')
    #
    # # Add the column_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     column_sql_df.to_sql('Columns', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # # Add the column information to sample_sql_df
    # column_names_df = pd.DataFrame.from_dict(column_dict, orient='index')
    # column_names_df.reset_index(inplace=True)
    # column_names_df.rename(columns={'index': 'OriginalColumnName', 0: 'ColumnName', 1: 'Height_Depth', 2: 'Height_Depth_UnitID'}, inplace=True)
    #
    # merged_columns_df = sample_df.merge(column_names_df, left_on=['Column'], right_on=['OriginalColumnName'], how='left')
    # merged_columns_df = merged_columns_df.merge(column_sql_df, left_on=['ColumnName'], right_on=['ColumnName'], how='left')
    #
    # sample_sql_df['SampleColumnID'] = pd.Series(merged_columns_df['ColumnID'], dtype=pd.Int64Dtype())
    # sample_sql_df['HeightDepth'] = merged_columns_df['Height_Depth']
    # sample_sql_df['HeightDepthUnitID'] = pd.Series(merged_columns_df['Height_Depth_UnitID'], dtype=pd.Int64Dtype())
    #
    # print(f'Imported {column_sql_df.shape[0]} columns')
    #
    # print('Importing sample ages')
    #
    # sample_ages_sql_df = pd.DataFrame(columns=table_properties['SampleAges'])
    #
    # # Look for unique sample ages
    # sample_ages_sql_df['OldestDirectAge'] = sample_df['Max. Stratigraphic Age (Ma)']
    # sample_ages_sql_df['YoungestDirectAge'] = sample_df['Min. Stratigraphic Age (Ma)']
    # sample_ages_sql_df['DirectAge'] = sample_df['Est. Stratigraphic Age (Ma)']
    # sample_ages_sql_df.dropna(axis=0, how='all', inplace=True)
    # sample_ages_sql_df.drop_duplicates(inplace=True)
    # sample_ages_sql_df.reset_index(drop=True, inplace=True)
    #
    # sample_ages_sql_df['SampleAgeID'] = pd.Series(list(range(1, sample_ages_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    # sample_ages_sql_df['DirectAgeUnitID'] = pd.Series(age_unit_id, dtype=pd.Int64Dtype())
    # sample_ages_sql_df['SampleAgeCreated'] = pd.to_datetime('now')
    # sample_ages_sql_df['SampleAgeModified'] = pd.to_datetime('now')
    #
    # merged_age_df = merged_sample_id_df.merge(sample_ages_sql_df,
    #                             left_on=['Max. Stratigraphic Age (Ma)', 'Min. Stratigraphic Age (Ma)',
    #                                      'Est. Stratigraphic Age (Ma)'],
    #                             right_on=['OldestDirectAge', 'YoungestDirectAge', 'DirectAge'], how='left')
    #
    # samples_sample_ages_sql_df = pd.DataFrame(columns=table_properties['Samples_SampleAges'])
    # samples_sample_ages_sql_df['SampleID'] = pd.Series(merged_age_df['SampleID'], dtype=pd.Int64Dtype())
    # samples_sample_ages_sql_df['SampleAgeID'] = pd.Series(merged_age_df['SampleAgeID'], dtype=pd.Int64Dtype())
    # samples_sample_ages_sql_df['Samples_SampleAgesCreated'] = pd.to_datetime('now')
    # samples_sample_ages_sql_df['Samples_SampleAgesModified'] = pd.to_datetime('now')
    # samples_sample_ages_sql_df.dropna(axis=0, how='any', inplace=True)
    # samples_sample_ages_sql_df.drop_duplicates(inplace=True)
    # samples_sample_ages_sql_df.reset_index(drop=True, inplace=True)
    #
    # # Add the sample_ages_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     sample_ages_sql_df.to_sql('SampleAges', conn, if_exists='replace', index=False)
    #     samples_sample_ages_sql_df.to_sql('Samples_SampleAges', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # print(f'Imported {sample_ages_sql_df.shape[0]} sample ages')
    #
    #
    # # Set default age for samples
    # # Check if they have the same number of rows and can be just dropped into the database, they should
    # if samples_sample_ages_sql_df.shape[0] == sample_sql_df.shape[0]:
    #     sample_sql_df['DefaultSampleAgeID'] = pd.Series(samples_sample_ages_sql_df['SampleAgeID'], dtype=pd.Int64Dtype())
    # else:
    #     print(f'Samples table has {sample_sql_df.shape[0]} samples and Samples_SampleAge table has {samples_sample_ages_sql_df.shape[0]} samples')
    #     return
    #
    # # Everything should now be in the Samples table, so it is ready for import
    # sample_sql_df['SampleCreated'] = pd.to_datetime('now')
    # sample_sql_df['SampleModified'] = pd.to_datetime('now')
    # try:
    #     conn = sqlite3.connect(db)
    #     sample_sql_df.to_sql('Samples', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # print(f'Imported {sample_sql_df.shape[0]} samples')
    #
    #
    # print('Importing regions')
    # region_sql_df = pd.DataFrame(columns=table_properties['Regions'])
    #
    # # Find any instances where a region name is in multiple columns
    # duplicates_df = sample_df.map(lambda x: x.strip().lower() if isinstance(x, str) else x)
    # duplicates = set()
    # region_columns = ['Continent', 'Large Regions', 'Country/Small Region', 'Locality']
    # for i in range(len(region_columns)):
    #     for j in range(i + 1, len(region_columns)):
    #         col1, col2 = region_columns[i], region_columns[j]
    #         duplicates.update(duplicates_df[col1] [duplicates_df[col1].isin(duplicates_df[col2])])
    # if len(list(duplicates)) > 0:
    #     # If there is only one duplicate of nan, continue
    #     if len(list(duplicates)) == 1 and pd.isna(list(duplicates)[0]):
    #         duplicates = set()
    #     else:
    #         print('Duplicate region names found:')
    #         print(list(duplicates))
    #         print('Please check the region names in the sample sheet.')
    #         return
    #
    # # If any region column is blank, fill with the value from the next one
    # shifted_region_df = sample_df[region_columns].apply(shift_left, axis=1)
    #
    # # append 'Continent', 'Large Regions', and 'Country/Small Region' into one 'RegionName' column
    # continent_names = list(shifted_region_df['Continent'].unique())
    # large_region_names = list(shifted_region_df['Large Regions'].unique())
    # country_names = list(sample_df['Country/Small Region'].unique())
    # locality_names = list(sample_df['Locality'].unique())
    # # Remove nan float values from each list
    # continent_names = [region for region in continent_names if pd.notnull(region)]
    # large_region_names = [region for region in large_region_names if pd.notnull(region)]
    # country_names = [region for region in country_names if pd.notnull(region)]
    # locality_names = [region for region in locality_names if pd.notnull(region)]
    # region_names = continent_names + large_region_names + country_names + locality_names
    # duplicates = []
    # distinct_names = set()
    # for region_name in region_names:
    #     if region_name in distinct_names:
    #         duplicates.append(region_name)
    #     else:
    #         distinct_names.add(region_name)
    # if len(list(duplicates)) > 0:
    #     # If there is only one duplicate of nan, continue
    #     if len(list(duplicates)) == 1 and pd.isna(list(duplicates)[0]):
    #         pass
    #     else:
    #         print('Duplicate region names found:')
    #         print(duplicates)
    #         print('Please check the region names in the sample sheet.')
    #         return
    #
    # # Check for children with multiple parents
    # multiple_parents = []
    # for large_region_name in large_region_names:
    #     if pd.isnull(large_region_name):
    #         continue
    #     # Get the continent values for the region name
    #     continent_values = shifted_region_df[shifted_region_df['Large Regions'] == large_region_name]['Continent'].unique()
    #     if len(continent_values) > 1:
    #         multiple_parents.append(large_region_name)
    # for country_name in country_names:
    #     if pd.isnull(country_name):
    #         continue
    #     # Get the large region values for the country
    #     large_region_values = shifted_region_df[shifted_region_df['Country/Small Region'] == country_name]['Large Regions'].unique()
    #     if len(large_region_values) > 1:
    #         multiple_parents.append(country_name)
    # for locality_name in locality_names:
    #     if pd.isnull(locality_name):
    #         continue
    #     # Get the country values for the locality
    #     country_values = shifted_region_df[shifted_region_df['Locality'] == locality_name]['Country/Small Region'].unique()
    #     if len(country_values) > 1:
    #         multiple_parents.append(locality_name)
    # if multiple_parents != []:
    #     print('Regions with multiple parents found:')
    #     print(multiple_parents)
    #     print('Please check the region names in the sample sheet.')
    #     return
    #
    # region_sql_df['RegionName'] = region_names
    # region_sql_df['RegionID'] = pd.Series(list(range(1, len(region_names) + 1)), dtype=pd.Int64Dtype())
    # region_dict_df = pd.DataFrame(columns=['RegionName', 'RegionID'])
    # region_dict_df['RegionName'] = region_sql_df['RegionName']
    # region_dict_df['RegionID'] = pd.Series(region_sql_df['RegionID'], dtype=pd.Int64Dtype())
    #
    # # Create dictionaries for the region names and their corresponding IDs
    # region_parent_id_dictionary = {}
    # region_parent_row_dictionary = {}
    #
    # shifted_region_df = sample_df[region_columns].apply(shift_left, axis=1)
    #
    # # For each unique 'Continent', find all the unique 'Large Region' values
    # continents = list(shifted_region_df['Continent'].unique())
    # for continent in continents:
    #     large_region_parent_id = region_sql_df.loc[region_sql_df['RegionName'] == continent, 'RegionID'].values[0]
    #     continent_parent_row = continents.index(continent)
    #     # Parent ID for top level is empty
    #     region_parent_id_dictionary[continent] = None
    #     region_parent_row_dictionary[continent] = continent_parent_row
    #     child_large_regions = list(shifted_region_df[shifted_region_df['Continent'] == continent]['Large Regions'].unique())
    #     for large_region in child_large_regions:
    #         if pd.isnull(large_region):
    #             continue
    #         country_small_region_parent_id = \
    #             region_sql_df.loc[region_sql_df['RegionName'] == large_region, 'RegionID'].values[0]
    #         if large_region != continent:
    #             large_region_parent_row = child_large_regions.index(large_region)
    #             region_parent_id_dictionary[large_region] = int(large_region_parent_id)
    #             region_parent_row_dictionary[large_region] = large_region_parent_row
    #         child_country_small_regions = list(
    #             shifted_region_df[(shifted_region_df['Continent'] == continent) & (shifted_region_df['Large Regions'] ==
    #                large_region)]['Country/Small Region'].unique())
    #         for country_small_region in child_country_small_regions:
    #             if pd.isnull(country_small_region):
    #                 continue
    #             locality_parent_id = \
    #                 region_sql_df.loc[region_sql_df['RegionName'] == country_small_region, 'RegionID'].values[0]
    #             if country_small_region != large_region:
    #                 country_small_region_parent_row = child_country_small_regions.index(country_small_region)
    #                 region_parent_id_dictionary[country_small_region] = int(country_small_region_parent_id)
    #                 region_parent_row_dictionary[country_small_region] = country_small_region_parent_row
    #             locality_regions = list(shifted_region_df[(shifted_region_df['Continent'] == continent) & (
    #                     shifted_region_df['Large Regions'] == large_region) & (shifted_region_df['Country/Small Region']
    #                                                                    == country_small_region)]['Locality'].unique())
    #             for locality_region in locality_regions:
    #                 if pd.isnull(locality_region):
    #                     continue
    #                 if locality_region != country_small_region:
    #                     locality_parent_row = locality_regions.index(locality_region)
    #                     region_parent_id_dictionary[locality_region] = int(locality_parent_id)
    #                     region_parent_row_dictionary[locality_region] = locality_parent_row
    #
    # # Add each dictionary to the appropriate column in regions_sql_df
    # region_sql_df['ParentRegionID'] = pd.Series(region_sql_df['RegionName'].map(region_parent_id_dictionary),dtype=pd.Int64Dtype())
    # region_sql_df['RegionParentRow'] = pd.Series(region_sql_df['RegionName'].map(region_parent_row_dictionary),dtype=pd.Int64Dtype())
    #
    # # Add the time stamps
    # region_sql_df['RegionCreated'] = pd.to_datetime('now')
    # region_sql_df['RegionModified'] = pd.to_datetime('now')
    #
    # # Add the region_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     region_sql_df.to_sql('Regions', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # print(f'Imported {region_sql_df.shape[0]} regions')
    #
    # # Create the Samples_Regions table
    # sample_region_sql_df = pd.DataFrame(columns=table_properties['Samples_Regions'])
    #
    # merged_continent_df = merged_sample_id_df.merge(region_sql_df, left_on=['Continent'], right_on=['RegionName'], how='left')
    # merged_large_region_df = merged_sample_id_df.merge(region_sql_df, left_on=['Large Regions'], right_on=['RegionName'], how='left')
    # merged_country_df = merged_sample_id_df.merge(region_sql_df, left_on=['Country/Small Region'], right_on=['RegionName'], how='left')
    # merged_locality_df = merged_sample_id_df.merge(region_sql_df, left_on=['Locality'], right_on=['RegionName'], how='left')
    # continents_selected = merged_continent_df[['SampleID', 'RegionID']]
    # large_regions_selected = merged_large_region_df[['SampleID', 'RegionID']]
    # countries_selected = merged_country_df[['SampleID', 'RegionID']]
    # localities_selected = merged_locality_df[['SampleID', 'RegionID']]
    # regions_combined_df = pd.concat([continents_selected, large_regions_selected, countries_selected, localities_selected], ignore_index=True)
    #
    # sample_region_sql_df['SampleID'] = pd.Series(regions_combined_df['SampleID'], dtype=pd.Int64Dtype())
    # sample_region_sql_df['RegionID'] = pd.Series(regions_combined_df['RegionID'], dtype=pd.Int64Dtype())
    # sample_region_sql_df['Samples_RegionsCreated'] = pd.to_datetime('now')
    # sample_region_sql_df['Samples_RegionsModified'] = pd.to_datetime('now')
    # sample_region_sql_df.dropna(axis=0, how='any', inplace=True)
    # sample_region_sql_df.drop_duplicates(inplace=True)
    # sample_region_sql_df.reset_index(drop=True, inplace=True)
    #
    # # Add the sample_region_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     sample_region_sql_df.to_sql('Samples_Regions', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # print(f'Imported {sample_region_sql_df.shape[0]} sample-region links')
    #
    #
    # print('Importing units')
    # unit_sql_df = pd.DataFrame(columns=table_properties['Units'])
    #
    # # Check for duplicate unit names
    # duplicates_df = sample_df.map(lambda x: x.strip().lower() if isinstance(x, str) else x)
    # duplicates = set()
    # unit_columns = ['Major Geographic-Geologic Description', 'Intermediate Geologic-Geographic Unit', 'Minor Geologic-Geographic Unit', 'Sub-Minor Geologic-Geographic Unit']
    # for i in range(len(unit_columns)):
    #     for j in range(i + 1, len(unit_columns)):
    #         col1, col2 = unit_columns[i], unit_columns[j]
    #         duplicates.update(duplicates_df[col1] [duplicates_df[col1].isin(duplicates_df[col2])])
    # if len(list(duplicates)) > 0:
    #     # If there is only one duplicate of nan, continue
    #     if len(list(duplicates)) == 1 and pd.isna(list(duplicates)[0]):
    #         pass
    #     else:
    #         print('Duplicate unit names found:')
    #         print(duplicates)
    #         print('Please check the unit names in the sample sheet.')
    #         return
    #
    # # If any unit column is blank, fill with the value from the next one
    # shifted_unit_df = sample_df[unit_columns].apply(shift_left, axis=1)
    #
    # # append 'Major Unit' and 'Minor Unit' into one 'UnitName' column
    # major_unit_names = list(shifted_unit_df['Major Geographic-Geologic Description'].unique())
    # intermediate_unit_names = list(shifted_unit_df['Intermediate Geologic-Geographic Unit'].unique())
    # minor_unit_names = list(shifted_unit_df['Minor Geologic-Geographic Unit'].unique())
    # sub_minor_unit_names = list(shifted_unit_df['Sub-Minor Geologic-Geographic Unit'].unique())
    # # Remove nan float values from each list
    # major_unit_names = [name for name in major_unit_names if pd.notnull(name)]
    # intermediate_unit_names = [name for name in intermediate_unit_names if pd.notnull(name)]
    # minor_unit_names = [name for name in minor_unit_names if pd.notnull(name)]
    # sub_minor_unit_names = [name for name in sub_minor_unit_names if pd.notnull(name)]
    # unit_names = major_unit_names + intermediate_unit_names + minor_unit_names + sub_minor_unit_names
    # duplicates = []
    # distinct_names = set()
    # for unit_name in unit_names:
    #     if unit_name in distinct_names:
    #         duplicates.append(unit_name)
    #     else:
    #         distinct_names.add(unit_name)
    # if len(list(duplicates)) > 0:
    #     # If there is only one duplicate of nan, continue
    #     if len(list(duplicates)) == 1 and pd.isna(list(duplicates)[0]):
    #         pass
    #     else:
    #         print('Duplicate unit names found:')
    #         print(list(duplicates))
    #         print('Please check the unit names in the sample sheet.')
    #         return
    #
    # # Check for children with multiple parents
    # multiple_parents = []
    # for intermediate_unit_name in intermediate_unit_names:
    #     if pd.isnull(intermediate_unit_name):
    #         continue
    #     # Get the major unit values for the intermediate unit
    #     major_unit_values = shifted_unit_df[shifted_unit_df['Intermediate Geologic-Geographic Unit'] == intermediate_unit_name]['Major Geographic-Geologic Description'].unique()
    #     if len(major_unit_values) > 1:
    #         multiple_parents.append(intermediate_unit_name)
    # for minor_unit_name in minor_unit_names:
    #     if pd.isnull(minor_unit_name):
    #         continue
    #     # Get the intermediate unit values for the minor unit
    #     intermediate_unit_values = shifted_unit_df[shifted_unit_df['Minor Geologic-Geographic Unit'] == minor_unit_name]['Intermediate Geologic-Geographic Unit'].unique()
    #     if len(intermediate_unit_values) > 1:
    #         multiple_parents.append(minor_unit_name)
    # for sub_minor_unit_name in sub_minor_unit_names:
    #     if pd.isnull(sub_minor_unit_name):
    #         continue
    #     # Get the minor unit values for the sub-minor unit
    #     minor_unit_values = shifted_unit_df[shifted_unit_df['Sub-Minor Geologic-Geographic Unit'] == sub_minor_unit_name]['Minor Geologic-Geographic Unit'].unique()
    #     if len(minor_unit_values) > 1:
    #         multiple_parents.append(sub_minor_unit_name)
    # if multiple_parents != []:
    #     print('Units with multiple parents found:')
    #     print(multiple_parents)
    #     print('Please check the unit names in the sample sheet.')
    #     return
    #
    # unit_sql_df['UnitName'] = unit_names
    # unit_sql_df['UnitID'] = pd.Series(list(range(1, len(unit_names) + 1)), dtype=pd.Int64Dtype())
    # unit_dict_df = pd.DataFrame(columns=['UnitName', 'UnitID'])
    # unit_dict_df['UnitName'] = unit_sql_df['UnitName']
    # unit_dict_df['UnitID'] = pd.Series(unit_sql_df['UnitID'], dtype=pd.Int64Dtype())
    #
    # # Create dictionaries for the unit names and their corresponding IDs
    # unit_parent_id_dictionary = {}
    # unit_parent_row_dictionary = {}
    #
    # # For each unique 'Major Unit', find all the unique 'Minor Unit' values
    # major_units = list(shifted_unit_df['Major Geographic-Geologic Description'].unique())
    # for major_unit in major_units:
    #     intermediate_unit_parent_id = unit_sql_df.loc[unit_sql_df['UnitName'] == major_unit, 'UnitID'].values[0]
    #     major_unit_parent_row = major_units.index(major_unit)
    #     # Check if the major unit is a key in the dictionary
    #     if major_unit not in unit_parent_id_dictionary:
    #         # Parent ID for top level is empty
    #         unit_parent_id_dictionary[major_unit] = None
    #         unit_parent_row_dictionary[major_unit] = major_unit_parent_row
    #     child_intermediate_units = list(shifted_unit_df[shifted_unit_df['Major Geographic-Geologic Description'] ==
    #                                                     major_unit]['Intermediate Geologic-Geographic Unit'].unique())
    #     for intermediate_unit in child_intermediate_units:
    #         if pd.isnull(intermediate_unit):
    #             continue
    #         minor_unit_parent_id = unit_sql_df.loc[unit_sql_df['UnitName'] == intermediate_unit, 'UnitID'].values[0]
    #         if intermediate_unit != major_unit:
    #             if intermediate_unit not in unit_parent_id_dictionary:
    #                 intermediate_unit_parent_row = child_intermediate_units.index(intermediate_unit)
    #                 unit_parent_id_dictionary[intermediate_unit] = intermediate_unit_parent_id
    #                 unit_parent_row_dictionary[intermediate_unit] = intermediate_unit_parent_row
    #         child_minor_units = list(shifted_unit_df[(shifted_unit_df['Major Geographic-Geologic Description'] == major_unit) & (
    #                 shifted_unit_df['Intermediate Geologic-Geographic Unit'] == intermediate_unit)]['Minor Geologic-Geographic Unit'].unique())
    #         for minor_unit in child_minor_units:
    #             if pd.isnull(minor_unit):
    #                 continue
    #             sub_minor_unit_parent_id = unit_sql_df.loc[unit_sql_df['UnitName'] == minor_unit, 'UnitID'].values[0]
    #             if minor_unit != intermediate_unit:
    #                 if minor_unit not in unit_parent_id_dictionary:
    #                     minor_unit_parent_row = child_minor_units.index(minor_unit)
    #                     unit_parent_id_dictionary[minor_unit] = minor_unit_parent_id
    #                     unit_parent_row_dictionary[minor_unit] = minor_unit_parent_row
    #             child_sub_minor_units = list(shifted_unit_df[(shifted_unit_df['Major Geographic-Geologic Description'] == major_unit) & (
    #                     shifted_unit_df['Intermediate Geologic-Geographic Unit'] == intermediate_unit) & (
    #                     shifted_unit_df['Minor Geologic-Geographic Unit'] == minor_unit)]['Sub-Minor Geologic-Geographic Unit'].unique())
    #             for sub_minor_unit in child_sub_minor_units:
    #                 if pd.isnull(sub_minor_unit):
    #                     continue
    #                 if sub_minor_unit != minor_unit:
    #                     if sub_minor_unit not in unit_parent_id_dictionary:
    #                         sub_minor_unit_parent_row = child_sub_minor_units.index(sub_minor_unit)
    #                         unit_parent_id_dictionary[sub_minor_unit] = sub_minor_unit_parent_id
    #                         unit_parent_row_dictionary[sub_minor_unit] = sub_minor_unit_parent_row
    #
    # # Add each dictionary to the appropriate column in unit_sql_df
    # unit_sql_df['ParentUnitID'] = pd.Series(unit_sql_df['UnitName'].map(unit_parent_id_dictionary),dtype=pd.Int64Dtype())
    # unit_sql_df['UnitParentRow'] = pd.Series(unit_sql_df['UnitName'].map(unit_parent_row_dictionary),dtype=pd.Int64Dtype())
    #
    # # Add the time stamps
    # unit_sql_df['UnitCreated'] = pd.to_datetime('now')
    # unit_sql_df['UnitModified'] = pd.to_datetime('now')
    #
    # # Add the unit_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     unit_sql_df.to_sql('Units', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    # print(f'Imported {unit_sql_df.shape[0]} units')
    #
    # # Create the Samples_Units table
    # sample_unit_sql_df = pd.DataFrame(columns=table_properties['Samples_Units'])
    #
    # merged_major_unit_df = merged_sample_id_df.merge(unit_sql_df, left_on=['Major Geographic-Geologic Description'], right_on=['UnitName'], how='left')
    # merged_intermediate_unit_df = merged_sample_id_df.merge(unit_sql_df, left_on=['Intermediate Geologic-Geographic Unit'], right_on=['UnitName'], how='left')
    # merged_minor_unit_df = merged_sample_id_df.merge(unit_sql_df, left_on=['Minor Geologic-Geographic Unit'], right_on=['UnitName'], how='left')
    # merged_sub_minor_unit_df = merged_sample_id_df.merge(unit_sql_df, left_on=['Sub-Minor Geologic-Geographic Unit'], right_on=['UnitName'], how='left')
    # major_units_selected = merged_major_unit_df[['SampleID', 'UnitID']]
    # intermediate_units_selected = merged_intermediate_unit_df[['SampleID', 'UnitID']]
    # minor_units_selected = merged_minor_unit_df[['SampleID', 'UnitID']]
    # sub_minor_units_selected = merged_sub_minor_unit_df[['SampleID', 'UnitID']]
    # units_combined_df = pd.concat([major_units_selected, intermediate_units_selected, minor_units_selected, sub_minor_units_selected], ignore_index=True)
    #
    # sample_unit_sql_df['SampleID'] = pd.Series(units_combined_df['SampleID'], dtype=pd.Int64Dtype())
    # sample_unit_sql_df['UnitID'] = pd.Series(units_combined_df['UnitID'], dtype=pd.Int64Dtype())
    # sample_unit_sql_df['Samples_UnitsCreated'] = pd.to_datetime('now')
    # sample_unit_sql_df['Samples_UnitsModified'] = pd.to_datetime('now')
    # sample_unit_sql_df.dropna(axis=0, how='any', inplace=True)
    # sample_unit_sql_df.drop_duplicates(inplace=True)
    # sample_unit_sql_df.reset_index(drop=True, inplace=True)
    #
    # # Add the sample_unit_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     sample_unit_sql_df.to_sql('Samples_Units', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # print(f'Imported {sample_unit_sql_df.shape[0]} sample-unit links')
    #
    #
    # print('Importing rock types')
    #
    # rock_type_sql_df = pd.DataFrame(columns=table_properties['RockTypes'])
    # # Check for duplicate rock type names
    # duplicates_df = sample_df.map(lambda x: x.strip().lower() if isinstance(x, str) else x)
    # duplicates = set()
    # rock_type_columns = ['Class-1 Rock Type', 'Class-2 Rock Type', 'Class-3 Rock Type', 'Class-4 Rock Type']
    # for i in range(len(rock_type_columns)):
    #     for j in range(i + 1, len(rock_type_columns)):
    #         col1, col2 = rock_type_columns[i], rock_type_columns[j]
    #         duplicates.update(duplicates_df[col1] [duplicates_df[col1].isin(duplicates_df[col2])])
    # if len(list(duplicates)) > 0:
    #     # If there is only one duplicate of nan, continue
    #     if len(list(duplicates)) == 1 and pd.isna(list(duplicates)[0]):
    #         pass
    #     else:
    #         print('Duplicate rock type names found:')
    #         print(list(duplicates))
    #         print('Please check the rock type names in the sample sheet.')
    #         return
    #
    # # If any rock type column is blank, fill with the value from the next one
    # shifted_rock_type_df = sample_df[rock_type_columns].apply(shift_left, axis=1)
    #
    # # append columns into one 'RockTypeName' column
    # class1_names = list(shifted_rock_type_df['Class-1 Rock Type'].unique())
    # class2_names = list(shifted_rock_type_df['Class-2 Rock Type'].unique())
    # class3_names = list(shifted_rock_type_df['Class-3 Rock Type'].unique())
    # class4_names = list(shifted_rock_type_df['Class-4 Rock Type'].unique())
    # # Remove nan float values from each list
    # class1_names = [name for name in class1_names if pd.notnull(name)]
    # class2_names = [name for name in class2_names if pd.notnull(name)]
    # class3_names = [name for name in class3_names if pd.notnull(name)]
    # class4_names = [name for name in class4_names if pd.notnull(name)]
    # rock_type_names = class1_names + class2_names + class3_names + class4_names
    # duplicates = []
    # distinct_names = set()
    # for rock_type_name in rock_type_names:
    #     if rock_type_name in distinct_names:
    #         duplicates.append(rock_type_name)
    #     else:
    #         distinct_names.add(rock_type_name)
    # if len(list(duplicates)) > 0:
    #     # If there is only one duplicate of nan, continue
    #     if len(list(duplicates)) == 1 and pd.isna(list(duplicates)[0]):
    #         pass
    #     else:
    #         print('Duplicate rock type names found:')
    #         print(list(duplicates))
    #         print('Please check the rock type names in the sample sheet.')
    #         return
    #
    # # Check for children with multiple parents
    # multiple_parents = []
    # for class2_name in class2_names:
    #     if pd.isna(class2_name):
    #         continue
    #     # Get the class1 values for the class2 name
    #     class1_values = \
    #     shifted_rock_type_df[shifted_rock_type_df['Class-2 Rock Type'] == class2_name][
    #         'Class-1 Rock Type'].unique()
    #     if len(class1_values) > 1:
    #         multiple_parents.append(class2_name)
    # for class3_name in class3_names:
    #     if pd.isna(class3_name):
    #         continue
    #     # Get the class2 values for the class3 name
    #     class2_values = \
    #     shifted_rock_type_df[shifted_rock_type_df['Class-3 Rock Type'] == class3_name][
    #         'Class-2 Rock Type'].unique()
    #     if len(class2_values) > 1:
    #         multiple_parents.append(class3_name)
    # for class4_name in class4_names:
    #     if pd.isna(class4_name):
    #         continue
    #     # Get the class3 values for the class4 name
    #     class3_values = \
    #     shifted_rock_type_df[shifted_rock_type_df['Class-4 Rock Type'] == class4_name][
    #         'Class-3 Rock Type'].unique()
    #     if len(class3_values) > 1:
    #         multiple_parents.append(class4_name)
    #
    # if multiple_parents != []:
    #     print('Rock types with multiple parents found:')
    #     print(multiple_parents)
    #     print('Please check the rock type names in the sample sheet.')
    #     return
    #
    # rock_type_sql_df['RockTypeName'] = rock_type_names
    # rock_type_sql_df['RockTypeID'] = pd.Series(list(range(1, len(rock_type_names) + 1)), dtype=pd.Int64Dtype())
    # rock_type_dict_df = pd.DataFrame(columns=['RockTypeName', 'RockTypeID'])
    # rock_type_dict_df['RockTypeName'] = rock_type_sql_df['RockTypeName']
    # rock_type_dict_df['RockTypeID'] = pd.Series(rock_type_sql_df['RockTypeID'], dtype=pd.Int64Dtype())
    #
    # # Create dictionaries for the rock type names and their corresponding IDs
    # rock_type_parent_id_dictionary = {}
    # rock_type_parent_row_dictionary = {}
    #
    # # For each unique 'Class-1 Rock Type', find all the unique 'Class-2 Rock Type' values
    # class1_names = list(shifted_rock_type_df['Class-1 Rock Type'].unique())
    # for class1_name in class1_names:
    #     class2_parent_id = rock_type_sql_df.loc[rock_type_sql_df['RockTypeName'] == class1_name, 'RockTypeID'].values[0]
    #     class1_parent_row = class1_names.index(class1_name)
    #     # Parent ID for top level is empty
    #     rock_type_parent_id_dictionary[class1_name] = None
    #     rock_type_parent_row_dictionary[class1_name] = class1_parent_row
    #     child_class2_names = list(
    #         shifted_rock_type_df[shifted_rock_type_df['Class-1 Rock Type'] == class1_name][
    #             'Class-2 Rock Type'].unique())
    #     for class2_name in child_class2_names:
    #         if pd.isnull(class2_name):
    #             continue
    #         class3_parent_id = \
    #         rock_type_sql_df.loc[rock_type_sql_df['RockTypeName'] == class2_name, 'RockTypeID'].values[0]
    #         if class2_name != class1_name:
    #             class2_parent_row = child_class2_names.index(class2_name)
    #             rock_type_parent_id_dictionary[class2_name] = int(class2_parent_id)
    #             rock_type_parent_row_dictionary[class2_name] = class2_parent_row
    #         child_class3_names = list(
    #             shifted_rock_type_df[(shifted_rock_type_df['Class-1 Rock Type'] == class1_name) & (
    #                     shifted_rock_type_df['Class-2 Rock Type'] == class2_name)][
    #                 'Class-3 Rock Type'].unique())
    #         for class3_name in child_class3_names:
    #             if pd.isnull(class3_name):
    #                 continue
    #             class4_parent_id = \
    #             rock_type_sql_df.loc[rock_type_sql_df['RockTypeName'] == class3_name, 'RockTypeID'].values[0]
    #             if class3_name != class2_name:
    #                 class3_parent_row = child_class3_names.index(class3_name)
    #                 rock_type_parent_id_dictionary[class3_name] = class4_parent_id
    #                 rock_type_parent_row_dictionary[class3_name] = class3_parent_row
    #             child_class4_names = list(
    #                 shifted_rock_type_df[(shifted_rock_type_df['Class-1 Rock Type'] == class1_name) & (
    #                         shifted_rock_type_df['Class-2 Rock Type'] == class2_name) & (
    #                         shifted_rock_type_df['Class-3 Rock Type'] == class3_name)][
    #                     'Class-4 Rock Type'].unique())
    #             for class4_name in child_class4_names:
    #                 if pd.isnull(class4_name):
    #                     continue
    #                 if class4_name != class3_name:
    #                     class4_parent_row = child_class4_names.index(class4_name)
    #                     rock_type_parent_id_dictionary[class4_name] = class4_parent_id
    #                     rock_type_parent_row_dictionary[class4_name] = class4_parent_row
    #
    # # Add each dictionary to the appropriate column in rock_type_sql_df
    # rock_type_sql_df['ParentRockTypeID'] = pd.Series(rock_type_sql_df['RockTypeName'].map(rock_type_parent_id_dictionary),dtype=pd.Int64Dtype())
    # rock_type_sql_df['RockTypeParentRow'] = pd.Series(rock_type_sql_df['RockTypeName'].map(rock_type_parent_row_dictionary),dtype=pd.Int64Dtype())
    # # Add the time stamps
    # rock_type_sql_df['RockTypeCreated'] = pd.to_datetime('now')
    # rock_type_sql_df['RockTypeModified'] = pd.to_datetime('now')
    #
    # # Add the rock_type_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     rock_type_sql_df.to_sql('RockTypes', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # print(f'Imported {rock_type_sql_df.shape[0]} rock types')
    #
    #
    # # Create the Samples_RockTypes table
    # sample_rock_type_sql_df = pd.DataFrame(columns=table_properties['Samples_RockTypes'])
    # merged_class1_df = merged_sample_id_df.merge(rock_type_sql_df, left_on=['Class-1 Rock Type'], right_on=['RockTypeName'], how='left')
    # merged_class2_df = merged_sample_id_df.merge(rock_type_sql_df, left_on=['Class-2 Rock Type'], right_on=['RockTypeName'], how='left')
    # merged_class3_df = merged_sample_id_df.merge(rock_type_sql_df, left_on=['Class-3 Rock Type'], right_on=['RockTypeName'], how='left')
    # merged_class4_df = merged_sample_id_df.merge(rock_type_sql_df, left_on=['Class-4 Rock Type'], right_on=['RockTypeName'], how='left')
    # class1_selected = merged_class1_df[['SampleID', 'RockTypeID']]
    # class2_selected = merged_class2_df[['SampleID', 'RockTypeID']]
    # class3_selected = merged_class3_df[['SampleID', 'RockTypeID']]
    # class4_selected = merged_class4_df[['SampleID', 'RockTypeID']]
    # rock_types_combined_df = pd.concat([class1_selected, class2_selected, class3_selected, class4_selected], ignore_index=True)
    #
    # sample_rock_type_sql_df['SampleID'] = pd.Series(rock_types_combined_df['SampleID'], dtype=pd.Int64Dtype())
    # sample_rock_type_sql_df['RockTypeID'] = pd.Series(rock_types_combined_df['RockTypeID'], dtype=pd.Int64Dtype())
    # sample_rock_type_sql_df['Samples_RockTypesCreated'] = pd.to_datetime('now')
    # sample_rock_type_sql_df['Samples_RockTypesModified'] = pd.to_datetime('now')
    # sample_rock_type_sql_df.dropna(axis=0, how='any', inplace=True)
    # sample_rock_type_sql_df.drop_duplicates(inplace=True)
    # sample_rock_type_sql_df.reset_index(drop=True, inplace=True)
    #
    # # Add the sample_rock_type_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     sample_rock_type_sql_df.to_sql('Samples_RockTypes', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # print(f'Imported {sample_rock_type_sql_df.shape[0]} sample-rock type links')
    #
    #
    # print('Creating aliquots')
    #
    # # Create the Aliquots table
    # aliquot_sql_df = pd.DataFrame(columns=table_properties['Aliquots'])
    #
    # # No aliquots on the database, so just repeat the sample names
    # aliquot_sql_df['AliquotName'] = sample_sql_df['SampleName']
    # aliquot_sql_df['AliquotID'] = pd.Series(list(range(1, sample_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    # aliquot_sql_df['SampleID'] = pd.Series(sample_sql_df['SampleID'], dtype=pd.Int64Dtype())
    #
    # # No nested aliquots, so parentID is null, just repeat the sample IDs for order in the root
    # aliquot_sql_df['AliquotParentRow'] = pd.Series(list(range(1, sample_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    # aliquot_sql_df['AliquotCreated'] = pd.to_datetime('now')
    # aliquot_sql_df['AliquotModified'] = pd.to_datetime('now')
    #
    # # Add the aliquot_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     aliquot_sql_df.to_sql('Aliquots', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    # print(f'Imported {aliquot_sql_df.shape[0]} aliquots')
    #
    #
    # # --------------------
    # # Import the spot and analysis tags from Puetz et al. (2024) into the database file.
    # # --------------------
    # # These are mostly in the Samples sheet as well.
    #
    # # Create the Spot Composition table
    # spot_composition_sql_df = pd.DataFrame(columns=table_properties['SpotCompositions'])
    # spot_composition_sql_df['SpotCompositionName'] = sample_df['Mineral']
    # spot_composition_sql_df.dropna(axis=0, how='all', inplace=True)
    # spot_composition_sql_df.drop_duplicates(inplace=True)
    # spot_composition_sql_df.reset_index(drop=True, inplace=True)
    # spot_composition_sql_df['SpotCompositionID'] = pd.Series(list(range(1, spot_composition_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    # spot_composition_sql_df['SpotCompositionCreated'] = pd.to_datetime('now')
    # spot_composition_sql_df['SpotCompositionModified'] = pd.to_datetime('now')
    #
    # # Add the spot_composition_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     spot_composition_sql_df.to_sql('SpotCompositions', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # print(f'Imported {spot_composition_sql_df.shape[0]} spot compositions')
    #
    #
    # print('Importing U-Pb analysis methods')
    #
    # # Create the UPbAnalysisMethods table
    # analysis_method_sql_df = pd.DataFrame(columns=table_properties['UPbAnalysisMethods'])
    # analysis_method_sql_df['UPbAnalysisMethodName'] = sample_df['Mass Spectrometer']
    # analysis_method_sql_df.dropna(axis=0, how='all', inplace=True)
    # analysis_method_sql_df.drop_duplicates(inplace=True)
    # analysis_method_sql_df.reset_index(drop=True, inplace=True)
    # analysis_method_sql_df['UPbAnalysisMethodID'] = pd.Series(list(range(1, analysis_method_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    # analysis_method_sql_df['UPbAnalysisMethodCreated'] = pd.to_datetime('now')
    # analysis_method_sql_df['UPbAnalysisMethodModified'] = pd.to_datetime('now')
    #
    # # Add the analysis_method_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     analysis_method_sql_df.to_sql('UPbAnalysisMethods', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # print(f'Imported {analysis_method_sql_df.shape[0]} analysis methods')
    #
    #
    # print('Importing lab facilities')
    #
    # # Create the LabFacilities table
    # lab_facility_sql_df = pd.DataFrame(columns=table_properties['LabFacilities'])
    # lab_facility_sql_df['LabFacilityName'] = sample_df['Spectrometer Location']
    # lab_facility_sql_df['LabFacilityDescription'] = sample_df['Institution']
    # lab_facility_sql_df.dropna(axis=0, how='all', inplace=True)
    # lab_facility_sql_df.drop_duplicates(inplace=True)
    # lab_facility_sql_df.reset_index(drop=True, inplace=True)
    # lab_facility_sql_df['LabFacilityID'] = pd.Series(list(range(1, lab_facility_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    # lab_facility_sql_df['LabFacilityCreated'] = pd.to_datetime('now')
    # lab_facility_sql_df['LabFacilityModified'] = pd.to_datetime('now')
    #
    # # Add the lab_facility_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     lab_facility_sql_df.to_sql('LabFacilities', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # print(f'Imported {lab_facility_sql_df.shape[0]} lab facilities')
    #
    #
    # print('Importing instruments')
    #
    # # Create the Instruments table
    # instrument_sql_df = pd.DataFrame(columns=table_properties['Instruments'])
    # instrument_sql_df['InstrumentName'] = [instrument.strip() for instrument in sample_df['Spectrometer Model']]
    # instrument_sql_df.dropna(axis=0, how='all', inplace=True)
    # instrument_sql_df.drop_duplicates(inplace=True)
    # instrument_sql_df.reset_index(drop=True, inplace=True)
    # instrument_sql_df['InstrumentID'] = pd.Series(list(range(1, instrument_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    # instrument_sql_df['InstrumentCreated'] = pd.to_datetime('now')
    # instrument_sql_df['InstrumentModified'] = pd.to_datetime('now')
    #
    # # Add the instrument_sql_df to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     instrument_sql_df.to_sql('Instruments', conn, if_exists='replace', index=False)
    #     conn.commit()
    #     conn.close()
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # print(f'Imported {instrument_sql_df.shape[0]} instruments')

    # --------------------
    # Import the U-Pb data from Puetz et al. (2024) into the database file.
    # --------------------
    print('Loading U-Pb data sheet')
    start_time = time.time()
    sheet_name = 'UPb_Data'
    try:
        upb_analysis_df = pd.read_excel(full_data, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        print(f"Failed to parse sheet with pandas:\n{e}")
        return
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
    concordance_format_id = 3

    print('Checking for grain duplicates')
    # Identify duplicate grain names
    upb_analysis_sql_df = pd.DataFrame(columns=table_properties['UPbAnalyses'])
    spot_sql_df = pd.DataFrame(columns=table_properties['Spots'])
    upb_analysis_df = edit_duplicate_grain_name(upb_analysis_df)
    spot_sql_df['SpotName'] = upb_analysis_df['Sample&Grain']
    spot_sql_df['SpotID'] = pd.Series(list(range(1, spot_sql_df.shape[0] + 1)), dtype=pd.Int64Dtype())
    upb_analysis_df['SpotID'] = pd.Series(list(range(1, upb_analysis_df.shape[0] + 1)), dtype=pd.Int64Dtype())

    # Map analyses back to samples
    sample_to_analysis = merged_sample_id_df[['Ref-Sample Key', 'Sample_ID', 'Mass Spectrometer', 'Spectrometer Location',
                                    'Institution', 'Spectrometer Model']]
    merged_sample_analysis_df = upb_analysis_df.merge(sample_to_analysis, on='Ref-Sample Key', how='left')
    spot_sql_df['AliquotID'] = merged_sample_analysis_df['SampleID']


    #
    # # create dictionary for sample number and sample fields
    # # add each sample to the database
    # try:
    #     conn = sqlite3.connect(db)
    #     cursor = conn.cursor()
    #     for i in range(1, rows):
    #         # get sample information
    #
    #         sample_name = sample_df.iloc[i, 1]
    #         if pd.isna(sample_name):
    #             continue
    #         print(f'importing {sample_name}')
    #
    #         # Regions
    #         # add each continent, large region, country/small region, and locality to the database
    #         # check if continent is in the database
    #         continent_name = sample_df.iloc[i, 4]
    #         large_region_name = sample_df.iloc[i, 3]
    #         country_name = sample_df.iloc[i, 2]
    #         locality_name = sample_df.iloc[i, 7]
    #         if pd.isna(continent_name) and pd.isna(large_region_name) and pd.isna(country_name) and pd.isna(locality_name):
    #             continent_id = None
    #             region_id = None
    #             country_id = None
    #             locality_id = None
    #             region_ids = []
    #         else:
    #             cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
    #                            (continent_name,))
    #             continent_id = cursor.fetchone()
    #             if continent_id is None:
    #                 # if not, add it to the database
    #                 # get the largest value for RegionParentRow of the continent_id
    #                 print(f'importing {continent_name}')
    #                 cursor.execute(f'SELECT MAX(RegionParentRow) FROM Regions WHERE ParentRegionID IS NULL')
    #                 parent_row = cursor.fetchone()
    #                 if parent_row[0] is None:
    #                     parent_row = 0
    #                 else:
    #                     parent_row = parent_row[0] + 1
    #                 cursor.execute(f'INSERT INTO Regions (RegionName, RegionParentRow) VALUES (?, ?)',
    #                                (continent_name, parent_row))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
    #                                (continent_name,))
    #                 continent_id = cursor.fetchone()
    #                 if continent_id is None:
    #                     print(f"Failed to add region {continent_name} to the database")
    #                     return
    #             continent_id = continent_id[0]
    #             # check if large region is in the database
    #             cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
    #                            (large_region_name,))
    #             region_id = cursor.fetchone()
    #             if region_id is None:
    #                 # if not, add it to the database
    #                 # get the largest value for RegionParentRow of the continent_id
    #                 print(f'importing {large_region_name}')
    #                 cursor.execute(f'SELECT MAX(RegionParentRow) FROM Regions WHERE ParentRegionID = ?',
    #                                (continent_id,))
    #                 parent_row = cursor.fetchone()
    #                 if parent_row[0] is None:
    #                     parent_row = 0
    #                 else:
    #                     parent_row = parent_row[0] + 1
    #                 cursor.execute(
    #                     f'INSERT INTO Regions (RegionName, ParentRegionID, RegionParentRow) VALUES (?,?,?)',
    #                     (large_region_name, continent_id, parent_row))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
    #                                (large_region_name,))
    #                 region_id = cursor.fetchone()
    #                 if region_id is None:
    #                     print(f"Failed to add region {large_region_name} to the database")
    #                     return
    #             region_id = region_id[0]
    #             cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
    #                            (country_name,))
    #             country_id = cursor.fetchone()
    #             if country_id is None:
    #                 # if not, add it to the database
    #                 # get the largest value for RegionParentRow of the region_id
    #                 cursor.execute(f'SELECT MAX(RegionParentRow) FROM Regions WHERE ParentRegionID = ?',
    #                                (region_id,))
    #                 parent_row = cursor.fetchone()
    #                 if parent_row[0] is None:
    #                     parent_row = 0
    #                 else:
    #                     parent_row = parent_row[0] + 1
    #                 cursor.execute(
    #                     f'INSERT INTO Regions (RegionName, ParentRegionID, RegionParentRow) VALUES (?,?,?)',
    #                     (country_name, region_id, parent_row))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
    #                                (country_name,))
    #                 country_id = cursor.fetchone()
    #                 if country_id is None:
    #                     print(f"Failed to add region {country_name} to the database")
    #                     return
    #             country_id = country_id[0]
    #             # check if locality is in the database
    #             cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
    #                            (locality_name,))
    #             locality_id = cursor.fetchone()
    #             if locality_id is None:
    #                 # if not, add it to the database
    #                 # get the largest value for RegionParentRow of the region_id
    #                 print(f'importing {locality_name}')
    #                 cursor.execute(f'SELECT MAX(RegionParentRow) FROM Regions WHERE ParentRegionID = ?',
    #                                (country_id,))
    #                 parent_row = cursor.fetchone()
    #                 if parent_row[0] is None:
    #                     parent_row = 0
    #                 else:
    #                     parent_row = parent_row[0] + 1
    #                 cursor.execute(f'INSERT INTO Regions (RegionName, ParentRegionID, RegionParentRow) VALUES (?,?,?)',
    #                                (locality_name, country_id, parent_row))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT RegionID FROM Regions WHERE RegionName = ? COLLATE NOCASE',
    #                                (locality_name,))
    #                 locality_id = cursor.fetchone()
    #                 if locality_id is None:
    #                     print(f"Failed to add region {locality_name} to the database")
    #                     return
    #             locality_id = locality_id[0]
    #             region_ids = [continent_id, region_id, country_id, locality_id]
    #
    #         # Units
    #         major_unit_name = sample_df.iloc[i, 5]
    #         minor_unit_name = sample_df.iloc[i, 6]
    #         if pd.isna(major_unit_name) and pd.isna(minor_unit_name):
    #             major_unit_id = None
    #             minor_unit_id = None
    #             unit_ids = []
    #         else:
    #             cursor.execute(f'SELECT UnitID FROM Units WHERE UnitName = ? COLLATE NOCASE', (major_unit_name,))
    #             major_unit_id = cursor.fetchone()
    #             if major_unit_id is None:
    #                 # if not, add it to the database
    #                 # get the largest value for UnitParentRow of the major_unit_id
    #                 cursor.execute(f'SELECT MAX(UnitParentRow) FROM Units WHERE ParentUnitID IS NULL')
    #                 parent_row = cursor.fetchone()
    #                 if parent_row[0] is None:
    #                     parent_row = 0
    #                 else:
    #                     parent_row = parent_row[0] + 1
    #                 cursor.execute(f'INSERT INTO Units (UnitName, UnitParentRow) VALUES (?, ?)',
    #                                  (major_unit_name, parent_row))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT UnitID FROM Units WHERE UnitName = ? COLLATE NOCASE', (major_unit_name,))
    #                 major_unit_id = cursor.fetchone()
    #                 if major_unit_id is None:
    #                     print(f"Failed to add unit {major_unit_name} to the database")
    #                     return
    #             major_unit_id = major_unit_id[0]
    #             # check if minor unit is in the database
    #             cursor.execute(f'SELECT UnitID FROM Units WHERE UnitName = ? COLLATE NOCASE', (minor_unit_name,))
    #             minor_unit_id = cursor.fetchone()
    #             if minor_unit_id is None:
    #                 # if not, add it to the database
    #                 # get the largest value for UnitParentRow of the minor_unit_id
    #                 cursor.execute(f'SELECT MAX(UnitParentRow) FROM Units WHERE ParentUnitID = ?',
    #                                (major_unit_id,))
    #                 parent_row = cursor.fetchone()
    #                 if parent_row[0] is None:
    #                     parent_row = 0
    #                 else:
    #                     parent_row = parent_row[0] + 1
    #                 cursor.execute(f'INSERT INTO Units (UnitName, ParentUnitID, UnitParentRow) VALUES (?, ?, ?)',
    #                                (minor_unit_name, major_unit_id, parent_row))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT UnitID FROM Units WHERE UnitName = ? COLLATE NOCASE', (minor_unit_name,))
    #                 minor_unit_id = cursor.fetchone()
    #                 if minor_unit_id is None:
    #                     print(f"Failed to add unit {minor_unit_name} to the database")
    #                     return
    #             minor_unit_id = minor_unit_id[0]
    #             unit_ids = [major_unit_id, minor_unit_id]
    #
    #         # GPS location
    #         gps_lat = sample_df.iloc[i, 8]
    #         gps_lon = sample_df.iloc[i, 9]
    #         if pd.isna(gps_lat) or pd.isna(gps_lon):
    #             gps_id = None
    #         else:
    #             cursor.execute(f'SELECT GPSLocationID FROM GPSLocations WHERE GPSLatDeg = ? AND GPSLonDeg = ?',
    #                            (gps_lat, gps_lon))
    #             gps_id = cursor.fetchone()
    #             if gps_id is None:
    #                 # if not, add it to the database
    #                 cursor.execute(f'INSERT INTO GPSLocations (GPSLatDeg, GPSLonDeg, GPSFormatID) VALUES (?, ?, ?)',
    #                                (gps_lat, gps_lon, gps_format_id))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT GPSLocationID FROM GPSLocations WHERE GPSLatDeg = ? AND GPSLonDeg = ?',
    #                                (gps_lat, gps_lon))
    #                 gps_id = cursor.fetchone()
    #                 if gps_id is None:
    #                     print(f"Failed to add sample {sample_name} to the database")
    #                     return
    #             gps_id = gps_id[0]
    #
    #         # Sample age
    #         sample_age_max = sample_df.iloc[i, 10]
    #         sample_age_est = sample_df.iloc[i, 11]
    #         sample_age_min = sample_df.iloc[i, 12]
    #         if pd.isna(sample_age_max) and pd.isna(sample_age_est) and pd.isna(sample_age_min):
    #             sample_age_id = None
    #         else:
    #             cursor.execute(f'''SELECT SampleAgeID FROM SampleAges WHERE OldestDirectAge = ? AND
    #                                     YoungestDirectAge = ? AND DirectAge = ? AND DirectAgeUnitID = ?''',
    #                            (sample_age_max, sample_age_min, sample_age_est, age_unit_id))
    #             sample_age_id = cursor.fetchone()
    #             if sample_age_id is None:
    #                 # if not, add it to the database
    #                 cursor.execute(f'INSERT INTO SampleAges (OldestDirectAge, YoungestDirectAge, DirectAge, DirectAgeUnitID) VALUES (?, ?, ?, ?)',
    #                                (sample_age_max, sample_age_min, sample_age_est, age_unit_id))
    #                 conn.commit()
    #                 cursor.execute(f'''SELECT SampleAgeID FROM SampleAges WHERE OldestDirectAge = ? AND
    #                                     YoungestDirectAge = ? AND DirectAge = ? AND DirectAgeUnitID = ?''',
    #                                (sample_age_max, sample_age_min, sample_age_est, age_unit_id))
    #                 sample_age_id = cursor.fetchone()
    #                 if sample_age_id is None:
    #                     print(f"Failed to add sample {sample_name} to the database")
    #                     return
    #             sample_age_id = sample_age_id[0]
    #
    #         # Mineral
    #         # check if mineral is in the database
    #         spot_composition_name = sample_df.iloc[i, 13]
    #         if pd.isna(spot_composition_name):
    #             spot_composition_id = None
    #         else:
    #             cursor.execute(
    #                 f'SELECT SpotCompositionID FROM SpotCompositions WHERE SpotCompositionName = ? COLLATE NOCASE',
    #                 (spot_composition_name,))
    #             spot_composition_id = cursor.fetchone()
    #             if spot_composition_id is None:
    #                 # if not, add it to the database
    #                 # get the largest value for SpotCompositionParentRow of the spot_composition_id
    #                 cursor.execute(
    #                     f'SELECT MAX(SpotCompositionParentRow) FROM SpotCompositions WHERE ParentSpotCompositionID IS NULL')
    #                 parent_row = cursor.fetchone()
    #                 if parent_row[0] is None:
    #                     parent_row = 0
    #                 else:
    #                     parent_row = parent_row[0] + 1
    #                 cursor.execute(
    #                     f'INSERT INTO SpotCompositions (SpotCompositionName, SpotCompositionParentRow) VALUES (?,?)',
    #                     (spot_composition_name, parent_row))
    #                 conn.commit()
    #                 cursor.execute(
    #                     f'SELECT SpotCompositionID FROM SpotCompositions WHERE SpotCompositionName = ? COLLATE NOCASE',
    #                     (spot_composition_name,))
    #                 spot_composition_id = cursor.fetchone()
    #                 if spot_composition_id is None:
    #                     print(f"Failed to add mineral {spot_composition_name} to the database")
    #                     return
    #             spot_composition_id = spot_composition_id[0]
    #
    #         # Methods
    #         method_name = sample_df.iloc[i, 14]
    #         if pd.isna(method_name):
    #             method_id = None
    #         else:
    #             # check if method is in the database
    #             cursor.execute(f'SELECT UPbAnalysisMethodID FROM UPbAnalysisMethods WHERE UPbAnalysisMethodName = ? COLLATE NOCASE',
    #                            (method_name,))
    #             method_id = cursor.fetchone()
    #             if method_id is None:
    #                 # if not, add it to the database
    #                 # get the largest value for UPbAnalysisMethodParentRow of the method_id
    #                 print(f'importing {method_name}')
    #                 cursor.execute(f'SELECT MAX("UPbAnalysisMethodParentRow") FROM UPbAnalysisMethods WHERE "ParentUPbAnalysisMethodID" IS NULL')
    #                 parent_row = cursor.fetchone()
    #                 if parent_row[0] is None:
    #                     parent_row = 0
    #                 else:
    #                     parent_row = parent_row[0] + 1
    #                 cursor.execute(f'INSERT INTO UPbAnalysisMethods (UPbAnalysisMethodName, UPbAnalysisMethodParentRow) VALUES (?, ?)',
    #                                (method_name, parent_row))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT UPbAnalysisMethodID FROM UPbAnalysisMethods WHERE UPbAnalysisMethodName = ? COLLATE NOCASE',
    #                                (method_name,))
    #                 method_id = cursor.fetchone()
    #                 if method_id is None:
    #                     print(f"Failed to add method {method_name} to the database")
    #                     return
    #             method_id = method_id[0]
    #
    #         # Lab facilities
    #         facility_name = sample_df.iloc[i, 15]
    #         facility_description = sample_df.iloc[i, 16]
    #         if pd.isna(facility_name):
    #             facility_id = None
    #         else:
    #             # check if facility is in the database
    #             cursor.execute(f'SELECT LabFacilityID FROM LabFacilities WHERE LabFacilityName = ? COLLATE NOCASE',
    #                            (facility_name,))
    #             facility_id = cursor.fetchone()
    #             if facility_id is None:
    #                 # if not, add it to the database
    #                 print(f'importing {facility_name}')
    #                 cursor.execute(f'INSERT INTO LabFacilities (LabFacilityName, LabFacilityDescription) VALUES (?, ?)',
    #                                (facility_name, facility_description))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT LabFacilityID FROM LabFacilities WHERE LabFacilityName = ? COLLATE NOCASE',
    #                                (facility_name,))
    #                 facility_id = cursor.fetchone()
    #                 if facility_id is None:
    #                     print(f"Failed to add facility {facility_name} to the database")
    #                     return
    #             facility_id = facility_id[0]
    #
    #         # Instruments
    #         instrument_name = sample_df.iloc[i, 17]
    #         if pd.isna(instrument_name):
    #             instrument_id = None
    #         else:
    #             # check if instrument is in the database
    #             cursor.execute(f'SELECT InstrumentID FROM Instruments WHERE InstrumentName = ? COLLATE NOCASE',
    #                              (instrument_name,))
    #             instrument_id = cursor.fetchone()
    #             if instrument_id is None:
    #                 # if not, add it to the database
    #                 print(f'importing {instrument_name}')
    #                 cursor.execute(f'INSERT INTO Instruments (InstrumentName) VALUES (?)', (instrument_name,))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT InstrumentID FROM Instruments WHERE InstrumentName = ? COLLATE NOCASE',
    #                                   (instrument_name,))
    #                 instrument_id = cursor.fetchone()
    #                 if instrument_id is None:
    #                     print(f"Failed to add instrument {instrument_name} to the database")
    #                     return
    #             instrument_id = instrument_id[0]
    #
    #         # Rock types
    #         rock_type1_name = sample_df.iloc[i, 18]
    #         rock_type2_name = sample_df.iloc[i, 19]
    #         rock_type3_name = sample_df.iloc[i, 20]
    #         if pd.isna(rock_type1_name) and pd.isna(rock_type2_name) and pd.isna(rock_type3_name):
    #             rock_type1_id = None
    #             rock_type2_id = None
    #             rock_type3_id = None
    #             rock_type_ids = []
    #         else:
    #             cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ? COLLATE NOCASE',
    #                            (rock_type1_name,))
    #             rock_type1_id = cursor.fetchone()
    #             if rock_type1_id is None:
    #                 # if not, add it to the database
    #                 # get the largest value for RockTypeParentRow of the rock_type1_id
    #                 print(f'importing {rock_type1_name}')
    #                 cursor.execute(f'SELECT MAX(RockTypeParentRow) FROM RockTypes WHERE ParentRockTypeID IS NULL')
    #                 parent_row = cursor.fetchone()
    #                 if parent_row[0] is None:
    #                     parent_row = 0
    #                 else:
    #                     parent_row = parent_row[0] + 1
    #                 cursor.execute(f'INSERT INTO RockTypes (RockTypeName, RockTypeParentRow) VALUES (?, ?)',
    #                                   (rock_type1_name, parent_row))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ? COLLATE NOCASE',
    #                                   (rock_type1_name,))
    #                 rock_type1_id = cursor.fetchone()
    #                 if rock_type1_id is None:
    #                     print(f"Failed to add rock type {rock_type1_name} to the database")
    #                     return
    #             rock_type1_id = rock_type1_id[0]
    #             # check if rock type 2 is in the database
    #             cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ? COLLATE NOCASE',
    #                            (rock_type2_name,))
    #             rock_type2_id = cursor.fetchone()
    #             if rock_type2_id is None:
    #                 # if not, add it to the database
    #                 # get the largest value for RockTypeParentRow of the rock_type2_id
    #                 print(f'importing {rock_type2_name}')
    #                 cursor.execute(f'SELECT MAX(RockTypeParentRow) FROM RockTypes WHERE ParentRockTypeID = ?',
    #                                (rock_type1_id,))
    #                 parent_row = cursor.fetchone()
    #                 if parent_row[0] is None:
    #                     parent_row = 0
    #                 else:
    #                     parent_row = parent_row[0] + 1
    #                 cursor.execute(f'INSERT INTO RockTypes (RockTypeName, ParentRockTypeID, RockTypeParentRow) VALUES (?, ?, ?)',
    #                                (rock_type2_name, rock_type1_id, parent_row))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ? COLLATE NOCASE',
    #                                (rock_type2_name,))
    #                 rock_type2_id = cursor.fetchone()
    #                 if rock_type2_id is None:
    #                     print(f"Failed to add rock type {rock_type2_name} to the database")
    #                     return
    #             rock_type2_id = rock_type2_id[0]
    #             # check if rock type 3 is in the database
    #             cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ? COLLATE NOCASE',
    #                              (rock_type3_name,))
    #             rock_type3_id = cursor.fetchone()
    #             if rock_type3_id is None:
    #                 # if not, add it to the database
    #                 # get the largest value for RockTypeParentRow of the rock_type3_id
    #                 print(f'importing {rock_type3_name}')
    #                 cursor.execute(f'SELECT MAX(RockTypeParentRow) FROM RockTypes WHERE ParentRockTypeID = ?',
    #                                (rock_type2_id,))
    #                 parent_row = cursor.fetchone()
    #                 if parent_row[0] is None:
    #                     parent_row = 0
    #                 else:
    #                     parent_row = parent_row[0] + 1
    #                 cursor.execute(f'INSERT INTO RockTypes (RockTypeName, ParentRockTypeID, RockTypeParentRow) VALUES (?, ?, ?)',
    #                                (rock_type3_name, rock_type2_id, parent_row))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT RockTypeID FROM RockTypes WHERE RockTypeName = ? COLLATE NOCASE',
    #                                (rock_type3_name,))
    #                 rock_type3_id = cursor.fetchone()
    #                 if rock_type3_id is None:
    #                     print(f"Failed to add rock type {rock_type3_name} to the database")
    #                     return
    #             rock_type3_id = rock_type3_id[0]
    #             rock_type_ids = [rock_type1_id, rock_type2_id, rock_type3_id]
    #
    #         # Sample
    #         cursor.execute(f'SELECT SampleID FROM Samples WHERE SampleName = ? COLLATE NOCASE', (sample_name,))
    #         sample_id = cursor.fetchone()
    #         if sample_id is None:
    #             # if not, add it to the database
    #             cursor.execute(f'INSERT INTO Samples (SampleName, SampleGPSLocationID) Values (?, ?)',
    #                            (sample_name, gps_id))
    #             conn.commit()
    #             cursor.execute(f'SELECT SampleID FROM Samples WHERE SampleName = ? COLLATE NOCASE', (sample_name,))
    #             sample_id = cursor.fetchone()
    #             if sample_id is None:
    #                 print(f"Failed to add sample {sample_name} to the database")
    #                 return
    #         sample_id = sample_id[0]
    #
    #         # add the sample name and reference key to the dictionary
    #         ref_sample_key = sample_df.iloc[i, 0]
    #         ref_sample_dict[ref_sample_key] = sample_id
    #
    #         # Many to many
    #         for region_id in region_ids:
    #             cursor.execute(f'SELECT SampleID, RegionID FROM Samples_Regions WHERE SampleID = ? AND RegionID = ?',
    #                            (sample_id, region_id))
    #             result = cursor.fetchone()
    #             if result is None:
    #                 # if not, add it to the database
    #                 cursor.execute(f'INSERT INTO Samples_Regions (SampleID, RegionID) Values (?, ?)',
    #                                (sample_id, region_id))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT SampleID, RegionID FROM Samples_Regions WHERE SampleID = ? AND RegionID = ?',
    #                                 (sample_id, region_id))
    #                 result = cursor.fetchone()
    #                 if result is None:
    #                     print(f"Failed to add sample {sample_name} to the database")
    #                     return
    #
    #         for rock_type_id in rock_type_ids:
    #             cursor.execute(f'SELECT SampleID, RockTypeID FROM Samples_RockTypes WHERE SampleID = ? AND RockTypeID = ?',
    #                            (sample_id, rock_type_id))
    #             result = cursor.fetchone()
    #             if result is None:
    #                 # if not, add it to the database
    #                 cursor.execute(f'INSERT INTO Samples_RockTypes (SampleID, RockTypeID) Values (?, ?)',
    #                                (sample_id, rock_type_id))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT SampleID, RockTypeID FROM Samples_RockTypes WHERE SampleID = ? AND RockTypeID = ?',
    #                                (sample_id, rock_type_id))
    #                 result = cursor.fetchone()
    #                 if result is None:
    #                     print(f"Failed to add sample {sample_name} to the database")
    #                     return
    #
    #         if sample_age_id is not None:
    #             cursor.execute(f'SELECT SampleID, SampleAgeID FROM Samples_SampleAges WHERE SampleID = ? AND SampleAgeID = ?',
    #                            (sample_id, sample_age_id))
    #             result = cursor.fetchone()
    #             if result is None:
    #                 # if not, add it to the database
    #                 cursor.execute(f'INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) Values (?, ?)',
    #                                (sample_id, sample_age_id))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT SampleID, SampleAgeID FROM Samples_SampleAges WHERE SampleID = ? AND SampleAgeID = ?',
    #                                (sample_id, sample_age_id))
    #                 result = cursor.fetchone()
    #                 if result is None:
    #                     print(f"Failed to associate {sample_age_est} with sample {sample_name}")
    #                     return
    #             cursor.execute(f'SELECT SampleID, DefaultSampleAgeID FROM Samples WHERE SampleID = ? AND DefaultSampleAgeID = ?',
    #                            (sample_id, sample_age_id))
    #             result = cursor.fetchone()
    #             if result is None:
    #                 # if not, add it to the database
    #                 cursor.execute(f'UPDATE Samples SET DefaultSampleAgeID = ? WHERE SampleID = ?',
    #                                (sample_age_id, sample_id))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT SampleID, DefaultSampleAgeID FROM Samples WHERE SampleID = ? AND DefaultSampleAgeID = ?',
    #                                (sample_id, sample_age_id))
    #                 result = cursor.fetchone()
    #                 if result is None:
    #                     print(f"Failed to set default age for {sample_name}")
    #                     return
    #
    #         for unit_id in unit_ids:
    #             cursor.execute(f'SELECT SampleID, UnitID FROM Samples_Units WHERE SampleID = ? AND UnitID = ?',
    #                            (sample_id, unit_id))
    #             result = cursor.fetchone()
    #             if result is None:
    #                 # if not, add it to the database
    #                 cursor.execute(f'INSERT INTO Samples_Units (SampleID, UnitID) Values (?, ?)',
    #                                (sample_id, unit_id))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT SampleID, UnitID FROM Samples_Units WHERE SampleID = ? AND UnitID = ?',
    #                                (sample_id, unit_id))
    #                 result = cursor.fetchone()
    #                 if result is None:
    #                     print(f"Failed to add sample {sample_name} to the database")
    #                     return
    #
    #         # Check if the region name contains "Core"
    #         for region_id in region_ids:
    #             region_name = cursor.execute(f'SELECT RegionName FROM Regions WHERE RegionID = ?',
    #                                          (region_id,)).fetchone()
    #             if region_name is None:
    #                 print(f"Failed to find region {region_id} in the database")
    #                 return
    #             region_name = region_name[0]
    #             # If the region name contains "Core", get the column name and height/depth
    #             if re.search(r'\bCore\b', region_name, re.IGNORECASE):
    #                 # Check if it ends with the pattern " at [0-9]+ m" or " at [0-9]+ ft" with or without a space
    #                 pattern = r'(.*) at (\d+(?:-\d+)?) ?(m|ft)$'
    #                 match = re.search(pattern, region_name)
    #                 if match:
    #                     # Extract the column, height/depth, and unit
    #                     column = match.group(1)
    #                     depth = match.group(2)
    #                     unit = match.group(3)
    #
    #                     # Get the unit ID for the unit
    #                     cursor.execute(
    #                         "SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = ? COLLATE NOCASE",
    #                         (unit,))
    #                     unit_id = cursor.fetchone()
    #                     if unit_id is None:
    #                         print(f"Failed to find unit {unit} in the database.")
    #                         continue
    #                     unit_id = unit_id[0]
    #
    #                     # Check if the column name is already in the database
    #                     cursor.execute("SELECT ColumnID FROM Columns WHERE ColumnName = ? COLLATE NOCASE",
    #                                    (column,))
    #                     column_id = cursor.fetchone()
    #                     if column_id is None:
    #                         # Insert the new column into the database
    #                         cursor.execute("INSERT INTO Columns (ColumnName) VALUES (?)", (column,))
    #                         conn.commit()
    #                         cursor.execute("SELECT ColumnID FROM Columns WHERE ColumnName = ? COLLATE NOCASE",
    #                                        (column,))
    #                         column_id = cursor.fetchone()
    #                         if column_id is None:
    #                             print(f"Failed to insert column {column} into the database.")
    #                             return
    #                     column_id = column_id[0]
    #                     # Get all the samples associated with the region
    #                     cursor.execute("SELECT SampleID FROM Samples_Regions WHERE RegionID = ?", (region_id,))
    #                     sample_ids = cursor.fetchall()
    #                     if sample_ids is None:
    #                         print(f"SampleID for region {region_name} not found.")
    #                         continue
    #                     for sample_id in sample_ids:
    #                         sample_id = sample_id[0]
    #                         # Check if the column already exists for the sample
    #                         cursor.execute(
    #                             "SELECT SampleColumnID FROM Samples WHERE SampleID = ? AND SampleColumnID = ?",
    #                             (sample_id, column_id))
    #                         sample_column_id = cursor.fetchone()
    #                         if sample_column_id is None:
    #                             # Insert the new column for the sample
    #                             cursor.execute(
    #                                 f"UPDATE Samples SET (SampleColumnID, HeightDepth, HeightDepthUnitID) = (?, ?, ?) WHERE SampleID = {sample_id}",
    #                                 (column_id, depth, unit_id))
    #                             conn.commit()
    #                             cursor.execute("""SELECT SampleColumnID FROM Samples
    #                                                     WHERE SampleID = ? AND SampleColumnID = ? AND HeightDepth = ? AND
    #                                                     HeightDepthUnitID = ?""",
    #                                            (sample_id, column_id, depth, unit_id))
    #                             sample_column_id = cursor.fetchone()
    #                             if sample_column_id is None:
    #                                 print(f"Failed to insert column {column} for sample {sample_id}.")
    #                                 return
    #
    #         sample_analysis_tags_dict[sample_id] = [method_id, facility_id, instrument_id]
    #
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     return
    #
    # # --------------------
    # # Import the spot compositions from Puetz et al. (2024) into the database file.
    # # --------------------
    # sheet_name = 'UPb_Data'
    # try:
    #     upb_df = pd.read_excel(full_data, header=None, sheet_name=sheet_name, engine="openpyxl")
    # except Exception as e:
    #     print(f"Failed to parse sheet with pandas:\n{e}")
    #     return
    # while not upb_df.empty and upb_df.iloc[0].isna().all():
    #     upb_df = upb_df.iloc[1:].reset_index(drop=True)
    # rows, cols = upb_df.shape
    #
    # spot_composition_id = 1
    # spot_size_unit_id = 5
    # ratio_error_format_id = 1
    # age_error_format_id = 2
    # age_unit_id = 2
    # concordance_format_id = 3
    #
    # for i in range(1, rows):
    #     # get analysis information
    #
    #     # reference
    #     ref_sample_key = upb_df.iloc[i, 0]
    #     if pd.isna(ref_sample_key):
    #         continue
    #     print(f'{i}/{rows}')
    #     ref_id = ref_sample_key.split('-')[0]
    #     if ref_id in reference_dict:
    #         reference_id = reference_dict[ref_id]
    #     else:
    #         print(f"Failed to find reference {ref_id} in the dictionary")
    #         return
    #
    #     # Sample
    #     sample_id = ref_sample_dict[ref_sample_key]
    #
    #     # Aliquot
    #     try:
    #         conn = sqlite3.connect(db)
    #         cursor = conn.cursor()
    #         cursor.execute(f'SELECT SampleName FROM Samples WHERE SampleID = ?', (sample_id,))
    #         sample_name = cursor.fetchone()
    #         if sample_name is None:
    #             print(f"Failed to find sample {sample_id} in the database")
    #             return
    #         new_aliquot = True
    #         sample_name = sample_name[0]
    #         cursor.execute(f'SELECT AliquotID FROM Aliquots WHERE SampleID = ?', (sample_id,))
    #         aliquot_id = cursor.fetchall()
    #         if len(aliquot_id) > 0:
    #             # check if the name we want to use exists
    #             cursor.execute(f'SELECT AliquotID FROM Aliquots WHERE AliquotName = ?', (sample_name,))
    #             aliquot_id = cursor.fetchone()
    #         if not aliquot_id:
    #             # if not, add it to the database
    #             # get the largest value for AliquotParentRow of the aliquot_id
    #             cursor.execute(f'SELECT MAX(AliquotParentRow) FROM Aliquots WHERE ParentAliquotID IS NULL AND SampleID = ?',
    #                            (sample_id,))
    #             parent_row = cursor.fetchone()
    #             if parent_row[0] is None:
    #                 parent_row = 0
    #             else:
    #                 parent_row = parent_row[0] + 1
    #             aliquot_name = sample_name
    #             cursor.execute(f'INSERT INTO Aliquots (AliquotName, AliquotParentRow, SampleID) VALUES (?, ?, ?)',
    #                            (aliquot_name, parent_row, sample_id))
    #             conn.commit()
    #             cursor.execute(f'SELECT AliquotID FROM Aliquots WHERE AliquotName = ? COLLATE NOCASE', (aliquot_name,))
    #             aliquot_id = cursor.fetchone()
    #             if aliquot_id is None:
    #                 print(f"Failed to add aliquot {aliquot_name} to the database")
    #                 return
    #         aliquot_id = aliquot_id[0]
    #         conn.commit()
    #         conn.close()
    #     except sqlite3.Error as e:
    #         print(f"SQLite error: {e}")
    #         return
    #
    #
    #     # Spot
    #     spot_name = upb_df.iloc[i, 1]
    #     if pd.isna(spot_name):
    #         continue
    #     try:
    #         conn = sqlite3.connect(db)
    #         cursor = conn.cursor()
    #         cursor.execute(f'SELECT SpotID FROM Spots WHERE SpotName = ? COLLATE NOCASE', (spot_name,))
    #         spot_id = cursor.fetchone()
    #         if spot_id is None:
    #             # if not, add it to the database
    #             # print(f'importing {spot_name}')
    #             cursor.execute(f'INSERT INTO Spots (SpotName, AliquotID, SpotCompositionID) VALUES (?, ?, ?)',
    #                            (spot_name, aliquot_id, spot_composition_id))
    #             conn.commit()
    #             cursor.execute(f'SELECT SpotID FROM Spots WHERE SpotName = ? COLLATE NOCASE', (spot_name,))
    #             spot_id = cursor.fetchone()
    #             if spot_id is None:
    #                 print(f"Failed to add spot {spot_name} to the database")
    #                 return
    #         spot_id = spot_id[0]
    #         conn.commit()
    #         conn.close()
    #     except sqlite3.Error as e:
    #         print(f"SQLite error: {e}")
    #         return
    #
    #     # spot_context
    #     spot_context = upb_df.iloc[i, 2]
    #     if pd.isna(spot_context):
    #         spot_context_id = None
    #     else:
    #         try:
    #             conn = sqlite3.connect(db)
    #             cursor = conn.cursor()
    #             cursor.execute(f'SELECT SpotContextID FROM SpotContexts WHERE SpotContextName = ? COLLATE NOCASE',
    #                            (spot_context,))
    #             spot_context_id = cursor.fetchone()
    #             if spot_context_id is None:
    #                 # if not, add it to the database
    #                 # get the largest value for SpotContextParentRow of the spot_context_id
    #                 cursor.execute(f'SELECT MAX(SpotContextParentRow) FROM SpotContexts WHERE ParentSpotContextID IS NULL')
    #                 parent_row = cursor.fetchone()
    #                 if parent_row[0] is None:
    #                     parent_row = 0
    #                 else:
    #                     parent_row = parent_row[0] + 1
    #                 cursor.execute(f'INSERT INTO SpotContexts (SpotContextName, SpotContextParentRow) VALUES (?,?)',
    #                                (spot_context, parent_row))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT SpotContextID FROM SpotContexts WHERE SpotContextName = ? COLLATE NOCASE',
    #                                (spot_context,))
    #                 spot_context_id = cursor.fetchone()
    #                 if spot_context_id is None:
    #                     print(f"Failed to add spot context {spot_context} to the database")
    #                     return
    #             spot_context_id = spot_context_id[0]
    #             conn.commit()
    #             conn.close()
    #         except sqlite3.Error as e:
    #             print(f"SQLite error: {e}")
    #             return
    #
    #     # Spot tags
    #     if spot_context_id is not None:
    #         try:
    #             conn = sqlite3.connect(db)
    #             cursor = conn.cursor()
    #             cursor.execute(f'SELECT SpotID FROM Spots_SpotContexts WHERE SpotID = ? AND SpotContextID = ?',
    #                            (spot_id, spot_context_id))
    #             result = cursor.fetchone()
    #             if result is None:
    #                 # if not, add it to the database
    #                 cursor.execute(f'INSERT INTO Spots_SpotContexts (SpotID, SpotContextID) VALUES (?, ?)',
    #                                (spot_id, spot_context_id))
    #                 conn.commit()
    #                 cursor.execute(f'SELECT SpotID FROM Spots_SpotContexts WHERE SpotID = ? AND SpotContextID = ?',
    #                                (spot_id, spot_context_id))
    #                 result = cursor.fetchone()
    #                 if result is None:
    #                     print(f"Failed to add spot tags {spot_name} to the database")
    #                     return
    #         except sqlite3.Error as e:
    #             print(f"SQLite error: {e}")
    #             return
    #
    #     # Analysis tags
    #     analysis_tags = sample_analysis_tags_dict[sample_id]
    #     method_id = analysis_tags[0]
    #     lab_facility_id = analysis_tags[1]
    #     instrument_id = analysis_tags[2]
    #
    #     # Spot size
    #     spot_size = upb_df.iloc[i, 3]
    #     if pd.isna(spot_size):
    #         spot_size = None
    #
    #
    #     # ratios
    #     pb6_u8 = upb_df.iloc[i, 5]
    #     if pd.isna(pb6_u8):
    #         pb6_u8 = None
    #     pb6_u8_err = upb_df.iloc[i, 6]
    #     if pd.isna(pb6_u8_err):
    #         pb6_u8_err = None
    #     pb7_u5 = upb_df.iloc[i, 7]  # calculated based on 238U/235U = 137.818
    #     if pd.isna(pb7_u5):
    #         pb7_u5 = None
    #     pb7_u5_err = upb_df.iloc[i, 8]  # calculated based on 238U/235U = 137.818
    #     if pd.isna(pb7_u5_err):
    #         pb7_u5_err = None
    #     pb7_pb6 = upb_df.iloc[i, 9]
    #     if pd.isna(pb7_pb6):
    #         pb7_pb6 = None
    #     pb7_pb6_err = upb_df.iloc[i, 10]
    #     if pd.isna(pb7_pb6_err):
    #         pb7_pb6_err = None
    #     rho = upb_df.iloc[i, 11]
    #     if pd.isna(rho):
    #         rho = None
    #
    #     # ages
    #     pb6_u8_age = upb_df.iloc[i, 13]
    #     if pd.isna(pb6_u8_age):
    #         pb6_u8_age = None
    #     pb6_u8_age_err = upb_df.iloc[i, 14]
    #     if pd.isna(pb6_u8_age_err):
    #         pb6_u8_age_err = None
    #     pb7_u5_age = upb_df.iloc[i, 15]  # calculated based on 238U/235U = 137.818
    #     if pd.isna(pb7_u5_age):
    #         pb7_u5_age = None
    #     pb7_u5_age_err = upb_df.iloc[i, 16]  # calculated based on 238U/235U = 137.818
    #     if pd.isna(pb7_u5_age_err):
    #         pb7_u5_age_err = None
    #     pb7_pb6_age = upb_df.iloc[i, 17]
    #     if pd.isna(pb7_pb6_age):
    #         pb7_pb6_age = None
    #     pb7_pb6_age_err = upb_df.iloc[i, 18]
    #     if pd.isna(pb7_pb6_age_err):
    #         pb7_pb6_age_err = None
    #     best_age = upb_df.iloc[i, 28]
    #     if pd.isna(best_age):
    #         best_age = None
    #     best_age_err = upb_df.iloc[i, 29]
    #     if pd.isna(best_age_err):
    #         best_age_err = None
    #     concordance = upb_df.iloc[i, 30]
    #     if pd.isna(concordance):
    #         concordance = None
    #
    #     if (pd.isna(pb6_u8) and pd.isna(pb6_u8_err) and pd.isna(pb7_pb6) and pd.isna(pb7_pb6_err) and
    #             pd.isna(pb6_u8_age) and pd.isna(pb6_u8_age_err) and pd.isna(pb7_u5_age) and pd.isna(pb7_u5_age_err) and
    #             pd.isna(pb7_pb6_age) and pd.isna(pb7_pb6_age_err) and pd.isna(best_age) and pd.isna(best_age_err)):
    #         continue
    #     print(f'importing {spot_name} data')
    #     try:
    #         conn = sqlite3.connect(db)
    #         cursor = conn.cursor()
    #         # check if analysis is in the database
    #         cursor.execute(f'''SELECT UPbAnalysisID FROM UPbAnalyses WHERE
    #                         iif(:spot_id IS NULL, SpotID IS NULL, SpotID = :spot_id) AND
    #                         iif(:reference_id IS NULL, "ReferenceID" IS NULL, "ReferenceID" = :reference_id) AND
    #                         iif(:lab_facility_id IS NULL, LabFacilityID IS NULL, LabFacilityID = :lab_facility_id) AND
    #                         iif(:instrument_id IS NULL, InstrumentID IS NULL, InstrumentID = :instrument_id) AND
    #                         iif(:method_id IS NULL, UPbAnalysisMethodID IS NULL, UPbAnalysisMethodID = :method_id) AND
    #                         iif(:pb7_pb6 IS NULL, "207Pb/206Pb" IS NULL, "207Pb/206Pb" = :pb7_pb6) AND
    #                         iif(:pb7_pb6_err IS NULL, "207Pb/206PbError" IS NULL, "207Pb/206PbError" = :pb7_pb6_err) AND
    #                         iif(:pb7_u5 IS NULL, "207Pb/235U" IS NULL, "207Pb/235U" = :pb7_u5) AND
    #                         iif(:pb7_u5_err IS NULL, "207Pb/235UError" IS NULL, "207Pb/235UError" = :pb7_u5_err) AND
    #                         iif(:pb6_u8 IS NULL, "206Pb/238U" IS NULL, "206Pb/238U" = :pb6_u8) AND
    #                         iif(:pb6_u8_err IS NULL, "206Pb/238UError" IS NULL, "206Pb/238UError" = :pb6_u8_err) AND
    #                         iif(:ratio_error_format_id IS NULL, "RatioErrorFormatID" IS NULL, "RatioErrorFormatID" = :ratio_error_format_id) AND
    #                         iif(:rho IS NULL, "ErrorCorr/Rho" IS NULL, "ErrorCorr/Rho" = :rho) AND
    #                         iif(:pb7_pb6_age IS NULL, "207Pb/206PbAge" IS NULL, "207Pb/206PbAge" = :pb7_pb6_age) AND
    #                         iif(:pb7_pb6_age_err IS NULL, "207Pb/206PbAgeError" IS NULL, "207Pb/206PbAgeError" = :pb7_pb6_age_err) AND
    #                         iif(:pb7_u5_age IS NULL, "207Pb/235UAge" IS NULL, "207Pb/235UAge" = :pb7_u5_age) AND
    #                         iif(:pb7_u5_age_err IS NULL, "207Pb/235UAgeError" IS NULL, "207Pb/235UAgeError" = :pb7_u5_age_err) AND
    #                         iif(:pb6_u8_age IS NULL, "206Pb/238UAge" IS NULL, "206Pb/238UAge" = :pb6_u8_age) AND
    #                         iif(:pb6_u8_age_err IS NULL, "206Pb/238UAgeError" IS NULL, "206Pb/238UAgeError" = :pb6_u8_age_err) AND
    #                         iif(:best_age IS NULL, "BestAge" IS NULL, "BestAge" = :best_age) AND
    #                         iif(:best_age_err IS NULL, "BestAgeError" IS NULL, "BestAgeError" = :best_age_err) AND
    #                         iif(:age_error_format_id IS NULL, "AgeErrorFormatID" IS NULL, "AgeErrorFormatID" = :age_error_format_id) AND
    #                         iif(:concordance IS NULL, "Concordance" IS NULL, "Concordance" = :concordance) AND
    #                         iif(:concordance_format_id IS NULL, "ConcordanceFormatID" IS NULL, "ConcordanceFormatID" = :concordance_format_id) AND
    #                         iif(:spot_size IS NULL, "SpotSize" IS NULL, "SpotSize" = :spot_size) AND
    #                         iif(:spot_size_unit_id IS NULL, "SpotSizeUnitID" IS NULL, "SpotSizeUnitID" = :spot_size_unit_id)''',
    #                        {'spot_id': spot_id, 'reference_id': reference_id, 'lab_facility_id': lab_facility_id,
    #                         'instrument_id': instrument_id, 'method_id': method_id, 'pb7_pb6': pb7_pb6,
    #                         'pb7_pb6_err': pb7_pb6_err,
    #                         'pb7_u5': pb7_u5, 'pb7_u5_err': pb7_u5_err, 'pb6_u8': pb6_u8, 'pb6_u8_err': pb6_u8_err,
    #                         'ratio_error_format_id': ratio_error_format_id, 'rho': rho, 'pb7_pb6_age': pb7_pb6_age,
    #                         'pb7_pb6_age_err': pb7_pb6_age_err, 'pb7_u5_age': pb7_u5_age,
    #                         'pb7_u5_age_err': pb7_u5_age_err,
    #                         'pb6_u8_age': pb6_u8_age, 'pb6_u8_age_err': pb6_u8_age_err, 'best_age': best_age,
    #                         'best_age_err': best_age_err, 'age_error_format_id': age_error_format_id,
    #                         'concordance': concordance,
    #                         'concordance_format_id': concordance_format_id, 'spot_size': spot_size,
    #                         'spot_size_unit_id': spot_size_unit_id})
    #         analysis_id = cursor.fetchone()
    #         if analysis_id is None:
    #             # if not, add it to the database
    #             print(f'Adding {spot_name} analysis to the database')
    #             cursor.execute(f'''INSERT INTO UPbAnalyses (SpotID, "ReferenceID", LabFacilityID, InstrumentID,
    #                         UPbAnalysisMethodID, "207Pb/206Pb", "207Pb/206PbError", "207Pb/235U", "207Pb/235UError",
    #                         "206Pb/238U", "206Pb/238UError", "RatioErrorFormatID", "ErrorCorr/Rho", "207Pb/206PbAge",
    #                         "207Pb/206PbAgeError", "207Pb/235UAge", "207Pb/235UAgeError", "206Pb/238UAge",
    #                         "206Pb/238UAgeError", "BestAge", "BestAgeError", "AgeErrorFormatID", AgeUnitID,
    #                         "Concordance", "ConcordanceFormatID", SpotSize, SpotSizeUnitID)
    #                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    #                      (spot_id, reference_id, lab_facility_id, instrument_id, method_id, pb7_pb6,
    #                         pb7_pb6_err, pb7_u5, pb7_u5_err, pb6_u8, pb6_u8_err, ratio_error_format_id, rho,
    #                         pb7_pb6_age, pb7_pb6_age_err, pb7_u5_age, pb7_u5_age_err, pb6_u8_age, pb6_u8_age_err,
    #                         best_age, best_age_err, age_error_format_id, age_unit_id, concordance,
    #                         concordance_format_id, spot_size, spot_size_unit_id))
    #             conn.commit()
    #             cursor.execute(f'''SELECT UPbAnalysisID FROM UPbAnalyses WHERE
    #                         iif(:spot_id IS NULL, SpotID IS NULL, SpotID = :spot_id) AND
    #                         iif(:reference_id IS NULL, "ReferenceID" IS NULL, "ReferenceID" = :reference_id) AND
    #                         iif(:lab_facility_id IS NULL, LabFacilityID IS NULL, LabFacilityID = :lab_facility_id) AND
    #                         iif(:instrument_id IS NULL, InstrumentID IS NULL, InstrumentID = :instrument_id) AND
    #                         iif(:method_id IS NULL, UPbAnalysisMethodID IS NULL, UPbAnalysisMethodID = :method_id) AND
    #                         iif(:pb7_pb6 IS NULL, "207Pb/206Pb" IS NULL, "207Pb/206Pb" = :pb7_pb6) AND
    #                         iif(:pb7_pb6_err IS NULL, "207Pb/206PbError" IS NULL, "207Pb/206PbError" = :pb7_pb6_err) AND
    #                         iif(:pb7_u5 IS NULL, "207Pb/235U" IS NULL, "207Pb/235U" = :pb7_u5) AND
    #                         iif(:pb7_u5_err IS NULL, "207Pb/235UError" IS NULL, "207Pb/235UError" = :pb7_u5_err) AND
    #                         iif(:pb6_u8 IS NULL, "206Pb/238U" IS NULL, "206Pb/238U" = :pb6_u8) AND
    #                         iif(:pb6_u8_err IS NULL, "206Pb/238UError" IS NULL, "206Pb/238UError" = :pb6_u8_err) AND
    #                         iif(:ratio_error_format_id IS NULL, "RatioErrorFormatID" IS NULL, "RatioErrorFormatID" = :ratio_error_format_id) AND
    #                         iif(:rho IS NULL, "ErrorCorr/Rho" IS NULL, "ErrorCorr/Rho" = :rho) AND
    #                         iif(:pb7_pb6_age IS NULL, "207Pb/206PbAge" IS NULL, "207Pb/206PbAge" = :pb7_pb6_age) AND
    #                         iif(:pb7_pb6_age_err IS NULL, "207Pb/206PbAgeError" IS NULL, "207Pb/206PbAgeError" = :pb7_pb6_age_err) AND
    #                         iif(:pb7_u5_age IS NULL, "207Pb/235UAge" IS NULL, "207Pb/235UAge" = :pb7_u5_age) AND
    #                         iif(:pb7_u5_age_err IS NULL, "207Pb/235UAgeError" IS NULL, "207Pb/235UAgeError" = :pb7_u5_age_err) AND
    #                         iif(:pb6_u8_age IS NULL, "206Pb/238UAge" IS NULL, "206Pb/238UAge" = :pb6_u8_age) AND
    #                         iif(:pb6_u8_age_err IS NULL, "206Pb/238UAgeError" IS NULL, "206Pb/238UAgeError" = :pb6_u8_age_err) AND
    #                         iif(:best_age IS NULL, "BestAge" IS NULL, "BestAge" = :best_age) AND
    #                         iif(:best_age_err IS NULL, "BestAgeError" IS NULL, "BestAgeError" = :best_age_err) AND
    #                         iif(:age_error_format_id IS NULL, "AgeErrorFormatID" IS NULL, "AgeErrorFormatID" = :age_error_format_id) AND
    #                         iif(:concordance IS NULL, "Concordance" IS NULL, "Concordance" = :concordance) AND
    #                         iif(:concordance_format_id IS NULL, "ConcordanceFormatID" IS NULL, "ConcordanceFormatID" = :concordance_format_id) AND
    #                         iif(:spot_size IS NULL, "SpotSize" IS NULL, "SpotSize" = :spot_size) AND
    #                         iif(:spot_size_unit_id IS NULL, "SpotSizeUnitID" IS NULL, "SpotSizeUnitID" = :spot_size_unit_id)''',
    #                        {'spot_id': spot_id, 'reference_id': reference_id, 'lab_facility_id': lab_facility_id,
    #                          'instrument_id': instrument_id, 'method_id': method_id, 'pb7_pb6': pb7_pb6, 'pb7_pb6_err': pb7_pb6_err,
    #                          'pb7_u5': pb7_u5, 'pb7_u5_err': pb7_u5_err, 'pb6_u8': pb6_u8, 'pb6_u8_err': pb6_u8_err,
    #                          'ratio_error_format_id': ratio_error_format_id, 'rho': rho, 'pb7_pb6_age': pb7_pb6_age,
    #                          'pb7_pb6_age_err': pb7_pb6_age_err, 'pb7_u5_age': pb7_u5_age, 'pb7_u5_age_err': pb7_u5_age_err,
    #                          'pb6_u8_age': pb6_u8_age, 'pb6_u8_age_err': pb6_u8_age_err, 'best_age': best_age,
    #                          'best_age_err': best_age_err, 'age_error_format_id': age_error_format_id, 'concordance': concordance,
    #                          'concordance_format_id': concordance_format_id, 'spot_size': spot_size, 'spot_size_unit_id': spot_size_unit_id})
    #             analysis_id = cursor.fetchone()
    #             if analysis_id is None:
    #                 print(f"Failed to add analysis {spot_name} to the database")
    #                 return
    #         analysis_id = analysis_id[0]
    #         conn.commit()
    #         conn.close()
    #     except sqlite3.Error as e:
    #         print(f"SQLite error: {e}")
    #         return

if __name__ == "__main__":
    Puetz_importer()
