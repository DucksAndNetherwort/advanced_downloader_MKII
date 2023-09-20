
- [[#Sequence of operations|Sequence of operations]]
	- [[#Sequence of operations#The Download Loop|The Download Loop]]

## Sequence of operations

A logger is acquired, and lists are made for existing downloaded tracks (`existing`), and all playlist IDs (`playlistIDs`).
Following that, a list of lists called `allPlaylistItems` is created, with \[0] being a list of track IDs, and \[1] being a list of lists with playlist IDs corresponding to the track IDs.

`playlistIDs` is then iterated over, fetching each playlist and adding the contents to `allPlaylistItems`, making sure each track is only in there once, and each track has a full list of the playlists it's a member of.

`todo` is then constructed so that it is a list of lists, with the `[0]` of each list being a track id that needs to be downloaded, and `[1]` being a list of playlists it belongs to

`playlistItemsToDownload` is a list of integers containing the number of items each playlist needs downloaded, and `correspondingPlaylists` is a list of playlist names that go with the counts

`playlistBars` is then created as a list containing a tqdm progress bar for each playlist in `correspondingPlaylists`.

### The Download Loop

The loop iterates over a tqdm progress bar with a description of "Overall Progress", wrapping `todo` as an iterator, and `in` is used to get a track for the current iteration.

Within each iteration, the variable `parserInput` of `parserInput_t` is populated with the necessary data to feed the description parsers, following which the aforementioned `parserInput` is fed to `DescriptionParser.parse()` to obtain the metadata for the current track.

Following the metadata acquisition, a check is performed to see if the uploader of the current track is in the catalog of parsers, and if it isn't, either the appropriate count in `parserMisses` is incremented, or said counter is created and set to 1. The intention is that later on, the resultant data can be shown to determine what parsers should be created.

The title to use as the filename is constructed, along with a counter for the number of attempts and a success flag.

A `while not success` loop is entered, and a progress bar is created, following which `dl.getTrack` is called, downloading the track, and the `success` flag is set to the result

If a rate limit was encountered, the progress hook will lower the rate limit target and wait 10 seconds, and if the number of attempts exceeds 2, the rate of rate limiting will be raised. If the attempts counter exceeds 4, the program will terminate.

On successful download, the playlist bars will be incremented accordingly

If a enough downloads are successful in a row, the rate limits will be loosened

Once the track has been successfully downloaded, it will be added to the database, and the cycle will repeat.