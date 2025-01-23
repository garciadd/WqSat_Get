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

def save_config(landsat_user=None, landsat_password=None, sentinel_user=None, sentinel_password=None, data_path=None):
    """
    Creates or updates the config.yaml file. If the file already exists, updates
    only the fields provided while preserving existing values.
    
    Args:
        landsat_user (str, optional): Landsat username.
        landsat_password (str, optional): Landsat password.
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
    landsat_config = data['credentials'].setdefault('landsat', {})
    sentinel_config = data['credentials'].setdefault('sentinel', {})

    # Update values only if new ones are provided
    if landsat_user is not None:
        landsat_config['user'] = landsat_user
    if landsat_password is not None:
        landsat_config['password'] = landsat_password
    if sentinel_user is not None:
        sentinel_config['user'] = sentinel_user
    if sentinel_password is not None:
        sentinel_config['password'] = sentinel_password

    # Update data path if provided
    if data_path is not None:
        data['data_path'] = data_path

    # If the file does not exist, ensure default values for missing fields
    if not os.path.exists(config_path()):
        landsat_config.setdefault('user', '*****')
        landsat_config.setdefault('password', '*****')
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
            print(f"Directory {data_path} set as data_path")

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
        # tar = tarfile.open(fileobj=byte_stream, mode="r:{}".format(file_format))
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

def process_coordinates(W, N, E, S):
    """Process the coordinates to validate and return them as standard Python floats."""
    # Convert to float using Python's standard float
    W, N, E, S = float(W), float(N), float(E), float(S)

    latitude_range = [-90, 90]  # Valid range for latitude
    longitude_range = [-180, 180]  # Valid range for longitude
    
    # Validate that North is greater than South
    if not N > S:
        raise ValueError("The north coordinate must be greater than the south coordinate")

    # Validate that West is less than East
    if not W < E:
        raise ValueError("The west coordinate must be less than the east coordinate")

    # Validate coordinates are within valid range
    if not (latitude_range[0] <= N <= latitude_range[1] and
            latitude_range[0] <= S <= latitude_range[1] and
            longitude_range[0] <= W <= longitude_range[1] and
            longitude_range[0] <= E <= longitude_range[1]):
        raise ValueError("Coordinates are out of valid range")

    return W, N, E, S

def validate_download_config(args):
    """
    Validate the configuration for satellite image download.
    
    Args:
        data (dict): Configuration dictionary parsed from the workflow file.
    
    Returns:
        dict: Validated and possibly augmented configuration.
    
    Raises:
        ValueError: If critical fields are invalid and no tiles are provided.
    """
        
    # Validate platform
    platform = args.get['platform']
    if platform not in ['SENTINEL-2', 'SENTINEL-3']:
        raise ValueError(f"Invalid platform: {platform}. Valid options are 'SENTINEL-2', 'SENTINEL-3'.")

    # Validate product_type
    product_type = args.get['product_type']
    if platform == 'SENTINEL-2' and product_type not in ['S2MSI1C', 'S2MSI2A']:
        raise ValueError(f"Invalid product type for {platform}: {product_type}. Valid options are 'S2MSI1C', 'S2MSI2A'.")
    elif platform == 'SENTINEL-3' and product_type not in ['OL_1_EFR___', 'OL_1_ERR___']:
        raise ValueError(f"Invalid product type for {platform}: {product_type}. Valid options are 'OL_1_EFR___', 'OL_1_ERR___'.")

    # Validate start_date and end_date
    try:
        start_date = datetime.datetime.strptime(args.get['start_date'], "%Y-%m-%d")
        end_date = datetime.datetime.strptime(args.get['end_date'], "%Y-%m-%d")
        if end_date <= start_date:
            raise ValueError("The end date must be after the start date.")
    except ValueError:
        raise ValueError("'start_date' and 'end_date' must be in the format YYYY-MM-DD.")
    
    # Validate region or coordinates
    coordinates = args.get("coordinates")
    region = args.get("region")
    if not coordinates and not region:
        raise ValueError("Either 'coordinates' or 'region' must be provided.")
    if coordinates:
        if not isinstance(coordinates, list) or len(coordinates) != 4:
            raise ValueError("'coordinates' must be a list of 4 values [W, S, E, N].")
        try:
            # Process and validate coordinates
            args["coordinates"] = process_coordinates(*coordinates)
        except ValueError as e:
            raise ValueError(f"Invalid coordinates: {e}")
    elif region:
        coordinates = get_coordinates(region)
        if not coordinates:
            raise ValueError(f"Region '{region}' not found in regions.yaml.")
        args["coordinates"] = coordinates  # Prioritize region-derived coordinates

    # Validate cloud and set default
    cloud = args.get("cloud")
    if cloud is None:
        args["cloud"] = 100  # Default value
    elif not isinstance(cloud, int) or not (0 <= cloud <= 100):
        raise ValueError("'cloud' must be an integer between 0 and 100.")
    
    return args