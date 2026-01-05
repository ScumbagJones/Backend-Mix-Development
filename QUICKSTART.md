# Quick Start Guide

Get up and running in 5 minutes!

## 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Install ffmpeg (required for audio conversion)
# Ubuntu/Debian:
sudo apt install ffmpeg

# macOS:
brew install ffmpeg

# Windows: Download from https://ffmpeg.org/download.html
```

## 2. Set Up API Keys

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your keys
nano .env  # or use your favorite editor
```

### Getting API Keys:

**Spotify** (for reading playlists):
1. Go to https://developer.spotify.com/dashboard
2. Create an app
3. Copy Client ID and Client Secret to `.env`

**AzuraCast** (optional, for uploading):
1. Log into your AzuraCast instance
2. Go to Profile → API Keys
3. Create new key with "All Permissions"
4. Copy to `.env`

## 3. Basic Usage

### Extract a Playlist

```bash
# Spotify
python src/main.py extract --url "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --output my_playlist.json

# YouTube
python src/main.py extract --url "https://www.youtube.com/playlist?list=PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG" --output my_playlist.json
```

### Identify Songs (Match with MusicBrainz)

```bash
python src/main.py identify --input my_playlist.json --output identified.json
```

### Download Audio from YouTube

```bash
python src/main.py download --input identified.json --output downloaded.json
```

### Do Everything at Once (Quick Mode)

```bash
python src/main.py quick --url "PLAYLIST_URL" --output final.json
```

This will:
1. Extract playlist metadata
2. Identify all songs
3. Download MP3s from YouTube
4. Save everything to `final.json`

## 4. Example Workflow

```bash
# 1. Extract Spotify playlist
python src/main.py extract --url "https://open.spotify.com/playlist/..." --output party_mix.json

# 2. Identify and download in one command
python src/main.py identify --input party_mix.json --download --output party_mix_final.json

# 3. Check downloads folder
ls downloads/
```

Your MP3s will be in the `downloads/` folder with proper metadata!

## 5. Using with BUTT (Broadcast Using This Tool)

After downloading, you can create an M3U playlist for BUTT:

```bash
# Generate M3U playlist
ls downloads/*.mp3 > my_playlist.m3u

# Or use absolute paths
find "$(pwd)/downloads" -name "*.mp3" > my_playlist.m3u
```

Then in BUTT:
1. Settings → Record
2. Add your M3U playlist
3. Start streaming!

## 6. Upload to AzuraCast (Optional)

```python
# Add this to main.py or create upload script
from src.azuracast import AzuraCastClient
from src.utils.models import Playlist
import json

# Load your playlist
with open("final.json") as f:
    playlist = Playlist(**json.load(f))

# Initialize client
client = AzuraCastClient()

# Test connection
client.test_connection()

# Upload all tracks
client.batch_upload(playlist.tracks)

# Create playlist in AzuraCast
client.create_playlist_from_tracks(playlist, schedule_enable=True)
```

## Troubleshooting

**"No module named 'spotipy'"**
- Run: `pip install -r requirements.txt`

**"SPOTIFY_CLIENT_ID not set"**
- Edit `.env` file and add your Spotify credentials

**"ffmpeg not found"**
- Install ffmpeg: `sudo apt install ffmpeg` (Linux) or `brew install ffmpeg` (Mac)

**Downloads fail**
- Make sure you have internet connection
- YouTube might block repeated requests - add delays
- Some videos may be region-restricted

**Identification fails**
- MusicBrainz has rate limits (1 request/second)
- Some tracks might not be in their database
- Check spelling of artist/title

## Next Steps

- Add more extractors (SoundCloud, Apple Music)
- Set up AzuraCast integration
- Create automated workflows
- Build a web interface

Need help? Check the full README.md or open an issue!
