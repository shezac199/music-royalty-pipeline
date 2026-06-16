# Data Model

## artist_dim

| Column      | Description                   |
| ----------- | ----------------------------- |
| artist_id   | MusicBrainz artist identifier |
| artist_name | Artist name                   |
| country     | Artist country                |
| artist_type | Person / Group                |

---

## track_dim

| Column       | Description                           |
| ------------ | ------------------------------------- |
| track_id     | MusicBrainz recording identifier      |
| track_name   | Track name                            |
| artist_id    | Associated artist                     |
| artist_name  | Artist name                           |
| isrc         | International Standard Recording Code |
| release_date | Track release date                    |

---

## platform_dim

| Column          | Description             |
| --------------- | ----------------------- |
| platform_id     | Platform identifier     |
| platform_name   | Spotify / YouTube       |
| rate_per_stream | Royalty rate per stream |

---

## territory_dim

| Column               | Description          |
| -------------------- | -------------------- |
| territory_id         | Territory identifier |
| country_code         | ISO country code     |
| country_name         | Country name         |
| territory_multiplier | Royalty multiplier   |

---

## stream_fact

| Column           | Description                  |
| ---------------- | ---------------------------- |
| event_id         | Stream event identifier      |
| track_id         | Track played                 |
| artist_id        | Artist associated with track |
| platform_id      | Streaming platform           |
| territory_id     | Listener territory           |
| stream_timestamp | Event timestamp              |
| play_count       | Number of plays              |

---

## royalty_fact

| Column           | Description               |
| ---------------- | ------------------------- |
| track_id         | Track identifier          |
| artist_id        | Artist identifier         |
| platform_id      | Platform identifier       |
| territory_id     | Territory identifier      |
| calculation_date | Royalty calculation date  |
| royalty_amount   | Calculated royalty amount |