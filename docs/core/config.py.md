This file handles the database based configuration, storing a form of key/value pair in the `config` table of the playlist database

- [[#validConfigKeys|validConfigKeys]]
- [[#Functions|Functions]]
- [[#Functions#setConfig(connection: sqlite3.Connection, key: str, value: str) -> bool:|setConfig(connection: sqlite3.Connection, key: str, value: str) -> bool:]]
- [[#Functions#removeConfig(connection: sqlite3.Connection, key: str) -> bool:|removeConfig(connection: sqlite3.Connection, key: str) -> bool:]]
- [[#Functions#showConfig(connection: sqlite3.Connection, key: str) -> list:|showConfig(connection: sqlite3.Connection, key: str) -> list:]]

### validConfigKeys
The `validConfigKeys` list variable is used to keep track of what keys are considered valid/legal

## Functions

### setConfig(connection: sqlite3.Connection, key: str, value: str) -> bool:
`setConfig` takes a database connection along with a key/value pair,
and will set the given key in the database to the given value, creating the key if needed.
Returns `True` if the key was valid, i.e. found in `validConfigKeys`, or `False` if it is found to be invalid

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