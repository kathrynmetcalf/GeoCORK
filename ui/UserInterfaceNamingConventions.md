# GeoChron Naming Conventions for UI objects

## Static Objects
- **Static** objects are objects that are not expected to change during the lifetime of the user interface.
- Examples:
  -  Labels
  -  Spacings
  -  Layouts
- Naming Convention:
  -  **static** + **_** + **objectName** + **_** + **objectType** + **_** + **objectDescription**
  -  **objectName** is the name of the object
  -  **objectType** is the type of object (Label, Button, etc.)
  -  **objectDescription** is a description of the object (DatabaseAuthor, DatabaseName, etc.)

## Dynamic Objects
- **Dynamic** objects are objects that are expected to change during the lifetime of the user interface.
- Examples:
  -  Line Edits (le)
  -  Check Boxes (cb)
  -  Radio Buttons (rb)
- Naming Convention:
  -  **objectType** + **_** + **objectName** + + **_** + **objectDescription**
  -  **objectType** is the type of object (TextField, CheckBox, etc.)
  -  **objectName** is the name of the object
  - Examples:
    - **le_DatabaseAuthor**
    -  **cb_DatabaseName**
    -  **rb_DatabaseType**