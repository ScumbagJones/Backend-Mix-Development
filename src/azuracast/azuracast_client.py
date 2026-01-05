"""AzuraCast API client for uploading music and creating playlists."""

import os
import requests
from typing import List, Dict, Optional
from pathlib import Path

from ..utils.models import Track, Playlist


class AzuraCastClient:
    """Client for interacting with AzuraCast API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        station_id: Optional[int] = None
    ):
        """
        Initialize AzuraCast client.

        Args:
            base_url: AzuraCast instance URL (e.g., http://your-azuracast.com)
            api_key: API key for authentication
            station_id: Station ID to upload to
        """
        self.base_url = (base_url or os.getenv("AZURACAST_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("AZURACAST_API_KEY")
        self.station_id = station_id or int(os.getenv("AZURACAST_STATION_ID", "1"))

        if not self.base_url or not self.api_key:
            raise ValueError(
                "AZURACAST_BASE_URL and AZURACAST_API_KEY must be set"
            )

        self.headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json"
        }

    def upload_file(self, file_path: str, track: Track) -> Optional[Dict]:
        """
        Upload a music file to AzuraCast.

        Args:
            file_path: Path to audio file
            track: Track object with metadata

        Returns:
            Response data from AzuraCast or None
        """
        url = f"{self.base_url}/api/station/{self.station_id}/files"

        file_path = Path(file_path)
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return None

        try:
            # Prepare file upload
            with open(file_path, "rb") as f:
                files = {
                    "file": (file_path.name, f, "audio/mpeg")
                }

                # Upload file
                response = requests.post(
                    url,
                    headers=self.headers,
                    files=files
                )

                response.raise_for_status()
                data = response.json()

                print(f"  ✓ Uploaded: {file_path.name}")

                # Update track with AzuraCast info
                if "id" in data:
                    track.azuracast_id = str(data["id"])
                    track.azuracast_uploaded = True

                return data

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Upload failed: {e}")
            return None

    def batch_upload(self, tracks: List[Track]) -> Dict[str, int]:
        """
        Upload multiple tracks to AzuraCast.

        Args:
            tracks: List of tracks with local_path set

        Returns:
            Dictionary with upload statistics
        """
        stats = {
            "total": len(tracks),
            "success": 0,
            "failed": 0,
            "skipped": 0
        }

        print(f"\nUploading {len(tracks)} tracks to AzuraCast...")
        print("=" * 50)

        for i, track in enumerate(tracks):
            print(f"[{i+1}/{len(tracks)}] {track.artist} - {track.title}")

            # Skip if no local file
            if not track.local_path or not Path(track.local_path).exists():
                print("  ⊘ No local file, skipping")
                stats["skipped"] += 1
                continue

            # Skip if already uploaded
            if track.azuracast_uploaded:
                print("  ⊘ Already uploaded, skipping")
                stats["skipped"] += 1
                continue

            # Upload
            result = self.upload_file(track.local_path, track)

            if result:
                stats["success"] += 1
            else:
                stats["failed"] += 1

        print(f"\n{'='*50}")
        print(f"Upload complete!")
        print(f"  Success: {stats['success']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"{'='*50}")

        return stats

    def create_playlist(
        self,
        name: str,
        track_ids: List[str],
        schedule_enable: bool = False
    ) -> Optional[Dict]:
        """
        Create a playlist in AzuraCast.

        Args:
            name: Playlist name
            track_ids: List of track IDs (from AzuraCast)
            schedule_enable: Enable scheduling for this playlist

        Returns:
            Response data or None
        """
        url = f"{self.base_url}/api/station/{self.station_id}/playlists"

        payload = {
            "name": name,
            "type": "default",
            "source": "songs",
            "order": "sequential",
            "include_in_automation": schedule_enable,
            "media_items": [{"id": track_id} for track_id in track_ids]
        }

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload
            )

            response.raise_for_status()
            data = response.json()

            print(f"✓ Created playlist: {name}")
            return data

        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to create playlist: {e}")
            return None

    def create_playlist_from_tracks(
        self,
        playlist: Playlist,
        schedule_enable: bool = False
    ) -> Optional[Dict]:
        """
        Create AzuraCast playlist from Playlist object.

        Args:
            playlist: Playlist with tracks that have azuracast_id set
            schedule_enable: Enable scheduling

        Returns:
            Response data or None
        """
        # Get track IDs
        track_ids = [
            track.azuracast_id
            for track in playlist.tracks
            if track.azuracast_id
        ]

        if not track_ids:
            print("No tracks have AzuraCast IDs. Upload tracks first.")
            return None

        print(f"\nCreating playlist with {len(track_ids)} tracks...")

        return self.create_playlist(
            name=playlist.name,
            track_ids=track_ids,
            schedule_enable=schedule_enable
        )

    def get_station_info(self) -> Optional[Dict]:
        """
        Get information about the station.

        Returns:
            Station info or None
        """
        url = f"{self.base_url}/api/station/{self.station_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error getting station info: {e}")
            return None

    def test_connection(self) -> bool:
        """
        Test connection to AzuraCast instance.

        Returns:
            True if connection successful
        """
        try:
            info = self.get_station_info()
            if info:
                print(f"✓ Connected to AzuraCast")
                print(f"  Station: {info.get('name', 'Unknown')}")
                print(f"  URL: {self.base_url}")
                return True
            return False

        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
