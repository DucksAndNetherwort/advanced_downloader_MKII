#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	description = input.description
	title = input.title
	uploader = input.uploader
	id = input.id

	m = metadata_t
	m.genre = 'Hardbass'
	m.artist = []
	m.artist.append('Alan Aztec')
	m.title = title.split(' - ')[1].split('(')[0].strip()
	if '(' in title:
		m.artist.append(title.split('(')[1].split(')')[0].strip())
	m.artist = ' '.join(m.artist)
	return(m)