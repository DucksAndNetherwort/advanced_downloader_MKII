#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
import sqlite3
from sqlite3 import Error
import logging
from pathlib import Path

from core.type import metadata_t, metadata_adapter, convertMetadata
from core.dl import getPlaylistInfo

dbname = Path("playlist.db")

tracksTable = 'tracks'
playlistsTable = 'playlists'
configTable = 'config'

def connect(path: str) -> sqlite3.Connection:
	"""
	Attempts to connect to a database at the given path, returning a connection to said database.
	"""
	log = logging.getLogger('db/connect')

	sqlite3.register_converter('metadata', metadata_adapter)

	connection = None
	try:
		connection = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
		log.debug(f"Connection to SQLite DB at {str(path)} successful")
	except Error as e:
		log.debug(f"The error '{e}' occurred")

	return connection

def checkdbPath(dbPath: str) -> Path:
	"""
	Checks if a db path is valid, creating any directories as needed, and returns a path to a database file,
	raising TypeError (e.g. for argparse type verification) if the path points to the wrong sort of file.
	"""
	log = logging.getLogger('db/checkdbPath')

	path = Path(dbPath.strip()).resolve()
	
	if (not path.suffix in ('', dbname.suffix)) and (not path.name == dbname.name): #if the path points to a file with an extension and isn't pointing to playlist.db, it's invalid
		log.debug('path points to an invalid file type')
		raise TypeError

	if not path.exists(): #if the directory does not exist, create it
		log.debug("directory being checked does not exist")
		path.mkdir(parents=True)

	if path.is_dir(): #if the path points to an existing directory, append the standard db name and return
		log.debug('db path is directory')
		return path/dbname

	if path.name == dbname.name and path.suffix == dbname.suffix: #if the path points to a db file, just return it as the correct type
		return Path(path)
	
	log.debug('this log command should never be able to run, if it does I am confuse')

def checkDB(connection: sqlite3.Connection) -> bool:
	"""
	Checks if the given database meets the format requirements, returning True only if requirements are met
	"""
	log = logging.getLogger('db/checkDB')

	cursor = connection.cursor()

	
	required_tracksTable_columns = ['id', 'filename', 'metadata', 'playlists'] #columns and types required for the tracks table
	required_tracksTable_column_types = ['TEXT', 'TEXT', 'metadata', 'TEXT']

	required_playlistsTable_columns = ['id', 'name'] #columns and types required for the playlists table
	required_playlistsTable_column_types = ['TEXT', 'TEXT']

	required_configTable_columns = ['key', 'value'] #columns and types required for the playlists table
	required_configTable_column_types = ['TEXT', 'TEXT']


	cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
	tables = cursor.fetchall()
	table_names = [table[0] for table in tables]

	# Check if the required tables exist in the database
	if tracksTable in table_names and playlistsTable in table_names and configTable in table_names:
		# Check if the required columns exist in tracks table
		cursor.execute(f"PRAGMA table_info({tracksTable});")
		tracksTable_columns = cursor.fetchall()
		tracksTable_column_names = [column[1] for column in tracksTable_columns]

		# Check if the required columns exist in playlists table
		cursor.execute(f"PRAGMA table_info({playlistsTable});")
		playlistsTable_columns = cursor.fetchall()
		playlistsTable_column_names = [column[1] for column in playlistsTable_columns]

		# Check if the required columns exist in config table
		cursor.execute(f"PRAGMA table_info({configTable});")
		configTable_columns = cursor.fetchall()
		configTable_column_names = [column[1] for column in configTable_columns]

		# Check if the tables and columns exist, and their data types match
		tracksTable_valid = (
			set(required_tracksTable_columns) <= set(tracksTable_column_names) and
			all(column[2] == required_type for column, required_type in zip(tracksTable_columns, required_tracksTable_column_types))
		)
		playlistsTable_valid = (
			set(required_playlistsTable_columns) <= set(playlistsTable_column_names) and
			all(column[2] == required_type for column, required_type in zip(playlistsTable_columns, required_playlistsTable_column_types))
		)
		configTable_valid = (
			set(required_configTable_columns) <= set(configTable_column_names) and
			all(column[2] == required_type for column, required_type in zip(configTable_columns, required_configTable_column_types))
		)

		# Return True if the tables and columns exist with correct data types, False otherwise
		cursor.close()
		return ((tracksTable_valid and playlistsTable_valid) and configTable_valid)

	cursor.close()
	return False

