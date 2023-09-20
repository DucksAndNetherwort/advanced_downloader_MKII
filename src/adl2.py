#!/usr/bin/env python3
#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
import logging
import argparse
from pathlib import Path
import sqlite3
import tqdm
from yt_dlp.utils import format_bytes
from time import sleep #I hate that I have to do this

from core import DescriptionParser, dl, db, config
from core.type import parserInput_t, metadata_t

parser = argparse.ArgumentParser( #get an argument parser
	prog = 'adl2.py',
	description = 'youtube playlist downloader intended to download and maintain large music libraries, now rewritten to actually be good',
	epilog = 'Written by Ducks And Netherwort (ducksnetherwort.ddns.net, github.com/DucksAndNetherwort)'
)

#logging.basicConfig(level='DEBUG') #pre startup logger

currentRateLimit = 6 #rate limit to use for downloading
decreaseLimitBy = 2 #amount to decrease the limit by each failure
increaseLimitBy = 0.5 #amount to increase limity by when things go well
rateLimited = False #whether the current attempt got rate limited

def connectDB(path: Path) -> sqlite3.Connection:
	"""
	Connect to, check, and initialize the database
	"""
	log = logging.getLogger('main/connectDB')

	connection = db.connect(path)
	if connection == None:
		log.fatal("db connection failure")
		exit(1)
	
	dbValid = db.checkDB(connection)
	if not dbValid:
		initSuccess = db.initializeDB(connection)
		if not initSuccess:
			log.fatal('failed to initialize the database')
			exit(1)
	
	return connection

def trackProgressHook(progressBar, progress):
	global currentRateLimit
	global decreaseLimitBy
	global increaseLimitBy
	global rateLimited

	# Update the overall progress bar with appropriate units
	log = logging.getLogger('trackProgressHook')
	if progress['status'] == 'downloading':
		progressBar.update(progress['downloaded_bytes'] - progressBar.n)
		progressBar.refresh()
	elif progress['status'] == 'error' and 'message' in progress:
		log.debug(f'got download error {progress["message"]}')
		if '429 Too Many Requests' or '403 Forbidden' in progress['message']:
			currentRateLimit = currentRateLimit - decreaseLimitBy
			if currentRateLimit < 4:
				currentRateLimit = 4

def update(connection: sqlite3.Connection, playlistDirectory: Path):
	log = logging.getLogger('update')
	log.info(f'updating playlist at {playlistDirectory}')
	bruh = logging.getLogger('yt-dlp').setLevel(logging.WARNING)

	global currentRateLimit
	global decreaseLimitBy
	global increaseLimitBy
	global rateLimited

	existing = db.getAllDownloadedTracks(connection)
	playlistIDs = db.getPlaylists(connection)
	allPlaylistItems = [[], []] #[0] is a list of track ids, [1] is a matching list of lists containing playlists the respective item belongs to
	for i, plID in enumerate(playlistIDs): #get all the items of the remote playlists and put them in allPlaylistItems
		log.info(f'fetching listing for remote playlist {db.getPlaylistNameFromID(connection, plID)} ({i + 1} of {len(playlistIDs)})')
		for track in dl.getPlaylist(plID):
			if track not in allPlaylistItems[0]:
				allPlaylistItems[0].append(track)
				allPlaylistItems[1].append([plID])
			else:
				index = allPlaylistItems[0].index(track)
				allPlaylistItems[1][index].append(plID)

	todo = []
	for index, id in enumerate(allPlaylistItems[0]): #make sure to only download what's needed, and update playlist lists only for incorrect items
		if id not in existing['id']:
			addition = [id, ] #[0] is the id, [1] is list of playlists it belongs to
			addition.append(allPlaylistItems[1][index])
			todo.append(addition)
		else:
			oldPlaylists = existing['playlists'][existing['id'].index(id)]
			if not oldPlaylists == allPlaylistItems[1][index]:
				db.updateTrackPlaylists(connection, id, allPlaylistItems[1][index])
		
	log.debug('constructing list of items to download')
	playlistItemsToDownload = [] #list of counts for how many items need to be downloaded for each playlist
	correspondingPlaylists = [] #list of playlist names with matching indexes
	for item in todo:
		for pl in item[1]:
			plname = db.getPlaylistNameFromID(connection, pl)
			if plname in correspondingPlaylists:
				playlistItemsToDownload[correspondingPlaylists.index(plname)] += 1
			else:
				correspondingPlaylists.append(plname)
				playlistItemsToDownload.append(1)

	log.info('finished constructing list of items to download')
	log.info(f'need to download {len(todo)} of {len(allPlaylistItems[0])} total remote playlist items')

	#time to actually start updating the playlist

	playlistBars = []
	for index, pl in enumerate(correspondingPlaylists):
		playlistBars.append(tqdm.tqdm(total=playlistItemsToDownload[index], leave=True, desc=pl, unit='track', unit_scale=True))
	
	parserMisses = [[], []] #store what uploaders are not available for parsing, and how many each one occurs. Maybe I'll even make use of it someday

	configRateLimit = int(config.getConfig(connection, 'startingRateLimit')) #get the starting rate limit from config
	if not configRateLimit == None:
		if configRateLimit > 0:
			currentRateLimit = configRateLimit
	
	for track in tqdm.tqdm(todo, leave=True, desc='Overall Progress', unit='track', unit_scale=True): #track[0] is the id, track[1] is the playlists
		parserInput: parserInput_t = parserInput_t(None, None, None, None)#collect parser input data
		parserInput.id = track[0]
		parserInput.uploader, parserInput.title, parserInput.description, filesizeEstimate = dl.getDescription(track[0])

		skipThisIteration = False
		if parserInput.title == None: #just in case a track is unavailable
			if 'Video unavailable' or 'Private video' in parserInput.uploader.msg:
				skipThisIteration = True
			else:
				log.fatal(f'Something went wrong getting the video description, the error was {parserInput.uploader}')
				exit(1)

		if not skipThisIteration:
			metadata = DescriptionParser.parse(parserInput)
			if not DescriptionParser.isPresent(parserInput.uploader): #perform checks and increments for the parser misses counter
				if parserInput.uploader in parserMisses[0]:
					parserMisses[1][parserMisses[0].index(parserInput.uploader)] += 1
				else:
					parserMisses[0].append(parserInput.uploader)
					parserMisses[1].append(1)

			filenameTitle = dl.filenameCleaner(parserInput.title)

			attempts = 0
			successes = 0
			success = False
			while not success:
				with tqdm.tqdm(unit="B", unit_scale=True, leave=False, desc=filenameTitle, total=filesizeEstimate) as trackBar:
					progressHook = [lambda data: trackProgressHook(trackBar, data)]
					success = dl.getTrack(parserInput.id, metadata, False if config.getConfig(connection, 'useMetadataTitle') == '0' else True, playlistDirectory, filenameTitle, f'{currentRateLimit}M', progressHook) #mom, can we have short function call? No, we have short function call at home. Short funtion call at home:

				if rateLimited:
					log.debug(f"got rate limited, after delay the new target will be {currentRateLimit}M")
					sleep(10)
					rateLimited = False

				attempts += 1
				if attempts > 2:
					log.warn('time to be a bit more aggressive with the rate limiting')
					decreaseLimitBy = decreaseLimitBy + 2

				if attempts > 4:
					log.fatal(f"youtube got huffy and isn't letting us download, exiting, last attempted rate limit is {currentRateLimit}")
					exit(1)
				
				successes = (successes + 1) if success else 0 #increment the successes counter if this was a success
				if successes > 3:
					currentRateLimit = currentRateLimit + increaseLimitBy
					successes = 0

		for playlist in track[1]: #increments each playlist progress bar the track is part of
			playlistBars[correspondingPlaylists.index(db.getPlaylistNameFromID(connection, playlist))].update(1)
		
		if not skipThisIteration:
			db.addTrack(connection, parserInput.id, filenameTitle + '.mp3', metadata, track[1])
		else:
			db.addTrack(connection, parserInput.id, 'failed', metadata_t(title=parserInput.uploader.msg), track[1])
	
	log.info('Playlist update completed, have a nice day!')

