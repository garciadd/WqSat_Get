import io
import os
import tarfile
import tempfile
import zipfile

import pytest

from wqsat_get import utils


def test_validate_inputs_invalid_tile():
    with pytest.raises(ValueError):
        utils.validate_inputs({'tile': 123})


def test_validate_inputs_invalid_tiles_list():
    with pytest.raises(ValueError):
        utils.validate_inputs({'tiles_list': ['A', 2]})


def test_validate_inputs_invalid_dates_order():
    config = {'start_date': '2025-01-10', 'end_date': '2025-01-05'}
    with pytest.raises(ValueError):
        utils.validate_inputs(config)


def test_validate_inputs_invalid_dates_format():
    config = {'start_date': '2025/01/01', 'end_date': '2025-01-02'}
    with pytest.raises(ValueError):
        utils.validate_inputs(config)


def test_validate_inputs_invalid_point_coordinates():
    config = {'roi_lat_lon': (100.0, 200.0)}
    with pytest.raises(ValueError):
        utils.validate_inputs(config)


def test_validate_inputs_invalid_bbox_order():
    config = {'roi_lat_lon': {'N': 39.0, 'S': 40.0, 'E': -3.0, 'W': -3.5}}
    with pytest.raises(ValueError):
        utils.validate_inputs(config)


def test_validate_inputs_invalid_platform():
    with pytest.raises(ValueError):
        utils.validate_inputs({'platform': 'SENTINEL-5'})


def test_validate_inputs_invalid_product_type():
    config = {'platform': 'SENTINEL-2', 'product_type': 'INVALID'}
    with pytest.raises(ValueError):
        utils.validate_inputs(config)


def test_validate_inputs_invalid_cloud():
    config = {'cloud': 150}
    with pytest.raises(ValueError):
        utils.validate_inputs(config)


def test_validate_inputs_valid_config():
    config = {
        'tile': 'S2A_TEST_TILE',
        'start_date': '2025-01-01',
        'end_date': '2025-01-02',
        'roi_lat_lon': {'N': 40.1, 'S': 39.9, 'E': -3.0, 'W': -3.5},
        'platform': 'SENTINEL-2',
        'product_type': 'S2MSI1C',
        'cloud': 20
    }
    assert utils.validate_inputs(config) is True


def test_update_get_regions(monkeypatch, tmp_path):
    """
    update_regions should create/update the YAML file, and get_regions/get_coordinates should retrieve values.
    """
    # redirect regions_file to a temporary file
    temp_regions = tmp_path / 'regions.yaml'
    monkeypatch.setattr(utils, 'regions_file', lambda: str(temp_regions))

    utils.update_regions('test_region', W=-3.5, S=39.9, E=-3.0, N=40.1)
    regions = utils.get_regions()
    assert 'test_region' in regions
    assert regions['test_region']['W'] == -3.5
    coords = utils.get_coordinates('test_region')
    assert coords == {'W': -3.5, 'S': 39.9, 'E': -3.0, 'N': 40.1}
    # requesting non-existent region should return None
    assert utils.get_coordinates('no_region') is None


def test_open_compressed_zip(tmp_path):
    """
    open_compressed should extract ZIP archives from a byte stream.
    """
    # create a zip file in memory
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, 'w') as zf:
        zf.writestr('file.txt', 'content')
    mem_zip_bytes = mem_zip.getvalue()
    out_dir = tmp_path / 'zip_extract'
    utils.open_compressed(mem_zip_bytes, file_format='zip', output_folder=str(out_dir))
    extracted = out_dir / 'file.txt'
    assert extracted.exists() and extracted.read_text() == 'content'


def test_open_compressed_tar(tmp_path):
    """
    open_compressed should extract tar archives when file_format is a tar extension.
    """
    tmp_tar_path = tmp_path / 'archive.tar'
    # create a tar archive on disk
    with tarfile.open(tmp_tar_path, 'w') as tar:
        inner_file = tmp_path / 'inner.txt'
        inner_file.write_text('hello')
        tar.add(inner_file, arcname='inner.txt')
    data = tmp_tar_path.read_bytes()
    out_dir = tmp_path / 'tar_extract'
    utils.open_compressed(data, file_format='tar', output_folder=str(out_dir), file_path=str(tmp_tar_path))
    extracted = out_dir / 'inner.txt'
    assert extracted.exists() and extracted.read_text() == 'hello'


def test_open_compressed_invalid(tmp_path):
    with pytest.raises(ValueError):
        utils.open_compressed(b'data', file_format='rar', output_folder=str(tmp_path))