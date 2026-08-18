# socialmedia adapter

creating an adapter

## Overview

This BioCypher pipeline processes file data using the sentiment to create a knowledge graph.

## Features

- **Data Source**: file data processing
- **Adapter**: sentiment
- **Output**: Neo4j knowledge graph
- **Docker Support**: Containerized deployment
- **Testing**: Comprehensive test suite

## Installation

### Prerequisites

- Python 3.11 or higher
- Neo4j database (local or remote)

### Setup

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd socialmedia adapter
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

   Or using uv:
   ```bash
   uv sync
   ```

3. Configure your data source in `create_knowledge_graph.py`

4. Update the schema configuration in `config/schema_config.yaml` if needed

## Usage

### Basic Usage

Run the pipeline to create the knowledge graph:

```bash
python create_knowledge_graph.py
```

### Configuration

The pipeline uses two main configuration files:

- `config/biocypher_config.yaml` - BioCypher settings
- `config/schema_config.yaml` - Schema mapping configuration
### Docker Usage

Build and run with Docker:

```bash
docker-compose up -d
```

This will:
1. Build the BioCypher pipeline
2. Import the data into Neo4j
3. Start the Neo4j instance

Access Neo4j at: http://localhost:7474
## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=sentimentdataset.csv --cov-report=html
```

## Project Structure

```
socialmedia adapter/
├── config/
│   ├── biocypher_config.yaml
│   └── schema_config.yaml
├── src/sentimentdataset.csv/
│   └── adapters/
│       └── sentiment.py
├── create_knowledge_graph.py
├── docker-compose.yml
├── Dockerfile
├── tests/
│   └── test_sentiment.py
├── pyproject.toml
└── README.md
```

## Development

### Code Style

This project uses:
- **Black** for code formatting
- **isort** for import sorting
- **mypy** for type checking

Format code:
```bash
black .
isort .
```

Type checking:
```bash
mypy src/
```

## License

MIT

## Author

BioCypher User - user@example.com
