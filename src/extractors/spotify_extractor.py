"""Extract playlist metadata from Spotify."""

import os
import re
from typing import Optional
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from ..utils.models import Track, Playlist


class SpotifyExtractor:
    """Extract playlist information from Spotify."""

    def __init__(self):
        """Initialize Spotify client."""
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError(
                "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env file"
            )

        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def extract_playlist(self, playlist_url_or_id: str) -> Optional[Playlist]:
        """
        Extract playlist metadata from Spotify.

        Args:
            playlist_url_or_id: Spotify playlist URL or ID

        Returns:
            Playlist object with tracks
        """
        # Extract playlist ID from URL if needed
        playlist_id = self._extract_playlist_id(playlist_url_or_id)

        if not playlist_id:
            print("Invalid Spotify playlist URL or ID")
            return None

        try:
            # Get playlist info
            playlist_data = self.sp.playlist(playlist_id)

            playlist = Playlist(
                name=playlist_data["name"],
                description=playlist_data.get("description", ""),
                source="spotify",
                source_id=playlist_id,
                source_url=playlist_data["external_urls"]["spotify"],
                owner=playlist_data["owner"]["display_name"],
                total_tracks=playlist_data["tracks"]["total"],
                extracted=True
            )

            # Get all tracks (handle pagination)
            tracks = []
            results = playlist_data["tracks"]

            while results:
                for item in results["items"]:
                    if item["track"] is None:
                        continue  # Skip local files/unavailable tracks

                    track_data = item["track"]
                    track = self._parse_track(track_data)
                    tracks.append(track)

                # Get next page if exists
                if results["next"]:
                    results = self.sp.next(results)
                else:
                    break

            playlist.tracks = tracks

            print(f"Extracted playlist: {playlist.name}")
            print(f"  Tracks: {len(tracks)}")
            print(f"  Owner: {playlist.owner}")

            return playlist

        except Exception as e:
            print(f"Error extracting Spotify playlist: {e}")
            return None

    def _parse_track(self, track_data: dict) -> Track:
        """
        Parse Spotify track data into Track object.

        Args:
            track_data: Track data from Spotify API

        Returns:
            Track object
        """
        artists = [artist["name"] for artist in track_data["artists"]]
        artist_str = ", ".join(artists)

        track = Track(
            title=track_data["name"],
            artist=artist_str,
            album=track_data["album"]["name"],
            duration_ms=track_data["duration_ms"],
            source="spotify",
            source_id=track_data["id"],
            source_url=track_data["external_urls"]["spotify"],
            album_artist=track_data["album"]["artists"][0]["name"],
            track_number=track_data["track_number"],
            release_year=self._extract_year(track_data["album"].get("release_date", ""))
        )

        # Extract ISRC if available
        if "external_ids" in track_data and "isrc" in track_data["external_ids"]:
            track.isrc = track_data["external_ids"]["isrc"]

        return track

    def _extract_playlist_id(self, url_or_id: str) -> Optional[str]:
        """
        Extract playlist ID from URL or return ID if already an ID.

        Args:
            url_or_id: Spotify URL or playlist ID

        Returns:
            Playlist ID or None
        """
        # If it's already an ID (no slashes or colons except spotify:playlist:)
        if "spotify.com" in url_or_id:
            # Extract from URL: https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
            match = re.search(r"playlist/([a-zA-Z0-9]+)", url_or_id)
            if match:
                return match.group(1)
        elif url_or_id.startswith("spotify:playlist:"):
            # Extract from URI: spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
            return url_or_id.split(":")[-1]
        elif re.match(r"^[a-zA-Z0-9]+$", url_or_id):
            # Already an ID
            return url_or_id

        return None

    def _extract_year(self, date_str: str) -> Optional[int]:
        """Extract year from date string."""
        if not date_str:
            return None

        try:
            return int(date_str.split("-")[0])
        except:
            return None

    def search_track(self, artist: str, title: str) -> Optional[Track]:
        """
        Search for a specific track on Spotify.

        Args:
            artist: Artist name
            title: Track title

        Returns:
            Track object if found
        """
        try:
            query = f"artist:{artist} track:{title}"
            results = self.sp.search(q=query, type="track", limit=1)

            if not results["tracks"]["items"]:
                return None

            track_data = results["tracks"]["items"][0]
            return self._parse_track(track_data)

        except Exception as e:
            print(f"Error searching Spotify: {e}")
            return None
