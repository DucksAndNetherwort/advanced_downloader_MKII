#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	description = input.description
	title = input.title
	uploader = input.uploader
	id = input.id

	m = metadata_t
	m.genre = 'Nightcore'
	if ' - ' in title:
		m.title = title.split(' - ')[1].strip(': ')
	else:
		m.title = title
	artist = []
	section = False
	for line in description.split('\n'):
		if 'support the artist' in line.lower():
			section = True
		if '➥ ' in line and section:
			artist.append(line.strip('➥ :') + ', ')
		if '▬' in line and section:
			m.artist = ''.join(artist).strip(', ')
			break
	return(m)