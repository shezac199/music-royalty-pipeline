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
    
if __name__ == "__main__":

    client = MusicBrainzClient()

    result = client.search_artist("Ed Sheeran")

    print(result)