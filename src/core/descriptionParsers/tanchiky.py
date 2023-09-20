#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	m = metadata_t
	if len(input.title.split('-')) > 1:
		m.artist = input.title.split('-')[0].strip()
		m.title = input.title.split('-')[1].strip()
	else:
		m.artist = 'Tanchiky'
		m.title = input.title
	m.genre = 'Tanchiky'
	return(m)