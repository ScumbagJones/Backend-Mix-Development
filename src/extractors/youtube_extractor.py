"""Extract playlist metadata from YouTube."""

import re
from typing import Optional, List
import yt_dlp

from ..utils.models import Track, Playlist


class YouTubeExtractor:
    """Extract playlist information from YouTube."""

    def extract_playlist(self, playlist_url: str) -> Optional[Playlist]:
        """
        Extract playlist metadata from YouTube.

        Args:
            playlist_url: YouTube playlist URL

        Returns:
            Playlist object with tracks
        """
        # Validate URL
        if not self._is_valid_playlist_url(playlist_url):
            print("Invalid YouTube playlist URL")
            return None

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,  # Don't download, just get metadata
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                playlist_data = ydl.extract_info(playlist_url, download=False)

                if not playlist_data:
                    return None

                # Extract playlist ID
                playlist_id = self._extract_playlist_id(playlist_url)

                playlist = Playlist(
                    name=playlist_data.get("title", "Unknown Playlist"),
                    description=playlist_data.get("description", ""),
                    source="youtube",
                    source_id=playlist_id or "",
                    source_url=playlist_url,
                    owner=playlist_data.get("uploader", "Unknown"),
                    total_tracks=len(playlist_data.get("entries", [])),
                    extracted=True
                )

                # Parse tracks
                tracks = []
                for entry in playlist_data.get("entries", []):
                    if entry is None:
                        continue

                    track = self._parse_track(entry)
                    tracks.append(track)

                playlist.tracks = tracks

                print(f"Extracted playlist: {playlist.name}")
                print(f"  Tracks: {len(tracks)}")
                print(f"  Owner: {playlist.owner}")

                return playlist

        except Exception as e:
            print(f"Error extracting YouTube playlist: {e}")
            return None

    def extract_video(self, video_url: str) -> Optional[Track]:
        """
        Extract metadata from a single YouTube video.

        Args:
            video_url: YouTube video URL

        Returns:
            Track object
        """
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_data = ydl.extract_info(video_url, download=False)

                if not video_data:
                    return None

                return self._parse_track(video_data)

        except Exception as e:
            print(f"Error extracting YouTube video: {e}")
            return None

    def _parse_track(self, video_data: dict) -> Track:
        """
        Parse YouTube video data into Track object.

        Args:
            video_data: Video data from yt-dlp

        Returns:
            Track object
        """
        # Try to parse artist and title from video title
        title = video_data.get("title", "Unknown")
        artist, parsed_title = self._parse_title(title)

        track = Track(
            title=parsed_title,
            artist=artist,
            duration_ms=int(video_data.get("duration", 0) * 1000),
            source="youtube",
            source_id=video_data.get("id", ""),
            source_url=f"https://www.youtube.com/watch?v={video_data.get('id', '')}"
        )

        # Try to extract album from description or tags
        description = video_data.get("description", "")
        if description:
            # Look for album info in description (common patterns)
            album_match = re.search(r"album[:\s]+([^\n]+)", description, re.IGNORECASE)
            if album_match:
                track.album = album_match.group(1).strip()

        return track

    def _parse_title(self, title: str) -> tuple[str, str]:
        """
        Try to extract artist and title from YouTube video title.

        Common patterns:
        - "Artist - Title"
        - "Artist: Title"
        - "Title by Artist"
        - "Title (Artist)"

        Args:
            title: Video title

        Returns:
            Tuple of (artist, title)
        """
        # Pattern 1: "Artist - Title" or "Artist: Title"
        match = re.match(r"^([^-:]+)[\s\-:]+(.+)$", title)
        if match:
            artist = match.group(1).strip()
            song_title = match.group(2).strip()

            # Remove common suffixes
            song_title = self._clean_title(song_title)

            return artist, song_title

        # Pattern 2: "Title by Artist"
        match = re.match(r"^(.+?)\s+by\s+(.+)$", title, re.IGNORECASE)
        if match:
            song_title = self._clean_title(match.group(1).strip())
            artist = match.group(2).strip()
            return artist, song_title

        # Pattern 3: "Title (Artist)"
        match = re.match(r"^(.+?)\s*\(([^)]+)\)$", title)
        if match:
            song_title = self._clean_title(match.group(1).strip())
            artist = match.group(2).strip()
            return artist, song_title

        # Default: Use uploader as artist, title as-is
        return "Unknown Artist", self._clean_title(title)

    def _clean_title(self, title: str) -> str:
        """
        Remove common suffixes from title.

        Args:
            title: Song title

        Returns:
            Cleaned title
        """
        # Remove common patterns
        patterns = [
            r"\s*\(Official (Audio|Video|Music Video)\)",
            r"\s*\[Official (Audio|Video|Music Video)\]",
            r"\s*\(Lyrics?\)",
            r"\s*\[Lyrics?\]",
            r"\s*\(HD\)",
            r"\s*\[HD\]",
            r"\s*\(4K\)",
            r"\s*\[4K\]",
        ]

        for pattern in patterns:
            title = re.sub(pattern, "", title, flags=re.IGNORECASE)

        return title.strip()

    def _is_valid_playlist_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube playlist URL."""
        return "youtube.com/playlist" in url or "list=" in url

    def _extract_playlist_id(self, url: str) -> Optional[str]:
        """Extract playlist ID from URL."""
        match = re.search(r"[?&]list=([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)
        return None
