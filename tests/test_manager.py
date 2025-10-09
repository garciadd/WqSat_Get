import os
import tempfile
import yaml
import pandas as pd
import pytest

from wqsat_get.manager import GetManager


class DummySentinel:
    """A dummy version of SentinelGet used to capture initialization args."""

    def __init__(self, **kwargs):
        # store kwargs for later assertions
        self.kwargs = kwargs

    def search(self):  # pragma: no cover
        return pd.DataFrame([{"Id": "1", "Name": "dummy", "Online": True}])

    def download(self):  # pragma: no cover
        return ["dummy"], []


def test_getmanager_init_with_dict(monkeypatch):
    """
    GetManager should accept a configuration dict, validate it once and not raise.
    """
    # record calls to validate_inputs
    calls = {}

    def dummy_validate_inputs(config):
        calls['config'] = config
        return True

    # patch the utils.validate_inputs function
    from wqsat_get import utils
    monkeypatch.setattr(utils, "validate_inputs", dummy_validate_inputs)

    config = {
        'credentials': {'username': 'user', 'password': 'pass'},
        'platform': 'SENTINEL-2',
        'product_type': 'S2MSI1C',
        'start_date': '2025-01-01',
        'end_date': '2025-01-02',
        'roi_lat_lon': {'N': 40.1, 'S': 39.9, 'E': -3.0, 'W': -3.5},
        'cloud': 20
    }
    mgr = GetManager(config=config)
    # validate_inputs should have been called exactly once with our config
    assert calls.get('config') == config


def test_getmanager_missing_config():
    """
    Instantiating GetManager without config or config_file must raise a ValueError.
    """
    with pytest.raises(ValueError):
        GetManager()


def test_getmanager_from_yaml_file_not_found(tmp_path):
    """
    Passing a non-existing YAML file to GetManager should raise FileNotFoundError.
    """
    missing_file = tmp_path / "missing_config.yaml"
    with pytest.raises(FileNotFoundError):
        GetManager(config_file=str(missing_file))


def test_getmanager_from_yaml_invalid(monkeypatch, tmp_path):
    """
    If the YAML file is invalid, GetManager should raise a ValueError.
    """
    # Create a temporary invalid YAML file
    invalid_yaml = tmp_path / "bad.yaml"
    invalid_yaml.write_text("::: invalid yaml :::")
    with pytest.raises(ValueError):
        GetManager(config_file=str(invalid_yaml))


def test_getmanager_get_client(monkeypatch):
    """
    get_sentinel_client should instantiate SentinelGet with correct parameters.
    """
    # prepare configuration
    config = {
        'credentials': {'username': 'foo', 'password': 'bar'},
        'platform': 'SENTINEL-3',
        'product_type': 'OL_1_EFR___',
        'start_date': '2025-01-01',
        'end_date': '2025-01-03',
        'roi_lat_lon': (40.0, -3.5),
        'cloud_cover': 0,
        'tile': None,
        'tiles_list': None,
        'output_dir': '/tmp/out'
    }
    mgr = GetManager(config=config)

    # patch SentinelGet class to return DummySentinel and record arguments
    import wqsat_get.manager as manager_mod
    monkeypatch.setattr(manager_mod, 'SentinelGet', DummySentinel)
    sentinel = mgr.get_sentinel_client()
    # ensure DummySentinel was used and arguments match config
    assert isinstance(sentinel, DummySentinel)
    args = sentinel.kwargs
    # credentials must be passed through
    assert args['credentials'] == config['credentials']
    # other parameters should map correctly
    assert args['platform'] == config['platform']
    assert args['product_type'] == config['product_type']
    assert args['start_date'] == config['start_date']
    assert args['end_date'] == config['end_date']
    assert args['roi_lat_lon'] == config['roi_lat_lon']
    assert args['cloud'] == config['cloud_cover']
    assert args['tile'] == config['tile']
    assert args['tiles_list'] == config['tiles_list']
    # output_dir defaults to the value provided
    assert str(args['output_dir']) == config['output_dir']


def test_getmanager_missing_credentials(monkeypatch):
    """
    If credentials dictionary is missing username or password, get_sentinel_client should raise ValueError.
    """
    config = {
        'credentials': {'username': '', 'password': ''},
        'platform': 'SENTINEL-2',
        'product_type': 'S2MSI1C',
        'start_date': '2025-01-01',
        'end_date': '2025-01-02',
        'roi_lat_lon': {'N': 40.1, 'S': 39.9, 'E': -3.0, 'W': -3.5}
    }
    mgr = GetManager(config=config)
    with pytest.raises(ValueError):
        mgr.get_sentinel_client()