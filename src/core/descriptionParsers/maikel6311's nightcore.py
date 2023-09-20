#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	description = input.description
	title = input.title
	uploader = input.uploader
	id = input.id

	m = metadata_t
	if '_' in title:
		m.title = title.split(' _ ')[1].split(' - ')[1].strip()
		m.artist = title.split(' _ ')[0].strip()
		m.genre = 'Nightcore/' + title.split(' _ ')[1].split(' - ')[0].strip()
	else:
		m.title = title.split(' - ')[1].strip()
		m.genre = title.split(' - ')[0]
	if 'music: ' in description.lower():
		for line in description.split('\n'):
			if 'music: ' in line.lower():
				m.artist = line.split(': ')[1].split(' - ')[0].strip()
				m.title = line.split(': ')[1].split(' - ')[1].strip()
				break
	return(m)