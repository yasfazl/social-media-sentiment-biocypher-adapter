# Social Media Sentiment BioCypher Adapter

## Purpose

This project converts `data/sentimentdataset.csv` into a Neo4j-compatible knowledge graph using BioCypher.

## Graph Model

**Nodes**

- `User`
- `SocialMediaPost`
- `Emotion`
- `Hashtag`

**Relationships**

- `User -> POSTED -> SocialMediaPost`
- `SocialMediaPost -> EXPRESSES -> Emotion`
- `SocialMediaPost -> HAS_TAG -> Hashtag`

`SocialMediaPost` nodes retain the original post `text`, `timestamp`, `platform`, `country`, `likes`, `retweets`, and both CSV identifier columns as provenance properties. Country, platform, time components, and engagement values are not modeled as separate nodes. Year, month, day, and hour are derivable from the timestamp and are not duplicated as graph properties.

## Normalization and Duplicates

All string values are trimmed. User and emotion identities use case-normalized values while preserving their human-readable labels as node properties. Hashtags are split into individual values, stripped of `#`, lowercased, and deduplicated within each post; empty hashtags are skipped.

Node IDs are deterministic. Post IDs are hashes of a canonical semantic payload containing the normalized user, timestamp, text, emotion, platform, country, likes, retweets, and sorted normalized hashtags. Exact semantic duplicates collapse, while otherwise matching records with different platforms or countries remain separate. Source CSV identifiers are retained as provenance arrays on collapsed posts.

## Dataset Setup

The `data/` directory is intentionally gitignored. Place the dataset at:

```text
data/sentimentdataset.csv
```

The CSV must include these columns:

```text
Text, Sentiment, Timestamp, User, Platform, Hashtags, Retweets, Likes, Country
```

The dataset's two identifier columns (the leading unnamed column and `Unnamed: 0`) are retained as provenance; they do not define post identity.

## Installation

```bash
python3 -m pip install -e .
```

## Testing

```bash
python3 -m pytest -q
```

## Graph Generation

```bash
python3 create_knowledge_graph.py
```

BioCypher writes Neo4j-compatible CSV files, headers, and `neo4j-admin-import-call.sh` to `output_v3/`. Output directories are intentionally gitignored.

## Project Structure

```text
socialmedia adapter/
├── config/
│   ├── biocypher_config.yaml
│   └── schema_config.yaml
├── data/
│   └── sentimentdataset.csv
├── src/
│   └── sentimentdataset/
│       └── csv/
│           └── adapters/
│               └── sentiment.py
├── tests/
│   └── test_sentiment.py
├── create_knowledge_graph.py
├── pyproject.toml
└── README.md
```

Adapter source: `src/sentimentdataset/csv/adapters/sentiment.py`

## Author

Yasamin Fazeli
