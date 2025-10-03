# WqSat_Get: A Python Package for Satellite Image Download

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub Actions Status](https://github.com/garciadd/WqSat_Get/workflows/CI/badge.svg)](https://github.com/garciadd/WqSat_Get/actions)
[![Code Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)](https://your-coverage-report-url)

---

## Overview

WqSat_Get provides a simple way to search, filter, and download Copernicus Sentinel-2 and Sentinel-3 satellite data. It integrates with YAML-based configurations for repeatable workflows, supports both interactive notebooks and command line execution, and includes a robust logging system.

---

## Authors

Daniel García-Díaz & Fernando Aguilar Gómez
Email: (garciad & aguilarf) @ifca.unican.es
Spanish National Research Council (CSIC); Institute of Physics of Cantabria (IFCA)
Advanced Computing and e-Science

---

## Features

- Search Sentinel-2 and Sentinel-3 data:
  - By single tile or list of tiles.
  - By region of interest (lat/lon bounding box).
  - By parameters (date range, platform, product type, cloud coverage).
- Download selected products into structured directories.
- YAML configuration files for reproducible workflows.
- CLI and Jupyter/Notebook support.
- **Logging system**:
  - Logs all levels (DEBUG and above) to a timestamped file in `logs/`.
  - Console shows only `INFO` and above.
  - Sensitive data (credentials) are masked.
- Error handling with clear messages and traceability.

---

## Installation

To install **WqSat-Get**, clone the repository and install the dependencies using `pip`:

```{Python}
# Clone the repository
git clone https://github.com/garciadd/WqSat_Get.git

# Navigate to the package directory
cd WqSat_Get

# Install the package
pip install .
```

---

## Dependencies

Ensure the following Python libraries are installed:

- pandas
- requests
- tqdm
- pyyaml

To install all required dependencies, use:

```{Python}
pip install -r requirements.txt
```

---

## Credentials

To use this package, you need a valid **Copernicus Data Space Ecosystem** account:

- Register at [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/). Registration is free and allows access to the required APIs.
- Store your `username` and `password` in your YAML configuration (masked in logs).

**Example YAML snippet:**

```{yaml}
username: your_username
password: your_password
platform: SENTINEL-2
product_type: S2MSI2A
start_date: 2023-01-01
end_date: 2023-02-01
cloud: 20
roi_lat_lon:
  W: -5.0
  S: 43.0
  E: -4.0
  N: 44.0
output_dir: ./downloads
```

---

## Usage

### From Python (load configuration from YAML)

```{Python}
config_path = "******"  # Path to your configuration file
manager = GetManager(config_file=config_path)
results = manager.search()
# downloaded, pending = manager.download()
```

### From Python (load configuration from dictionary)

```{Python}
config = {
    'credentials': {'username': '******',
                    'password': '******'},
    'platform': "SENTINEL-2",
    'product_type': "S2MSI1C",
    'start_date': "2024-01-01",
    'end_date': "2024-01-15",
    'roi_lat_lon':{'N': 39.8, 'S': 39.2, 'E': 3.6, 'W': 2.9}, 
    'cloud_cover': 20,
    'output_dir': "*******"  # Path to your output directory
    }

manager = GetManager(config=config)
results = manager.search()
# downloaded, pending = manager.download()
```

### From CLI

```{bash}
python -m wqsat_get --config settings.yaml
```

Options:

- `--search_only`: Only search without downloading.

---

## Logging Example

```text
[2025-08-14 17:05:32,125] INFO - root: Starting product search...
[2025-08-14 17:05:34,217] INFO - root: Search completed. Products found: 11
```

- Console → only `INFO` and above.
- File in `logs/` → full details (DEBUG and above).

---

## Error Handling

- **Invalid Coordinates**: Ensure `N > S` and `E > W`.
- **Date Format Errors**: Dates must be in `YYYY-MM-DD` format.
- **Platform/Product Type Validation**: Use only valid platform and product type combinations.
- **API Access Errors**: Ensure credentials are correctly set in the `credentials.yaml` file.

---

## License

This project is licensed under the Apache-2.0 License. See the `LICENSE` file for details.
