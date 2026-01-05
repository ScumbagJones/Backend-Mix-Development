"""Extract playlist metadata from SoundCloud."""

import re
from typing import Optional
import requests
from bs4 import BeautifulSoup

from ..utils.models import Track, Playlist


class SoundCloudExtractor:
    """Extract playlist information from SoundCloud."""

    def __init__(self):
        """Initialize SoundCloud extractor."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def extract_playlist(self, playlist_url: str) -> Optional[Playlist]:
        """
        Extract playlist metadata from SoundCloud.

        Args:
            playlist_url: SoundCloud playlist URL

        Returns:
            Playlist object with tracks
        """
        try:
            response = self.session.get(playlist_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract playlist info from meta tags
            playlist_name = self._extract_meta(soup, 'og:title') or "Unknown Playlist"
            description = self._extract_meta(soup, 'og:description') or ""

            # Extract playlist ID from URL
            playlist_id = self._extract_playlist_id(playlist_url)

            # Try to find track data in page
            tracks = self._extract_tracks_from_html(soup)

            playlist = Playlist(
                name=playlist_name,
                description=description,
                source="soundcloud",
                source_id=playlist_id or "",
                source_url=playlist_url,
                owner=self._extract_owner(soup),
                total_tracks=len(tracks),
                extracted=True
            )

            playlist.tracks = tracks

            print(f"Extracted SoundCloud playlist: {playlist.name}")
            print(f"  Tracks: {len(tracks)}")

            return playlist

        except Exception as e:
            print(f"Error extracting SoundCloud playlist: {e}")
            return None

    def extract_track(self, track_url: str) -> Optional[Track]:
        """
        Extract metadata from a single SoundCloud track.

        Args:
            track_url: SoundCloud track URL

        Returns:
            Track object
        """
        try:
            response = self.session.get(track_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            title = self._extract_meta(soup, 'og:title') or "Unknown"
            artist = self._extract_meta(soup, 'twitter:title') or "Unknown Artist"

            # Try to parse artist from title (usually "Artist - Title")
            if " - " in title:
                parts = title.split(" - ", 1)
                artist = parts[0].strip()
                title = parts[1].strip()

            track = Track(
                title=title,
                artist=artist,
                source="soundcloud",
                source_id=self._extract_track_id(track_url) or "",
                source_url=track_url
            )

            return track

        except Exception as e:
            print(f"Error extracting SoundCloud track: {e}")
            return None

    def _extract_tracks_from_html(self, soup: BeautifulSoup) -> list:
        """Extract tracks from HTML page."""
        tracks = []

        # Look for track items in the HTML structure
        # SoundCloud dynamically loads content, so this might be limited
        track_items = soup.find_all('article', class_='trackItem')

        for item in track_items:
            try:
                title_elem = item.find('a', class_='trackItem__trackTitle')
                artist_elem = item.find('a', class_='trackItem__username')

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    artist = artist_elem.get_text(strip=True) if artist_elem else "Unknown"
                    track_url = title_elem.get('href', '')

                    if not track_url.startswith('http'):
                        track_url = f"https://soundcloud.com{track_url}"

                    track = Track(
                        title=title,
                        artist=artist,
                        source="soundcloud",
                        source_id=self._extract_track_id(track_url) or "",
                        source_url=track_url
                    )
                    tracks.append(track)

            except Exception as e:
                print(f"Error parsing track item: {e}")
                continue

        return tracks

    def _extract_meta(self, soup: BeautifulSoup, property_name: str) -> Optional[str]:
        """Extract meta tag content."""
        meta = soup.find('meta', property=property_name)
        if not meta:
            meta = soup.find('meta', attrs={'name': property_name})
        return meta.get('content') if meta else None

    def _extract_owner(self, soup: BeautifulSoup) -> str:
        """Extract playlist owner."""
        owner = self._extract_meta(soup, 'twitter:title')
        if owner and ' by ' in owner:
            return owner.split(' by ')[-1].strip()
        return "Unknown"

    def _extract_playlist_id(self, url: str) -> Optional[str]:
        """Extract playlist ID from URL."""
        match = re.search(r'soundcloud\.com/([^/]+)/sets/([^/?]+)', url)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        return None

    def _extract_track_id(self, url: str) -> Optional[str]:
        """Extract track ID from URL."""
        match = re.search(r'soundcloud\.com/([^/]+)/([^/?]+)', url)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        return None

    def search_track(self, artist: str, title: str) -> Optional[Track]:
        """
        Search for a track on SoundCloud.

        Args:
            artist: Artist name
            title: Track title

        Returns:
            Track object if found
        """
        query = f"{artist} {title}"
        search_url = f"https://soundcloud.com/search?q={query}"

        try:
            response = self.session.get(search_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find first track result
            track_link = soup.find('a', href=re.compile(r'/[^/]+/[^/]+$'))

            if track_link:
                track_url = track_link.get('href')
                if not track_url.startswith('http'):
                    track_url = f"https://soundcloud.com{track_url}"

                return self.extract_track(track_url)

        except Exception as e:
            print(f"Error searching SoundCloud: {e}")

        return None
