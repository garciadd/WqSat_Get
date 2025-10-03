"""
Given two dates and the coordinates, download N Sentinel Collections scenes from ESA Sentinel dataHUB.
The downloaded Sentinel collection scenes are compatible with:

Sentinel-2:
    * Level-1:
        - S2MSI1C: Top-of-atmosphere reflectances in cartographic geometry
    * Level-2:
        - S2MSI2A: Bottom-of-atmosphere reflectance in cartographic geometry
    
Sentinel-3:
    * Level-1:
        - OL_1_EFR___: Full Resolution TOA Reflectance
    * Level-2:
        - OL_2_LFR___: the level-2 Land Product provides land and atmospheric geophysical parameters computed for full Resolution.  
        - OL_2_WFR___: the Level-2 Water Product provides water and atmospheric geophysical parameters computed for Full Resolution.
----------------------------------------------------------------------------------------------------------

Authors: Daniel García-Díaz & Fernando Aguilar
Email: (garciad & aguilarf) @ifca.unican.es
Spanish National Research Council (CSIC); Institute of Physics of Cantabria (IFCA)
Advanced Computing and e-Science
Date: Apr 2023
"""

import requests
import os
import pandas as pd
from tqdm import tqdm
from wqsat_get import utils
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SentinelGet:
    """
    Class to interact with the Copernicus Open Access Hub for downloading Sentinel-2 and Sentinel-3 products.
    """

    def __init__(self, credentials, start_date=None, end_date=None, roi_lat_lon=None, platform=None, product_type=None, 
                 tile=None, tiles_list=None, output_dir=None, cloud=100):
        """
        Initialize the Sentinel client with optional search parameters.

        Args:
            credentials (dict): Dictionary containing 'username' and 'password'.
            start_date (str, optional): Start date in YYYY-MM-DD format.
            end_date (str, optional): End date in YYYY-MM-DD format.
            roi_lat_lon (tuple or dict, optional): Coordinates (lat, lon) or bounding box {'N','S','E','W'}.
            platform (str, optional): 'SENTINEL-2' or 'SENTINEL-3'.
            product_type (str, optional): Platform-specific product type.
            tile (str, optional): Specific product name.
            tiles_list (list, optional): List of product names.
            output_dir (str, optional): Folder to save downloaded products.
            cloud (int, optional): Maximum cloud coverage percentage.
        """

        self.start_date = start_date
        self.end_date = end_date
        self.roi_lat_lon = roi_lat_lon
        self.platform = platform
        self.product_type = product_type
        self.tile = tile
        self.tiles_list = tiles_list
        self.cloud = cloud

        # Validate credentials
        if not isinstance(credentials, dict) or 'username' not in credentials or 'password' not in credentials:
            logger.error("Credentials must be a dictionary with 'username' and 'password'.")
            raise ValueError("Credentials must be a dictionary with 'username' and 'password'.")
        self.credentials = credentials
                
        ## Set output directory
        self.output_path = Path(output_dir) if output_dir else Path.cwd()
        self.output_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Output directory set to: {self.output_path}")
                
        # HTTP session
        self.api_url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?'
        self.session = requests.Session()
        
    def get_keycloak_token(self):
        """
        Retrieves Keycloak credentials for authentication.

        Returns:
            dict: A dictionary containing Keycloak credentials (e.g., token, client_id, etc.)
        """

        url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        data = {
            "client_id": "cdse-public",
            "username": self.credentials['username'],
            "password": self.credentials['password'],
            "grant_type": "password",
            }
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            token = response.json().get("access_token")
            if not token:
                raise ValueError("Failed to retrieve access token from Keycloak.")
            logger.debug("Keycloak token retrieved successfully.")
            return token
        except requests.exceptions.RequestException as e:
            logger.error(f"Keycloak token creation failed: {e}")
            raise Exception(f"Keycloak token creation failed: {e}")

    def search(self):
        """
        Determines search type: by tile, list of tiles, or parameters.
        """
        logger.info("Starting product search in SentinelGet...")
        if self.tile:
            return self.search_by_name()
        elif self.tiles_list:
            return self.search_by_list()
        else:
            return self.search_by_parameters()
    
    def search_by_name(self):
        """Searches for a single product by its name (tile)."""

        url_query = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Name eq '{self.tile}'"
        response = self.session.get(url_query)
        response.raise_for_status()

        # Parse the response
        json_feed = response.json()

        if "value" not in json_feed:
            logger.warning(f"No results found for tile: {self.tile}")
            return pd.DataFrame()
        
        logger.debug(f"Search by name completed: {self.tile}")   
        return pd.DataFrame.from_dict(json_feed['value'])
    
    def search_by_list(self):
        """Searches for multiple products using a list of product names."""

        url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products/OData.CSC.FilterList"
        payload = {"FilterProducts": [{"Name": name} for name in self.tiles_list]}
        headers = {'Content-Type': 'application/json'}
        
        response = self.session.post(url, json=payload, headers=headers)
        response.raise_for_status()

        # Parse the response
        json_feed = response.json()
        
        if "value" not in json_feed:
            logger.warning("No results found for tiles list.")
            return pd.DataFrame()
        
        logger.debug("Search by list completed.")
        return pd.DataFrame.from_dict(json_feed['value'])
    
    def search_by_parameters(self):
        """Search products by spatial, temporal, platform, product type, cloud cover."""

        start_date, end_date, roi_lat_lon, platform, product_type, cloud = (
            self.start_date, self.end_date, self.roi_lat_lon, self.platform, 
            self.product_type, self.cloud)

        if not all([start_date, end_date, roi_lat_lon, platform, product_type]):
            logger.error("Missing required parameters for search by parameters.")
            raise ValueError("Missing required parameters for search by parameters.")
        
        if isinstance(roi_lat_lon, tuple) and len(roi_lat_lon) == 2:  # Punto
            lat, lon = roi_lat_lon
            footprint = f"POINT({lon} {lat})"
        else: # Bounding box
            # Create the spatial query footprint
            footprint = 'POLYGON(({0} {1},{2} {1},{2} {3},{0} {3},{0} {1}))'.format(roi_lat_lon['W'],
                                                                                    roi_lat_lon['S'],
                                                                                    roi_lat_lon['E'],
                                                                                    roi_lat_lon['N'])

        # Build query
        if platform == 'SENTINEL-2':
            url_query = (f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{platform}' and "
            f"OData.CSC.Intersects(area=geography'SRID=4326;{footprint}') and "
            f"ContentDate/Start gt {start_date} and ContentDate/Start lt {end_date} and "
            f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {cloud}) and "
            f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{product_type}')")
        
        elif platform == 'SENTINEL-3':
            url_query = (f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{platform}' and "
            f"OData.CSC.Intersects(area=geography'SRID=4326;{footprint}') and "
            f"ContentDate/Start gt {start_date} and ContentDate/Start lt {end_date} and "
            f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{product_type}')")
        
        # Execute the API request
        response = self.session.get(url_query)
        response.raise_for_status()
        json_feed = response.json() # Parse the response
        if "value" not in json_feed:
            logger.warning("No results found with the given parameters.")
            return pd.DataFrame()
        
        logger.debug("Search by parameters completed.")
        return pd.DataFrame.from_dict(json_feed['value'])
    
    def download(self):
        """Download products found in search or provided tiles_list."""
        logger.info("Starting download process...")
        keycloak_token = self.get_keycloak_token()
        results = self.search()
        
        if results.empty:
            logger.info("No products found to download.")
            return [], []
        
        session = requests.Session()
        session.headers.update({'Authorization': f'Bearer {keycloak_token}'})
        
        downloaded, pending = [], []
        logger.info(f"Retrieving {len(results)} results.")
        
        for _, row in results.iterrows():
            name = row['Name']
            if row.get('Online') is False:
                pending.append(name)
                logger.info(f"Product {name} is offline, skipping.")
                continue
            
            tile_path = os.path.join(self.output_path, name)
            if os.path.exists(tile_path):
                downloaded.append(name)
                logger.info(f"Product {name} already downloaded.")
                continue
            
            url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products(%s)/$value" % row['Id']
            response = session.head(url, allow_redirects=False)

            if response.status_code in (301, 302, 303, 307):
                url = response.headers['Location']

            response = session.get(url, stream=True)
            if response.status_code != 200:
                pending.append(name)
                logger.warning(f"Failed download for {name}, status {response.status_code}")
                continue
            
            total_size = int(response.headers.get('content-length', 0))
            chunk_size = 1024
            data = bytearray()
            
            with tqdm(desc=f"Downloading {name}", total=total_size, unit='B', unit_scale=True) as bar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    data.extend(chunk)
                    bar.update(len(chunk))
            
            utils.open_compressed(byte_stream=data, file_format='zip', output_folder=self.output_path)
            downloaded.append(name)
            logger.info(f"Product {name} downloaded successfully.")
            
        logger.info("Download process completed.")
        return downloaded, pending