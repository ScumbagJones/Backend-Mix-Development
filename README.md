# Playlist to AzuraCast Converter

A system to extract playlist metadata from streaming services, identify songs, download audio (from legal sources), and integrate with AzuraCast.

## Features

- 🎵 **Song Identification**: Match songs using MusicBrainz and AcoustID
- 📋 **Playlist Extraction**: Extract metadata from Spotify, YouTube, Apple Music, SoundCloud, Bandcamp
- 🎧 **Audio Download**: Download audio from YouTube and other legal sources
- 📡 **AzuraCast Integration**: Automatic upload and playlist creation
- 🎚️ **BUTT Compatible**: Generate playlists for BUTT streaming tool

## Project Structure

```
.
├── src/
│   ├── identification/     # Song matching and identification
│   ├── extractors/         # Playlist metadata extractors
│   ├── downloaders/        # Audio download modules
│   ├── azuracast/          # AzuraCast API integration
│   └── utils/              # Shared utilities
├── config/                 # Configuration files
├── requirements.txt        # Python dependencies
└── README.md
```

## Legal Notice

This tool is designed for:
- Managing your personal music library
- Working with content you have rights to use
- Downloading from sources where you have permission
- Educational and personal radio station purposes with proper licensing

**Important**: Ensure you have proper rights/licenses for any music you broadcast or use commercially.

## Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure your API keys
cp config/config.example.json config/config.json
# Edit config.json with your API keys
```

## Usage

```bash
# Extract playlist metadata
python src/main.py extract --url "spotify:playlist:xxxxx"

# Identify and match songs
python src/main.py identify --playlist playlist.json

# Download audio (from legal sources)
python src/main.py download --playlist matched_playlist.json

# Upload to AzuraCast
python src/main.py upload --playlist playlist.json --azuracast-url "http://your-azuracast.com"
```

## API Keys Needed

- Spotify: Client ID & Secret (for playlist reading)
- MusicBrainz: User agent (free, no key needed)
- AzuraCast: API Key
- YouTube: No key needed (uses yt-dlp)

## Roadmap

- [x] Project structure
- [ ] Song identification system
- [ ] Playlist extractors
- [ ] YouTube downloader
- [ ] AzuraCast integration
- [ ] Web UI (optional)
