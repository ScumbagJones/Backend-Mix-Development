# How to Run on Your Local Machine

Since you're getting "unable to connect" from Firefox, this is because the server is running in a remote/sandboxed environment and your browser can't reach it directly.

## Option 1: Run on Your Local Machine (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/ScumbagJones/Backend-Mix-Development.git
cd Backend-Mix-Development

# 2. Checkout the branch
git checkout claude/discuss-issue-A0rtS

# 3. Install Python dependencies
pip3 install -r requirements.txt

# 4. Your Spotify credentials are already in .env (or add them)
# Make sure .env has:
# SPOTIFY_CLIENT_ID=150572e085cb4fc8a5c9c82303335dcf
# SPOTIFY_CLIENT_SECRET=e85da1a46f5a44a5abf41c004393fa5b

# 5. Start the web server
python3 web_app.py

# 6. Open in your browser
# http://localhost:8002
```

Now you can use your actual Firefox/Chrome browser!

## Option 2: Use the CLI (No Browser Needed)

If you don't want to run the web interface, use the command line:

```bash
# Quick mode - do everything at once
python3 -m src.main quick --url "https://open.spotify.com/playlist/0IKdJHrfWHKvokMMbYYCXw"

# Or step by step:
python3 -m src.main extract --url "YOUR_URL" --output playlist.json
python3 -m src.main identify --input playlist.json --output identified.json
python3 -m src.main download --input identified.json
```

## What You'll Need

- **Python 3.8+** (you have 3.11 ✓)
- **ffmpeg** (for audio conversion)
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - Mac: `brew install ffmpeg`
  - Windows: Download from https://ffmpeg.org/
- **Internet connection** (to actually download from Spotify/YouTube)

## Testing

Try with your playlist:
```bash
python3 -m src.main quick --url "https://open.spotify.com/playlist/0IKdJHrfWHKvokMMbYYCXw"
```

Your MP3s will appear in the `downloads/` folder!

## Troubleshooting

**"Unable to connect" in browser:**
- Make sure you ran `python3 web_app.py` first
- Check it says "Running on http://127.0.0.1:8002"
- Try http://localhost:8002 or http://127.0.0.1:8002

**"Module not found" errors:**
- Run: `pip3 install -r requirements.txt`

**"Spotify API error":**
- Check your .env file has the credentials
- Make sure there are no extra spaces

**"ffmpeg not found":**
- Install ffmpeg (see above)

**Downloads fail:**
- Some YouTube videos might be region-restricted
- Try a different playlist first
- Check your internet connection

## Port Already in Use?

If port 8002 is busy, edit `web_app.py` and change:
```python
app.run(host='0.0.0.0', port=8002, debug=True)
```
To any other port like 8003, 8080, etc.
