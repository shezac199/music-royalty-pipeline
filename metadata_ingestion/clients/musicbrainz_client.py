import requests

class MusicBrainzClient:
    BASE_URL = "https://musicbrainz.org/ws/2"

    def search_artist(self, artist_name: str):
        
        endpoint = f"{self.BASE_URL}/artist"

        params = {
            "query": artist_name,
            "fmt": "json"
        }

        response = requests.get(
            endpoint,
            params=params,
            headers={
                "User-Agent": "music-royalty-pipeline/1.0"
            },
            timeout=30
        )

        response.raise_for_status()

        return response.json()
    
    def get_artist_metadata(self, artist_name: str):

        response = self.search_artist(artist_name)

        artists = response.get("artists", [])

        if not artists:
            raise ValueError(f"No artist found with name: {artist_name}")
        
        artist = artists[0]

        return {
        "artist_id": artist.get("id"),
        "artist_name": artist.get("name"),
        "country": artist.get("country"),
        "artist_type": artist.get("type")
    }
        
    
if __name__ == "__main__":

    client = MusicBrainzClient()

    artist = client.get_artist_metadata(
        "Ed Sheeran"
    )

    print(artist)