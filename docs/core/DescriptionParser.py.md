Used to manage the description parsers located in core/descriptionParsers, and run parsing operations using them.
Parsers with filenames starting with `_` will be ignored, and not loaded.

- [[#Functions|Functions]]
	- [[#Functions#parse(input: parserInput_t) -> metadata_t:|parse(input: parserInput_t) -> metadata_t:]]

## Functions

### parse(input: parserInput_t) -> metadata_t:
Takes `parserInput_t` as the input, and returns a populated `metadata_t`.