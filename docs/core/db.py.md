This file manages the database, and most database related tasks.

- [[#Global Variables|Global Variables]]
	- [[#Global Variables#dbname = Path("playlist.db")|dbname = Path("playlist.db")]]
	- [[#Global Variables#tracksTable = 'tracks'|tracksTable = 'tracks']]
	- [[#Global Variables#playlistsTable = 'playlists'|playlistsTable = 'playlists']]
	- [[#Global Variables#configTable = 'config'|configTable = 'config']]
- [[#Functions|Functions]]
	- [[#Functions#connect(path: str) -> sqlite3.Connection:|connect(path: str) -> sqlite3.Connection:]]
	- [[#Functions#checkdbPath(dbPath: str) -> Path:|checkdbPath(dbPath: str) -> Path:]]
	- [[#Functions#checkDB(connection: sqlite3.Connection) -> bool:|checkDB(connection: sqlite3.Connection) -> bool:]]
	- [[#Functions#initializeDB(connection: sqlite3.Connection) -> bool:|initializeDB(connection: sqlite3.Connection) -> bool:]]
	- [[#Functions#addPlaylist(connection: sqlite3.Connection, playlistId: str) -> None:|addPlaylist(connection: sqlite3.Connection, playlistId: str) -> None:]]
	- [[#Functions#getPlaylists(connection: sqlite3.Connection) -> list\[str\]:|getPlaylists(connection: sqlite3.Connection) -> list\[str\]:]]
	- [[#Functions#getPlaylistNameFromID(connection: sqlite3.Connection, id: str) -> str:|getPlaylistNameFromID(connection: sqlite3.Connection, id: str) -> str:]]
	- [[#Functions#getAllDownloadedTracks(connection: sqlite3.Connection) -> dict:|getAllDownloadedTracks(connection: sqlite3.Connection) -> dict:]]
	- [[#Functions#updateTrackPlaylists(connection: sqlite3.Connection, id: str, newPlaylists: str) -> None:|updateTrackPlaylists(connection: sqlite3.Connection, id: str, newPlaylists: str) -> None:]]

## Global Variables

### dbname = Path("playlist.db")
Contains a pathlib path that is just "playlist.db", used for validity checking

### tracksTable = 'tracks'
Contains the name for the database `tracks` table

### playlistsTable = 'playlists'
Contains the name for the database `playlists` table

### configTable = 'config'
Contains the name for the database `config` table

## Functions

### connect(path: str) -> sqlite3.Connection:
Attempts to connect to a database at the given path, returning a connection to the database if succesful, otherwise returning `None`.

### checkdbPath(dbPath: str) -> Path:
Checks a path to see if it points to a database of valid type, creating directories as needed,
returning the resulting path as a `pathlib` `Path`,
or raising `TypeError` if the path points to the wrong sort of file.
Intended for use with the `argparse` module for type checking.

### checkDB(connection: sqlite3.Connection) -> bool:
Checks the DB on the given connection to see if it meets all the requirements,
returning `True` if it does.

### initializeDB(connection: sqlite3.Connection) -> bool:
Initializes the database to meet the format requirements,
returns `True` if successful.

### addPlaylist(connection: sqlite3.Connection, playlistId: str) -> None:
Adds a YouTube playlist id to the database, automatically fetching the name for later use.

### getPlaylists(connection: sqlite3.Connection) -> list\[str\]:
Returns a `list` of all the YouTube playlist ids in the database.

### getPlaylistNameFromID(connection: sqlite3.Connection, id: str) -> str:
Takes a YouTube playlist id and returns it's name as saved in the database.

### getAllDownloadedTracks(connection: sqlite3.Connection) -> dict:
Returns a dict of lists containing information on every track previously downloaded.
The dict's contents are as follows:

| dict\["id"\] | dict\["filename"\] | dict\["metadata"\] | dict\["playlists"\] |
| ------------ | ------------------ | ------------------ | ------------------- |
| id as `str`  | filename as `str`  | metadata as `type.metadata_t` | list of playlist IDs, each as `str` type|

### updateTrackPlaylists(connection: sqlite3.Connection, id: str, newPlaylists: str) -> None:
Update the given id's list of YouTube playlist memberships to the given list.