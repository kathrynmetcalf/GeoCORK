from Schema.GeoCORKTable import GeoCORKTable

class GeoCORKSchema()
    def __init__(self):


        RockTypes = GeoCORKTable('RockTypes', attributes, TableType.TREE, True, False, False, False, 'RockTypes', 'Samples_RockTypes', 'RockTypeID', 'SampleID')

        self.tables = [RockTypes]

        print(RockTypes.create_query())

        print(RockTypes.child_tables)


        for table in self.tables:
            if table.contains_foreign_keys
                # do something
                pass



