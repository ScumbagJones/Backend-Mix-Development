"""Download audio from YouTube using yt-dlp."""

import os
import re
from typing import Optional, Dict, List
from pathlib import Path
import yt_dlp
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK

from ..utils.models import Track


class YouTubeDownloader:
    """Download and convert YouTube videos to audio files."""

    def __init__(
        self,
        download_dir: str = "./downloads",
        audio_format: str = "mp3",
        audio_quality: str = "320"
    ):
        """
        Initialize YouTube downloader.

        Args:
            download_dir: Directory to save downloaded files
            audio_format: Output audio format (mp3, m4a, wav, etc.)
            audio_quality: Audio quality in kbps (128, 192, 256, 320)
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.audio_format = audio_format
        self.audio_quality = audio_quality

    def download_track(
        self,
        track: Track,
        search_query: Optional[str] = None
    ) -> bool:
        """
        Download a track from YouTube.

        Args:
            track: Track object with metadata
            search_query: Optional custom search query. If not provided,
                         uses "artist - title"

        Returns:
            True if download successful, False otherwise
        """
        if not search_query:
            search_query = f"{track.artist} - {track.title}"

        print(f"Searching YouTube for: {search_query}")

        try:
            # Search YouTube and get best match
            video_info = self._search_youtube(search_query)

            if not video_info:
                print(f"  ✗ No YouTube results found")
                return False

            video_url = video_info["url"]
            video_title = video_info["title"]

            print(f"  Found: {video_title}")
            print(f"  Downloading from: {video_url}")

            # Download and convert
            output_file = self._download_audio(video_url, track)

            if not output_file:
                return False

            # Add metadata tags
            self._add_metadata(output_file, track)

            # Update track object
            track.local_path = str(output_file)
            track.file_format = self.audio_format
            track.file_size_bytes = output_file.stat().st_size

            print(f"  ✓ Downloaded: {output_file.name}")
            return True

        except Exception as e:
            print(f"  ✗ Error downloading: {e}")
            return False

    def _search_youtube(self, query: str) -> Optional[Dict]:
        """
        Search YouTube and return best match.

        Args:
            query: Search query

        Returns:
            Dictionary with video info or None
        """
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search YouTube
                search_results = ydl.extract_info(
                    f"ytsearch1:{query}",
                    download=False
                )

                if not search_results or "entries" not in search_results:
                    return None

                entries = search_results["entries"]
                if not entries or len(entries) == 0:
                    return None

                video = entries[0]

                return {
                    "url": f"https://www.youtube.com/watch?v={video['id']}",
                    "title": video.get("title", ""),
                    "duration": video.get("duration", 0),
                    "uploader": video.get("uploader", "")
                }

        except Exception as e:
            print(f"YouTube search error: {e}")
            return None

    def _download_audio(
        self,
        url: str,
        track: Track
    ) -> Optional[Path]:
        """
        Download and convert video to audio.

        Args:
            url: YouTube video URL
            track: Track object for filename

        Returns:
            Path to downloaded file or None
        """
        # Create safe filename
        safe_artist = self._sanitize_filename(track.artist)
        safe_title = self._sanitize_filename(track.title)
        filename = f"{safe_artist} - {safe_title}.{self.audio_format}"
        output_path = self.download_dir / filename

        # yt-dlp options
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(output_path.with_suffix("")),
            "quiet": False,
            "no_warnings": False,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": self.audio_format,
                "preferredquality": self.audio_quality,
            }],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # yt-dlp might add extension, find the actual file
            for ext in [self.audio_format, "m4a", "opus", "webm"]:
                potential_file = output_path.with_suffix(f".{ext}")
                if potential_file.exists():
                    # Rename to desired extension if different
                    if potential_file.suffix != f".{self.audio_format}":
                        final_file = potential_file.with_suffix(f".{self.audio_format}")
                        potential_file.rename(final_file)
                        return final_file
                    return potential_file

            return output_path if output_path.exists() else None

        except Exception as e:
            print(f"Download error: {e}")
            return None

    def _add_metadata(self, file_path: Path, track: Track):
        """
        Add ID3 metadata tags to audio file.

        Args:
            file_path: Path to audio file
            track: Track object with metadata
        """
        try:
            if file_path.suffix.lower() != ".mp3":
                return  # Only works for MP3

            audio = MP3(str(file_path), ID3=ID3)

            # Add ID3 tags if they don't exist
            try:
                audio.add_tags()
            except:
                pass

            # Set metadata
            audio.tags.add(TIT2(encoding=3, text=track.title))
            audio.tags.add(TPE1(encoding=3, text=track.artist))

            if track.album:
                audio.tags.add(TALB(encoding=3, text=track.album))

            if track.release_year:
                audio.tags.add(TDRC(encoding=3, text=str(track.release_year)))

            if track.track_number:
                audio.tags.add(TRCK(encoding=3, text=str(track.track_number)))

            audio.save()

        except Exception as e:
            print(f"Error adding metadata: {e}")

    def _sanitize_filename(self, name: str) -> str:
        """
        Create safe filename from string.

        Args:
            name: String to sanitize

        Returns:
            Safe filename string
        """
        # Remove invalid characters
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        # Limit length
        return name[:100]

    def batch_download(
        self,
        tracks: List[Track],
        skip_existing: bool = True
    ) -> Dict[str, int]:
        """
        Download multiple tracks.

        Args:
            tracks: List of tracks to download
            skip_existing: Skip if file already exists

        Returns:
            Dictionary with success/failure counts
        """
        stats = {
            "total": len(tracks),
            "success": 0,
            "failed": 0,
            "skipped": 0
        }

        for i, track in enumerate(tracks):
            print(f"\n[{i+1}/{len(tracks)}] {track.artist} - {track.title}")

            # Check if already downloaded
            if skip_existing and track.local_path and Path(track.local_path).exists():
                print("  ⊘ Already downloaded, skipping")
                stats["skipped"] += 1
                continue

            # Download
            success = self.download_track(track)

            if success:
                stats["success"] += 1
            else:
                stats["failed"] += 1

        print(f"\n{'='*50}")
        print(f"Download complete!")
        print(f"  Success: {stats['success']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"{'='*50}")

        return stats

    def download_by_url(
        self,
        url: str,
        track: Optional[Track] = None
    ) -> Optional[Path]:
        """
        Download audio from a direct YouTube URL.

        Args:
            url: YouTube video URL
            track: Optional Track object for metadata

        Returns:
            Path to downloaded file or None
        """
        if not track:
            # Create a basic track object from video info
            try:
                with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    track = Track(
                        title=info.get("title", "Unknown"),
                        artist=info.get("uploader", "Unknown"),
                        source="youtube",
                        source_id=info.get("id", ""),
                        source_url=url
                    )
            except:
                track = Track(
                    title="Unknown",
                    artist="Unknown",
                    source="youtube",
                    source_id="",
                    source_url=url
                )

        return self._download_audio(url, track)
