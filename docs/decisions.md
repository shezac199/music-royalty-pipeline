# Architectural Decision Records

> This document captures the key trade-offs considered while designing this platform. Each decision explains what was chosen, what was rejected, and why.

---

## ADR-001: MusicBrainz + Last.fm over Spotify

**Decision:** Use MusicBrainz and Last.fm as the primary metadata sources instead of the Spotify API.

**Rejected alternative:** Spotify Web API.

**Reasoning:**
In February 2026, Spotify changed its Developer Mode policy to require a Premium subscription for all API access, even for personal and non-commercial projects. This makes it unsuitable for a zero-cost project.

More importantly, MusicBrainz is a better fit for a royalty processing pipeline specifically:
- It provides ISRC codes (International Standard Recording Codes), which are the actual identifiers used in real-world royalty systems by distributors like DistroKid and TuneCore, and by Performing Rights Organisations (PROs)
- It has over 1 million artists and 25 million recordings, requires no authentication, and is completely free
- Last.fm provides real trending track data and play counts, which makes the event generator more realistic than any simulated data Spotify could have provided

The pivot away from Spotify is documented here as an engineering decision, not a workaround. Using ISRC as the royalty key is more production-accurate than using Spotify's proprietary track IDs.

**Trade-off accepted:** MusicBrainz rate-limits to 1 request per second per IP. This required building a rate limiter with exponential backoff into the ingestion layer — which is itself a useful engineering pattern to demonstrate.

---

## ADR-002: Confluent Cloud over Self-Hosted Kafka

**Decision:** Use Confluent Cloud free tier instead of running Kafka on EC2.

**Rejected alternative:** Self-hosted Kafka on a t2.micro EC2 instance.

**Reasoning:**
A t2.micro has 1GB RAM. Kafka alone needs 4–6GB to run stably. Running it on free-tier EC2 would mean spending more time fighting memory issues than learning streaming concepts. Confluent Cloud gives a fully managed Kafka cluster with the same API — topics, partitions, offsets, consumer groups all behave identically. In production, most companies use managed Kafka (Confluent, MSK) anyway, so this is the more realistic choice.

**Trade-off accepted:** Less control over broker configuration. Acceptable for a project at this scale.

---

## ADR-003: Delta Lake over Plain Parquet

**Decision:** Use Delta Lake on S3 for all storage layers.

**Rejected alternative:** Plain Parquet files on S3.

**Reasoning:**
Royalty calculation requires correctness. Plain Parquet has no ACID guarantees — if a batch job fails mid-write, you get partial files with no way to roll back. Delta Lake gives ACID transactions, which means failed jobs don't corrupt the table. It also gives time travel (audit any previous version of a table), schema enforcement (rejects bad records at write time), and upsert support (needed for SCD Type 2 on the artist dimension). For a royalty pipeline where data accuracy directly affects payments, ACID is not optional.

**Trade-off accepted:** Slightly more complex setup than plain Parquet. Worth it for data reliability.

---

## ADR-004: Micro-Batch over True Streaming

**Decision:** Use Spark Structured Streaming in micro-batch mode rather than continuous processing mode.

**Rejected alternative:** Continuous processing (Apache Flink or Spark continuous mode).

**Reasoning:**
Music royalty calculations don't require millisecond latency. A few minutes of lag between a play event and it appearing in the pipeline is completely acceptable. Micro-batch gives exactly-once semantics out of the box, is simpler to reason about, integrates cleanly with Delta Lake, and is much easier to debug. True streaming (Flink) adds significant operational complexity for no real business benefit in this use case.

**Trade-off accepted:** Higher latency than true streaming. Acceptable because royalties are calculated daily, not in real time.

---

## ADR-005: Watermark Threshold of 10 Minutes

**Decision:** Set the watermark for late-arriving events to 10 minutes.

**Rejected alternatives:** 1 minute (too tight), 1 hour (too loose).

**Reasoning:**
The event generator pushes events with `event_time` as close to real time as possible, but network delays, API throttling, and Lambda cold starts can introduce lag. A 1-minute watermark would drop too many legitimate late events. A 1-hour watermark holds too much state in memory, which is expensive. 10 minutes balances completeness (catching most late arrivals) with memory efficiency. Events arriving after the 10-minute window are not dropped — they are picked up by the nightly batch reconciliation job, which is the correctness layer.

**Trade-off accepted:** Events more than 10 minutes late are not reflected in real-time aggregates. Corrected by batch layer.

---

## ADR-006: SCD Type 2 on Artist Dimension Only

**Decision:** Implement SCD Type 2 for the artist dimension table only.

**Rejected alternative:** SCD Type 2 across all dimensions (track, label, territory).

**Reasoning:**
SCD Type 2 tracks historical changes with effective date ranges. Artists do change — they switch labels, change names, merge under different entities. Capturing that history is important for accurate historical royalty attribution. However, implementing SCD Type 2 across every dimension in a personal project would take weeks and risk never finishing. Tracks and territories change rarely and can be handled with simple overwrites. Doing it right for one dimension and explaining the pattern clearly is more valuable than doing it poorly for all.

**Trade-off accepted:** Track and territory dimensions use simple upserts. Historical accuracy on those is acceptable to sacrifice at this scale.

---

## ADR-007: AWS Glue over Self-Managed Spark

**Decision:** Use AWS Glue for both streaming and batch Spark jobs.

**Rejected alternative:** Running Spark on EC2 directly.

**Reasoning:**
AWS Glue is serverless — no cluster to manage, no memory tuning for EC2 instances, no cost when not running. It natively supports Spark and Delta Lake. The free tier gives 1 million DPU seconds per month, which is more than enough for a personal project. Running self-managed Spark on a t2.micro would require constant babysitting. In real companies, managed Spark (Glue, Databricks, EMR Serverless) is standard. Using Glue is both the practical and the production-realistic choice.

**Trade-off accepted:** Less flexibility in Spark configuration. Not a concern at this scale.

---

## ADR-008: Quarantine Pattern over Silent Drops for Bad Data

**Decision:** Write records that fail data quality checks to a `quarantine/` path rather than dropping them.

**Rejected alternative:** Silently filter out bad records in the Silver layer.

**Reasoning:**
In a royalty pipeline, a silently dropped record means an artist doesn't get paid for a play. That's a real business problem. The quarantine pattern ensures every record is accounted for — either it passed validation and moved to Silver, or it failed and sits in quarantine for investigation and potential reprocessing. This also makes debugging much easier: you can always look at quarantine to understand why data didn't make it through, rather than wondering where it went.

**Trade-off accepted:** Slightly more storage used for quarantine data. Completely worth it for auditability.
