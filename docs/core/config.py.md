This file handles the database based configuration, storing a form of key/value pair in the `config` table of the playlist database

- [[#validConfigKeys|validConfigKeys]]
- [[#Functions|Functions]]
- [[#Functions#setConfig(connection: sqlite3.Connection, key: str, value: str) -> bool:|setConfig(connection: sqlite3.Connection, key: str, value: str) -> bool:]]
- [[#Functions#removeConfig(connection: sqlite3.Connection, key: str) -> bool:|removeConfig(connection: sqlite3.Connection, key: str) -> bool:]]
- [[#Functions#showConfig(connection: sqlite3.Connection, key: str) -> list:|showConfig(connection: sqlite3.Connection, key: str) -> list:]]

### validConfigKeys
The `validConfigKeys` list variable is used to keep track of what keys are considered valid/legal

## configValidValues
dictionary of valid values for each key, dict key is config key,

value is tuple containing a string describing the meaning of the key and it's values, as well as either a list of
allowable values or a regex, followed by the default value
Examples:
'useMetadataTitle': ('whether to add the title extracted from the title to the file metadata and filename', \['0', '1'\], '0')
'anOptionThatTakesAnyPositiveNumber': ('it takes a positive number', r'\[0-9\]+', '5')

## Functions

### setConfig(connection: sqlite3.Connection, key: str, value: str) -> bool:
`setConfig` takes a database connection along with a key/value pair,
and will set the given key in the database to the given value, creating the key if needed.
Returns `True` if the key was valid, i.e. found in `validConfigKeys` and the value was allowed for the key, or `False` if it is found to be invalid, or the value is not allowed

### removeConfig(connection: sqlite3.Connection, key: str) -> bool:
`removeConfig` takes a database connection along with a key,
and removes the key from the database.
If the key is `all`, it will wipe the entire configuration
Like `setConfig`, it returns `True` only if the key was valid, and `False` otherwise.

### showConfig(connection: sqlite3.Connection, key: str) -> list:
`showConfig` takes a database connection and a key, returning a list of tuples.
Under normal conditions, it will return a list of one tuple containing the key/value pair
corresponding to the given key,
but when the key is `all`, the list will contain tuples for every key/value pair
found in the database.

Instead of returning a bool to indicate whether the key was valid, `showConfig` returns `None`
when the key is invalid