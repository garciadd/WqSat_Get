"""
Given two dates and the coordinates, download N Sentinel Collections scenes from ESA Sentinel dataHUB.
The downloaded Sentinel collection scenes are compatible with:

Sentinel-2:
    - S2MSI1C: Top-of-atmosphere reflectances in cartographic geometry
    - S2MSI2A: Bottom-of-atmosphere reflectance in cartographic geometry
    
Sentinel-3:
    - OL_1_EFR___: Full Resolution TOA Reflectance
    - OL_1_ERR___: Reduced Resolution TOA Reflectance
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
        Initializes the Download class with the provided parameters.
        Depending on the input parameters, the search method will be determined.
        
        Parameters
        ----------
        inidate : Initial date of the query in format: datetime.strptime "%Y-%m-%dT%H:%M:%SZ"
        enddate : Final date of the query in format: datetime.strptime "%Y-%m-%dT%H:%M:%SZ"
        coordinates : dict. Coordinates that delimit the region to be searched.
            Example: {"W": -2.830, "S": 41.820, "E": -2.690, "N": 41.910}}
        producttype : str
            Dataset type. A list of productypes can be found in https://mapbox.github.io/usgs/reference/catalog/ee.html
        cloud: int
            Cloud cover percentage to narrow your search
        
        Attention please!!
        ------------------
        Registration and login credentials are required to access all system features and download data.
        To register, please create a username and password.
        Once registered, the username and password must be added to the credentials.yaml file.
        Example: sentinel: {password: password, user: username}
        """
        
        #Search parameters
        self.start_date = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        self.end_date = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        self.platform = platform.upper() #All caps
        self.producttype = product_type
        self.cloud = int(cloud)
        self.coord = coordinates
        self.tiles_list = tiles_list
        self.tile = tile

        ## Define output path for downloads
        self.output_path = utils.load_data_path()
        os.makedirs(self.output_path, exist_ok=True)
        
        # Set up API and credentials
        self.api_url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?'
        self.credentials = utils.load_credentials().get('sentinel', {})
        if not self.credentials:
            raise ValueError("Missing Sentinel API credentials in credentials.yaml")
        
        # Open the request session
        self.session = requests.Session()
        
    def get_keycloak(self):
        """Retrieves an authentication token from the Keycloak authentication service."""

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
            return response.json().get("access_token")
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
        """Searches for a single product by its name."""

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

        if not all([self.start_date, self.end_date, self.coord, self.platform, self.producttype]):
            raise ValueError("Missing required parameters for search by parameters.")

        # Create the spatial query footprint
        footprint = 'POLYGON(({0} {1},{2} {1},{2} {3},{0} {3},{0} {1}))'.format(self.coord['W'],
                                                                                self.coord['S'],
                                                                                self.coord['E'],
                                                                                self.coord['N'])

        # Construct the API query
        if self.platform == 'SENTINEL-2':
            url_query = (f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{self.platform}' and "
            f"OData.CSC.Intersects(area=geography'SRID=4326;{footprint}') and "
            f"ContentDate/Start gt {self.start_date} and ContentDate/Start lt {self.end_date} and "
            f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {self.cloud}) and "
            f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{self.producttype}')")
        
        elif self.platform == 'SENTINEL-3':
            url_query = (f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{self.platform}' and "
            f"OData.CSC.Intersects(area=geography'SRID=4326;{footprint}') and "
            f"ContentDate/Start gt {self.start_date} and ContentDate/Start lt {self.end_date} and "
            f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{self.producttype}')")
        
        # Execute the API request
        response = self.session.get(url_query)
        response.raise_for_status()

        # Parse the response
        json_feed = response.json()

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