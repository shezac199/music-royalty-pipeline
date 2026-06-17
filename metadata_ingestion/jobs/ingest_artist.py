import json
from pathlib import Path
import time
import logging
import pandas as pd

from metadata_ingestion.clients.musicbrainz_client import MusicBrainzClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "artist_metadata.json"

artists_df = pd.read_csv(
    "metadata_ingestion/input/artist_seed.csv"
)

def run():
    client = MusicBrainzClient()

    artist_metadata = []
    failed = []
    total_artists = len(artists_df)

    for i, artist_name in enumerate(artists_df["artist_name"], start = 1):
        log.info(f"[{i}/{total_artists}] Fetching metadata for: {artist_name}")

        try:
            metadata = client.get_artist_metadata(artist_name)
            artist_metadata.append(metadata)
            log.info(f"  Done: {metadata['artist_name']} | {metadata['country']} | genres: {metadata['genres'][:3]}")
        
        except Exception as e:
            log.warning(f"  Failed for {artist_name}: {e}")
            failed.append(artist_name)
            continue
            
        time.sleep(2) 

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(artist_metadata, f, indent=4, ensure_ascii=False)

if __name__ == '__main__':
    run()