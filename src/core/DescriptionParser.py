#Copyright (C) 2023  Ducks And Netherwort, full license can be found in LICENSE at the root of this project
from core.type import metadata_t, parserInput_t
from core.dl import getPlaylistInfo

import os
import importlib.util

# Get the directory path of the parsers directory
dir_path = os.path.join(os.path.dirname(__file__), "descriptionParsers")

# Create an empty dictionary to store your functions
parsers = {}

# Loop through all the files in the directory
for filename in os.listdir(dir_path):
    # Check if the file is a Python file
    if filename.endswith(".py") and not filename.startswith("_"):
        # Load the module
        module_name = filename[:-3]
        spec = importlib.util.spec_from_file_location(module_name, os.path.join(dir_path, filename))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Check if the module has a parse function
        if hasattr(module, "parse") and callable(module.parse):
            # Add the function to the dictionary
            parsers[module_name] = module.parse


def uploaderCleaner(uploader: str) -> str:
    return(uploader.lower())

def isPresent(uploader: str) -> bool:
    """
    Checks whether there is a dedicated parser for an uploader
    """
    return True if uploaderCleaner(uploader) in parsers.keys() else False

def parse(input: parserInput_t) -> metadata_t:
    """
    Parses track metadata from the input
    """
    output: metadata_t = metadata_t(None, None, None, None)
    if uploaderCleaner(input.uploader) in parsers.keys():
        output = parsers[uploaderCleaner(input.uploader)](input)
    else:
        output = parsers['generic'](input)
    output.uploader = input.uploader
    if len(output.genre.split('=')) > 1 and 'youtube.com' in output.genre: #let's try to sort out those pesky "playlist as genre name" things
        getPlaylistInfo(output.genre.split('=')[1].strip()).get('title', 'bad playlist')
    return(output)