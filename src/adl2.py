#!/usr/bin/env python3
#Copyright (C) 2024  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
import logging
import logging.handlers
import argparse
from pathlib import Path
import sqlite3
import tqdm
from yt_dlp.utils import format_bytes
from time import sleep #I hate that I have to do this
import platform
import PySimpleGUI as sg

from core import DescriptionParser, dl, db, config
from core.type import parserInput_t, metadata_t

parser = argparse.ArgumentParser( #get an argument parser
	prog = 'adl2.py',
	description = 'youtube playlist downloader intended to download and maintain large music libraries, now rewritten to actually be good',
	epilog = 'Written by Ducks And Netherwort (ducksnetherwort.ddns.net, github.com/DucksAndNetherwort)'
)

#logging.basicConfig(level='DEBUG') #pre startup debug logger
buffer = ''

defaultLogLevel = 'INFO' #used if log level has not been set in config
logFileName = 'log.txt'

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

def trackProgressHook(window: sg.Window, progress):
	global currentRateLimit
	global decreaseLimitBy
	global increaseLimitBy
	global rateLimited

	# Update the overall progress bar with appropriate units
	log = logging.getLogger('trackProgressHook')
	if progress['status'] == 'downloading':
		window.write_event_value('progressUpdate', tuple(['download progress', progress['downloaded_bytes']]))
	elif progress['status'] == 'error' and 'message' in progress:
		log.debug(f'got download error {progress["message"]}')
		if '429 Too Many Requests' or '403 Forbidden' in progress['message']:
			currentRateLimit = currentRateLimit - decreaseLimitBy
			if currentRateLimit < 4:
				currentRateLimit = 4

def update(dbPath: str, window: sg.Window, playlistDirectory: Path, ffmpegPath: str = None):
	log = logging.getLogger('update')
	log.info(f'updating playlist at {playlistDirectory}')
	bruh = logging.getLogger('yt-dlp').setLevel(logging.WARNING)

	global currentRateLimit
	global decreaseLimitBy
	global increaseLimitBy
	global rateLimited

	connection = db.connect(dbPath)
	log.debug('got another db connection just for this thread')
	window.write_event_value('progressUpdate', ['starting', 1])
	
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

	window.write_event_value('progressUpdate', tuple(['started', len(todo)]))
	window.write_event_value('progressUpdate', tuple(['playlist totals', playlistItemsToDownload, correspondingPlaylists]))
	log.debug('sent startup data to GUI')

	'''playlistBars = []
	for index, pl in enumerate(correspondingPlaylists):
		playlistBars.append(tqdm.tqdm(total=playlistItemsToDownload[index], leave=True, desc=pl, unit='track', unit_scale=True))'''
	
	parserMisses = [[], []] #store what uploaders are not available for parsing, and how many each one occurs. Maybe I'll even make use of it someday

	configRateLimit = int(config.getConfig(connection, 'startingRateLimit')) #get the starting rate limit from config
	if not configRateLimit == None:
		if configRateLimit > 0:
			currentRateLimit = configRateLimit
	
	for iteration, track in enumerate(todo): #track[0] is the id, track[1] is the playlists
		window.write_event_value('progressUpdate', tuple(['overall progress', iteration]))
		parserInput: parserInput_t = parserInput_t(None, None, None, None)#collect parser input data
		parserInput.id = track[0]
		parserInput.uploader, parserInput.title, parserInput.description, filesizeEstimate = dl.getDescription(track[0])
		log.debug('fetched description')

		skipThisIteration = False
		if parserInput.title == None: #just in case a track is unavailable
			if 'Video unavailable' or 'Private video' in parserInput.uploader.msg:
				skipThisIteration = True
			else:
				log.fatal(f'Something went wrong getting the video description, the error was {parserInput.uploader}')
				exit(1)

		if not skipThisIteration:
			metadata = DescriptionParser.parse(parserInput)
			log.debug('parsed metadata')
			if not DescriptionParser.isPresent(parserInput.uploader): #perform checks and increments for the parser misses counter
				if parserInput.uploader in parserMisses[0]:
					parserMisses[1][parserMisses[0].index(parserInput.uploader)] += 1
				else:
					parserMisses[0].append(parserInput.uploader)
					parserMisses[1].append(1)
				window.write_event_value('progressUpdate', tuple(['parser misses', parserMisses]))

			filenameTitle = dl.filenameCleaner(parserInput.title)

			attempts = 0
			successes = 0
			success = False
			while not success:
				window.write_event_value('progressUpdate', tuple(['download size', filesizeEstimate]))
				progressHook = [lambda data: trackProgressHook(window, data)]
				log.debug('starting download')
				success = dl.getTrack(parserInput.id, metadata, False if config.getConfig(connection, 'useMetadataTitle') == '0' else True, playlistDirectory, filenameTitle, f'{currentRateLimit}M', progressHook, ffmpegPath) #mom, can we have short function call? No, we have short function call at home. Short funtion call at home:

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
				
				log.debug('download successful')
				successes = (successes + 1) if success else 0 #increment the successes counter if this was a success
				if successes > 3:
					currentRateLimit = currentRateLimit + increaseLimitBy
					successes = 0

		log.debug('updating progress bars')
		for playlist in track[1]: #increments each playlist progress bar the track is part of
			window.write_event_value('progressUpdate', tuple(['increment playlist', db.getPlaylistNameFromID(connection, playlist)]))
			#playlistBars[correspondingPlaylists.index(db.getPlaylistNameFromID(connection, playlist))].update(1)
		
		if not skipThisIteration:
			db.addTrack(connection, parserInput.id, filenameTitle + '.mp3', metadata, track[1])
		else:
			db.addTrack(connection, parserInput.id, 'failed', metadata_t(title=parserInput.uploader.msg), track[1])
	
	log.info('Playlist update completed, have a nice day!')

