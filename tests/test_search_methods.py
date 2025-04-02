# tests/test_search_methods.py

import pandas as pd
import pytest
import requests
from wqsat_get.sentinel_get import Download

# Clase auxiliar para simular la respuesta de requests
class DummyResponse:
    def __init__(self, json_data, status_code, headers=None, content=b""):
        self._json_data = json_data
        self.status_code = status_code
        self._headers = headers or {}
        self.content = content

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError(f"HTTP Error: {self.status_code}")

    @property
    def headers(self):
        return self._headers

def test_search_by_name(monkeypatch):
    """
    Prueba que search_by_name devuelva un DataFrame con los datos esperados.
    """
    # Creamos la instancia pasando el parámetro 'tile'
    download_instance = Download(tile="dummyTile")
    
    # Simulamos la respuesta JSON que devolvería la API
    dummy_json = {"value": [{"Id": "1", "Name": "dummyTile", "Online": True}]}
    
    def dummy_get(url):
        return DummyResponse(dummy_json, 200)
    
    # Reemplazamos el método get de la sesión por nuestro dummy_get
    monkeypatch.setattr(download_instance.session, "get", dummy_get)
    
    df = download_instance.search_by_name()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["Name"] == "dummyTile"

def test_search_by_list(monkeypatch):
    """
    Prueba que search_by_list devuelva un DataFrame con los datos esperados.
    """
    # Creamos la instancia pasando una lista de tiles
    tiles = ["tileA", "tileB"]
    download_instance = Download(tiles_list=tiles)
    
    # Simulamos la respuesta JSON para una búsqueda por lista
    dummy_json = {
        "value": [
            {"Id": "2", "Name": "tileA", "Online": True},
            {"Id": "3", "Name": "tileB", "Online": True}
        ]
    }
    
    def dummy_post(url, json, headers):
        # Podemos validar que el payload contenga la lista de tiles si se desea
        return DummyResponse(dummy_json, 200)
    
    # Reemplazamos el método post de la sesión por nuestro dummy_post
    monkeypatch.setattr(download_instance.session, "post", dummy_post)
    
    df = download_instance.search_by_list()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert set(df["Name"].tolist()) == set(tiles)

def test_search_by_parameters(monkeypatch):
    """
    Prueba que search_by_parameters devuelva un DataFrame con los datos esperados.
    """
    # Creamos la instancia pasando todos los parámetros necesarios
    download_instance = Download(
        start_date="2025-01-01",
        end_date="2025-01-31",
        coordinates=(40.0, -3.0),  # Se generará un POINT con estas coordenadas
        platform="SENTINEL-2",
        product_type="S2MSI2A",
        cloud=50
    )
    
    # Simulamos la respuesta JSON para la búsqueda por parámetros
    dummy_json = {"value": [{"Id": "4", "Name": "paramTile", "Online": True}]}
    
    def dummy_get(url):
        return DummyResponse(dummy_json, 200)
    
    # Reemplazamos el método get de la sesión por nuestro dummy_get
    monkeypatch.setattr(download_instance.session, "get", dummy_get)
    
    df = download_instance.search_by_parameters()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["Name"] == "paramTile"

