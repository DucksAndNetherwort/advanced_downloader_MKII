A simple file to handle the string tagging system.

- [[#Functions|Functions]]
	- [[#Functions#tag(data: str, tag: str) -> str:|tag(data: str, tag: str) -> str:]]
	- [[#Functions#parse(input: str, tag: str) -> str:|parse(input: str, tag: str) -> str:]]


The tagging system operates on short "tags", comprised of one uppercase letter, and puts the data between two tags with less than/greater than symbols surrounding the data, with only one instance of a tag allowed per string.
The tagged strings looks something like the following, in this case with the tags "T" and "G": `T<data that is tagged>T G<other tagged data>G`.

## Functions

### tag(data: str, tag: str) -> str:
Adds the given tag to the given string, returning the resulting string

### parse(input: str, tag: str) -> str:
Parses the given tag from the given string, returning the parsed data