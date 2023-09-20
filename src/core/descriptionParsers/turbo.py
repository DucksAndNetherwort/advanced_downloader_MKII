#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	description = input.description
	title = input.title
	uploader = input.uploader
	id = input.id

	m = metadata_t
	m.genre = 'Eurobeat'
	m.artist = 'Turbo'
	if ' _ ' in title or ' - ' in title or ' / ' in title:
		for split in (' _ ', ' / ', ' - '):
			if len(title.split(split)) > 1:
				m.title = title.split(split)[0]
				break
	return(m)