def initializeDB(connection: sqlite3.Connection) -> bool:
	"""
	Attempts to initialize the supplied DB.
	Returns True on successful initialization, False otherwise.
	"""
	log = logging.getLogger('db/initializeDB')

	cursor = connection.cursor()

	tracksTable_schema = f'''
		CREATE TABLE IF NOT EXISTS {tracksTable} (
			id TEXT,
			filename TEXT,
			metadata metadata,
			playlists TEXT
		);
	'''

	playlistsTable_schema = f'''
		CREATE TABLE IF NOT EXISTS {playlistsTable} (
			id TEXT,
			name TEXT
		);
	'''

	configTable_schema = f'''
		CREATE TABLE IF NOT EXISTS {configTable} (
			key TEXT,
			value TEXT
		);
	'''

	cursor.execute(tracksTable_schema)
	cursor.execute(playlistsTable_schema)
	cursor.execute(configTable_schema)

	connection.commit()
	cursor.close()

	success = checkDB(connection)
	if(not success):
		log.debug('for some reason DB initialization failed')
	return(success)

def addPlaylist(connection: sqlite3.Connection, playlistId: str) -> None:
	"""
	add a youtube playlist to the local database
	"""
	log = logging.getLogger('db/addPlaylist')
	
	cursor = connection.cursor()
	cursor.execute("SELECT * FROM playlists WHERE id = ?", (playlistId, ))
	if cursor.fetchall():
		log.debug('playlist is already in db')
		return

	playlistName = getPlaylistInfo(playlistId).get('title', 'bad playlist') #['title']
	if playlistName == 'bad playlist':
		log.fatal('playlist was no good, exiting')
		exit(1)
	
	cursor.execute("INSERT INTO playlists (id, name) VALUES (:id, :name)", {"id": playlistId, "name": playlistName})
	connection.commit()
	cursor.close()

def getPlaylists(connection: sqlite3.Connection) -> list[str]:
	"""
	returns a list of IDs for all the playlists that have been added to the database
	"""
	log = logging.getLogger("db/getPlaylists")
	cursor = connection.cursor()
	cursor.execute("SELECT id FROM playlists")
	raw = cursor.fetchall()
	cursor.close()

	clean = []
	for item in raw:
		clean.append(item[0])

	return clean

def getPlaylistNameFromID(connection: sqlite3.Connection, id: str) -> str:
	"""
	get the name of a playlist in the database from the id for that playlist
	"""
	cursor = connection.cursor()
	cursor.execute("SELECT name FROM playlists WHERE id = :id", {'id': id,})
	result = cursor.fetchone()[0]
	cursor.close()
	return result
	"""
	split a playlist string from the db into a list of playlist ids
	"""
	return string.split(', ')

def getAllDownloadedTracks(connection: sqlite3.Connection) -> dict:
	"""
	returns a dict of lists with every track that has been previously downloaded, irrespective of the source playlist. Uses the same naming as the tracks table columns
	"""
	log = logging.getLogger('db/getAllDownloadedTrackIDs')
	cursor = connection.cursor()

	result = {'id': [], 'filename': [], 'metadata': [], 'playlists': []}
	cursor.execute("SELECT id, filename, metadata, playlists FROM tracks")
	for index, item in enumerate(cursor.fetchall()):
		result['id'].append(item[0])
		result['filename'].append(item[1])
		result['metadata'].append(item[2])
		result['playlists'].append(item[3].split(' '))

	cursor.close()
	return result

def updateTrackPlaylists(connection: sqlite3.Connection, id: str, newPlaylists: list[str]) -> None:
	cursor = connection.cursor()

	newPlaylistString = ' '.join(newPlaylists)
	cursor.execute('UPDATE tracks SET playlists = :newPlaylists WHERE id = :id', {'id': id, 'newPlaylists': newPlaylistString})

	connection.commit()
	cursor.close()
	return

def addTrack(connection: sqlite3.Connection, id: str, filename: str, metadata: metadata_t, playlistIDs: list[str]) -> None:
	"""
	adds a track to the database
	"""
	log = logging.getLogger('db/addPlaylist')
	
	cursor = connection.cursor()
	cursor.execute("SELECT * FROM playlists WHERE id = ?", (id, ))
	if cursor.fetchall():
		log.debug('track is already in db')
		return

	cursor.execute("INSERT INTO tracks (id, filename, metadata, playlists) VALUES (:id, :filename, :metadata, :playlists)", {"id": id, "filename": filename, "metadata": convertMetadata(metadata), "playlists": ' '.join(playlistIDs)})
	connection.commit()
	cursor.close()


'''
tables: tracks, playlists, config
columns(tracks): id (text) | filename (text) | metadata (metadata type) | playlists (text, space seperated)
columns(playlists): id (text) | name (text)
columns(config): key (text) | value (text)
'''