def main():
	cliArgs = True #true to get arguments from the command line, false for hardcoded args in fakeArgs
	fakeArgs = "--loglevel=DEBUG -p C:\\Users\\\\Music\\DucksMix\\playlist.db -u".split()

	parser.add_argument('-p', '--playlist', type=db.checkdbPath, required=True, help='path to local playlist folder/database file')
	parser.add_argument('-u', '--update', action='store_true', help='update the local playlist')
	parser.add_argument('-a', '--addplaylist', type=str, help='youtube playlist link/id to add to the local playlist, must be done one at a time')
	parser.add_argument('--setconfig', action='append', nargs=2, help="first argument is the configuration option key, second is the new value")
	parser.add_argument('--removeconfig', action='append', help="remove a key from configuration, or use 'all' to clear all configuration")
	parser.add_argument('--showconfig', action='append', help="show the value of a configuration key, or 'all' to show the values of all config options in database")
	parser.add_argument('--ffmpeglocation', default=('ffmpeg/ffmpeg.exe' if platform.system() == "Windows" and Path("ffmpeg/ffmpeg.exe").is_file() else None), help='specify a specific path to find ffmpeg') #might have to be tweaked for linux
	parser.add_argument('--loglevel', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='logging level, defaults to INFO')

	args = parser.parse_args() if cliArgs else parser.parse_args(fakeArgs)

	logging.basicConfig(level=args.loglevel) #set up logging
	log = logging.getLogger("Main")
	log.debug('parsed args and started logger')
	log.debug(f'ffmpeg path is {args.ffmpeglocation}')

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
			update(dbConn, args.playlist.parent, args.ffmpeglocation)

global totalRemoteItems
global remotePlaylistTotals
global correspondingRemotePlaylists
global remotePlaylistCounts

