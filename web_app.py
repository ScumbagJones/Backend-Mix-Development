"""
Web interface for Playlist Converter
Runs on http://localhost:8002
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
from pathlib import Path
import json
from threading import Thread
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.extractors import SpotifyExtractor, YouTubeExtractor, SoundCloudExtractor, BandcampExtractor
from src.identification import SongMatcher
from src.downloaders import YouTubeDownloader
from src.utils.models import Playlist, Track

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Global state for tracking jobs
jobs = {}


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/extract', methods=['POST'])
def extract_playlist():
    """Extract playlist metadata from URL."""
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        # Determine source
        if 'spotify.com' in url or url.startswith('spotify:'):
            extractor = SpotifyExtractor()
            playlist = extractor.extract_playlist(url)
        elif 'youtube.com' in url or 'youtu.be' in url:
            extractor = YouTubeExtractor()
            playlist = extractor.extract_playlist(url)
        elif 'soundcloud.com' in url:
            extractor = SoundCloudExtractor()
            playlist = extractor.extract_playlist(url)
        elif 'bandcamp.com' in url:
            extractor = BandcampExtractor()
            playlist = extractor.extract_album(url)
        else:
            return jsonify({'error': 'Unsupported URL. Use Spotify, YouTube, SoundCloud, or Bandcamp.'}), 400

        if not playlist:
            return jsonify({'error': 'Failed to extract playlist'}), 500

        # Store in memory (in production, use database)
        job_id = f"job_{len(jobs) + 1}"
        jobs[job_id] = {
            'playlist': playlist,
            'status': 'extracted',
            'progress': 0
        }

        return jsonify({
            'success': True,
            'job_id': job_id,
            'playlist': {
                'name': playlist.name,
                'owner': playlist.owner,
                'total_tracks': len(playlist.tracks),
                'tracks': [
                    {
                        'title': t.title,
                        'artist': t.artist,
                        'album': t.album,
                        'duration_ms': t.duration_ms
                    }
                    for t in playlist.tracks
                ]
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/identify/<job_id>', methods=['POST'])
def identify_tracks(job_id):
    """Identify tracks using MusicBrainz."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    playlist = job['playlist']

    try:
        matcher = SongMatcher()
        results = matcher.batch_identify(playlist.tracks)

        job['status'] = 'identified'
        matched = sum(1 for r in results if r.matched)

        return jsonify({
            'success': True,
            'matched': matched,
            'total': len(results)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<job_id>', methods=['POST'])
def download_tracks(job_id):
    """Download tracks from YouTube."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    playlist = job['playlist']

    try:
        downloader = YouTubeDownloader()

        # Start download in background
        def download_async():
            stats = downloader.batch_download(playlist.tracks)
            job['status'] = 'downloaded'
            job['stats'] = stats

        thread = Thread(target=download_async)
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Download started',
            'total': len(playlist.tracks)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get job status."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    return jsonify({
        'status': job['status'],
        'stats': job.get('stats', {})
    })


@app.route('/api/quick', methods=['POST'])
def quick_convert():
    """Do everything in one shot."""
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        # Extract
        if 'spotify.com' in url or url.startswith('spotify:'):
            extractor = SpotifyExtractor()
            playlist = extractor.extract_playlist(url)
        elif 'youtube.com' in url or 'youtu.be' in url:
            extractor = YouTubeExtractor()
            playlist = extractor.extract_playlist(url)
        elif 'soundcloud.com' in url:
            extractor = SoundCloudExtractor()
            playlist = extractor.extract_playlist(url)
        elif 'bandcamp.com' in url:
            extractor = BandcampExtractor()
            playlist = extractor.extract_album(url)
        else:
            return jsonify({'error': 'Unsupported URL'}), 400

        if not playlist:
            return jsonify({'error': 'Failed to extract playlist'}), 500

        # Identify
        matcher = SongMatcher()
        results = matcher.batch_identify(playlist.tracks)
        matched = sum(1 for r in results if r.matched)

        # Download
        downloader = YouTubeDownloader()
        stats = downloader.batch_download(playlist.tracks)

        return jsonify({
            'success': True,
            'playlist_name': playlist.name,
            'total_tracks': len(playlist.tracks),
            'identified': matched,
            'downloaded': stats['success'],
            'failed': stats['failed']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'spotify_configured': bool(os.getenv('SPOTIFY_CLIENT_ID')),
        'azuracast_configured': bool(os.getenv('AZURACAST_API_KEY'))
    })


if __name__ == '__main__':
    print("=" * 70)
    print("🎵 Playlist Converter Web Interface")
    print("=" * 70)
    print()
    print("Server running at: http://localhost:8002")
    print()
    print("Configured:")
    print(f"  ✓ Spotify: {'Yes' if os.getenv('SPOTIFY_CLIENT_ID') else 'No'}")
    print(f"  ✓ AzuraCast: {'Yes' if os.getenv('AZURACAST_API_KEY') else 'No'}")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    print()

    app.run(host='0.0.0.0', port=8002, debug=True)
