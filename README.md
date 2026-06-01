# Royalty Processing & Music Analytics Platform

> A cloud-native hybrid batch + streaming pipeline that calculates music royalties accurately across millions of streaming events from YouTube and Last.fm — combining real-time event processing with batch reconciliation to ensure distributors and artists get paid correctly.

---

## The Business Problem

Music distributors need to calculate royalties accurately across millions of streaming events from multiple platforms and territories. A single late-arriving event, duplicate play, or bad record can mean incorrect payments to artists and labels.

This platform solves that by:
- Ingesting real track and artist metadata from MusicBrainz, Last.fm, and YouTube APIs
- Simulating high-volume play events at scale against real track catalogues and ISRC codes
- Processing events in real time with deduplication and late-data handling
- Reconciling via batch jobs to correct any streaming-layer errors
- Producing royalty payout tables at the Gold layer, broken down by platform and territory

> **Core principle: Streaming provides freshness. Batch provides correctness.**

---

## Architecture Overview

![Architecture Diagram](docs/High-Level-Architecture.png)

---

## Architecture Zones

### 1. Source Systems

| Source | Type | What We Fetch | Auth Required |
|---|---|---|---|
| MusicBrainz API | Batch | Track metadata, ISRC codes, label, release territories | None |
| Last.fm API | Batch | Trending tracks, play counts, artist tags | Free API key |
| YouTube Data API | Batch | Video metadata, view counts, channel info | Free API key |

**Why this stack over Spotify:**
Spotify's API now requires a Premium subscription even for personal projects (Feb 2026 policy change). MusicBrainz is a better fit anyway — it provides ISRC codes, which are the actual industry-standard identifiers used in real royalty systems. Last.fm provides real trend and popularity data to seed the event generator meaningfully.

The event generator pulls real track IDs and ISRC codes from MusicBrainz and trending tracks from Last.fm before simulating play events — so Kafka processes real catalogue data, not made-up IDs.

---

### 2. Streaming Event Generation

Python-based event producer that:
1. Fetches real trending tracks from Last.fm API
2. Enriches those tracks with ISRC codes and territory data from MusicBrainz
3. Simulates play/view events against those real tracks at scale
4. Pushes events continuously into Kafka

Example event:

```json
{
  "event_id": "uuid",
  "track_id": "5Z01UMMf7V1o0MzF86s6WJ",
  "isrc": "GBAHS1600463",
  "track_name": "Blinding Lights",
  "artist": "The Weeknd",
  "label": "Republic Records",
  "platform": "YOUTUBE",
  "territory": "US",
  "event_time": "2026-05-21T10:00:00Z"
}
```

> Events are simulated at scale — this mirrors how a proper load-test environment works in production. The catalogue data (track IDs, ISRC codes, territories, labels) is real.

---

### 3. Streaming Layer — Confluent Cloud Kafka

**Topic:** `track_usage_events`

Responsibilities:
- Buffer streaming events
- Decouple producers and consumers
- Enable scalable, fault-tolerant ingestion

Concepts demonstrated:
- Event-driven architecture
- Partitioning strategy
- Offset management
- Scalable consumers

---

### 4. Real-Time Processing — Spark Structured Streaming (AWS Glue)

Consumes from Kafka and writes to Bronze Delta layer.

Responsibilities:
- Parse and validate JSON schemas
- Deduplicate records
- Apply event-time processing
- Handle late-arriving events using **watermarks**
- Write raw events into Bronze layer with exactly-once semantics

Demonstrates:
- Micro-batch streaming
- Exactly-once semantics
- Checkpointing and fault tolerance
- Watermark threshold decisions (see `docs/decisions.md`)

---

### 5. Lakehouse Storage — AWS S3 + Delta Lake

```
s3://music-analytics/
├── bronze/
│   ├── streaming_events/
│   └── metadata/
├── silver/
│   ├── validated_events/
│   └── enriched_tracks/
└── gold/
    ├── royalty_payouts/
    ├── daily_usage_aggregates/
    └── platform_territory_metrics/
```

#### Bronze Layer
- Immutable raw storage
- Raw streaming events + API metadata
- Replayable and auditable

#### Silver Layer
- Schema standardisation
- Metadata enrichment (join events with track/artist/ISRC data)
- Deduplication
- **Data quality validation** (see below)

#### Gold Layer
- Daily usage aggregates
- Platform and territory metrics
- **Royalty payout tables** — the primary business output

---

### 6. Data Quality Layer (Bronze → Silver)

Explicit validation step before any data reaches Silver:

