"""Main CLI interface for playlist converter."""

import argparse
import json
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

from extractors import SpotifyExtractor, YouTubeExtractor
from identification import SongMatcher
from downloaders import YouTubeDownloader
from utils.models import Playlist, Track


# Load environment variables
load_dotenv()


class PlaylistConverter:
    """Main playlist converter orchestrator."""

    def __init__(self):
        """Initialize all components."""
        self.song_matcher = SongMatcher()
        self.youtube_downloader = YouTubeDownloader(
            download_dir=os.getenv("DOWNLOAD_DIR", "./downloads"),
            audio_format=os.getenv("AUDIO_FORMAT", "mp3"),
            audio_quality=os.getenv("AUDIO_QUALITY", "320")
        )

    def extract_playlist(self, url: str, output_file: str = None) -> Playlist:
        """
        Extract playlist metadata from URL.

        Args:
            url: Playlist URL (Spotify or YouTube)
            output_file: Optional file to save playlist JSON

        Returns:
            Playlist object
        """
        playlist = None

        # Determine source and extract
        if "spotify.com" in url or url.startswith("spotify:"):
            print("Detected Spotify playlist")
            extractor = SpotifyExtractor()
            playlist = extractor.extract_playlist(url)

        elif "youtube.com" in url or "youtu.be" in url:
            print("Detected YouTube playlist")
            extractor = YouTubeExtractor()
            playlist = extractor.extract_playlist(url)

        else:
            print("Unsupported URL. Supported: Spotify, YouTube")
            return None

        if not playlist:
            print("Failed to extract playlist")
            return None

        # Save to file if requested
        if output_file:
            self._save_playlist(playlist, output_file)

        return playlist

    def identify_tracks(self, playlist: Playlist, output_file: str = None) -> Playlist:
        """
        Identify all tracks in playlist using MusicBrainz.

        Args:
            playlist: Playlist with tracks to identify
            output_file: Optional file to save updated playlist

        Returns:
            Updated playlist with identification data
        """
        print(f"\nIdentifying {len(playlist.tracks)} tracks...")
        print("=" * 50)

        results = self.song_matcher.batch_identify(playlist.tracks)

        # Update playlist status
        playlist.identified = True

        # Save results
        if output_file:
            self._save_playlist(playlist, output_file)

        # Print summary
        matched = sum(1 for r in results if r.matched)
        print(f"\nIdentification complete: {matched}/{len(results)} matched")

        return playlist

    def download_tracks(self, playlist: Playlist, output_file: str = None) -> Playlist:
        """
        Download all tracks in playlist from YouTube.

        Args:
            playlist: Playlist with tracks to download
            output_file: Optional file to save updated playlist

        Returns:
            Updated playlist with download info
        """
        print(f"\nDownloading {len(playlist.tracks)} tracks from YouTube...")
        print("=" * 50)

        stats = self.youtube_downloader.batch_download(playlist.tracks)

        # Update playlist status
        playlist.downloaded = True

        # Save results
        if output_file:
            self._save_playlist(playlist, output_file)

        return playlist

    def _save_playlist(self, playlist: Playlist, filename: str):
        """Save playlist to JSON file."""
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(playlist.model_dump(), f, indent=2)

        print(f"\nSaved playlist to: {filename}")

    def _load_playlist(self, filename: str) -> Playlist:
        """Load playlist from JSON file."""
        with open(filename, "r") as f:
            data = json.load(f)
            return Playlist(**data)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert playlists from streaming services to AzuraCast",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract Spotify playlist
  python main.py extract --url "https://open.spotify.com/playlist/..." --output playlist.json

  # Extract and identify in one go
  python main.py extract --url "https://youtube.com/playlist?list=..." --identify --output playlist.json

  # Identify tracks from saved playlist
  python main.py identify --input playlist.json --output identified.json

  # Download tracks
  python main.py download --input playlist.json --output downloaded.json

  # Full pipeline: extract, identify, and download
  python main.py extract --url "PLAYLIST_URL" --identify --download --output final.json
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract playlist metadata")
    extract_parser.add_argument("--url", required=True, help="Playlist URL")
    extract_parser.add_argument("--output", "-o", help="Output JSON file")
    extract_parser.add_argument("--identify", action="store_true", help="Also identify tracks")
    extract_parser.add_argument("--download", action="store_true", help="Also download tracks")

    # Identify command
    identify_parser = subparsers.add_parser("identify", help="Identify tracks using MusicBrainz")
    identify_parser.add_argument("--input", "-i", required=True, help="Input playlist JSON")
    identify_parser.add_argument("--output", "-o", help="Output JSON file")
    identify_parser.add_argument("--download", action="store_true", help="Also download tracks")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download tracks from YouTube")
    download_parser.add_argument("--input", "-i", required=True, help="Input playlist JSON")
    download_parser.add_argument("--output", "-o", help="Output JSON file")

    # Quick command (does everything)
    quick_parser = subparsers.add_parser("quick", help="Extract, identify, and download in one command")
    quick_parser.add_argument("--url", required=True, help="Playlist URL")
    quick_parser.add_argument("--output", "-o", default="playlist.json", help="Output JSON file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize converter
    converter = PlaylistConverter()

    try:
        if args.command == "extract":
            # Extract playlist
            playlist = converter.extract_playlist(args.url, args.output)

            if not playlist:
                return

            # Optional: identify
            if args.identify:
                playlist = converter.identify_tracks(playlist, args.output)

            # Optional: download
            if args.download:
                playlist = converter.download_tracks(playlist, args.output)

        elif args.command == "identify":
            # Load playlist
            playlist = converter._load_playlist(args.input)

            # Identify
            playlist = converter.identify_tracks(playlist, args.output or args.input)

            # Optional: download
            if args.download:
                playlist = converter.download_tracks(playlist, args.output or args.input)

        elif args.command == "download":
            # Load playlist
            playlist = converter._load_playlist(args.input)

            # Download
            playlist = converter.download_tracks(playlist, args.output or args.input)

        elif args.command == "quick":
            # Do everything
            print("Starting full pipeline...")

            # Extract
            playlist = converter.extract_playlist(args.url)

            if not playlist:
                return

            # Identify
            playlist = converter.identify_tracks(playlist)

            # Download
            playlist = converter.download_tracks(playlist, args.output)

            print("\n" + "=" * 50)
            print("✓ Pipeline complete!")
            print(f"  Playlist: {playlist.name}")
            print(f"  Tracks: {len(playlist.tracks)}")
            print(f"  Output: {args.output}")
            print("=" * 50)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
