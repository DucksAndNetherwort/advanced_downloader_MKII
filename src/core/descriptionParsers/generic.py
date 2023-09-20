#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t

def parse(input: parserInput_t):
	m = metadata_t('Unknown', 'Unknown', 'Unknown')
	m.artist = input.uploader
	m.genre = 'Unknown'
	if 'nightcore' in m.title.lower():
		m.genre = 'Nightcore'
	if ' _ ' in m.title:
		m.title = m.title.split(' _ ')[0]
	if ' - ' in m.title:
		if len(m.title.split(' - ')) == 3:
			if 'lyrics' in m.title.lower():
				m.artist = m.title.split(' - ')[0]
				m.title = m.title.split(' - ')[1][0: 60]
			else:
				m.genre = m.title.split(' - ')[0]
				m.artist = m.title.split(' - ')[1]
				m.title = m.title.split(' - ')[2][0: 60]
		else:
			if ' - ' in m.title:
				if 'dj' in m.title.split(' - ')[1].lower():
					m.title = m.title.split(' - ')[0][0: 60]
					m.artist = m.title.split(' - ')[1]
				else:
					m.title = m.title.split(' - ')[1][0: 60]
					if 'nightcore' in m.title.split(' - ')[0].lower():
						m.genre = m.title.split(' - ')[0]
					else:
						m.artist = m.title.split(' - ')[0]
	else:
		m.title = m.title[0: 60]
	if '[' in m.title and not '[HD]' in m.title:
		m.genre = m.title.split(']')[0].split('[')[1]
		if len(m.title.split(' - ')[0].split(']')) > 1:
			m.artist = m.title.split(' - ')[0].split(']')[1].strip('[]()- ')
	m.genre = m.genre.replace('[HD]', '').replace('_', ' ').strip()
	if m.artist == 'Unknown' or m.artist == '' or m.artist == input.uploader:
		if '(' in m.title:
			m.artist = m.title.split('(')[1].split(')')[0].strip()
			if 'lyrics' in m.artist.lower():
				m.artist = ''
	if m.artist == '':
		m.artist = input.uploader
	return(m)