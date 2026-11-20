from collections import namedtuple

from PyQt6 import QtCore as QtC


# Map model column names back to database items
table_model_cols = namedtuple('table_model_cols', ['model_col_name', 'reference_table', 'table_cols', 'tag_table'])
sample_name = table_model_cols("Sample Name", "Samples", ["SampleName"], '')
age = table_model_cols("Age (Ma)", "Samples", ["AverageAge", "AverageAgeError"], '')
age_signature = table_model_cols("Age Signatures", "AgeSignatures", ["AgeSignatureName"], "Samples_AgeSignatures")

eventTypeNames = {event_type: event_type.name for event_type in QtC.QEvent.Type}

