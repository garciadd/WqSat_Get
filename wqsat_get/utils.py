import os
import io
import yaml
import tarfile
import zipfile
import datetime
import ast  # To safely evaluate strings into Python literals (lists, dicts, etc.)

def base_dir():
    """Returns the base directory where config.yaml is stored."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def config_path():
    """Returns the full path of the config.yaml file."""
    return os.path.join(base_dir(), 'config.yaml')

def regions_path():
    """Returns the full path of the regions.yaml file."""
    return os.path.join(base_dir(), 'regions.yaml')

def save_config(sentinel_user=None, sentinel_password=None, data_path=None):
    """
    Creates or updates the config.yaml file. If the file already exists, updates
    only the fields provided while preserving existing values.
    
    Args:
        sentinel_user (str, optional): Sentinel username.
        sentinel_password (str, optional): Sentinel password.
        data_path (str, optional): Path to the data directory.
    """

    try:
        # Load the existing configuration, if it exists
        with open(config_path(), 'r') as file:
            data = yaml.safe_load(file) or {}
    except FileNotFoundError:
        data = {}  # Start with an empty config if the file does not exist

    # Ensure default structure for credentials
    data.setdefault('credentials', {})
    sentinel_config = data['credentials'].setdefault('sentinel', {})

    # Update values only if new ones are provided
    if sentinel_user is not None:
        sentinel_config['user'] = sentinel_user
    if sentinel_password is not None:
        sentinel_config['password'] = sentinel_password

    # Update data path if provided
    if data_path is not None:
        data['data_path'] = data_path

    # If the file does not exist, ensure default values for missing fields
    if not os.path.exists(config_path()):
        sentinel_config.setdefault('user', '*****')
        sentinel_config.setdefault('password', '*****')
        data.setdefault('data_path', '*****')

    # Save the updated data back to the file
    with open(config_path(), 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
    print("Config file saved successfully.")

def load_credentials():
    """Loads and returns the credentials from the config.yaml file."""
    try:
        with open(config_path(), 'r') as file:
            data = yaml.safe_load(file)
            return data.get('credentials', {})
    except FileNotFoundError:
        print("Error: 'config.yaml' file not found.")
        return {}
    
def load_data_path():
    """
    Loads and returns the data path from the config.yaml file. Creates the directory if it doesn't exist.
    Raises an error if the directory cannot be created.
    """
    try:
        with open(config_path(), 'r') as file:
            data = yaml.safe_load(file)
            data_path = data.get('data_path', None)

            # Ensure the directory exists
            if data_path:
                if not os.path.exists(data_path):
                    try:
                        os.makedirs(data_path)
                        print(f"Directory '{data_path}' created.")
                    except Exception as e:
                        raise OSError(f"Failed to create the directory '{data_path}': {e}")

            return data_path
        
    except FileNotFoundError:
        print("Error: 'config.yaml' file not found.")
        return None
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")

def update_regions(region, W, S, E, N):
    """Update the YAML file (regions.yaml) with new region and its coordinates."""
    # Load the current data from the file
    try:
        with open(regions_path(), 'r') as file:
            data = yaml.safe_load(file) or {}
    except FileNotFoundError:
        data = {}

    # Add new region or update if already exists
    data[region] = {'W': W, 'S': S, 'E': E, 'N': N}

    # Save the updated data back to the file
    with open(regions_path(), 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
    print(f"Region '{region}' added successfully.")

def get_regions():
    """Show all regions stored in the YAML file (regions.yaml)."""
    # Load the data from the file
    try:
        with open(regions_path(), 'r') as file:
            data = yaml.safe_load(file)
        print(f"Regions in the file: {data.keys()}")
    except FileNotFoundError:
        print("No regions found, 'regions.yaml' file not found.")

def get_coordinates(region):
    """Load the coordinates (W, S, E, N) of a specific region."""
    # Load the data from the file
    try:
        with open(regions_path(), 'r') as file:
            data = yaml.safe_load(file)
        if region in data:
            return data[region]
        else:
            print(f"Region '{region}' not found.")
            return None
    except FileNotFoundError:
        print("No regions found, 'regions.yaml' file not found.")
        return None
    
def open_compressed(byte_stream, file_format, output_folder, file_path=None):
    """
    Extract and save a stream of bytes of a compressed file from memory.
    Parameters
    ----------
    byte_stream : BinaryIO
    file_format : str
        Compatible file formats: tarballs, zip files
    output_folder : str
        Folder to extract the stream
    Returns
    -------
    Folder name of the extracted files.
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
    
