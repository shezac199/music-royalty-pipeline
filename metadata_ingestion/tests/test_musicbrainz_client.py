from metadata_ingestion.clients.musicbrainz_client import MusicBrainzClient


def test_musicbrainz_flow():

    client = MusicBrainzClient()

    artist = client.get_artist_metadata(
        "Ed Sheeran"
    )

    print("\nArtist:")
    print(artist)

    releases = client.get_releases_for_artist(
        artist["artist_id"],
        limit=3
    )

    if not releases:
        print("No releases found")
        return
    
    print("\nReleases:")
    print(releases)

    tracks = client.get_tracks_for_release(
        releases[0]["release_id"]
    )

    print("\nTracks:")
    for track in tracks[:5]:
        print(f"  {track['title']} | ISRC: {track['isrc']} | Position: {track['track_position']}")

    real = [t for t in tracks if not t['isrc'].startswith('ZZMB')]
    synthetic = [t for t in tracks if t['isrc'].startswith('ZZMB')]
    print(f"\nISRC coverage: {len(real)} real, {len(synthetic)} synthetic out of {len(tracks)} tracks")


if __name__ == "__main__":
    test_musicbrainz_flow()