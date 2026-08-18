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
    
    # Initialize the adapter
    # TODO: Configure your CSV data source path here
    data_source = "data/your_data.csv"  # Update this with your actual CSV file path
    
    adapter = SentimentAdapter(
        data_source=data_source,
        # Add any additional configuration parameters here
    )
    
    # Create the knowledge graph
    logger.info("Creating knowledge graph...")
    bc.write_nodes(adapter.get_nodes())
    bc.write_edges(adapter.get_edges())
    
    logger.info("Knowledge graph creation completed successfully!")

    # Create final summary
    bc.summary()


if __name__ == "__main__":
    main()
