import json
from pathlib import Path
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

output_dir = Path("metadata_ingestion/output/raw_metadata")

output_dir.mkdir(
    parents=True,
    exist_ok=True
)

output_file = output_dir / "artists_metadata.json"
with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        artist_metadata,
        file,
        indent=4
    )

print(
    f"Saved {len(artist_metadata)} artists to {output_file}"
)