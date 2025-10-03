import os
import io
import yaml
import tarfile
import zipfile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def base_dir():
    """Return the base directory of the package."""
    return Path(__file__).resolve().parent.parent

def regions_file():
    """Returns the full path of the regions.yaml file."""
    return os.path.join(base_dir(), 'regions.yaml')
    
def update_regions(region, W, S, E, N):
    """Update the YAML file (regions.yaml) with new region and its coordinates."""
    # Load the current data from the file
    try:
        with open(regions_file(), 'r') as file:
            data = yaml.safe_load(file) or {}
    except FileNotFoundError:
        data = {}

    # Add new region or update if already exists
    data[region] = {'W': W, 'S': S, 'E': E, 'N': N}

    # Save the updated data back to the file
    with open(regions_file(), 'w') as file:
        yaml.dump(data, file)
    logger.info(f"Region '{region}' added or updated successfully.")

def get_regions():
    """Show all regions stored in the YAML file (regions.yaml)."""
    # Load the data from the file
    try:
        with open(regions_file(), 'r') as file:
            data = yaml.safe_load(file)
        logger.info(f"Stored regions: {list(data.keys())}")
        return data
    except FileNotFoundError:
        logger.warning("No regions file found.")
        return {}

def get_coordinates(region):
    """Load the coordinates (W, S, E, N) of a specific region."""
    # Load the data from the file
    regions = get_regions()
    coords = regions.get(region)
    if not coords:
        logger.warning(f"Region '{region}' not found.")
    return coords
    
def open_compressed(byte_stream, file_format, output_folder, file_path=None):
    """
    Extract a byte stream from memory and save files.

    Args:
        byte_stream: Bytes content.
        file_format: 'zip' or tar extensions.
        output_folder: Folder to extract into.
        file_path: Temporary path for tar files.
    """
    
    tar_extensions = ['tar', 'bz2', 'tb2', 'tbz', 'tbz2', 'gz', 'tgz', 'lz', 'lzma', 'tlz', 'xz', 'txz', 'Z', 'tZ']
    if file_format in tar_extensions:
        with open(file_path, 'wb') as f:
            f.write(byte_stream)
        tar = tarfile.open(file_path)
        tar.extractall(output_folder) # specify which folder to extract to
        
        os.remove(file_path)
        
    elif file_format == 'zip':
        zf = zipfile.ZipFile(io.BytesIO(byte_stream))
        zf.extractall(output_folder)
    else:
        raise ValueError('Invalid file format for the compressed byte_stream')

def validate_inputs(args: dict):
    """Validate all inputs for Sentinel downloads."""
    
    # tiles
    tile = args.get('tile')
    if tile and not isinstance(tile, str):
        raise ValueError("'tile' must be a string.")
    tiles_list = args.get('tiles_list')
    if tiles_list and (not isinstance(tiles_list, list) or not all(isinstance(t, str) for t in tiles_list)):
        raise ValueError("'tiles_list' must be a list of strings.")

    # dates
    start_date = args.get('start_date')
    end_date = args.get('end_date')
    if start_date and end_date:
        import datetime
        try:
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            if end <= start:
                raise ValueError("'end_date' must be after 'start_date'.")
        except ValueError:
            raise ValueError("Dates must be YYYY-MM-DD.")

    # coordinates
    coordinates = args.get('roi_lat_lon')
    if coordinates:
        if isinstance(coordinates, tuple) and len(coordinates) == 2:
            lat, lon = coordinates
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise ValueError("Lat/lon out of range.")
        elif isinstance(coordinates, dict) and all(k in coordinates for k in ['N','S','E','W']):
            if not (-90 <= coordinates['S'] < coordinates['N'] <= 90) or not (-180 <= coordinates['W'] < coordinates['E'] <= 180):
                raise ValueError("Coordinates out of range or misordered.")
        else:
            raise ValueError("Invalid coordinate format.")

    # platform
    valid_platforms = {"SENTINEL-2", "SENTINEL-3"}
    platform = args.get('platform')
    if platform and platform not in valid_platforms:
        raise ValueError(f"Invalid platform '{platform}'.")

    # product_type
    valid_products = {"SENTINEL-2": {"S2MSI1C", "S2MSI2A"},
                      "SENTINEL-3": {"OL_1_EFR___", "OL_2_LFR___", "OL_2_WFR___"}}
    product_type = args.get('product_type')
    if product_type:
        if not isinstance(product_type, str) or platform not in valid_products or product_type not in valid_products[platform]:
            raise ValueError(f"Invalid product_type '{product_type}' for platform '{platform}'.")

    # cloud
    cloud = args.get('cloud')
    if cloud is not None and (not isinstance(cloud, int) or not (0 <= cloud <= 100)):
        raise ValueError("'cloud' must be int 0-100.")

    return True