def parse_txt_to_dict(file_path):
    """
    Parses a custom text file into a dictionary.
    Supports optional commas at the end of lines and values with or without quotes.
    
    Args:
        file_path (str): Path to the text file to be parsed.
    
    Returns:
        dict: A dictionary with the parsed key-value pairs.
    
    Raises:
        ValueError: If the file format is invalid or parsing fails.
        FileNotFoundError: If the file does not exist.
        Handles lists and coordinate arrays properly.
    """

    config = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # Strip whitespace and ignore comments or empty lines
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Split on the first colon
                if ':' not in line:
                    raise ValueError(f"Invalid line format: '{line}' (missing ':')")
                key, value = line.split(':', 1)

                # Clean and process key-value pairs
                key = key.strip()
                value = value.strip().rstrip(',')

                # Remove surrounding quotes if present
                if value.startswith(("'", '"')) and value.endswith(("'", '"')):
                    value = value[1:-1]

                # Convert lists, coordinates, or other literals using ast.literal_eval
                try:
                    value = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    pass  # Leave value as a string if it's not a valid literal
                
                # Add the key-value pair to the dictionary
                config[key] = value
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {file_path} was not found.")
    except Exception as e:
        raise ValueError(f"Error parsing the file: {e}")

    return config

def validate_coordinates(W, N, E, S):
    """
    Validates geographic coordinates without modifying them.

    Args:
        W: Western longitude (float or str).
        N: Northern latitude (float or str).
        E: Eastern longitude (float or str).
        S: Southern latitude (float or str).

    Raises:
        ValueError: If coordinates are out of range or incorrectly ordered.
    """
    # Define valid ranges
    lat_range = (-90, 90)
    lon_range = (-180, 180)

    if not (lat_range[0] <= S < N <= lat_range[1]):
        raise ValueError("❌ N must be greater than S and within the range [-90, 90].")

    if not (lon_range[0] <= W < E <= lon_range[1]):
        raise ValueError("❌ W must be less than E and within the range [-180, 180].")

def validate_download_inputs(args):
    """
    Validates user input arguments for satellite image download.

    Args:
        args (dict): Dictionary containing the download parameters.

    Returns:
        bool: True if all inputs are valid.

    Raises:
        ValueError: If any input is invalid.
    """

    # Validate tile and tiles_list
    tile = args.get('tile')
    if tile and not isinstance(tile, str):
        raise ValueError("❌ 'tile' must be a string.")
    
    tiles_list = args.get('tiles_list')
    if tiles_list:
        if not isinstance(tiles_list, list) or not all(isinstance(t, str) for t in tiles_list):
            raise ValueError("❌ 'tiles_list' must be a list of strings.")

    # Validate dates
    start_date = args.get('start_date')
    end_date = args.get('end_date')
    if start_date and end_date:
        try:
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            if end <= start:
                raise ValueError("❌ 'end_date' must be later than 'start_date'.")
        except ValueError:
            raise ValueError("❌ 'start_date' and 'end_date' must be in YYYY-MM-DD format.")

    # Validate coordinates
    coordinates = args.get('coordinates')
    if coordinates:
        if isinstance(coordinates, tuple) and len(coordinates) == 2:
            lat, lon = coordinates
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("❌ Coordinates are out of valid range (-90 to 90 for latitude, -180 to 180 for longitude).")
        elif isinstance(coordinates, dict) and all(k in coordinates for k in ['N', 'S', 'E', 'W']):
            validate_coordinates(coordinates['W'], coordinates['N'], coordinates['E'], coordinates['S'])
        else:
            raise ValueError("❌ Invalid coordinate format. Use (lat, lon) or {'N': , 'S': , 'E': , 'W': }.")

    # Validate platform
    valid_platforms = {"SENTINEL-2", "SENTINEL-3"}
    platform = args.get('platform')
    if platform is not None and platform not in valid_platforms:
        raise ValueError(f"❌ 'platform' must be one of {valid_platforms}, not '{platform}'.")

    # Validate product_type (Must be valid for the selected platform)
    valid_products = {"SENTINEL-2": {"S2MSI1C", "S2MSI2A"},
                      "SENTINEL-3": {"OL_1_EFR___", "OL_2_LFR___", "OL_2_WFR___"}}
    product_type = args.get('product_type')
    if product_type is not None:
        if not isinstance(product_type, str):
            raise ValueError("❌ 'product_type' must be a string.")
        if platform not in valid_products or product_type not in valid_products[platform]:
            raise ValueError(f"❌ Invalid 'product_type' for platform {platform}. Must be one of {valid_products.get(platform, {})}.")

    # Validate cloud cover
    cloud = args.get('cloud')
    if cloud is not None:
        if not isinstance(cloud, int) or not (0 <= cloud <= 100):
            raise ValueError("❌ 'cloud' must be an integer between 0 and 100.")

    return True