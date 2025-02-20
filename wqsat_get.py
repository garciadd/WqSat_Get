import sys
import datetime
import argparse

# Subfunctions
from wqsat_get import sentinel_get
from wqsat_get import utils

def main():

    parser = argparse.ArgumentParser(description='Python package for downloading satellite images')

    # Set credentials and data path
    parser.add_argument('--config', '-c', type=str, help='Path to configuration file')

    # Region management
    parser.add_argument('--regions', '-r', type=str, help='Path to file for setting up regions.yaml')

    # Download satellite images
    parser.add_argument('--download', '-d', type=str, help='Path to the file with the download variables')
    
    # Parse command line arguments
    args = parser.parse_args()

    try:
        if args.config:
            setup_config(args.config)
        elif args.regions:
            setup_regions(args.regions)
        elif args.download:
            setup_download(args.download)
        else:
            print("You must provide at least one flag: --config (-c), --regions (-r), or --download (-d)")
            sys.exit(1)
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)

def setup_config(config_file):
    """
    Creates or updates the config.yaml file based on the input provided
    in a configuration file (config_file). Delegates the actual creation
    or update logic to save_config.
    
    Args:
        config_file (str): Path to the text file containing configuration variables.
    
    Raises:
        FileNotFoundError: If the config_file does not exist.
        ValueError: If the file has formatting errors or invalid fields.
    """
    try:
        # Parse the provided configuration file using the parse_txt_to_dict function
        config_data = utils.parse_txt_to_dict(config_file)

        # Save or update the configuration file
        utils.save_config(
            landsat_user=config_data.get('landsat_user'),
            landsat_password=config_data.get('landsat_password'),
            sentinel_user=config_data.get('sentinel_user'),
            sentinel_password=config_data.get('sentinel_password'),
            data_path=config_data.get('data_path'),
        )
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {config_file} was not found.")
    except ValueError as e:
        raise ValueError(f"Error processing the file {config_file}: {e}")
    
def setup_regions(regions_file):
    """
    Reads region data from a regions.txt file, parses the data, 
    and creates or updates the region in the regions.yaml file.
    
    Args:
        regions_file (str): Path to the regions text file.
    """
    try:
        # Parse the region data from the file
        region_data = utils.parse_txt_to_dict(regions_file)

        # Check if all coordinates are present
        if 'W' not in region_data or 'S' not in region_data or 'E' not in region_data or 'N' not in region_data:
            raise ValueError("Missing one or more coordinates (W, S, E, N) in the region data.")

        # Validate and process the coordinates
        W, N, E, S = utils.process_coordinates(region_data['W'], region_data['N'], region_data['E'], region_data['S'])
        # Update or create the region
        utils.update_regions('region', W, S, E, N)

    except FileNotFoundError:
        raise FileNotFoundError(f"The regions file {regions_file} was not found.")
    except ValueError as e:
        raise ValueError(f"Error processing the region file: {e}")
    
def setup_download(download_file):
    """
    Main function to set up and execute the download of satellite images.
    
    Args:
        download_file (str): Path to the download configuration file.
    
    Raises:
        FileNotFoundError: If the download file does not exist.
        ValueError: If there are issues in parsing or validation.
    """
    try:
        # Parse the download data from the file
        data = utils.parse_txt_to_dict(download_file)

        # Validate download-specific fields
        try:
            downloader = sentinel_get.Download(
                start_date=data["start_date"],
                end_date=data["end_date"],
                coordinates=data["coordinates"],
                platform=data["platform"],
                product_type=data["product_type"],
                cloud=data["cloud"]
            )
            downloaded_tiles, pending_tiles = downloader.download()

            if pending_tiles:
                print(f"Pending tiles not available for download: {pending_tiles}")

        except ValueError as e:
            print(f"Download validation failed: {e}")
            downloaded_tiles = []

        return downloaded_tiles, pending_tiles

    except (FileNotFoundError, ValueError) as e:
        raise ValueError(f"Download Error: {e}")
            
if __name__ == "__main__":
    main()