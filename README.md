# WqSat_Get: A Python Package for Satellite Image Download
[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub Actions Status](https://github.com/garciadd/WqSat_Get/workflows/CI/badge.svg)](https://github.com/garciadd/WqSat_Get/actions)
[![Code Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)](https://your-coverage-report-url)

## Overview
WqSat_Get is a Python package designed for efficient downloading of satellite images from Sentinel-2 and Sentinel-3 platforms. The package simplifies the process of querying, filtering, and downloading high-resolution satellite imagery using the Copernicus Open Access Hub API. It also supports execution via the command line.

## Authors
Daniel García-Díaz & Fernando Aguilar
Email: (garciad & aguilarf) @ifca.unican.es
Spanish National Research Council (CSIC); Institute of Physics of Cantabria (IFCA)
Advanced Computing and e-Science
—
## Features
* **Platform Support**: Download data from Sentinel-2 (S2MSI1C, S2MSI2A) and Sentinel-3 (OL\_1\_EFR___, OL\_1\_ERR___).
* **Customizable Queries**: Specify date ranges, coordinates, cloud cover, and product types.
* **Command Line Integration**: Run the package directly from the command line using configuration files.
* **Progress Tracking**: Integrated progress bars with `tqdm` for an enhanced user experience.

## Installation
To install **WqSat-Get**, clone the repository and install the dependencies using `pip`:
```
# Clone the repository
git clone https://github.com/garciadd/WqSat_Get.git

# Navigate to the package directory
cd WqSat_Get

# Install the package
pip install .
```

## Dependencies
Ensure the following Python libraries are installed:
* numpy
* pandas
* requests
* tqdm
* pyyaml

To install all required dependencies, use:
```
pip install -r requirements.txt
```

## Credentials
To use this package, you need to be registered on the [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/). Registration is free and allows access to the required APIs. Once registered, you must create a \`credentials.yaml\` file in your working directory containing your login credentials. The file should be structured as follows:
```
sentinel:
  user: your_username
  password: your_password
```
For detailed examples on how to create and update the `credentials.yaml` file programmatically, refer to the **Config** notebook included in the repository.

To configure the access to the data space directly, you can set the configuration providing your credentials like this:

```
utils.save_config(sentinel_user="new_user", sentinel_password="")
```


## Usage
### 1. From Python
Example: Downloading Sentinel-2 Images
```
import datetime

from wqsat_get import utils
from wqsat_get.sentinel_dl import download

# Define the query parameters
params = {
    "start_date": datetime.datetime(2023, 1, 1),
    "end_date": datetime.datetime(2023, 1, 31),
    "coordinates": utils.get_coordinates(region),
    "platform": "SENTINEL-2",
    "product_type": "S2MSI2A",
    "cloud": 20  # Maximum cloud cover percentage
}

# Initialize the downloader
s2_downloader = download(**params)

# Search and download
results = s2_downloader.search()
print(results)
downloaded, pending = s2_downloader.download()
print("Downloaded images:", downloaded)
print("Pending images:", pending)
```
### 2. From Command Line
Prepare a configuration file (e.g., `config.txt`) with the following format:
```
# Configuration file for WQSat-DL
start_date 2023-01-01
end_date 2023-01-31
coordinates (W,S,E,N): -2.83,41.82,-2.69,41.91
platform SENTINEL-2
product_type S2MSI2A
cloud 20
```
Run the command:
```
python3 wqsat_get.py -d config_commandLine_example.txt
```

## Error Handling
* **Invalid Coordinates**: Ensure `N > S` and `E > W`.
* **Date Format Errors**: Dates must be in `YYYY-MM-DD` format.
* **Platform/Product Type Validation**: Use only valid platform and product type combinations.
* **API Access Errors**: Ensure credentials are correctly set in the `credentials.yaml` file.
    
—
## License
This project is licensed under the Apache-2.0 License. See the `LICENSE` file for details.