def guiMain():
	settings = sg.UserSettings(path='.', use_config_file=True, convert_bools_and_none=True)
	ffmpegPath: str = settings['config'].get('ffmpegPath', ('ffmpeg/ffmpeg.exe' if platform.system() == "Windows" and Path("ffmpeg/ffmpeg.exe").is_file() else None))
	progressBarHeight = 15

	class Handler(logging.StreamHandler): #need this to compensate for not being in main thread
		def __init__(self):
			logging.StreamHandler.__init__(self)

		def emit(self, record):
			global buffer
			record = f'{record.levelname}:{record.name}:{record.msg}'
			print(record)
			buffer = f'{buffer}\n{str(record)}'.strip()
			window['log'].update(value=buffer)

	logHandler = Handler()
	logHandler.setLevel(settings['config'].get('logLevel', defaultLogLevel))
	logFileHandler = logging.handlers.RotatingFileHandler(logFileName, backupCount=3)
	logFileHandler.setLevel('DEBUG')
	
	logging.basicConfig(
		level='DEBUG',
		format='%(levelname)s:%(name)s:%(msg)s',
		#filename='log.txt',
		handlers=[logHandler, logFileHandler]
	)

	introTab = [
		[sg.Text('Welcome to Advanced Downloader MKII!')],
		[sg.Text('Before starting, make sure you have a copy of ffmpeg in the ffmpeg folder')],
		[sg.Text('(see the text file in there for details) or you have it otherwise installed.')],
		[sg.Text('Next, select a local playlist in the playlist tab. If you don\'t have one, select the folder you want it in.')],
		[sg.Text('You may also optionally select "Remember Playlist" to have it already selected at startup,')],
		[sg.Text('and if you do that you can also select the "Automatically connect playlist on startup" checkbox.')],
		[sg.Text('Now add some YouTube playlists by putting their link or ID into the box and hitting "Add to Local"')]
	]
	
	updateTab = [
		[sg.Text('Playlist Connected', background_color='#00f000', key='updatePagePlaylistConnectedIndicator', visible=False), sg.Text('Playlist Disconnected', background_color='#f00000', key='updatePagePlaylistDisconnectedWarning', visible=True), sg.Text('Warning: ffmpeg has not been detected in the ffmpeg folder, or this is not running on windows', background_color='#f00000', visible=(ffmpegPath == None and settings['config'].get('ignoreFFmpegErrors', 'False') == False))],
		[sg.Frame('Playlist Contents', expand_x=True, layout=[
			[sg.Button('Refresh'), sg.Text('Remote Playlist Count:'), sg.Text('', key='remotePlaylistCount'), sg.Text('Local Item Count:'), sg.Text('', key='playlistLocalItemsCount')]
		])],
		[sg.Frame('Playlist Update', expand_x=True, expand_y=True, layout=[
			[sg.Button('Update Playlist'), sg.Text('Overall Progress:'), sg.Text('Inactive', background_color='#f00000', key='downloadInactiveIndicator', visible=True), sg.Text('Starting', background_color='#FFA500', key='downloadStartingIndicator', visible=False), sg.Text('Completed', background_color='#00f000', visible=False), sg.ProgressBar(max_value=60, orientation='h', size=(10, progressBarHeight), expand_x=True, key='overallProgress', visible=False), sg.Push(), sg.Text('-/-', key='overallProgressCounter', visible=False)],
			[sg.Text('Per-playlist Progress:'), sg.Combo([], readonly=True, size=20, enable_events=True, key='perPlaylistProgressSelector'), sg.ProgressBar(max_value=60, orientation='h', size=(10, progressBarHeight), expand_x=True, key='perPlaylistProgress'), sg.Text('-/-', key='perPlaylistProgressCounter')],
			[sg.Text('Track Progress:'), sg.ProgressBar(max_value=60, orientation='h', size=(10, progressBarHeight), expand_x=True, key='trackProgress'), sg.Text('', key='trackDownloadProgressCounter')],
			[sg.Text('Current Track:'), sg.Text('', key='currentDownloadTrack')]
		])]
	]

	playlistTab = [
		[sg.Frame('Local Playlist', expand_x=True, layout=[
			[sg.Input(key='playlist', default_text=settings['config'].get('defaultPlaylist', ''), tooltip='select the folder containing the playlist'), sg.FolderBrowse(tooltip='select the folder containing the playlist'), sg.Button(button_text='Remember Playlist', tooltip='Click to automatically select this playlist on startup')],
			[sg.Button(button_text='Connect Playlist', tooltip='Connect to a local playlist to run operations on it'), sg.Text('Disconnected', key='playlistConnectionStatus', background_color='#f00000'), sg.Text('', key='playlistConnectionInfo')],
			[sg.Checkbox('Automatically connect playlist on startup', default=settings['config'].get('autoConnect', 'False'), enable_events=True, key='autoConnectPlaylist')]
		])],
		[sg.Frame('Remote Playlists', expand_x=True, expand_y=True, layout=[
			[sg.Input(key='remotePlaylistToAdd', tooltip='link to a youtube playlist, or the id of one'), sg.Button(button_text='Add to Local', key='addRemotePlaylist')],
			[sg.Text('', key='remotePlaylistAdditionInfo')]
		])]
	]

	settingsTab = [
		[sg.Frame('Application Settings', expand_x=True, layout=[
			[sg.Checkbox('Ignore "ffmpeg not detected error" (requires restart)', key='ignoreFFmpegErrors', tooltip='Check this if you have ffmpeg properly installed on PATH, or you aren\'t on windows', enable_events=True, default=settings['config'].get('ignoreFFmpegErrors', 'False'))],
			[sg.Text('theme (requires restart) (not working yet)')],
			[sg.Combo(sg.theme_list(), default_value=sg.theme(), s=(15,22), enable_events=True, readonly=True, k='theme')]
		])],
		[sg.Frame('Local Playlist Settings', expand_x=True, expand_y=True, layout=[
			[sg.Combo(config.validConfigKeys, readonly=True, enable_events=True, key='settingsKeySelection'), sg.Text('You must connect to a playlist first', background_color='#f00000', visible=False, key='configDBnotConnectedWarning'), sg.Combo([], readonly=True, key='newConfigValueDropdown', size=20, visible=False), sg.Input(key='newConfigValueTextBox', size=20, visible=False)],
			[sg.Button('Set new config value'), sg.Text('Current Value:'), sg.Text('', key='configCurrentValue'), sg.Text('Default Value:'), sg.Text('', key='defaultConfigValue')],
			[sg.Text('Invalid Value Selected', background_color='#f00000', key='invalidValueWarning', visible=False), sg.Text('Saved', background_color='#00f000', key='configSavedIndicator', visible=False), sg.Text('Provide a value', background_color='#f00000', key='provideAValueWarning', visible=False), sg.Text('Option Description:'), sg.Text('', key='configOptionDescription')]
		])]
	]

	infoTab = [
		[sg.Text('Advanced Downloader MKII Copyright (C) 2024 Ducks And Netherwort')],
		[sg.Text('This program comes with ABSOLUTELY NO WARRANTY; \nfor details see \'LICENSE\' in installation directory')]
	]

	logTab = [
		[sg.Text('Logging Level')],
		[sg.Combo(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default_value=settings['config'].get('logLevel', 'INFO'), readonly=True, enable_events=True, key='logLevelSelection')],
		[sg.Frame('Log Output', expand_x=False, layout=[
			[sg.Multiline(key='log', s=(None, 7), expand_x=False, write_only=True)]
		])]
	]

	layout = [
		[sg.TabGroup([[
			sg.Tab('Introduction', introTab),
			sg.Tab('Update', updateTab),
			sg.Tab('Playlist', playlistTab),
			sg.Tab('Settings', settingsTab),
			sg.Tab('Info', infoTab),
			sg.Tab('Logging', logTab),
		]])],
		[sg.Text('Advanced Downloader MKII Copyright (C) 2024 Ducks And Netherwort')],
	]

	icon = b"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"
	window = sg.Window('Advanced Downloader MKII', layout, finalize=True, icon=icon)

	global dbConn #this is so cleanup can happen in the case of a crash
	global playlistConnected
	playlistConnected = False

	log = logging.Logger('main')
	log.addHandler(logHandler)
	log.addHandler(logFileHandler)
	needRoll = Path(logFileName).is_file() #this section is for rotating in a new log file at every startup
	if needRoll:
		log.debug('rolling log file')
		logFileHandler.doRollover()
		log.debug('rolled over log file')

	if settings['config'].get('autoConnect', 'False'):
		log.debug('automatically connecting playlist')
		window.write_event_value('Connect Playlist', None) #this is to trigger playlist connection if the autoconnect feature has been enabled

	while True:
		event, values = window.read()
		# See if user wants to quit or window was closed
		if event == sg.WINDOW_CLOSED or event == 'Quit':
			break
		elif event == 'Connect Playlist': #Connect Playlist button got pressed
			log.info('playlist connection requested')
			window['playlistConnectionStatus'].update('Connecting', background_color='#FFA500')
			window.refresh()
			log.debug('checking db path')
			try:
				dbPath = db.checkdbPath(values['playlist'])
			except TypeError:
				log.warn('attempted to connect to a playlist database with invalid file type')
				window['playlistConnectionStatus'].update('Failure', background_color='#f00000')
				window['playlistConnectionInfo'].update('Invalid file type')
				continue

			log.debug('connecting to db')
			dbConn = db.connect(str(dbPath))
			if dbConn == None:
				log.warn('failed to connect to database')
				window['playlistConnectionStatus'].update('Failure', background_color='#f00000')
				window['playlistConnectionInfo'].update('Failed to connect to database')
				continue

			log.debug('checking db validity')
			dbValid = db.checkDB(dbConn)
			if not dbValid:
				log.debug('db was invalid, initializing')
				window['playlistConnectionStatus'].update('Had to initialize database')
				initSuccess = db.initializeDB(dbConn)
				if not initSuccess:
					log.warn('failed to initialize the database')
					window['playlistConnectionStatus'].update('Failure', background_color='#f00000')
					window['playlistConnectionInfo'].update('Failed to initialize database')
					continue

			log.info('db connection successful')
			playlistConnected = True
			window['playlistConnectionStatus'].update('Connected', background_color='#00f000')
			window.write_event_value('Refresh', None)
		
		elif event == 'Remember Playlist':
			log.debug('Got request to save playlist to settings')
			settings['config']['defaultPlaylist'] = values['playlist']
		
		elif event == 'logLevelSelection':
			log.info(f'changing logging level to {values["logLevelSelection"]}')
			settings['config']['logLevel'] = values['logLevelSelection']
			logHandler.setLevel(settings['config'].get('logLevel', defaultLogLevel))

		elif event == 'autoConnectPlaylist':
			log.debug(f'setting auto connect on startup to {values["autoConnectPlaylist"]}')
			settings['config']['autoConnect'] = values['autoConnectPlaylist']
		
		elif event == 'addRemotePlaylist':
			log.debug(f'adding remote playlist {values["remotePlaylistToAdd"]} to local')
			window['remotePlaylistAdditionInfo'].update('Adding Remote Playlist')
			window.refresh()
			if not playlistConnected:
				window['remotePlaylistAdditionInfo'].update('You must connect to a local playlist first')
				log.info('You must be connected to a local playlist to add a remote playlist to it')
				continue
			if values['remotePlaylistToAdd'] == '':
				window['remotePlaylistAdditionInfo'].update('Please provide a playlist link or ID')
				log.info('The system is not telepathic, please provide a remote playlist to add')
				continue

			log.info(f'adding playlist {values["remotePlaylistToAdd"]}')
			if(len(values['remotePlaylistToAdd'].split('=')) > 1):
				playlistId = values['remotePlaylistToAdd'].split('=')[1].strip()
			else:
				playlistId = values['remotePlaylistToAdd'].strip()
			log.debug(f'adding playlist with ID {playlistId}')
			
			window['remotePlaylistAdditionInfo'].update(f'Adding playlist with ID {playlistId}')
			window.refresh()
			playlistAdditionResult = db.addPlaylist(dbConn, playlistId)
			if playlistAdditionResult == -1:
				log.error(f'failed to add playlist {playlistId}') #seems yt-dlp crashes us anyway
				window['remotePlaylistAdditionInfo'].update(f'Failed to add {playlistId}')
			elif playlistAdditionResult == 1:
				log.info(f'playlist "{db.getPlaylistNameFromID(dbConn, playlistId)}" was already in database')
				window['remotePlaylistAdditionInfo'].update(f'Playlist "{db.getPlaylistNameFromID(dbConn, playlistId)}" was already in database')
			elif playlistAdditionResult == 0:
				log.info(f'successfully added playlist "{db.getPlaylistNameFromID(dbConn, playlistId)}"')
				window['remotePlaylistAdditionInfo'].update(f'Added playlist "{db.getPlaylistNameFromID(dbConn, playlistId)}"')
			else:
				log.critical('it seems the returns from db.addPlaylist have changed')
				exit(1)
		
		elif event == 'ignoreFFmpegErrors':
			log.debug(f'setting "ignore ffmpeg errors" to {values["ignoreFFmpegErrors"]}')
			settings['config']['ignoreFFmpegErrors'] = values['ignoreFFmpegErrors']
		
		elif event == 'settingsKeySelection':
			option = values['settingsKeySelection']
			log.debug(f'config option {option} has been selected')
			window['provideAValueWarning'].update(visible=False)
			window['configSavedIndicator'].update(visible=False)
			window['invalidValueWarning'].update(visible=False)
			if not playlistConnected:
				log.warn('tried to select config option without a playlist connected')
				window['configDBnotConnectedWarning'].update(visible=True)
				continue
			else:
				window['configDBnotConnectedWarning'].update(visible=False)

			currentValue = config.getConfig(dbConn, option)
			defaultValue = config.getDefaultValue(option)
			window['configCurrentValue'].update(currentValue)
			window['defaultConfigValue'].update(defaultValue)
			window['configOptionDescription'].update(config.getConfigDescription(option))
			dropdownInput = True if not config.doesValueUseRegex(option) else False

			window['newConfigValueDropdown'].update(visible=dropdownInput)
			window['newConfigValueTextBox'].update(visible=not dropdownInput)

			if dropdownInput:
				window['newConfigValueDropdown'].update(values=config.getAcceptibleValues(option))
		
		elif event == 'Set new config value':
			option = values['settingsKeySelection']
			log.debug('setting new config value')
			if option == '':
				log.debug('no option selected')
				continue

			window['provideAValueWarning'].update(visible=False)
			window['configSavedIndicator'].update(visible=False)
			window['invalidValueWarning'].update(visible=False)
			if not playlistConnected:
				log.warn('tried to set config without a playlist connected')
				window['configDBnotConnectedWarning'].update(visible=True)
				continue
			else:
				window['configDBnotConnectedWarning'].update(visible=False)

			dropdownInput = True if not config.doesValueUseRegex(option) else False
			newValue = values['newConfigValueDropdown'] if dropdownInput else values['newConfigValueTextBox']
			if newValue == '':
				log.debug('attempted to set a config value to empty string')
				window['provideAValueWarning'].update(visible=True)
				continue

			if not config.validateConfigValue(option, newValue):
				log.debug('invalid config option')
				window['invalidValueWarning'].update(visible=True)
				continue
			
			log.debug('new value seems legit')
			if not config.setConfig(dbConn, option, newValue): #just in case it says there is a problem with the key or value
				log.error(f'failed to save configuration value {newValue} to key {option}')
				window['invalidValueWarning'].update(visible=True)
				continue
			log.info('new setting saved successfully')
			window['configSavedIndicator'].update(visible=True)
			window['configCurrentValue'].update(newValue)
		
		elif event == 'Refresh':
			log.debug('refreshing playlist stats')
			if not playlistConnected:
				log.warning('cannot refresh information relating to a playlist that is not connected')
				continue
			numberOfPlaylists = len(db.getPlaylists(dbConn))
			numberOfTracks = len(db.getAllDownloadedTracks(dbConn)['id'])
			log.debug(f'number of playlists is {numberOfPlaylists}, number of tracks is {numberOfTracks}')
			window['remotePlaylistCount'].update(numberOfPlaylists)
			window['playlistLocalItemsCount'].update(numberOfTracks)

			window['updatePagePlaylistConnectedIndicator'].update(visible=playlistConnected)
			window['updatePagePlaylistDisconnectedWarning'].update(visible=not playlistConnected)
		
		elif event == 'Update Playlist':
			log.debug('got request to update playlist')
			if not playlistConnected:
				log.warning('can\'t update a playlist that isn\'t connected')
				continue

			window.start_thread(lambda: update(str(dbPath), window, dbPath.parent, ffmpegPath), 'updateReturned') #forgot to make this start a thread at first
		
		elif event == 'progressUpdate':
			data = values['progressUpdate']
			log.debug(f'received progress update {data}')
			operation = data[0]
			value = data[1: ]
			log.debug(type(value))
			if operation == 'overall progress':
				log.debug(f'received overall progress update {value}')
				window['overallProgress'].update(value)
			elif operation == 'starting':
				log.debug('received download starting message')
				window['downloadInactiveIndicator'].update(visible=False)
				window['downloadStartingIndicator'].update(visible=True)
			elif operation == 'started':
				log.debug(f'received download startup message with data {value}')
				window['downloadStartingIndicator'].update(visible=False)
				window['overallProgress'].update(visible=True, current_count=0, max=value)
				window['overallProgressCounter'].update(visible=True)
				totalRemoteItems: int = 0
				totalRemoteItems = value
			elif operation == 'playlist totals':
				log.debug(f'received playlist totals {value}')
				remotePlaylistTotals: list = value[0]
				correspondingRemotePlaylists: list = value[1]
				window['perPlaylistProgressSelector'].update(correspondingRemotePlaylists)
			elif operation == 'increment playlist':
				remotePlaylistCounts: list = []
				log.debug(f'incrementing playlist {value}')
				remotePlaylistCounts[correspondingRemotePlaylists.index(value)] += 1
			elif operation == 'download size':
				log.debug(f'download size should be {value}')
				window['trackProgress'].update(current_count=0, max=value)
			elif operation == 'download progress':
				log.debug(f'got download progress update {value}')
				window['trackProgress'].update(value)
			else:
				log.debug(f"got the unknown update parameter operation {operation}. This might be used later")
		
		elif event == 'perPlaylistProgressSelector':
			log.debug(f'progress selector selected {value}')
			window['perPlaylistProgress'].update(current_count=remotePlaylistCounts[correspondingRemotePlaylists.index(value)], max=remotePlaylistTotals[correspondingRemotePlaylists.index(value)])
		
		elif event == 'updateReturned':
			log.debug('update function returned successfully')



	# Finish up by removing from the screen
	if playlistConnected:
		dbConn.close()
	window.close()

if(__name__ == "__main__"):
	try:
		guiMain()
	except:
		if playlistConnected:
			dbConn.close()