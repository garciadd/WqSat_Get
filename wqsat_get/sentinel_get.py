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


class Download:

    def __init__(self, start_date=None, end_date=None, coordinates=None, platform=None, product_type=None, tile=None, tiles_list=None, cloud=100):
        """
        Initializes the Download class, validating input parameters and setting up API configuration.

        Args:
            start_date (str, optional): Start date for the download period.
            end_date (str, optional): End date for the download period.
            coordinates (tuple, optional): Geographical coordinates for the area of interest.
            platform (str, optional): Platform from which data will be downloaded (e.g., Sentinel).
            product_type (str, optional): Type of product to be downloaded.
            tile (str, optional): Specific tile for downloading data.
            tiles_list (list, optional): List of tiles for batch download.
            cloud (int, optional): Maximum cloud coverage percentage for filtering data. Default is 100.
        
        Raises:
            ValueError: If input validation fails or credentials are missing.
        """

        self.start_date = start_date
        self.end_date = end_date
        self.coordinates = coordinates
        self.platform = platform
        self.product_type = product_type
        self.tile = tile
        self.tiles_list = tiles_list
        self.cloud = cloud
                
        ## Define output path for downloads
        self.output_path = utils.load_data_path()
        os.makedirs(self.output_path, exist_ok=True)
        
        # Set up API and credentials
        self.api_url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?'
        self.credentials = utils.load_credentials().get('sentinel', {})
        if not self.credentials:
            raise ValueError("Missing Sentinel API credentials in credentials.yaml")
        
        # Initialize session
        self.session = requests.Session()
        
    def get_keycloak(self):
        """
        Retrieves Keycloak credentials for authentication.

        Returns:
            dict: A dictionary containing Keycloak credentials (e.g., token, client_id, etc.)
        
        Raises:
            ValueError: If Keycloak credentials are missing or cannot be fetched.
        """

        url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        data = {
            "client_id": "cdse-public",
            "username": self.credentials['user'],
            "password": self.credentials['password'],
            "grant_type": "password",
            }
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            token = response.json().get("access_token")
            if not token:
                raise ValueError("Failed to retrieve access token from Keycloak.")
            return token
        except requests.exceptions.RequestException as e:
            raise Exception(f"Keycloak token creation failed: {e}")

    def search(self):
        """Determines which search method to use based on the input parameters."""

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
            raise ValueError("No results found in response.")
        
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
            raise ValueError("No results found in response.")
        
        return pd.DataFrame.from_dict(json_feed['value'])
    
    def search_by_parameters(self):
        """Searches for products based on date range, coordinates, platform, and product type."""

        start_date, end_date, coordinates, platform, product_type, cloud = (
            self.start_date, self.end_date, self.coordinates, self.platform, 
            self.product_type, self.cloud)

        if not all([start_date, end_date, coordinates, platform, product_type]):
            raise ValueError("Missing required parameters for search by parameters.")
        
        if isinstance(coordinates, tuple) and len(coordinates) == 2:  # Punto
            lat, lon = coordinates
            footprint = f"POINT({lon} {lat})"
        else: # Bounding box
            # Create the spatial query footprint
            footprint = 'POLYGON(({0} {1},{2} {1},{2} {3},{0} {3},{0} {1}))'.format(coordinates['W'],
                                                                                    coordinates['S'],
                                                                                    coordinates['E'],
                                                                                    coordinates['N'])

        # Construct the API query
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
            raise ValueError("No results found in response.")
        
        return pd.DataFrame.from_dict(json_feed['value'])
    
    def download(self):
        """Downloads the products obtained from the search query."""

        keycloak_token = self.get_keycloak()
        results = self.search()
        
        if results.empty:
            print("No products found.")
            return [], []
        
        session = requests.Session()
        session.headers.update({'Authorization': f'Bearer {keycloak_token}'})
        
        downloaded, pending = [], []
        print('Retrieving {} results \n'.format(len(results)))
        
        for _, row in results.iterrows():
            if row['Online'] is False:
                pending.append(row['Name'])
                print(f"Product {row['Name']} is offline. Recovery mode activated.")
                continue
            
            tile_path = os.path.join(self.output_path, row['Name'])
            if os.path.exists(tile_path):
                print(f"Product {row['Name']} already downloaded.")
                downloaded.append(row['Name'])
                continue
            
            url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products(%s)/$value" % row['Id']
            response = session.head(url, allow_redirects=False)

            if response.status_code in (301, 302, 303, 307):
                url = response.headers['Location']

            response = session.get(url, stream=True)
            if response.status_code != 200:
                pending.append(row['Name'])
                print(f"Product {row['Name']} failed to download. Status: {response.status_code}")
                continue
            
            total_size = int(response.headers.get('content-length', 0))
            chunk_size = 1024
            data = bytearray()
            
            with tqdm(desc=f"Downloading {row['Name']}", total=total_size, unit='B', unit_scale=True) as bar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    data.extend(chunk)
                    bar.update(len(chunk))
            
            utils.open_compressed(byte_stream=data, file_format='zip', output_folder=self.output_path)
            downloaded.append(row['Name'])
        
        return downloaded, pending