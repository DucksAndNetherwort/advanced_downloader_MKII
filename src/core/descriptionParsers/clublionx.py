#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	description = input.description
	title = input.title
	uploader = input.uploader
	id = input.id

	m = metadata_t
	m.genre = 'Nightcore'
	m.title = title.split(' - ')[1].split('[')[0].strip()
	if 'genre' in description.lower():
		for line in description.split('\n'):
			if 'genre: ' in line.lower():
				m.genre = 'Nightcore/' + line.split(': ')[1].strip()
				break
	if '[' in title:
		m.artist = title.split('[')[1].strip(' ] ')
	return(m)