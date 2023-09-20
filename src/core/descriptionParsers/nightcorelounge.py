#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	description = input.description
	title = input.title
	uploader = input.uploader
	id = input.id

	m = metadata_t
	m.genre = 'Nightcore'
	if '[' in title:
		if len(title.split(' - ')[0].split(']')) > 1:
			m.artist = title.split('] ')[1].split(' - ')[0].strip()
	m.title = title.split(' - ')[1].strip()
	for line in description.split('\n'):
		if 'artist' in line.lower() and len(line.split(': ')) > 1:
			m.artist = line.split(': ')[1]
		if 'genre' in line.lower() and len(line.split(': ')) > 1:
			if len(line.split(': ')[1]) < 2:
				m.genre = 'Nightcore'
			else:
				m.genre = 'Nightcore/' + line.split(': ')[1].strip()
	if 'https' in m.artist:
		m.artist = ''
	return(m)