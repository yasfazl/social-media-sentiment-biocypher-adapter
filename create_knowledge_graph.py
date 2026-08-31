#!/usr/bin/env python3
"""
socialmedia adapter - creating an adapter

This script creates a knowledge graph using BioCypher and the SentimentAdapter.
"""

import logging
from pathlib import Path

from biocypher import BioCypher
from sentimentdataset.csv.adapters.sentiment import SentimentAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to create the knowledge graph."""
    logger.info("Starting socialmedia adapter knowledge graph creation")
    
    # Initialize BioCypher
    bc = BioCypher(
        biocypher_config_path="config/biocypher_config.yaml",
        schema_config_path="config/schema_config.yaml"
    )
    
    adapter = SentimentAdapter(data_source="data/sentimentdataset.csv")
    
    # Create the knowledge graph
    logger.info("Creating knowledge graph...")
    bc.write_nodes(adapter.get_nodes())
    bc.write_edges(adapter.get_edges())
    import_script = bc.write_import_call()
    
    logger.info("Knowledge graph creation completed successfully: %s", import_script)

    # Create final summary
    bc.summary()


if __name__ == "__main__":
    main()
