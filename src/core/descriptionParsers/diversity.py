#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	description = input.description
	title = input.title
	uploader = input.uploader
	id = input.id

	m = metadata_t
	title = title.split(' - ')
	if len(title) > 1:
		m.artist = title[0]
		m.title = title[1][0: 60]
	else:
		m.title = title[0]

	if 'genre:' in description.lower():
		for line in description.split('\n'):
			if 'genre:' in line.lower():
				m.genre = line.strip().split(': ')[len(line.strip().split(': ')) - 1].strip(' #')
				break
	return(m)