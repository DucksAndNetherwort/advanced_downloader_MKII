#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	description = input.description
	title = input.title
	uploader = input.uploader
	id = input.id

	m = metadata_t
	m.artist = uploader
	m.genre = 'HARDBASS'
	if ' _ ' in title:
		title = title.split(' _ ')[0]
	if ' - ' in title:
		if len(title.split(' - ')) == 3:
			#m.genre = title.split(' - ')[0]
			m.artist = title.split(' - ')[1]
			m.title = title.split(' - ')[2][0: 60]
		else:
			if ' - ' in title:
				if 'dj' in title.split(' - ')[1].lower():
					m.title = title.split(' - ')[0][0: 60]
					m.artist = title.split(' - ')[1]
				else:
					m.title = title.split(' - ')[1][0: 60]
					#m.genre = title.split(' - ')[0]
	else:
		m.title = title[0: 60]
	if '[' in title and not '[HD]' in title:
		m.genre = title.split(']')[0].split('[')[1]
		m.artist = title.split(' - ')[0].split(']')[1].strip('[]()- ')
	m.genre = m.genre.replace('[HD]', '').replace('_', ' ').strip()
	if m.artist == '':
		m.artist = uploader
	if not 'cosmowave' in m.artist.lower():
		m.artist = m.artist + '/Cosmowave'
	return(m)