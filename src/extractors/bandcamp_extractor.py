"""Extract playlist/album metadata from Bandcamp."""

import re
from typing import Optional
import requests
from bs4 import BeautifulSoup
import json

from ..utils.models import Track, Playlist


class BandcampExtractor:
    """Extract album/playlist information from Bandcamp."""

    def __init__(self):
        """Initialize Bandcamp extractor."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def extract_album(self, album_url: str) -> Optional[Playlist]:
        """
        Extract album metadata from Bandcamp (albums are treated as playlists).

        Args:
            album_url: Bandcamp album URL

        Returns:
            Playlist object with tracks
        """
        try:
            response = self.session.get(album_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Bandcamp embeds data in JavaScript - extract it
            track_data = self._extract_track_data(soup)

            if not track_data:
                print("Could not find track data in page")
                return None

            # Extract album info
            album_name = track_data.get('album_title') or track_data.get('current', {}).get('title', 'Unknown Album')
            artist_name = track_data.get('artist', 'Unknown Artist')

            playlist = Playlist(
                name=album_name,
                description=f"Bandcamp album by {artist_name}",
                source="bandcamp",
                source_id=self._extract_album_id(album_url) or "",
                source_url=album_url,
                owner=artist_name,
                total_tracks=0,
                extracted=True
            )

            # Parse tracks
            tracks = []
            track_info_list = track_data.get('trackinfo', [])

            for i, track_info in enumerate(track_info_list):
                track = Track(
                    title=track_info.get('title', f'Track {i+1}'),
                    artist=artist_name,
                    album=album_name,
                    duration_ms=int(track_info.get('duration', 0) * 1000),
                    source="bandcamp",
                    source_id=str(track_info.get('track_id', '')),
                    source_url=track_info.get('title_link', album_url),
                    track_number=i + 1,
                    release_year=self._extract_year(soup)
                )

                # Bandcamp sometimes has direct file URLs (for preview)
                if 'file' in track_info and isinstance(track_info['file'], dict):
                    file_url = track_info['file'].get('mp3-128')
                    if file_url:
                        track.source_url = file_url

                tracks.append(track)

            playlist.tracks = tracks
            playlist.total_tracks = len(tracks)

            print(f"Extracted Bandcamp album: {album_name}")
            print(f"  Artist: {artist_name}")
            print(f"  Tracks: {len(tracks)}")

            return playlist

        except Exception as e:
            print(f"Error extracting Bandcamp album: {e}")
            return None

    def _extract_track_data(self, soup: BeautifulSoup) -> Optional[dict]:
        """Extract embedded track data from page JavaScript."""
        # Find the script tag with track data
        scripts = soup.find_all('script', type='application/ld+json')

        for script in scripts:
            try:
                data = json.loads(script.string)
                if '@type' in data and 'MusicAlbum' in data['@type']:
                    # Found structured data
                    return self._parse_structured_data(data)
            except:
                continue

        # Fallback: look for TralbumData in script tags
        for script in soup.find_all('script'):
            if script.string and 'TralbumData' in script.string:
                # Extract JSON from JavaScript variable
                match = re.search(r'TralbumData\s*=\s*(\{.*?\});', script.string, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except:
                        pass

        return None

    def _parse_structured_data(self, data: dict) -> dict:
        """Parse structured data into our format."""
        result = {
            'album_title': data.get('name', ''),
            'artist': '',
            'trackinfo': []
        }

        # Get artist
        if 'byArtist' in data:
            artist = data['byArtist']
            if isinstance(artist, dict):
                result['artist'] = artist.get('name', '')
            elif isinstance(artist, list) and len(artist) > 0:
                result['artist'] = artist[0].get('name', '')

        # Get tracks
        if 'track' in data and 'itemListElement' in data['track']:
            for item in data['track']['itemListElement']:
                track_item = item.get('item', {})
                result['trackinfo'].append({
                    'title': track_item.get('name', ''),
                    'duration': track_item.get('duration', 0),
                    'track_id': '',
                    'title_link': track_item.get('url', '')
                })

        return result

    def _extract_album_id(self, url: str) -> Optional[str]:
        """Extract album ID from URL."""
        match = re.search(r'bandcamp\.com/album/([^/?]+)', url)
        if match:
            return match.group(1)
        return None

    def _extract_year(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract release year from page."""
        # Look for copyright or release date
        meta_date = soup.find('meta', property='music:release_date')
        if meta_date:
            date_str = meta_date.get('content', '')
            match = re.search(r'(\d{4})', date_str)
            if match:
                return int(match.group(1))

        # Look in text content
        date_elem = soup.find('div', class_='tralbumData')
        if date_elem:
            text = date_elem.get_text()
            match = re.search(r'released\s+.*?(\d{4})', text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def search_album(self, artist: str, album: str) -> Optional[Playlist]:
        """
        Search for an album on Bandcamp.

        Args:
            artist: Artist name
            album: Album name

        Returns:
            Playlist object if found
        """
        query = f"{artist} {album}"
        search_url = f"https://bandcamp.com/search?q={query}"

        try:
            response = self.session.get(search_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find first album result
            album_link = soup.find('a', href=re.compile(r'/album/'))

            if album_link:
                album_url = album_link.get('href')
                return self.extract_album(album_url)

        except Exception as e:
            print(f"Error searching Bandcamp: {e}")

        return None
