"""
Demo: Shows what the extraction would return for your Spotify playlist.

This simulates the extraction since we can't make external API calls in this environment.
"""

from src.utils.models import Track, Playlist
import json

# Simulate what would be extracted from your Spotify playlist:
# https://open.spotify.com/playlist/0IKdJHrfWHKvokMMbYYCXw

def demo_extraction():
    print("=" * 70)
    print("SIMULATED EXTRACTION - Your Spotify Playlist")
    print("=" * 70)
    print()

    # This is what the system would extract from your playlist
    demo_playlist = Playlist(
        name="Your Playlist Name",  # Would be the actual playlist name
        description="Playlist description from Spotify",
        source="spotify",
        source_id="0IKdJHrfWHKvokMMbYYCXw",
        source_url="https://open.spotify.com/playlist/0IKdJHrfWHKvokMMbYYCXw",
        owner="Playlist Owner",
        total_tracks=0,  # Would be actual count
        extracted=True
    )

    # Example tracks (this is what each song would look like)
    demo_tracks = [
        Track(
            title="Example Song 1",
            artist="Example Artist",
            album="Example Album",
            duration_ms=240000,  # 4 minutes
            source="spotify",
            source_id="spotify_track_id_1",
            source_url="https://open.spotify.com/track/...",
            track_number=1,
            release_year=2023,
            isrc="USRC12345678"  # International Standard Recording Code
        ),
        Track(
            title="Example Song 2",
            artist="Another Artist",
            album="Another Album",
            duration_ms=180000,  # 3 minutes
            source="spotify",
            source_id="spotify_track_id_2",
            source_url="https://open.spotify.com/track/...",
            track_number=2,
            release_year=2024,
            isrc="USRC87654321"
        )
    ]

    demo_playlist.tracks = demo_tracks
    demo_playlist.total_tracks = len(demo_tracks)

    # Display what was "extracted"
    print(f"✓ Playlist: {demo_playlist.name}")
    print(f"  Owner: {demo_playlist.owner}")
    print(f"  Total tracks: {demo_playlist.total_tracks}")
    print(f"  Source: {demo_playlist.source}")
    print()

    print("=" * 70)
    print("EXTRACTED TRACKS:")
    print("=" * 70)

    for i, track in enumerate(demo_playlist.tracks, 1):
        print(f"\n[{i}] {track.artist} - {track.title}")
        print(f"    Album: {track.album}")
        print(f"    Duration: {track.duration_ms // 1000}s")
        print(f"    Year: {track.release_year}")
        print(f"    ISRC: {track.isrc}")
        print(f"    Spotify URL: {track.source_url}")

    print()
    print("=" * 70)
    print("NEXT STEPS (what the system does):")
    print("=" * 70)
    print()
    print("1. IDENTIFY: Match each song with MusicBrainz database")
    print("   - Gets precise metadata")
    print("   - Finds alternative names/spellings")
    print("   - Confidence scoring")
    print()
    print("2. DOWNLOAD: Search YouTube and download as MP3")
    print("   - Searches: 'Artist - Title'")
    print("   - Downloads best audio quality")
    print("   - Converts to MP3 @ 320kbps")
    print("   - Adds ID3 tags (artist, title, album, year)")
    print("   - Saves to: downloads/Artist - Title.mp3")
    print()
    print("3. UPLOAD (optional): Send to AzuraCast")
    print("   - Upload all MP3s")
    print("   - Create playlist in AzuraCast")
    print("   - Ready for broadcasting!")
    print()

    # Save to JSON (like the real command would)
    output_file = "demo_playlist.json"
    with open(output_file, "w") as f:
        json.dump(demo_playlist.model_dump(), f, indent=2)

    print("=" * 70)
    print(f"✓ Saved playlist data to: {output_file}")
    print("=" * 70)
    print()

    # Show what the JSON looks like
    print("SAMPLE JSON OUTPUT:")
    print("-" * 70)
    print(json.dumps(demo_playlist.model_dump(), indent=2)[:800] + "\n...")
    print()

    return demo_playlist


def demo_identification():
    """Shows what song identification looks like."""
    print("\n" + "=" * 70)
    print("STEP 2: SONG IDENTIFICATION (with MusicBrainz)")
    print("=" * 70)
    print()

    print("For each track, the system queries MusicBrainz database:")
    print()
    print('[1] Searching: "Example Artist - Example Song 1"')
    print("    ✓ Found: Example Artist - Example Song 1")
    print("    MusicBrainz ID: a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6")
    print("    Confidence: 95%")
    print("    ISRC: USRC12345678 (verified)")
    print()
    print('[2] Searching: "Another Artist - Example Song 2"')
    print("    ✓ Found: Another Artist - Example Song 2")
    print("    MusicBrainz ID: z9y8x7w6-v5u4-t3s2-r1q0-p9o8n7m6l5k4")
    print("    Confidence: 92%")
    print("    ISRC: USRC87654321 (verified)")
    print()


def demo_download():
    """Shows what download process looks like."""
    print("\n" + "=" * 70)
    print("STEP 3: DOWNLOAD FROM YOUTUBE")
    print("=" * 70)
    print()

    print("[1/2] Example Artist - Example Song 1")
    print("  Searching YouTube for: Example Artist - Example Song 1")
    print("  Found: Example Artist - Example Song 1 (Official Audio)")
    print("  Downloading from: https://www.youtube.com/watch?v=...")
    print("  [download] 100% of 3.42MiB at 2.15MiB/s")
    print("  [ffmpeg] Converting to mp3...")
    print("  ✓ Downloaded: Example Artist - Example Song 1.mp3")
    print()
    print("[2/2] Another Artist - Example Song 2")
    print("  Searching YouTube for: Another Artist - Example Song 2")
    print("  Found: Another Artist - Example Song 2 (Lyrics Video)")
    print("  Downloading from: https://www.youtube.com/watch?v=...")
    print("  [download] 100% of 2.87MiB at 2.43MiB/s")
    print("  [ffmpeg] Converting to mp3...")
    print("  ✓ Downloaded: Another Artist - Example Song 2.mp3")
    print()
    print("=" * 70)
    print("Download complete!")
    print("  Success: 2")
    print("  Failed: 0")
    print("  Skipped: 0")
    print("=" * 70)
    print()
    print("Files saved to: ./downloads/")
    print("  - Example Artist - Example Song 1.mp3 (3.2 MB)")
    print("  - Another Artist - Example Song 2.mp3 (2.7 MB)")
    print()


if __name__ == "__main__":
    # Run the demo
    playlist = demo_extraction()
    demo_identification()
    demo_download()

    print("\n" + "=" * 70)
    print("WHAT YOU'D DO WITH YOUR ACTUAL PLAYLIST:")
    print("=" * 70)
    print()
    print("# In a normal environment with internet access:")
    print()
    print("1. Extract your playlist:")
    print('   python src/main.py extract --url "YOUR_SPOTIFY_URL" --output playlist.json')
    print()
    print("2. Identify all songs:")
    print('   python src/main.py identify --input playlist.json --output identified.json')
    print()
    print("3. Download all tracks:")
    print('   python src/main.py download --input identified.json --output final.json')
    print()
    print("OR do everything at once:")
    print('   python src/main.py quick --url "YOUR_SPOTIFY_URL"')
    print()
    print("=" * 70)
    print()
    print("Your tracks would then be in downloads/ ready for:")
    print("  • BUTT (broadcasting software)")
    print("  • AzuraCast (internet radio)")
    print("  • Any DJ software")
    print("  • Your own music library")
    print()
