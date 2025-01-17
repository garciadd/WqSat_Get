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

#imports apis
import datetime
import requests
import os
import pandas as pd
from tqdm import tqdm

# Subfunctions
from wqsat_get import utils


class download:

    def __init__(self, start_date, end_date, coordinates, platform, product_type, cloud=100):
        """
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

        if not all(key in self.coord for key in ['W', 'S', 'E', 'N']):
            raise ValueError("Coordinates must include 'W', 'S', 'E', and 'N'.")

        #work path
        self.output_path = os.path.join(utils.load_data_path(), self.platform, self.producttype)
        os.makedirs(self.output_path, exist_ok=True)
        
        #ESA APIs
        self.api_url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?'
        self.credentials = utils.load_credentials()['sentinel']
        
        # Open the request session
        self.session = requests.Session()
        
    def get_keycloak(self):
        data = {
            "client_id": "cdse-public",
            "username": self.credentials['user'],
            "password": self.credentials['password'],
            "grant_type": "password",
            }
        try:
            r = requests.post("https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
            data=data,
            )
            r.raise_for_status()
            return r.json().get("access_token")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Keycloak token creation failed: {e}")    
    
    def search(self, omit_corners=True):

        # Post the query to Copernicus
        footprint = 'POLYGON(({0} {1},{2} {1},{2} {3},{0} {3},{0} {1}))'.format(self.coord['W'],
                                                                                self.coord['S'],
                                                                                self.coord['E'],
                                                                                self.coord['N'])
        if self.platform == 'SENTINEL-2':
            url_query = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{self.platform}' and OData.CSC.Intersects(area=geography'SRID=4326;{footprint}') and ContentDate/Start gt {self.start_date} and ContentDate/Start lt {self.end_date} and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {self.cloud}) and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{self.producttype}')"
        elif self.platform == 'SENTINEL-3':
            url_query = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{self.platform}' and OData.CSC.Intersects(area=geography'SRID=4326;{footprint}') and ContentDate/Start gt {self.start_date} and ContentDate/Start lt {self.end_date} and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{self.producttype}')"
        response = self.session.get(url_query)

        response.raise_for_status()

        # Parse the response
        json_feed = response.json()
        if "value" not in json_feed:
            raise ValueError("No results found in response.")
        return pd.DataFrame.from_dict(json_feed['value'])
    
    def download(self):

        keycloak_token = self.get_keycloak()
        

        #results of the search
        results = self.search()
        
        session = requests.Session()
        session.headers.update({'Authorization': f'Bearer {keycloak_token}'})
        print("Authorized OK")

        if results.empty:
            print("No products found.")
            return [], []

        downloaded, pending= [], []
        print('Retrieving {} results \n'.format(len(results)))
        for index, row in results.iterrows():
            if row['Online']:

                print(f"Product {row['Name']} online")
                tile_path = os.path.join(self.output_path, row['Name'])
                if os.path.exists(tile_path):
                    print ('Already downloaded \n')
                    downloaded.append(row['Name'])
                    continue  # Skip to the next iteration

                url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products(%s)/$value" % row['Id']
                response = session.head(url, allow_redirects=False)
                if response.status_code in (301, 302, 303, 307):
                    url = response.headers['Location']
                    print(url)
                    #response = session.get(url, allow_redirects=False)
                response = session.get(url, stream=True)

                print(f"Status code {response.status_code}")
                if response.status_code == 200:

                    total_size = int(response.headers.get('content-length', 0))
                    chunk_size = 1024  # Define the chunk size

                    # Initialize an empty byte array to hold the data
                    data = bytearray()

                    with tqdm(
                        desc="Downloading",
                        total=total_size,
                        unit='iB',
                        unit_scale=True,
                        unit_divisor=1024,
                    ) as bar:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            # Update the byte array with the chunk
                            data.extend(chunk)
                            # Update the progress bar
                            bar.update(len(chunk))


                    downloaded.append(row['Name'])

                    print(f"Saving in... {tile_path}")

                    utils.open_compressed(byte_stream=data,
                                          file_format='zip',
                                          output_folder=self.output_path)
            
                else:
                    pending.append(row['Name'])
                    print ('The product is offline')
                    print ('Activating recovery mode ...')
                
            else:
                pending.append(row['Name'])
                print ('The product {} is offline'.format(row['Name']))
                print ('Activating recovery mode ... \n')
                
        return downloaded, pending