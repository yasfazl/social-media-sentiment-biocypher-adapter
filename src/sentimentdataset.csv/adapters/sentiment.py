"""
Sentiment Adapter

This adapter handles CSV data source for BioCypher.
"""

import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


class SentimentAdapter:
    """
    Adapter for CSV data source.
    
    This adapter implements the BioCypher adapter interface for CSV data.
    """
    
    def __init__(self, data_source: str | Path, **kwargs):
        """
        Initialize the adapter.
        
        Args:
            data_source: Path to the CSV data source
            **kwargs: Additional configuration parameters
        """
        self.data_source = data_source
        self.config = kwargs
        logger.info(f"Initialized SentimentAdapter with data source: {data_source}")
        
    def get_nodes(self):
        """
        Extract nodes from the data source.
        
        Yields:
            Tuples of (node_id, node_label, properties_dict) for each node
        """
        logger.info("Extracting nodes from data source")
        
        # Dummy protein nodes matching schema
        protein_nodes = [
            ("P12345", "protein", {
                "name": "Insulin",
                "description": "Hormone that regulates glucose metabolism",
                "organism": "Homo sapiens",
                "sequence": "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAEDLQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN"
            }),
            ("P01308", "protein", {
                "name": "Insulin-like growth factor I",
                "description": "Growth factor involved in cell growth and differentiation",
                "organism": "Homo sapiens",
                "sequence": "MGFPLRPVAVYFLHRGQHSRGEASLLCLKDQELVCGDREVFPLPPEVGQKVEVTTDINGQYKRVPQCSQCHSVECSVCQDLWELVDTQYCT"
            }),
        ]
        
        # Dummy gene nodes matching schema
        gene_nodes = [
            ("ENSG00000129965", "gene", {
                "name": "INS",
                "symbol": "INS",
                "description": "Insulin gene",
                "chromosome": "11",
                "start_position": 2157796,
                "end_position": 2160023
            }),
            ("ENSG00000117411", "gene", {
                "name": "IGF1",
                "symbol": "IGF1",
                "description": "Insulin-like growth factor 1 gene",
                "chromosome": "12",
                "start_position": 102395880,
                "end_position": 102481116
            }),
        ]
        
        for node in protein_nodes + gene_nodes:
            yield node
        
        logger.info(f"Extracted {len(protein_nodes) + len(gene_nodes)} nodes")
    
    def get_edges(self):
        """
        Extract edges from the data source.
        
        Yields:
            Tuples of (source_id, target_id, edge_label, edge_type, properties_dict) for each edge
        """
        logger.info("Extracting edges from data source")
        
        # Dummy edges matching schema (protein_encoded_by_gene with input_label "encoded_by")
        edges = [
            ("P12345", "ENSG00000129965", "encoded_by", "encoded_by", {
                "confidence": 0.95,
                "evidence": "experimental"
            }),
            ("P01308", "ENSG00000117411", "encoded_by", "encoded_by", {
                "confidence": 0.98,
                "evidence": "experimental"
            }),
        ]
        
        for edge in edges:
            yield edge
    
    def get_metadata(self) -> dict[str, any]:
        """
        Get metadata about the data source.
        
        Returns:
            Dictionary containing metadata
        """
        return {
            'name': 'SentimentAdapter',
            'data_source': str(self.data_source),
            'data_type': 'csv',
            'version': '0.1.0',
            'adapter_class': 'SentimentAdapter'
        }
    
    def validate_data_source(self) -> bool:
        """
        Validate that the CSV data source is accessible and properly formatted.
        
        Returns:
            True if data source is valid, False otherwise
        """
        try:
            data_path = Path(self.data_source)
            if not data_path.exists() or not data_path.is_file():
                return False
            
            # Try to read the CSV to validate format
            df = pd.read_csv(data_path, nrows=1)  # Read just first row
            return len(df.columns) > 0
            
        except Exception as e:
            logger.error(f"Data source validation failed: {e}")
            return False
