import yaml

# Subfunctions
from wqsat_get import sentinel_get
from wqsat_get import utils

class GetManager:
    def __init__(self, config: dict = None, config_file: str = None):
        if config is not None:
            self.config = config
        elif config_file is not None:
            self.config = self.from_yaml(config_file)
        else:
            raise ValueError("Either config or config_file must be provided.")
        
        self.settings = {
            'start_date': self.config.get('start_date'),
            'end_date': self.config.get('end_date'),
            'coordinates': self.config.get('coordinates'),
            'cloud': self.config.get('cloud'),
            'platform': self.config.get('platform'),
            'product_type': self.config.get('product_type'),
            'tile': self.config.get('tile'),
            'tiles_list': self.config.get('tiles_list'),
        }

        utils.validate_download_inputs(self.settings)

    def from_yaml(self, yaml_file: str) -> dict:
        with open(yaml_file, 'r') as file:
            return yaml.safe_load(file)
        
    def search(self,):
        runner = sentinel_get.Download(**self.settings)
        results = runner.search()
        return results
    
    def download(self,):

        runner = sentinel_get.Download(**self.settings)
        downloaded, pending = runner.download()
        return downloaded, pending
