def create_source(self):
    self.model.setTable('Sources')
    newSource = self.model.record()
    source = ('', '', '', '', '', '')
    newSource.setValue('Authors', source[0])
    newSource.setValue('Year', source[1])
    newSource.setValue('Title', source[2])
    newSource.setValue('Source', source[3])
    newSource.setValue('doi', source[4])
    newSource.setValue('Short Citation', source[5])
    if self.model.insertRecord(-1, newSource) is True:
        self.model.submitAll()
        '''This will commit all previous changes too, 
        but we only want to change the model before committing to the database'''


def create_region(self):
    self.model.setTable('Regions')
    newRegion = self.model.record()
    source = ('', '')
    newRegion.setValue('Name', source[0])
    newRegion.setValue('Description', source[1])
    if self.model.insertRecord(-1, newRegion) is True:
        self.model.submitAll()
        self.display_table()


def create_setting(self):
    self.model.setTable('Settings')
    newSetting = self.model.record()
    source = ('', '')
    newSetting.setValue('Name', source[0])
    newSetting.setValue('Description', source[1])
    if self.model.insertRecord(-1, newSetting) is True:
        self.model.submitAll()
        self.display_table()


def create_rocktype(self):
    self.model.setTable('Rock Types')
    newRockType = self.model.record()
    source = ('', '')
    newRockType.setValue('Name', source[0])
    newRockType.setValue('Description', source[1])
    if self.model.insertRecord(-1, newRockType) is True:
        self.model.submitAll()
        self.display_table()


def create_unit(self):
    self.model.setTable('Units')
    newUnit = self.model.record()
    source = ('', '')
    newUnit.setValue('Name', source[0])
    newUnit.setValue('Description', source[1])
    if self.model.insertRecord(-1, newUnit) is True:
        self.model.submitAll()
        self.display_table()


def create_agesignature(self):
    self.model.setTable('Age Signatures')
    newAgeSignature = self.model.record()
    source = ('', '')
    newAgeSignature.setValue('Name', source[0])
    newAgeSignature.setValue('Description', source[1])
    if self.model.insertRecord(-1, newAgeSignature) is True:
        self.model.submitAll()
        self.display_table()

# def create_sample(self):
#     self.model.setTable('Samples')
#     newSample = self.model.record()
#     source = ('', '', '', '', '', '')
#     newSample.setValue('Authors', source[0])
#     newSample.setValue('Year', source[1])
#     newSample.setValue('Title', source[2])
#     newSample.setValue('Source', source[3])
#     newSample.setValue('doi', source[4])
#     newSample.setValue('Short Citation', source[5])
#     if self.model.insertRecord(-1, newSample) is True:
#         self.model.submitAll()
#         self.display_table()