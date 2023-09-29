#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
import yt_dlp
from yt_dlp.utils import DownloadError, ThrottledDownload
import tempfile
from pathlib import Path
from shutil import copy
import logging

from core.type import metadata_t

def filenameCleaner(dirty: str) -> str:
	"""
	Strips out all characters that shouldn't be in a filename
	"""
	badCharSet = set('\/*?:"<>|')
	return ''.join([c for c in dirty if c not in badCharSet]).strip('. ')

def getPlaylistInfo(playlistId: str) -> dict:
	"""
	Get info/metadata for youtube playlist and return it in a dict
	"""
	log = logging.getLogger('dl/getPlaylistInfo')

	playlistUrl = f'https://www.youtube.com/playlist?list={playlistId}'
	# Set up yt_dlp options
	options = {
		'skip_playlist_entries': True,
		'extract_flat': 'in_playlist',
		'dump_single_json': True,
		'playlistend': 0,
		'ignoreerrors': True,
		'skip_download': True,
		'quiet': True,
		'limit_rate': '1M'
	}

	# Create a yt_dlp object
	ydl = yt_dlp.YoutubeDL(options)

	try:
		# Extract playlist metadata
		playlistInfo = ydl.extract_info(playlistUrl, download=False)
	except yt_dlp.DownloadError as e:
		log.error(f"Error extracting playlist info: {str(e)}")
		return None

	return playlistInfo

def getPlaylist(playlistId: str, progressHooks: list=[]) -> list[str]:
	"""
	Download playlist listing to a list, and return said list. Can also take custom progress hooks for yt_dlp.
	"""
	log = logging.getLogger('dl/getPlaylist')
 
	playlistUrl = f'https://www.youtube.com/playlist?list={playlistId}'
	# Create an empty list to store video IDs
	videoIds = []

	# Set up yt_dlp options
	options = {
		'extract_flat': 'in_playlist',
		'dump_single_json': True,
		'playlistend': 99999,
		'ignoreerrors': True,
		'skip_download': True,
		'progress_hooks': progressHooks,
		'quiet': True,
		'limit_rate': '1M'
	}

	# Create a yt_dlp object
	ydl = yt_dlp.YoutubeDL(options)

	# Download the playlist metadata
	try:
		playlistInfo = ydl.extract_info(playlistUrl, download=False)
		if type(playlistInfo) == None:
			log.critical(f'could not download playlist listing for {playlistUrl}')
	except yt_dlp.DownloadError as e:
		log.error(f"Error downloading playlist: {str(e)}")
		return videoIds

	# Extract video IDs from the playlist metadata
	for entry in playlistInfo['entries']:
		videoId = entry['id']
		videoIds.append(videoId)

	return videoIds

def getDescription(id: str, rateLimit: str = '3M') -> tuple[str, str, str, int]:
	"""
	gets the description and title of the video with the given id, returning the tuple (uploader, title, description, filesizeEstimate).
	On download error, returns the same tuple but the first item is the download error, and the rest are None
	"""
	log = logging.getLogger('dl/getDescription')
	ydl_opts = {
		'quiet': True,
		'skip_download': True,
		'extract_flat': True,
		'force_generic_extractor': True,
		'limit_rate': rateLimit
	}

	video_url = f'https://www.youtube.com/watch?v={id}'

	try:
		with yt_dlp.YoutubeDL(ydl_opts) as ydl:
			info_dict = ydl.extract_info(video_url, download=False)
			video_title = info_dict.get('title', 'Title not available')
			video_description = info_dict.get('description', 'Description not available')
			uploader = info_dict.get('uploader', 'Uploader not available')
			approximateFilesize = int(info_dict.get('filesize_approx', 69420))

	except DownloadError as e:
		log.debug(f'error is "{e.msg}"')
		return e, None, None, None


	return uploader, video_title, video_description, approximateFilesize

def getTrack(id: str, metadata: metadata_t, useMetadataTitle: bool, outputDir: Path, filenameTitle: str, rateLimit: str = '3M', progressHooks: list = [], ffmpegPath: str = None) -> bool:
	"""
	Downloads a track as mp3 with a filename of {filenameTitle}.mp3 to the directory of outputDir
	"""
	log = logging.getLogger('dl/getTrack')

	with tempfile.TemporaryDirectory(prefix='adlMK2_', ignore_cleanup_errors=True) as tempDir:
		outputPath = (outputDir / (filenameTitle + '.mp3'))
		outputPathString = str(outputPath)
		filenameTitle = filenameCleaner(filenameTitle)
		#log.debug(f"output path: {outputPathString}")
		ydl_opts = {
			'ffmpeg_location': ffmpegPath,
			'extract_flat': 'discard_in_playlist',
			'final_ext': 'mp3',
			'format': 'bestaudio/best',
			'fragment_retries': 10,
			'ignoreerrors': 'only_download',
			'quiet': True,
			'noprogress': True,
			#'outtmpl': {'pl_thumbnail': ''},
			'outtmpl': (tempDir + '/' + filenameTitle),
			'progress_hooks': progressHooks,
			'postprocessor_args': {'default': [
				'-metadata', f'artist={metadata.artist}',
				'-metadata',f'genre={metadata.genre}',
				'-metadata', f'title={metadata.title if useMetadataTitle else filenameTitle}',
				'-metadata', f'album={metadata.uploader}',
				'-metadata', f'publisher={metadata.uploader}',
				'-metadata', f'encoded_by=Advanced Downloader MKII',
				'-metadata', f"note={id}"],
				'sponskrub': []},
			'postprocessors': [{
				'key': 'FFmpegExtractAudio',
				'nopostoverwrites': False,
				'preferredcodec': 'mp3',
				'preferredquality': '5'
			},
			{'already_have_thumbnail': False, 'key': 'EmbedThumbnail'},
			{
				'key': 'FFmpegConcat',
				'only_multi_video': True,
				'when': 'playlist'
			}],
				'retries': 10,
				'writethumbnail': True
			}

		with yt_dlp.YoutubeDL(ydl_opts) as ydl:
			ydl.download(f"https://www.youtube.com/watch?v={id}")
			copy((Path(tempDir) / (filenameTitle + '.mp3')), outputDir)
	
	return True if outputPath.exists() else False