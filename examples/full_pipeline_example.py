"""Example: Complete pipeline from playlist URL to AzuraCast."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
from extractors import SpotifyExtractor, YouTubeExtractor
from identification import SongMatcher
from downloaders import YouTubeDownloader
from azuracast import AzuraCastClient

# Load environment variables
load_dotenv()


def example_spotify_to_azuracast():
    """
    Complete example: Spotify playlist → Download → Upload to AzuraCast.
    """
    # 1. Extract Spotify playlist
    print("=" * 60)
    print("STEP 1: Extracting Spotify playlist")
    print("=" * 60)

    spotify_url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"  # Top 50 Global
    extractor = SpotifyExtractor()
    playlist = extractor.extract_playlist(spotify_url)

    if not playlist:
        print("Failed to extract playlist")
        return

    # Limit to first 5 tracks for demo
    playlist.tracks = playlist.tracks[:5]
    print(f"\nExtracted: {playlist.name}")
    print(f"Tracks: {len(playlist.tracks)}")

    # 2. Identify tracks
    print("\n" + "=" * 60)
    print("STEP 2: Identifying tracks with MusicBrainz")
    print("=" * 60)

    matcher = SongMatcher()
    results = matcher.batch_identify(playlist.tracks)

    matched = sum(1 for r in results if r.matched)
    print(f"\nMatched: {matched}/{len(results)}")

    # 3. Download from YouTube
    print("\n" + "=" * 60)
    print("STEP 3: Downloading audio from YouTube")
    print("=" * 60)

    downloader = YouTubeDownloader()
    stats = downloader.batch_download(playlist.tracks)

    print(f"\nDownloaded: {stats['success']} tracks")

    # 4. Upload to AzuraCast (optional - comment out if not configured)
    if os.getenv("AZURACAST_API_KEY"):
        print("\n" + "=" * 60)
        print("STEP 4: Uploading to AzuraCast")
        print("=" * 60)

        try:
            client = AzuraCastClient()

            # Test connection
            if not client.test_connection():
                print("Could not connect to AzuraCast")
                return

            # Upload tracks
            upload_stats = client.batch_upload(playlist.tracks)

            # Create playlist
            if upload_stats['success'] > 0:
                client.create_playlist_from_tracks(playlist, schedule_enable=False)

            print("\n✓ Complete! Your playlist is ready in AzuraCast")

        except Exception as e:
            print(f"AzuraCast integration skipped: {e}")
    else:
        print("\n" + "=" * 60)
        print("STEP 4: AzuraCast upload (skipped - no API key configured)")
        print("=" * 60)
        print("Set AZURACAST_API_KEY in .env to enable upload")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Playlist: {playlist.name}")
    print(f"Tracks extracted: {len(playlist.tracks)}")
    print(f"Tracks identified: {matched}")
    print(f"Tracks downloaded: {stats['success']}")
    print(f"\nDownload location: ./downloads/")
    print("=" * 60)


def example_youtube_quick():
    """
    Quick example: Download playlist from YouTube.
    """
    print("=" * 60)
    print("Quick YouTube Playlist Download")
    print("=" * 60)

    # Extract YouTube playlist
    youtube_url = "https://www.youtube.com/playlist?list=PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG"
    extractor = YouTubeExtractor()
    playlist = extractor.extract_playlist(youtube_url)

    if not playlist:
        print("Failed to extract playlist")
        return

    # Limit for demo
    playlist.tracks = playlist.tracks[:3]

    print(f"\nPlaylist: {playlist.name}")
    print(f"Tracks: {len(playlist.tracks)}")

    # Download
    downloader = YouTubeDownloader()
    stats = downloader.batch_download(playlist.tracks)

    print(f"\n✓ Downloaded {stats['success']} tracks to ./downloads/")


def example_single_song():
    """
    Example: Search and download a single song.
    """
    print("=" * 60)
    print("Single Song Download")
    print("=" * 60)

    # Create a track manually
    from utils.models import Track

    track = Track(
        title="Bohemian Rhapsody",
        artist="Queen",
        source="manual",
        source_id="example"
    )

    # Identify
    print(f"\nSearching for: {track.artist} - {track.title}")

    matcher = SongMatcher()
    result = matcher.identify_track(track)

    if result.matched:
        print(f"✓ Found: {result.matched_artist} - {result.matched_title}")
        print(f"  Confidence: {result.confidence:.2%}")

    # Download
    print("\nDownloading from YouTube...")
    downloader = YouTubeDownloader()
    success = downloader.download_track(track)

    if success:
        print(f"✓ Downloaded to: {track.local_path}")
    else:
        print("✗ Download failed")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Playlist converter examples")
    parser.add_argument(
        "--example",
        choices=["spotify", "youtube", "single"],
        default="spotify",
        help="Which example to run"
    )

    args = parser.parse_args()

    if args.example == "spotify":
        example_spotify_to_azuracast()
    elif args.example == "youtube":
        example_youtube_quick()
    elif args.example == "single":
        example_single_song()
