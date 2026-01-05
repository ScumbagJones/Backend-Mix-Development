"""Data models for the playlist converter system."""

from typing import Optional, List
from pydantic import BaseModel, Field


class Track(BaseModel):
    """Represents a music track with metadata."""

    # Original metadata from source
    title: str
    artist: str
    album: Optional[str] = None
    duration_ms: Optional[int] = None
    source: str  # spotify, youtube, soundcloud, etc.
    source_id: str  # original ID from the source platform
    source_url: Optional[str] = None

    # Additional metadata
    album_artist: Optional[str] = None
    track_number: Optional[int] = None
    release_year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)

    # Identification data
    isrc: Optional[str] = None  # International Standard Recording Code
    musicbrainz_id: Optional[str] = None
    acoustid: Optional[str] = None

    # Match confidence (0-100)
    match_confidence: Optional[float] = None

    # Local file info (after download)
    local_path: Optional[str] = None
    file_format: Optional[str] = None
    file_size_bytes: Optional[int] = None

    # AzuraCast info (after upload)
    azuracast_id: Optional[str] = None
    azuracast_uploaded: bool = False


class Playlist(BaseModel):
    """Represents a playlist with tracks."""

    name: str
    description: Optional[str] = None
    source: str
    source_id: str
    source_url: Optional[str] = None
    owner: Optional[str] = None
    tracks: List[Track] = Field(default_factory=list)
    total_tracks: int = 0
    created_at: Optional[str] = None

    # Processing status
    extracted: bool = False
    identified: bool = False
    downloaded: bool = False
    uploaded_to_azuracast: bool = False


class IdentificationResult(BaseModel):
    """Result of song identification process."""

    query_title: str
    query_artist: str

    # Best match
    matched: bool = False
    musicbrainz_id: Optional[str] = None
    matched_title: Optional[str] = None
    matched_artist: Optional[str] = None
    matched_album: Optional[str] = None
    isrc: Optional[str] = None
    confidence: float = 0.0

    # Alternative matches
    alternatives: List[dict] = Field(default_factory=list)
