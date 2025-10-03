"""
manager.py
==========
Main entry point for the WqSat_get package, which manages the downloading of Sentinel-2 and Sentinel-3 data from the Copernicus Open Access Hub.

Supports:
- Loading configuration from a YAML file.
- Initialization directly from a dictionary (useful in notebooks).
- Execution from the command line interface (CLI).
"""

import sys
import yaml
import argparse
import logging
from pathlib import Path

# Subfunctions
from .logging_config import setup_logging
from .sentinel_get import SentinelGet
from . import utils

logger = logging.getLogger(__name__)


class GetManager:
    """
    Orchestator class to search and download Sentinel-2 and Sentinel-3 data 
    using a user-defined configuration.
    """
    
    def __init__(self, config: dict = None, config_file: str = None):
        """
        Initialize the manager with a validated configuration dictionary.
        """
        setup_logging()  # Initialize logging once at the start
        logger.info("Initialized WqSat_Get Module.")

        if config:
            self.config = config
        elif config_file:
            self.config = self.from_yaml(config_file)
        else:
            logger.error("'config' or 'config_file' must be provided to initialize WqSat_Get.")
            raise ValueError("'config' or 'config_file' must be provided to initialize WqSat_Get.")

        # Validate critical parameters at initialization
        utils.validate_inputs(self.config)
        logger.info(f"Configuration successfully initialized ...")



    def from_yaml(self, yaml_file: str) -> dict:
        """
        Load configuration from a YAML file and return a manager instance.
        """

        yaml_file = Path(yaml_file)
        if not yaml_file.is_file():
            logger.error(f"Configuration file '{yaml_file}' not found.")
            raise FileNotFoundError(f"Configuration file '{yaml_file}' not found.")
        
        try:
            with yaml_file.open('r', encoding="utf-8") as file:
                config_data = yaml.safe_load(file) or {}
            logger.debug(f"YAML configuration loaded successfully from: {yaml_file}")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file '{yaml_file}': {e}")
            raise ValueError(f"Error parsing YAML file '{yaml_file}': {e}")
        
        return config_data
        
    def search(self):
        """
        Perform a search for Sentinel products according to the configuration.
        """
        logger.info("Starting product search...")
        sentinel = self.get_sentinel_client()
        results = sentinel.search()
        logger.info(f"Search completed. Products found: {len(results)}")
        logger.debug(f"Search results detail:")
        for _, row in results.iterrows():
            logger.debug(f" - {row['Name']}")
        return results

    
    def download(self):
        """
        Download specified Sentinel products or those found in the last search.
        """
        logger.debug("Starting product download...")
        sentinel = self.get_sentinel_client()
        downloaded, pending = sentinel.download()
        logger.info(f"Download completed. Downloaded: {len(downloaded)}, Pending: {len(pending)}")
        logger.debug(f"Downloaded products: {downloaded}")
        logger.debug(f"Pending products: {pending}")
        return downloaded, pending

    def get_sentinel_client(self):
        """
        Get an instance of the Sentinel client based on the platform specified in the configuration.
        """
        credentials = self.config.get('credentials', {})
        if not credentials["username"] or not credentials["password"]:
            logger.error("'username' and 'password' must be provided in the configuration.")
            raise ValueError("'username' and 'password' must be provided in the configuration.")
        
        logger.debug(f"Creating SentinelGet client...")
        return SentinelGet(credentials=credentials,
                           platform=self.config.get('platform'),
                           product_type=self.config.get('product_type'),
                           roi_lat_lon=self.config.get('roi_lat_lon'),
                           start_date=self.config.get('start_date'),
                           end_date=self.config.get('end_date'),
                           cloud=self.config.get('cloud_cover'),
                           tile=self.config.get('tile'),
                           tiles_list=self.config.get('tiles_list'),
                           output_dir=self.config.get('output_dir', Path.cwd())
                           )

def main():

    parser = argparse.ArgumentParser(description="Download Sentinel-2 and Sentinel-3 data from the Copernicus Open Access Hub.")
    parser.add_argument('--config', "-c", required=True, type=str, help="Path to the YAML configuration file.")
    parser.add_argument("--search_only", action="store_true", help="Only search for products without downloading.")
    args = parser.parse_args()

    try:
        manager = GetManager(args.config)
        if args.search_only:
            manager.search()
        else:
            manager.download()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()