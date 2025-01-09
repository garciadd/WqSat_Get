import os
import io
from werkzeug.exceptions import BadRequest
import yaml
import tarfile
import zipfile

def base_dir():
    """Returns the base directory where config.yaml is stored."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def config_path():
    """Returns the full path of the config.yaml file."""
    return os.path.join(base_dir(), 'config.yaml')

def create_config(landsat_user=None, landsat_password=None, sentinel_user=None, sentinel_password=None, data_path=None):
    """Creates or initializes the config.yaml file."""
    # Default values
    landsat_user = landsat_user or '*****'
    landsat_password = landsat_password or '*****'
    sentinel_user = sentinel_user or '*****'
    sentinel_password = sentinel_password or '*****'
    data_path = data_path or os.path.join(os.path.dirname(base_dir()), 'data')

    # Structure of the config
    data = {
        'credentials': {
            'landsat': {'user': landsat_user, 'password': landsat_password},
            'sentinel': {'user': sentinel_user, 'password': sentinel_password},
        },
        'data_path': data_path,
    }

    # Write the YAML file
    with open(config_path(), 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
    print("Config file created successfully.")

def update_config(landsat_user=None, landsat_password=None, sentinel_user=None, sentinel_password=None, data_path=None):
    """Updates specific values in the config.yaml file."""
    # Try to load existing config or start fresh if not present
    try:
        with open(config_path(), 'r') as file:
            data = yaml.safe_load(file) or {}
    except FileNotFoundError:
        data = {}

    # Update credentials if provided
    data.setdefault('credentials', {})
    if landsat_user is not None:
        data['credentials'].setdefault('landsat', {})['user'] = landsat_user
    if landsat_password is not None:
        data['credentials'].setdefault('landsat', {})['password'] = landsat_password
    if sentinel_user is not None:
        data['credentials'].setdefault('sentinel', {})['user'] = sentinel_user
    if sentinel_password is not None:
        data['credentials'].setdefault('sentinel', {})['password'] = sentinel_password

    # Update data path if provided
    if data_path is not None:
        data['data_path'] = data_path

    # Save the updated data back to the file
    with open(config_path(), 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
    print("Config file updated successfully.")

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
    """Loads and returns the data path from the config.yaml file. Creates the directory if it doesn't exist."""
    try:
        with open(config_path(), 'r') as file:
            data = yaml.safe_load(file)
            data_path = data.get('data_path', None)

            # Ensure the directory exists
            if data_path and not os.path.exists(data_path):
                os.makedirs(data_path)
                print(f"Directory '{data_path}' created.")

            return data_path
    except FileNotFoundError:
        print("Error: 'config.yaml' file not found.")
        return None
    
def create_regions(region='Santander', W=-4.0, S=43.3, E=-3.7, N=43.5):
    """Create a YAML file (regions.yaml) with a region and its coordinates.
    
    Parameters:
        region_name (str): The name of the region. Defaults to 'Santander'.
        W (float): The West coordinate. Defaults to -4.0 (for Santander).
        S (float): The South coordinate. Defaults to 43.3 (for Santander).
        E (float): The East coordinate. Defaults to -3.7 (for Santander).
        N (float): The North coordinate. Defaults to 43.5 (for Santander).
    """
    # Prepare the data to write into the YAML file
    data = {region: {'W': W, 'S': S, 'E': E, 'N': N}}

    # Write the YAML file
    with open(os.path.join(base_dir(), 'regions.yaml'), 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
    print(f"File 'regions.yaml' created successfully with region '{region}'.")

def update_regions(region, W, S, E, N):
    """Update the YAML file (regions.yaml) with new region and its coordinates."""
    # Load the current data from the file
    try:
        with open(os.path.join(base_dir(), 'regions.yaml'), 'r') as file:
            data = yaml.safe_load(file)
    except FileNotFoundError:
        data = {}

    # Add new region
    data[region] = {'W': W, 'S': S, 'E': E, 'N': N}

    # Save the updated data back to the file
    with open(os.path.join(base_dir(), 'regions.yaml'), 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
    print(f"Region '{region}' added successfully.")

def get_regions():
    """Show all regions stored in the YAML file (regions.yaml)."""
    # Load the data from the file
    try:
        with open(os.path.join(base_dir(), 'regions.yaml'), 'r') as file:
            data = yaml.safe_load(file)
        print(f"Regions in the file: {data.keys()}")
    except FileNotFoundError:
        print("No regions found, 'regions.yaml' file not found.")

def get_coordinates(region):
    """Load the coordinates (W, S, E, N) of a specific region."""
    # Load the data from the file
    try:
        with open(os.path.join(base_dir(), 'regions.yaml'), 'r') as file:
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