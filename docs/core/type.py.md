This file handles the custom data types used by the system, and the `sqlite3` adapter for `metadata_t`.

- [[#Data Types|Data Types]]
	- [[#Data Types#metadata_t|metadata_t]]
	- [[#Data Types#parserInput_t|parserInput_t]]

## Data Types

### metadata_t
This data type is used to store track metadata, and contains the following:

| Variable name | Variable contents                                                                |
| ------------- | -------------------------------------------------------------------------------- |
| genre         | string to store the genre                                                        |
| artist        | string to store the artist name                                                  |
| title         | string to store the title of the track                                           |
| uploader      | string to store the name of the channel that uploaded the track                  |
| genreTag      | string containing the tag used to denote genre, used by the tagging system       |
| artistTag     | string containing the tag used to denote artist, used by the tagging system      |
| titleTag      | string containing the tag used to denote track title, used by the tagging system |
| uploaderTag   | string containing the rag used to denote uploader, used by the tagging system    |

`metadata_t` also contains the `__conform__(self, protocol)` function for use with `sqlite3`.

### parserInput_t
This data type is used to contain the input data for metadata parsers, and contains the following:

| Variable name | Variable contents                  |
| ------------- | ---------------------------------- |
| description   | entire video desctiption, as `str` |
| title         | video title, as `str`              |
| uploader      | uploader name, as `str`            |
| id            | video id, as `str`                 |
