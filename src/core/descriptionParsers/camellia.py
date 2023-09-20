#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	description = input.description
	title = input.title
	uploader = input.uploader
	id = input.id

	m = metadata_t
	m.genre = 'Camellia'
	m.artist = 'Camellia'
	if ' - ' in title:
		m.title = title.split(' - ')[1]
	else:
		m.title = title
	return(m)