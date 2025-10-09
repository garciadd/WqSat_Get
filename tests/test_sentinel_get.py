import pandas as pd
import pytest

from wqsat_get.sentinel_get import SentinelGet


class DummySession:
    """Session that captures last requested URL and returns dummy responses."""
    def __init__(self):
        self.last_url = None

    def get(self, url):
        self.last_url = url
        # return an object mimicking requests.Response with json() and raise_for_status()
        class Response:
            status_code = 200
            def json(self):
                return {"value": []}
            def raise_for_status(self):
                pass
        return Response()

    def post(self, *args, **kwargs):  # pragma: no cover
        return self.get(args[0])


def make_sentinel(**kwargs):
    creds = {'username': 'user', 'password': 'pass'}
    return SentinelGet(credentials=creds, **kwargs)


def test_search_by_parameters_missing(monkeypatch):
    """
    search_by_parameters should raise ValueError when required parameters are missing.
    """
    sentinel = make_sentinel(start_date='2025-01-01', end_date=None, roi_lat_lon=None,
                             platform=None, product_type=None)
    with pytest.raises(ValueError):
        sentinel.search_by_parameters()


def test_search_by_parameters_point(monkeypatch):
    """
    When coordinates are given as a point (lat, lon), the query should use POINT and include cloud filter for Sentinel-2.
    """
    session = DummySession()
    sentinel = make_sentinel(start_date='2025-01-01', end_date='2025-01-02',
                             roi_lat_lon=(40.0, -3.5), platform='SENTINEL-2',
                             product_type='S2MSI1C', cloud=10)
    monkeypatch.setattr(sentinel, 'session', session)
    df = sentinel.search_by_parameters()
    # DataFrame should be returned even if empty
    assert isinstance(df, pd.DataFrame)
    # The last URL should contain POINT(longitude latitude)
    assert "POINT(-3.5 40.0)" in session.last_url
    # cloud filter should be present in query
    assert "cloudCover" in session.last_url


def test_search_by_parameters_bbox(monkeypatch):
    """
    When coordinates are given as a bounding box, the query should use POLYGON and omit cloud filter for Sentinel-3.
    """
    session = DummySession()
    sentinel = make_sentinel(start_date='2025-01-01', end_date='2025-01-02',
                             roi_lat_lon={'N': 40.1, 'S': 39.9, 'E': -3.0, 'W': -3.5},
                             platform='SENTINEL-3', product_type='OL_1_EFR___', cloud=50)
    monkeypatch.setattr(sentinel, 'session', session)
    df = sentinel.search_by_parameters()
    assert isinstance(df, pd.DataFrame)
    assert "POLYGON((-3.5 39.9" in session.last_url  # polygon definition present
    # For Sentinel-3 the cloud filter is not added
    assert "cloudCover" not in session.last_url