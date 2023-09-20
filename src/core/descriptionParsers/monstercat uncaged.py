#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	description = input.description
	title = input.title
	uploader = input.uploader
	id = input.id

	m = metadata_t
	if title[0] == '[':
		if len(title.split(' - ')) > 2:
			m.title = title.split(' - ')[2].strip()
			m.genre = title.split(']')[0].split('[')[1].strip()
			m.artist = title.split(' - ')[1].strip()
		else:
			m.title = title.split(' - ')[1].strip()
			m.genre = title.split(']')[0].split('[')[1].strip()
			m.artist = title.split(']')[1].split(' - ')[0].strip()
	else:
		m.title = title.split(' - ')[1]
		m.artist = title.split(' - ')[0]
		if 'genre' in description.lower():
			for line in description.split('\n'):
				if 'genre: ' in line.lower():
					m.genre = line.split(': ')[1].strip()
					break
	return(m)