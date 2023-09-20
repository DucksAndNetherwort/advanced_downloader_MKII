#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project

def tag(data: str, tag: str) -> str:
	"""
	Adds the given tag to the given string
	"""
	if(len(tag) > 1):
		return None
	return(f'{tag}<{data}>{tag}')

def parse(input: str, tag: str) -> str:
	"""
	Parses data from the given tag in the given string
	"""
	data = ''
	for i in range(input.find(f'{tag}<') + 2, input.find(f'>{tag}')):
		data += input[i]
	return(data)