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
        time.sleep(2) 
        return response.json()

    def search_artist(self, artist_name: str) -> dict:
        return self._get("artist", {"query": artist_name, "fmt": "json"})

    def get_artist_metadata(self, artist_name: str) -> dict:
        response = self.search_artist(artist_name)
        artists = response.get("artists", [])

        if not artists:
            raise ValueError(f"No artist found with name: {artist_name}")
        
        mbid = artists[0].get("id")

        data = self._get(
            f"artist/{mbid}",
            {
                "inc": "aliases+genres+tags+ratings+url-rels",
                "fmt": "json"
            }
        )

        genres = [g.get("name") for g in data.get("genres", [])]
        tags = [t.get("name") for t in data.get("tags", [])]
        rating_data = data.get("rating", {})
        lifespan = data.get("life-span", {})
        area = data.get("area", {}).get("name")

        return {
            "artist_id": data.get("id"),
            "artist_name": data.get("name"),
            "sort_name": data.get("sort-name"),
            "country": data.get("country"),
            "area": area,
            "artist_type": data.get("type"),
            "gender": data.get("gender"),
            "disambiguation": data.get("disambiguation"),
            "begin_date": lifespan.get("begin"),
            "end_date": lifespan.get("end"),
            "active": not lifespan.get("ended", False),
            "genres": genres,
            "tags": tags,
            "rating": rating_data.get("value"),
            "rating_count": rating_data.get("votes-count")
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
                "limit": limit,
                "status": "official",
                "type": "album|single"
            }
        )

        releases = data.get("releases", [])

        releases = sorted(releases, key=lambda x: x.get("date") or "0", reverse=True)

        return [
            {
                "release_id": r.get("id"),
                "release_title": r.get("title"),
                "release_date": r.get("date"),
                "country": r.get("country")
            }
            for r in releases[:limit]
        ]

    def get_tracks_for_release(self, release_mbid: str) -> list:
        """
        Fetch all tracks and their ISRC codes for a given release MBID.
        Uses inc=recordings+isrcs to get both in a single API call.

        Returns a flat list of track dicts, each containing the ISRC.
        Some tracks may not have ISRC codes available.
        In those cases the ISRC field is generated as a synthetic value.
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
                #if not isrcs:
                    #continue

                tracks.append({
                    "track_id": recording.get("id"),
                    "title": recording.get("title") or track.get("title"),
                    "duration_ms": recording.get("length"),
                    "isrc": isrcs[0] if isrcs else f"ZZMB-{recording.get('id', '')[:10].upper()}",  #synthetic ISRCs
                    "release_id": release_mbid,
                    "release_title": release_title,
                    "release_date": release_date,
                    "track_position": track.get("position")
                })
        print(f"Found {len(tracks)} tracks for release: {release_title}")

        return tracks