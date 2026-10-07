# Social Media Sentiment BioCypher Adapter

This adapter converts the **Social Media Sentiments Analysis Dataset** from a
CSV table into a knowledge graph using [BioCypher](https://biocypher.org/). It
produces Neo4j-compatible node and relationship files that connect users,
posts, emotion labels, and hashtags.

## When should I use this adapter?

Use this adapter if you want to explore the dataset as a graph rather than as
a table. For example, the resulting graph can answer questions such as:

- Which hashtags occur in posts with a particular emotion label?
- Which posts are associated with a particular user?
- How do likes and retweets differ across platforms or emotion labels?

The adapter uses the emotion labels already provided by the dataset.

## Source dataset

This project uses the **Social Media Sentiments Analysis Dataset**, published
by **Kashish Parmar** on Kaggle.

- [Original dataset and description](https://www.kaggle.com/datasets/kashishparmar02/social-media-sentiments-analysis-dataset)
- Dataset file: `data/sentimentdataset.csv`
- Dataset license: [CC0 1.0 Public Domain](https://creativecommons.org/publicdomain/zero/1.0/)

A copy of the CSV file is included in this repository, as permitted by its
CC0 license.

### Dataset reference

Parmar, Kashish. *Social Media Sentiments Analysis Dataset*. Kaggle.  
https://www.kaggle.com/datasets/kashishparmar02/social-media-sentiments-analysis-dataset

When reporting results, record the dataset version or access date used in the
analysis.

## Graph model

### Nodes

| Node | Meaning |
| --- | --- |
| `User` | A normalized username from the dataset |
| `SocialMediaPost` | A distinct post after duplicate handling |
| `Emotion` | A normalized value from the `Sentiment` column |
| `Hashtag` | An individual normalized hashtag |

### Relationships

| Source | Relationship | Target |
| --- | --- | --- |
| `User` | `Posted` | `SocialMediaPost` |
| `SocialMediaPost` | `Expresses` | `Emotion` |
| `SocialMediaPost` | `HasTag` | `Hashtag` |

Relationship names are case-sensitive in Neo4j.

`SocialMediaPost` nodes retain the original `text`, `timestamp`, `platform`,
`country`, `likes`, and `retweets` values. The source identifiers are retained
as the provenance properties `source_row_ids` and `source_legacy_indices`.

Country and platform are stored as post properties rather than separate
nodes. Year, month, day, and hour are not duplicated as graph properties
because they can be derived from the timestamp.

## Input data

The included CSV is located at:

```text
data/sentimentdataset.csv
```

The adapter expects these columns:

| Column | Used for |
| --- | --- |
| `Text` | Post text |
| `Sentiment` | Emotion label |
| `Timestamp` | Post timestamp |
| `User` | User identity |
| `Platform` | Platform property |
| `Hashtags` | Hashtag nodes and relationships |
| `Retweets` | Retweet count |
| `Likes` | Like count |
| `Country` | Country property |

The original identifier columns, including the leading unnamed column and
`Unnamed: 0`, are retained as provenance. They do not determine post identity.

## Normalization and duplicate handling

The adapter trims surrounding whitespace from string values. User and emotion
identities use case-normalized values while retaining readable names as node
properties.

Hashtags are split into individual values, stripped of their leading `#`,
converted to lowercase, and deduplicated within each post. Empty hashtags are
skipped.

Post IDs are deterministic hashes of a normalized payload containing the user,
timestamp, text, emotion, platform, country, likes, retweets, and sorted
hashtags. Rows with identical payloads are combined into one post, while their
source identifiers are preserved in provenance arrays. A difference in any of
these fields produces a separate post node.

## Quick start with Python

### Requirements

- Python 3.11 or newer
- Git
- An internet connection on the first run if the configured Biolink ontology
  is not already cached

### 1. Clone and install

```bash
git clone https://github.com/yasfazl/social-media-sentiment-biocypher-adapter.git
cd social-media-sentiment-biocypher-adapter

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
```

On Windows, activate the environment with `.venv\\Scripts\\activate` instead
of the `source` command.

### 2. Generate the graph files

Run the pipeline from the repository root:

```bash
python create_knowledge_graph.py
```

BioCypher writes the following files to `output_v3/`:

- node CSV files and their headers;
- relationship CSV files and their headers; and
- `neo4j-admin-import-call.sh`, which contains the Neo4j bulk-import command.

This step generates import files. It does not start Neo4j or load the files
into a running database.

## Run the complete workflow with Docker

Docker Compose can build the adapter, generate the graph files, import them,
and start Neo4j. On macOS or Windows, start Docker Desktop first.

From the repository root, run:

```bash
docker compose up --build -d
```

Check the service status and logs with:

```bash
docker compose ps
docker compose logs
```

After Neo4j starts, open [http://localhost:7474](http://localhost:7474) and
connect using:

```text
Username: neo4j
Password: password
```

Stop the containers without deleting the imported graph:

```bash
docker compose down
```

To remove the containers **and permanently delete the Docker volume containing
the imported graph**, run:

```bash
docker compose down -v
```

## Import into an existing Neo4j installation

If you generated the files with Python and want to use an existing Neo4j
installation:

1. Stop the target Neo4j instance.
2. Inspect `output_v3/neo4j-admin-import-call.sh`.
3. Make sure the paths in the script point to the generated CSV files.
4. Run the script from the Neo4j installation directory, where
   `bin/neo4j-admin` is available.
5. Start Neo4j and connect to the imported database.

> **Warning:** The generated import command can contain
> `--overwrite-destination=true`. Use a new or disposable target database,
> because an existing database with the same name may be replaced.

Neo4j must be stopped during a full import. Use a Java version supported by
your Neo4j installation. See the
[Neo4j import documentation](https://neo4j.com/docs/operations-manual/current/import/)
for installation-specific requirements.

## Explore the graph

After importing the data, run these examples in the Neo4j Query interface.

Display users and their posts:

```cypher
MATCH (u:User)-[r:Posted]->(p:SocialMediaPost)
RETURN u, r, p
LIMIT 25;
```

Display posts and their emotion labels:

```cypher
MATCH (p:SocialMediaPost)-[r:Expresses]->(e:Emotion)
RETURN p, r, e
LIMIT 25;
```

Display the relationship types and their counts:

```cypher
MATCH ()-[r]->()
RETURN type(r) AS relationship, count(*) AS count
ORDER BY count DESC;
```

Find the most frequently used hashtags:

```cypher
MATCH (:SocialMediaPost)-[:HasTag]->(h:Hashtag)
RETURN h.name AS hashtag, count(*) AS posts
ORDER BY posts DESC
LIMIT 10;
```

## Tests

With the Python environment activated, run:

```bash
python -m pytest -sv
```

The included dataset allows the full integration test to run. A successful
test run should contain no failed tests; also check the output for unexpected
skipped tests.

## Configuration

- `config/schema_config.yaml` defines node types, relationships, and property
  mappings.
- `config/biocypher_config.yaml` defines the ontology, output format, logging,
  and output directory.
- `create_knowledge_graph.py` is the graph-generation entry point.
- `croissant.jsonld` contains machine-readable metadata for the adapter and
  source dataset.

## Project structure

```text
social-media-sentiment-biocypher-adapter/
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
├── croissant.jsonld
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Limitations

- The adapter is designed for this dataset's CSV structure. Other datasets may
  require changes to the column mappings and parsing logic.
- Emotion labels are copied from the source dataset and are not independently
  validated by the adapter.
- User identity is based on normalized usernames. Identical usernames across
  platforms may therefore be combined and do not establish a verified
  real-world identity.
- Duplicate handling uses post content and metadata rather than an original
  platform post ID. Different engagement values can therefore produce separate
  post nodes.
- The source dataset should be assessed for suitability and representativeness
  before drawing conclusions about real social-media activity.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| CSV not found | Confirm that `data/sentimentdataset.csv` exists and run the command from the repository root. |
| Python cannot import the adapter | Activate the virtual environment and run `python -m pip install -e .`. |
| Docker cannot copy `README.md` | Ensure that `.dockerignore` does not exclude `README.md`. |
| Import cannot find `/app/output_v3/` | Match the Docker volume path or update the generated script for the host installation. |
| Unsupported Java version | Install the Java version supported by the selected Neo4j release. |
| Port 7474 or 7687 is occupied | Stop the other Neo4j instance or change the published Docker ports. |

## License

The adapter code is distributed under the [MIT License](LICENSE).

The included dataset is distributed under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) according to its
Kaggle listing. The dataset reference above identifies its original creator and
source.

## Author

Yasamin Fazeli

For questions or problems, please
[open an issue](https://github.com/yasfazl/social-media-sentiment-biocypher-adapter/issues).
