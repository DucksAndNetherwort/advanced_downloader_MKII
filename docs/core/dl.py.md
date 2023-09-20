This file handles all download-related tasks.

- [[#Functions|Functions]]
	- [[#Functions#filenameCleaner(dirty: str) -> str:|filenameCleaner(dirty: str) -> str:]]
	- [[#Functions#getPlaylistInfo(playlistId: str) -> dict:|getPlaylistInfo(playlistId: str) -> dict:]]
	- [[#Functions#getPlaylist(playlistId: str, progressHooks: list=\[\]) -> list\[str\]:|getPlaylist(playlistId: str, progressHooks: list=\[\]) -> list\[str\]:]]
	- [[#Functions#getDescription(id: str, rateLimit: str = '3M') -> tuple\[str, str, int\]:|getDescription(id: str, rateLimit: str = '3M') -> tuple\[str, str, str, int\]:]]
	- [[#Functions#getTrack(id: str, metadata: metadata_t, useMetadataTitle: bool, outputDir: Path, filenameTitle: str, rateLimit: str = '3M', progressHooks: list = []) -> bool:|getTrack(id: str, metadata: metadata_t, useMetadataTitle: bool, outputDir: Path, filenameTitle: str, rateLimit: str = '3M', progressHooks: list = []) -> bool:]]

## Functions

### filenameCleaner(dirty: str) -> str:
Cleans filenames by stripping out any characters that aren't allowed to be in windows filenames.
### getPlaylistInfo(playlistId: str) -> dict:
Downloads the data for a youtube playlist from the given ID, and returns the dictionary downloaded by yt-dlp, so good luck finding documentation on what it contains!
### getPlaylist(playlistId: str, progressHooks: list=\[\]) -> list\[str\]:
Fetches all the video IDs from the playlist of the given ID, returning them as a list.
Yt-dlp compatible progress hooks may also be placed in the `progressHooks` list.
### getDescription(id: str, rateLimit: str = '3M') -> tuple\[str, str, str, int\]:
Downloads the description belonging to the track with the given ID, returning a tuple with the contents `(uploader, title, description, filesizeEstimate)`, with `title` being the video title as shown on YouTube, `description` being a `str` containing the description, and `filesizeEstimate` being an `int` containing the estimated size of the file. I have no idea what unit it's in.
### getTrack(id: str, metadata: metadata_t, useMetadataTitle: bool, outputDir: Path, filenameTitle: str, rateLimit: str = '3M', progressHooks: list = []) -> bool:
Downloads a track from YouTube. Returns `True` on success.
yt-dlp's `cli_to_api.py` was very useful for getting the options set correctly.

| Argument         | Type       | Description                                            |
| ---------------- | ---------- | ------------------------------------------------------ |
| id               | str        | ID of the track to download                            |
| metadata         | metadata_t | Metadata to add to the downloaded track                |
| useMetadataTitle | bool       | Whether to use the title in metadata for file metadata |
| outputDir        | Path       | Directory to place the downloaded track into           |
| filenameTitle    | str        | String to use as filename, without the .mp3 part       |
| rateLimit        | str        | (optional) rate limit to use, must have a unit letter  |
| progressHooks    | list       | progress hooks for yt-dlp                              |
