import time


from metadata_ingestion.clients.musicbrainz_client import MusicBrainzClient

artists = [
    "Ed Sheeran",
    "Taylor Swift",
    "Coldplay",
    "Adele",
    "Drake"
]

client = MusicBrainzClient()

artist_metadata = []

for artist in artists:
    metadata = client.get_artist_metadata(artist)
    artist_metadata.append(metadata)
    print(f"Fetched metadata for: {artist}")
    time.sleep(1)  # Wait 1 second between requests to avoid rate limiting

print(artist_metadata)