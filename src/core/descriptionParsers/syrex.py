#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	description = input.description
	title = input.title
	uploader = input.uploader
	id = input.id

	m = metadata_t
	if len(title.split(' - ')) > 1:
		m.title = title.split(' - ')[1]
	else:
		m.title = title[0: 60]
	if '(' in title:
		m.artist = title.split('(')[1].strip('()- ')
	elif len(title.split(' - ')) >= 3:
		m.artist = title.split(' - ')[2].strip('()- ')
	m.artist = m.artist.split('_')[0].strip(' []_()-')
	if 'lyrics' in m.artist.lower():
		m.artist = ''
	return(m)