def main():
	cliArgs = True #true to get arguments from the command line, false for hardcoded args in fakeArgs
	fakeArgs = "--loglevel=DEBUG -p C:\\Users\\kyren\\Music\\DucksMix\\playlist.db -u".split()

	parser.add_argument('-p', '--playlist', type=db.checkdbPath, required=True, help='path to local playlist folder/database file')
	parser.add_argument('-u', '--update', action='store_true', help='update the local playlist')
	parser.add_argument('-a', '--addplaylist', type=str, help='youtube playlist link/id to add to the local playlist, must be done one at a time')
	parser.add_argument('--setconfig', action='append', nargs=2, help="first argument is the configuration option key, second is the new value")
	parser.add_argument('--removeconfig', action='append', help="remove a key from configuration, or use 'all' to clear all configuration")
	parser.add_argument('--showconfig', action='append', help="show the value of a configuration key, or 'all' to show the values of all config options in database")
	parser.add_argument('--loglevel', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='logging level, defaults to INFO')

	args = parser.parse_args() if cliArgs else parser.parse_args(fakeArgs)

	logging.basicConfig(level=args.loglevel) #set up logging
	log = logging.getLogger("Main")
	log.debug('parsed args and started logger')

	with connectDB(args.playlist) as dbConn:

		if(args.addplaylist):
			log.info(f'adding playlist {args.addplaylist}')
			if(len(args.addplaylist.split('=')) > 1):
				playlistId = args.addplaylist.split('=')[1].strip()
			else:
				playlistId = args.addplaylist.strip()
			
			db.addPlaylist(dbConn, playlistId)
			log.info(f'successfully added playlist "{db.getPlaylistNameFromID(dbConn, playlistId)}"')
		
		#process configuration changes

		if(args.removeconfig):
			for item in args.removeconfig:
				if config.removeConfig(dbConn, item):
					log.info(f"removed option \"{item}\"")
				else:
					log.error(f'cannot remove invalid config option \"{item}\"')
					exit(1)
		
		if(args.setconfig):
			for item in args.setconfig:
				if config.setConfig(dbConn, item[0], item[1]):
					log.info(f"set option \"{item[0]}\" to value \"{item[1]}\"")
				else:
					log.error(f'cannot set invalid config option \"{item[0]}\"')
					exit(1)
		
		if(args.showconfig):
			for item in args.showconfig:
				if not item == 'all':
					value = config.showConfig(dbConn, item)
					if not value == None:
						log.info(f"current value of \"{item}\" is \"{value}\"")
					else:
						log.error(f'cannot display invalid config option \"{item}\"')
						exit(1)
				
				else:
					result = config.showConfig(dbConn, item)
					log.info("printing config")
					for pair in result:
						log.info(f'{pair[0]}: {pair[1]}')
					log.info('config printed')
		
		if(args.update):
			update(dbConn, args.playlist.parent)

if(__name__ == "__main__"):
	main()