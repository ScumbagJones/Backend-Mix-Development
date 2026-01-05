"""Song identification and matching using MusicBrainz."""

import musicbrainzngs as mb
from typing import Optional, List, Dict
import time
import os
from ..utils.models import Track, IdentificationResult


class SongMatcher:
    """Matches songs using MusicBrainz database."""

    def __init__(self):
        """Initialize MusicBrainz client."""
        app_name = os.getenv("MUSICBRAINZ_APP_NAME", "PlaylistConverter")
        app_version = os.getenv("MUSICBRAINZ_APP_VERSION", "1.0.0")
        contact = os.getenv("MUSICBRAINZ_CONTACT", "user@example.com")

        mb.set_useragent(app_name, app_version, contact)
        mb.set_rate_limit(limit_or_interval=1.0)  # Be nice to MusicBrainz

    def identify_track(self, track: Track) -> IdentificationResult:
        """
        Identify a track using MusicBrainz.

        Args:
            track: Track object with at least title and artist

        Returns:
            IdentificationResult with match data
        """
        result = IdentificationResult(
            query_title=track.title,
            query_artist=track.artist
        )

        try:
            # Search for recording
            search_results = self._search_recording(
                track.title,
                track.artist,
                track.album
            )

            if not search_results:
                return result

            # Get best match
            best_match = search_results[0]
            result.matched = True
            result.musicbrainz_id = best_match["id"]
            result.matched_title = best_match.get("title", "")
            result.confidence = best_match.get("score", 0) / 100.0

            # Extract artist name
            if "artist-credit" in best_match:
                artists = [ac["artist"]["name"] for ac in best_match["artist-credit"]
                          if isinstance(ac, dict) and "artist" in ac]
                result.matched_artist = ", ".join(artists)

            # Get ISRC if available
            if "isrc-list" in best_match and best_match["isrc-list"]:
                result.isrc = best_match["isrc-list"][0]

            # Get album info if available
            if "release-list" in best_match and best_match["release-list"]:
                result.matched_album = best_match["release-list"][0].get("title")

            # Store alternatives
            for match in search_results[1:6]:  # Top 5 alternatives
                alt = {
                    "id": match["id"],
                    "title": match.get("title", ""),
                    "score": match.get("score", 0)
                }
                if "artist-credit" in match:
                    artists = [ac["artist"]["name"] for ac in match["artist-credit"]
                              if isinstance(ac, dict) and "artist" in ac]
                    alt["artist"] = ", ".join(artists)
                result.alternatives.append(alt)

            # Update original track object
            track.musicbrainz_id = result.musicbrainz_id
            track.isrc = result.isrc
            track.match_confidence = result.confidence

        except Exception as e:
            print(f"Error identifying track {track.title} by {track.artist}: {e}")
            result.matched = False

        return result

    def _search_recording(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None
    ) -> List[Dict]:
        """
        Search MusicBrainz for a recording.

        Args:
            title: Song title
            artist: Artist name
            album: Optional album name

        Returns:
            List of matching recordings, sorted by score
        """
        # Build search query
        query_parts = [f'recording:"{title}"', f'artist:"{artist}"']

        if album:
            query_parts.append(f'release:"{album}"')

        query = " AND ".join(query_parts)

        try:
            # Search recordings
            result = mb.search_recordings(query=query, limit=10)

            if "recording-list" not in result:
                return []

            # Sort by score (MusicBrainz returns score 0-100)
            recordings = result["recording-list"]
            recordings.sort(key=lambda x: x.get("ext:score", 0), reverse=True)

            return recordings

        except mb.WebServiceError as e:
            print(f"MusicBrainz API error: {e}")
            return []
        except Exception as e:
            print(f"Error searching MusicBrainz: {e}")
            return []

    def identify_by_isrc(self, isrc: str) -> Optional[IdentificationResult]:
        """
        Look up track by ISRC code (most accurate method).

        Args:
            isrc: International Standard Recording Code

        Returns:
            IdentificationResult if found
        """
        try:
            result = mb.search_recordings(isrc=isrc, limit=1)

            if "recording-list" not in result or not result["recording-list"]:
                return None

            recording = result["recording-list"][0]

            id_result = IdentificationResult(
                query_title="",
                query_artist="",
                matched=True,
                musicbrainz_id=recording["id"],
                matched_title=recording.get("title", ""),
                isrc=isrc,
                confidence=1.0  # ISRC is exact match
            )

            # Extract artist
            if "artist-credit" in recording:
                artists = [ac["artist"]["name"] for ac in recording["artist-credit"]
                          if isinstance(ac, dict) and "artist" in ac]
                id_result.matched_artist = ", ".join(artists)

            return id_result

        except Exception as e:
            print(f"Error looking up ISRC {isrc}: {e}")
            return None

    def batch_identify(
        self,
        tracks: List[Track],
        delay: float = 1.0
    ) -> List[IdentificationResult]:
        """
        Identify multiple tracks with rate limiting.

        Args:
            tracks: List of tracks to identify
            delay: Delay between requests in seconds

        Returns:
            List of IdentificationResults
        """
        results = []

        for i, track in enumerate(tracks):
            print(f"Identifying {i+1}/{len(tracks)}: {track.title} - {track.artist}")

            result = self.identify_track(track)
            results.append(result)

            if result.matched:
                print(f"  ✓ Matched: {result.matched_title} (confidence: {result.confidence:.2f})")
            else:
                print(f"  ✗ No match found")

            # Rate limiting
            if i < len(tracks) - 1:
                time.sleep(delay)

        return results

    def get_track_details(self, musicbrainz_id: str) -> Optional[Dict]:
        """
        Get detailed information about a track from MusicBrainz.

        Args:
            musicbrainz_id: MusicBrainz recording ID

        Returns:
            Dictionary with detailed track info
        """
        try:
            result = mb.get_recording_by_id(
                musicbrainz_id,
                includes=["artists", "releases", "isrcs", "tags"]
            )

            if "recording" not in result:
                return None

            recording = result["recording"]

            details = {
                "id": recording["id"],
                "title": recording.get("title"),
                "length_ms": recording.get("length"),
                "artists": [],
                "isrc": None,
                "releases": [],
                "genres": []
            }

            # Extract artists
            if "artist-credit" in recording:
                details["artists"] = [
                    ac["artist"]["name"] for ac in recording["artist-credit"]
                    if isinstance(ac, dict) and "artist" in ac
                ]

            # Extract ISRC
            if "isrc-list" in recording and recording["isrc-list"]:
                details["isrc"] = recording["isrc-list"][0]

            # Extract releases (albums)
            if "release-list" in recording:
                details["releases"] = [
                    {
                        "title": rel.get("title"),
                        "date": rel.get("date"),
                        "country": rel.get("country")
                    }
                    for rel in recording["release-list"]
                ]

            # Extract genres/tags
            if "tag-list" in recording:
                details["genres"] = [tag["name"] for tag in recording["tag-list"]]

            return details

        except Exception as e:
            print(f"Error getting track details for {musicbrainz_id}: {e}")
            return None
