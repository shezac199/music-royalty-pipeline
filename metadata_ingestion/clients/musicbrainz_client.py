import time
import requests

class MusicBrainzClient:
    BASE_URL = "https://musicbrainz.org/ws/2"
    HEADERS = {"User-Agent": "music-royalty-pipeline/1.0"}

    def _get(self, endpoint: str, params: dict) -> dict:
        """
        Central request method with rate limiting.
        MusicBrainz enforces 1 request/sec — always sleep after every call.
        """
        response = requests.get(
            f"{self.BASE_URL}/{endpoint}",
            params=params,
            headers=self.HEADERS,
            timeout=30
        )
        response.raise_for_status()
        time.sleep(1) 
        return response.json()

    def search_artist(self, artist_name: str) -> dict:
        return self._get("artist", {"query": artist_name, "fmt": "json"})

    def get_artist_metadata(self, artist_name: str) -> dict:
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

    def get_releases_for_artist(self, artist_mbid: str, limit: int = 5) -> list:
        """
        Fetch releases (albums/singles) for a given artist MBID.
        Returns a list of release MBIDs and titles.

        We limit to 5 by default — enough to get a good track catalogue
        without burning through the rate limit in one run.
        """
        data = self._get(
            "release",
            {
                "artist": artist_mbid,
                "fmt": "json",
                "limit": limit
            }
        )

        releases = data.get("releases", [])

        return [
            {
                "release_id": r.get("id"),
                "release_title": r.get("title"),
                "release_date": r.get("date"),
                "country": r.get("country")
            }
            for r in releases
        ]

    def get_tracks_for_release(self, release_mbid: str) -> list:
        """
        Fetch all tracks and their ISRC codes for a given release MBID.
        Uses inc=recordings+isrcs to get both in a single API call.

        Returns a flat list of track dicts, each containing the ISRC.
        Not all tracks have ISRCs — we skip those cleanly.
        """
        data = self._get(
            f"release/{release_mbid}",
            {
                "inc": "recordings+isrcs",
                "fmt": "json"
            }
        )

        tracks = []
        release_title = data.get("title")
        release_date = data.get("date")

        for medium in data.get("media", []):
            for track in medium.get("tracks", []):
                recording = track.get("recording", {})
                isrcs = recording.get("isrcs", [])

                # skip tracks with no ISRC — not useful for royalty calc
                if not isrcs:
                    continue

                tracks.append({
                    "track_id": recording.get("id"),
                    "title": recording.get("title") or track.get("title"),
                    "duration_ms": recording.get("length"),
                    "isrc": isrcs[0],  # take primary ISRC
                    "release_id": release_mbid,
                    "release_title": release_title,
                    "release_date": release_date,
                    "track_position": track.get("position")
                })

        return tracks


if __name__ == "__main__":
    client = MusicBrainzClient()

    # get artist
    artist = client.get_artist_metadata("Ed Sheeran")
    print("Artist:", artist)

    # get releases for that artist
    releases = client.get_releases_for_artist(artist["artist_id"], limit=3)
    print(f"\nFound {len(releases)} releases")

    # get tracks + ISRCs for the first release
    if releases:
        first_release = releases[0]
        print(f"\nFetching tracks for: {first_release['release_title']}")
        tracks = client.get_tracks_for_release(first_release["release_id"])
        for t in tracks:
            print(f"  {t['title']} | ISRC: {t['isrc']}")
