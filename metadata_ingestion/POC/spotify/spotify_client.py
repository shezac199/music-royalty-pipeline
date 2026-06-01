import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config import (
    AWS_REGION,
    SPOTIFY_SECRET_NAME
)
from secrets_manager import get_secret


def get_spotify_credentials():
    """
    Retrieve Spotify credentials from AWS Secrets Manager.
    """

    return json.loads(
        get_secret(
            secret_name=SPOTIFY_SECRET_NAME,
            region_name=AWS_REGION
        )
    )

def get_spotify_client():
    credentials = get_spotify_credentials()

    auth_manager = SpotifyClientCredentials(
        client_id=credentials["SPOTIFY_CLIENT_ID"],
        client_secret=credentials["SPOTIFY_CLIENT_SECRET"]
    )

    return spotipy.Spotify(auth_manager=auth_manager)


if __name__ == "__main__":

    spotify = get_spotify_client()

    result = spotify.search(
        q="Shape of You",
        type="track",
        limit=1
    )

    print(
        f"Successfully authenticated with Spotify. "
        f"Found track: {result['tracks']['items'][0]['name']}"
    )