#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project

import sqlite3
import logging
import re

from core import db

validConfigKeys = ['useMetadataTitle', 'dontEmbedThumbnail', 'startingRateLimit']
"""
list of valid configuration keys
"""

configValidValues = {
	'useMetadataTitle': ('whether to add the title extracted from the track to the file metadata and filename', ['0', '1'], '0'),
	'dontEmbedThumnail': ('disable the inclusion of thumbnails in the downloaded file', ['0', '1'], '0'),
	'startingRateLimit': ('download rate limit to start off with', r'^[0-9]+$', '6')
}
"""
dictionary of valid values for each key, dict key is config key,
value is tuple containing a string describing the meaning of the key and it's values, as well as either a list of
allowable values or a regex, followed by the default value
Examples: 
'useMetadataTitle': ('whether to add the title extracted from the title to the file metadata and filename', ['0', '1'], '0')
'anOptionThatTakesAnyPositiveNumber': ('it takes a positive number', r'^[0-9]+$', '5')
"""

def checkConfigValueValidity(key: str, valueToCheck: str) -> bool:
	"""
	check if a value will be valid for a given key, true if it is, false if it isn't
	"""
	test = configValidValues[key][1]
	if type(test) == list:
		return True if valueToCheck in test else False
	elif type(test) == str:
		regex = re.compile(test)
		return True if regex.match(valueToCheck) != None else False

def doesValueUseRegex(key: str) -> bool:
	"""
	checks if the provided key uses regex to define it's valid values
	"""
	return True if type(configValidValues[key][1]) == str else False

def getDefaultValue(key: str) -> str:
	"""
	returns the default value for the given config key, or None if the key was invalid
	"""
	if key not in validConfigKeys:
		return None
	else: 
		return configValidValues[key][2]

def getConfig(connection: sqlite3.Connection, key: str) -> str:
	"""
	fetch the value corresponding to a key from the database, returns the key's default by default
	"""
	log = logging.getLogger('config/getConfig')

	if key not in validConfigKeys:
		log.warn("tried to get invalid key")
		return None
	
	cursor = connection.cursor()
	cursor.execute("SELECT value FROM config WHERE key = :key LIMIT 1", {"key": key,})
	result = cursor.fetchone()
	if result != None:
		result = result[0]

	if result == None:
		#log.debug("tried to fetch a key that wasn't in the db")
		cursor.close()
		return configValidValues[key][2]
	else:
		cursor.close()
		return result

def setConfig(connection: sqlite3.Connection, key: str, value: str) -> bool:
	"""
	add key/value pair to database config table, return True if key and value were valid, False if it wasn't
	"""
	log = logging.getLogger('config/setConfig')

	if key not in validConfigKeys: #don't want to put bad keys in db where something might try to use them
		log.warn("tried to set invalid key")
		return False
	
	if not checkConfigValueValidity(key, value):
		return False

	cursor = connection.cursor()
	cursor.execute("SELECT * FROM config WHERE key = :key", {"key": key,}) #check if the key is already there
	if cursor.fetchall():
		cursor.execute("SELECT * FROM config WHERE key = :key AND value = :value", {"key": key, "value": value}) #if it's not only there, but the same value, there's no need to do the op
		if cursor.fetchall():
			log.debug("tried to set key/value pair to identical key/value pair, not bothering")
			cursor.close()
			return True

		log.debug('key already in db, updating value')
		cursor.execute("UPDATE config SET value = :value WHERE key = :key", {"key": key, "value": value}) #update the value
	
	else:
		log.debug("key not in db, adding")
		cursor.execute("INSERT INTO config (key, value) VALUES (:key, :value)", {"key": key, "value": value}) #insert key/value pair

	connection.commit() #must always remember to clean up, just don't clear the table! hehehe
	cursor.close()
	return True

def removeConfig(connection: sqlite3.Connection, key: str) -> bool:
	"""
	delete a config key from the db, or every key in the db if the key is 'all', returns False if key is invalid
	"""
	log = logging.getLogger('config/removeConfig')

	if key not in validConfigKeys + ['all',]:
		log.debug('cannot delete invalid keys')
		return False

	cursor = connection.cursor() #wipe the lot of them if the key is 'all'
	if key == 'all':
		cursor.execute('DELETE FROM config')
		return True

	cursor.execute("SELECT * FROM config WHERE key = ?", (key, )) #check if the key is in db
	if cursor.fetchall():
		log.debug('key present, deleting')
		cursor.execute("DELETE FROM config WHERE key = :key", {'key': key,})

	else:
		log.debug('key not present in db, cannot delete')

	connection.commit()
	cursor.close()
	return True

def showConfig(connection: sqlite3.Connection, key: str) -> list:
	"""
	return the value of the given key, or everything in the db if the key is 'all'. Returns list of tuples, or None if the key is invalid
	"""
	log = logging.getLogger('config/showConfig')

	if key not in validConfigKeys + ['all',]:
		log.debug('cannot show invalid keys')
		return None
	
	cursor = connection.cursor()
	if key == 'all':
		cursor.execute("SELECT * FROM config")
		result = cursor.fetchall()
	
	else:
		cursor.execute("SELECT * FROM config WHERE key = :key LIMIT 1", {'key': key,})
		result = cursor.fetchone()[1]
	
	cursor.close()
	return result