import json
import time
import logging
from pathlib import Path
from metadata_ingestion.clients.musicbrainz_client import MusicBrainzClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"
ARTIST_METADATA_PATH = OUTPUT_DIR / "artist_metadata.json"
TRACK_METADATA_PATH = OUTPUT_DIR / "track_metadata.json"
ISRC_MAPPING_PATH = OUTPUT_DIR / "isrc_mapping.json"

RELEASES_PER_ARTIST = 5


