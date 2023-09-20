Contains all the non implementation-specific code for the downloader.
Each file is for one job, and each job is handled by one file,
taking after the unix philosophy.

[[config.py]] is for managing configuration
[[db.py]] is for database management
[[type.py]] is purely for custom datatypes
[[DescriptionParser.py]] is for managing all the parsers for metadata extraction
[[tagging.py]] handles the custom tagging system
And finally what is surely the most important component, [[dl.py]], which handles downloading 