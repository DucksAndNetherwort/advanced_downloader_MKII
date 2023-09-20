#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core import tagging

from dataclasses import dataclass
import sqlite3

@dataclass
class metadata_t:
	"""
	Custom data type for storing track metadata
	"""
	genre: str = ''
	artist: str = ''
	title: str = ''
	uploader: str = ''

	genreTag: str = 'G'
	artistTag: str = 'A'
	titleTag: str = 'T'
	uploaderTag: str = 'U'

def convertMetadata(metadata: metadata_t) -> str:
	"""
	no idea what's going on, gave up and changed this from __conform__ to convert along with changing self to thisThing, and it must be given a copy of itself
	"""
	#if protocol is sqlite3.PrepareProtocol:
	fields = [metadata.genre, metadata.artist, metadata.title, metadata.uploader]
	tags = [metadata.genreTag, metadata.artistTag, metadata.titleTag, metadata.uploaderTag]

	output = ''
	for tag, field in zip(tags, fields):
		output += f'{tagging.tag(field, tag)} '

	return output.strip()

def metadata_adapter(inBytes: bytes) -> metadata_t:
	"""
	SQLite adapter for metadata_t
	"""
	input = str(inBytes)
	out = metadata_t

	out.genre = tagging.parse(input, metadata_t.artistTag)
	out.artist = tagging.parse(input, metadata_t.artistTag)
	out.title = tagging.parse(input, metadata_t.titleTag)
	out.uploader = tagging.parse(input, metadata_t.uploaderTag)

	return(out)

@dataclass
class parserInput_t:
	"""
	Custom data type to provide the needed inputs for track parsers.
	"""
	description: str
	title: str
	uploader: str
	id: str