| Check | Rule |
|---|---|
| Null check | `track_id`, `isrc`, `event_id`, `event_time` must not be null |
| Duplicate detection | Deduplicate on `event_id` within watermark window |
| Timestamp validation | `event_time` must not be in the future |
| Territory validation | `territory` must be a valid ISO country code |
| Platform validation | `platform` must be one of: YOUTUBE, LASTFM |
| ISRC format check | Must match standard format: `[A-Z]{2}[A-Z0-9]{3}[0-9]{7}` |

Records that fail validation are written to a `quarantine/` path for investigation — not silently dropped.

---

### 7. Batch Processing — Spark Batch Jobs (AWS Glue)

Runs after the streaming layer to ensure correctness.

Responsibilities:
- Incremental processing of Silver → Gold
- Royalty calculations
- Historical reconciliation (catches events that arrived after streaming window closed)
- Late-event corrections
- SCD Type 2 on artist dimension (tracks label/name changes over time)

---

### 8. Royalty Calculation Logic

**Formula:**

```
royalty = plays × rate_per_stream × territory_multiplier × platform_weight
```

**Rate reference (approximated from public data):**

| Platform | Base Rate (USD/stream) |
|---|---|
| YouTube | $0.001 |
| Last.fm equivalent | $0.003 |

**Territory multipliers:**

| Territory | Multiplier |
|---|---|
| US | 1.0 |
| UK | 0.9 |
| EU | 0.8 |
| IN | 0.3 |

**Output:** Gold layer `royalty_payouts` table, partitioned by `isrc`, `artist_id`, `platform`, `territory`, `reporting_month`.

> Using ISRC as the primary royalty identifier mirrors real-world royalty systems used by distributors like DistroKid, TuneCore, and PROs (Performing Rights Organisations).

---

### 9. Analytics & Reporting Layer

Gold layer outputs consumed downstream:

- Monthly royalty statements per artist, keyed by ISRC
- Platform comparison metrics (YouTube vs Last.fm)
- Territory-level payout reports
- Daily usage trend tables

---

## Core Technologies

| Technology | Purpose |
|---|---|
| AWS S3 | Lakehouse storage |
| Confluent Cloud Kafka | Streaming ingestion (free tier) |
| Spark Structured Streaming | Real-time processing via AWS Glue |
| Delta Lake | ACID lakehouse on S3 |
| Spark Batch | Batch transforms and royalty calc via AWS Glue |
| Python | Event generation and API ingestion |
| MusicBrainz | Free track metadata and ISRC codes (no auth needed) |
| Last.fm | Free trending track and play count data |
| YouTube Data API | Free video and channel metadata |
| AWS Lambda | Scheduled API polling trigger (free tier) |

---

## How to Run

### Prerequisites
- Python 3.9+
- AWS account (free tier)
- Confluent Cloud account (free tier)
- Last.fm Developer account (free API key)
- YouTube Data API key (free)
- MusicBrainz requires no account or key

### Setup

```bash
git clone https://github.com/shezac199/music-analytics-platform
cd music-analytics-platform
pip install -r requirements.txt
cp .env.example .env
# Fill in your Last.fm and YouTube API keys, and Kafka bootstrap server in .env
```

### Run the event producer

```bash
python producer/event_generator.py
```

### Run the streaming job locally

```bash
python streaming_jobs/streaming_processor.py
```

### Run batch jobs

```bash
python batch_jobs/royalty_calculator.py
```

---

## Concepts Demonstrated

- Hybrid batch + streaming (lambda architecture)
- Event-driven design
- Lakehouse architecture (Bronze / Silver / Gold)
- Incremental processing
- SCD Type 2 on artist dimension
- Event-time processing with watermarks
- Exactly-once semantics
- Batch reconciliation for correctness
- Data quality validation with quarantine pattern
- ISRC-based royalty calculation with territory and platform weighting
- Rate limiting and API backoff strategies (MusicBrainz 1 req/sec constraint)
- Cloud-native storage on AWS free tier

---

## Architectural Decisions

See [`docs/decisions.md`](docs/decisions.md) for documented trade-offs including:
- Why MusicBrainz + Last.fm over Spotify
- Why Confluent Cloud over self-hosted Kafka
- Why Delta Lake over plain Parquet
- Why micro-batch over true streaming
- Watermark threshold rationale

---

## Project Structure

```
music-analytics-platform/
├── producer/               # Event generator (Last.fm + MusicBrainz seeded)
├── metadata_ingestion/     # MusicBrainz, Last.fm, YouTube ingestion
├── streaming_jobs/         # Spark Structured Streaming on Glue
├── batch_jobs/             # Spark batch + royalty calculation
├── datasets/               # Sample data and schemas
├── infrastructure/         # AWS setup scripts
├── tests/                  # Unit and integration tests
├── docs/
│   ├── architecture.png    # Architecture diagram
│   └── decisions.md        # Architectural decision records
├── .env.example
├── requirements.txt
└── README.md
```