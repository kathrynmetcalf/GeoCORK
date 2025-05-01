import pandas as pd
import openpyxl
import sqlite3
import re

def mark_spot_contexts(full_data, db, set_contexts, concordance_classes):
    # Load the Excel file
    sheet_name = 'UPb_Data'
    try:
        upb_df = pd.read_excel(full_data, header=None, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        print(f"Failed to parse sheet with pandas:\n{e}")
        return
    while not upb_df.empty and upb_df.iloc[0].isna().all():
        upb_df = upb_df.iloc[1:].reset_index(drop=True)
    rows, cols = upb_df.shape

    set_context_ids = []
    concordance_class_ids = []
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for context in set_contexts:
            cursor.execute("SELECT SpotContextID FROM SpotContexts WHERE SpotContextName = ? COLLATE NOCASE", (context,))
            context_id = cursor.fetchone()
            if context_id is None:
                print(f"Failed to find {context} context.")
                continue
            set_context_ids.append(context_id[0])
        for context in concordance_classes:
            cursor.execute("SELECT SpotContextID FROM SpotContexts WHERE SpotContextName = ? COLLATE NOCASE", (context,))
            context_id = cursor.fetchone()
            if context_id is None:
                print(f"Failed to find {context} context.")
                continue
            concordance_class_ids.append(context_id[0])
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return


    for i in range(rows):
        spot_name = upb_df.iloc[i, 2]
        concordance_class = upb_df.iloc[i, 1]
        if pd.isna(spot_name):
            continue
        try:
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            cursor.execute("SELECT SpotID FROM Spots WHERE SpotName = ? COLLATE NOCASE", (spot_name,))
            spot_id = cursor.fetchone()
            if spot_id is None:
                print(f"Spot {spot_name} not found in the database.")
                continue
            spot_id = spot_id[0]
            for set_context_id in set_context_ids:
                cursor.execute("SELECT SpotID, SpotContextID FROM Spots_SpotContexts WHERE SpotID = ? AND SpotContextID = ?",
                               (spot_id, set_context_id))
                existing_context = cursor.fetchone()
                if not existing_context:
                    cursor.execute("INSERT INTO Spots_SpotContexts (SpotID, SpotContextID) VALUES (?, ?)",
                                   (spot_id, set_context_id))
                    conn.commit()
                    cursor.execute("SELECT SpotID, SpotContextID FROM Spots_SpotContexts WHERE SpotID = ? AND SpotContextID = ?",
                                   (spot_id, set_context_id))
                    existing_context = cursor.fetchone()
                    if not existing_context:
                        print(f"Failed to set {set_context_id} context for spot {spot_name}.")
                        return
            for concordance_pair in zip(concordance_classes, concordance_class_ids):
                if concordance_pair[0] == concordance_class:
                    cursor.execute("SELECT SpotID, SpotContextID FROM Spots_SpotContexts WHERE SpotID = ? AND SpotContextID = ?",
                                   (spot_id, concordance_pair[1]))
                    existing_context = cursor.fetchone()
                    if not existing_context:
                        cursor.execute("INSERT INTO Spots_SpotContexts (SpotID, SpotContextID) VALUES (?, ?)",
                                       (spot_id, concordance_pair[1]))
                        conn.commit()
                        cursor.execute("SELECT SpotID, SpotContextID FROM Spots_SpotContexts WHERE SpotID = ? AND SpotContextID = ?",
                                       (spot_id, concordance_pair[1]))
                        existing_context = cursor.fetchone()
                        if not existing_context:
                            print(f"Failed to set {concordance_pair[0]} context for spot {spot_name}.")
                            return
            # Set rejected to false for analyses of that spot
            cursor.execute("SELECT UPbAnalysisID FROM UPbAnalyses WHERE SpotID = ?", (spot_id,))
            upb_analysis_ids = cursor.fetchall()
            if upb_analysis_ids is None:
                print(f"UPbAnalysisID for spot {spot_name} not found.")
                continue
            for upb_analysis_id in upb_analysis_ids:
                cursor.execute("UPDATE UPbAnalyses SET Rejected = 1 WHERE UPbAnalysisID = ?", (upb_analysis_id,))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return

if __name__ == "__main__":
    # Set concordant igneous cores
    full_data = "/Users/kametcalf/Zotero/storage/XJGWJAFY/DB7_nonmetamorphic.xlsx"
    db = "path_to_your_database.db"
    set_contexts = ["Core", "Igneous"]
    concordance_classes = ["Concordance class 1", "Concordance class 2", "Concordance class 3"]
    mark_spot_contexts(full_data, db, set_contexts, concordance_classes)

    # Set concordant metamorphic cores
    full_data = "/Users/kametcalf/Zotero/storage/5Y79FY5E/DB12_DZ_cores_metamorphic.xlsx"
    db = "path_to_your_database.db"
    set_contexts = ["Core", "Metamorphic"]
    concordance_classes = ["Concordance class 1", "Concordance class 2", "Concordance class 3"]
    mark_spot_contexts(full_data, db, set_contexts, concordance_classes)

    # Set concordant rims
    full_data = "/Users/kametcalf/Zotero/storage/W3YAKPW5/DB11_DZ_rims.xlsx"
    db = "path_to_your_database.db"
    set_contexts = ["Rim"]
    concordance_classes = ["Concordance class 1", "Concordance class 2", "Concordance class 3"]
