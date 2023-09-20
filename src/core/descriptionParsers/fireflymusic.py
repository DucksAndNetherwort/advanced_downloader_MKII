#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	description = input.description
	title = input.title
	uploader = input.uploader
	id = input.id

	m = metadata_t
	m.artist = []
	m.artist.append(title.split(' - ')[0].strip())
	m.title = title.split(' - ')[1].split('(')[0].strip()
	if '(' in title:
		m.artist.append(title.split('(')[1].split(')')[0])
	if 'genre' in description.lower():
		for line in description.split('\n'):
			if 'genre: ' in line.lower():
				m.genre = line.split(': ')[1].strip()
				break
	m.artist = ' '.join(m.artist)
	return(m)