# Spotify OAuth app settings.
# Copy to an ignored local env file and fill in real values on the runtime host.
export SPOTIPY_CLIENT_ID="replace-me"
export SPOTIPY_CLIENT_SECRET="replace-me"
export SPOTIPY_REDIRECT_URI="http://127.0.0.1:8080/callback"
export SPOTIPY_CACHE_PATH="$HOME/.cache-northridge-outside-spotify-token.json"

# Device + playlist.
export SPOTIPY_DEVICE_NAME="Outside Spotify"
export SPOTIPY_PLAYLIST_ID="replace-me"
export SPOTIPY_TARGET_VOLUME=100

# Logging + email.
export SPOTIFY_LOG_FILE="/usr/local/var/log/spotify/spotify.log"
export SPOTIFY_EMAIL_TO="replace-me@example.com"
