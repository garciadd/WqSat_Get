# tests/test_download.py

import os
import shutil
import pandas as pd
import pytest
import requests
from wqsat_get.sentinel_get import SentinelGet

# --- Clases Dummy para simular respuestas y dependencias ---

class DummyResponse:
    """
    Simula el objeto Response de requests.
    """
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

    def iter_content(self, chunk_size=1024):
        # Simula la iteración sobre el contenido en chunks.
        yield self.content

class DummySession:
    """
    Sesión dummy para reemplazar requests.Session en el método download().
    """
    def __init__(self):
        self.headers = {}

    def head(self, url, allow_redirects=False):
        # Simula una redirección para obtener la URL real de descarga.
        return DummyResponse({}, 302, headers={'Location': 'http://dummy_download_url'})

    def get(self, url, stream=False):
        # Simula una respuesta exitosa de descarga con contenido.
        headers = {'content-length': '10'}
        return DummyResponse({}, 200, headers=headers, content=b'1234567890')

class DummyUtils:
    """
    Funciones dummy para reemplazar las de wqsat_get.utils.
    """
    @staticmethod
    def validate_download_inputs(params):
        # Para los tests asumimos que la validación es exitosa.
        pass

    @staticmethod
    def load_data_path():
        # Usamos un directorio temporal para los tests.
        return "temp_download_test"

    @staticmethod
    def load_credentials():
        # Retornamos credenciales dummy.
        return {'sentinel': {'user': 'dummy', 'password': 'dummy'}}

    @staticmethod
    def open_compressed(byte_stream, file_format, output_folder):
        # Simula la extracción creando un archivo dummy.
        file_path = os.path.join(output_folder, "dummy_extracted.txt")
        os.makedirs(output_folder, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(byte_stream)

# --- Fixtures para parchear las funciones de utils ---
@pytest.fixture(autouse=True)
def alias_get_keycloak(monkeypatch):
    """
    Compatibilidad retroactiva: en la librería actual el método se llama
    `get_keycloak_token`. Creamos un alias `get_keycloak` en la clase
    para que los tests que lo invocan sigan funcionando.
    """
    try:
        # Si ya existe, no hacemos nada
        getattr(SentinelGet, "get_keycloak")
    except AttributeError:
        # Crear alias a nivel de clase (no tocamos la librería, sólo los tests)
        monkeypatch.setattr(
            SentinelGet,
            "get_keycloak",
            SentinelGet.get_keycloak_token,
            raising=False,
        )
@pytest.fixture(autouse=True)
def patch_utils(monkeypatch, tmp_path):
    """
    Parchea las funciones de wqsat_get.utils para que usen las versiones dummy.
    """
    import wqsat_get.utils as utils

     # Los tests antiguos esperaban validate_download_inputs → usa el validador real como alias
    monkeypatch.setattr(utils, "validate_download_inputs", utils.validate_inputs, raising=False)
    # Los tests antiguos esperaban load_data_path → devuelve un path temporal controlado en cada test
    import tempfile
    tmp_dir = tempfile.mkdtemp(prefix="wqsat_test_")
    monkeypatch.setattr(utils, "load_data_path", lambda: tmp_dir, raising=False)
    yield

@pytest.fixture
def clean_output_dir():
    """
    Asegura que el directorio de salida esté limpio antes de cada test.
    """
    output_path = DummyUtils.load_data_path()
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    yield
    if os.path.exists(output_path):
        shutil.rmtree(output_path)

@pytest.fixture
def download_instance(tmp_path, clean_output_dir):
    """
    Crea una instancia de SentinelGet con parámetros mínimos para probar search_by_name.
    Se pasan credenciales dummy (requeridas por la API actual) y un output_dir temporal.
    """
    outdir = tmp_path / "out"
    outdir.mkdir(parents=True, exist_ok=True)
    return SentinelGet(
        credentials={"username": "dummy", "password": "dummy"},
        tile="TestTile",
        output_dir=str(outdir)
    )

# --- Tests para la clase Download ---

def test_init_missing_credentials(monkeypatch):
    """
    Verifica que si las credenciales son inválidas, se lance ValueError.
    (Adaptado a la API actual: el constructor valida credenciales)
    """
    with pytest.raises(ValueError):
        SentinelGet(credentials={}, tile="X")

def test_get_keycloak_success(monkeypatch, download_instance):
    """
    Simula que get_keycloak obtiene correctamente un token.
    """
    def dummy_post(url, data):
        return DummyResponse({"access_token": "dummy_token"}, 200)
    monkeypatch.setattr(requests, "post", dummy_post)
    token = download_instance.get_keycloak()
    assert token == "dummy_token"

def test_get_keycloak_failure(monkeypatch, download_instance):
    """
    Simula que get_keycloak falla al no recibir token en la respuesta.
    """
    def dummy_post(url, data):
        return DummyResponse({}, 200)
    monkeypatch.setattr(requests, "post", dummy_post)
    with pytest.raises(ValueError, match="Failed to retrieve access token"):
        download_instance.get_keycloak()

def test_search_by_name(monkeypatch, download_instance):
    """
    Prueba que search_by_name retorne un DataFrame a partir de una respuesta dummy.
    """
    dummy_json = {"value": [{"Id": "1", "Name": "TestTile", "Online": True}]}
    def dummy_get(url):
        return DummyResponse(dummy_json, 200)
    monkeypatch.setattr(download_instance.session, "get", dummy_get)
    df = download_instance.search_by_name()
    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]["Name"] == "TestTile"

def test_download_no_results(monkeypatch, download_instance):
    """
    Simula que search() retorna un DataFrame vacío, por lo que download() debe retornar listas vacías.
    """
    monkeypatch.setattr(download_instance, "search", lambda: pd.DataFrame())
    # download() llama internamente a get_keycloak_token(), no a get_keycloak
    monkeypatch.setattr(download_instance, "get_keycloak_token", lambda: "dummy_token")    
    downloaded, pending = download_instance.download()
    assert downloaded == []
    assert pending == []

def test_download_offline(monkeypatch, download_instance):
    """
    Simula que el producto está offline para que se agregue a la lista de pendientes.
    """
    df = pd.DataFrame([{"Id": "1", "Name": "OfflineTile", "Online": False}])
    monkeypatch.setattr(download_instance, "search", lambda: df)
    monkeypatch.setattr(download_instance, "get_keycloak_token", lambda: "dummy_token")
    downloaded, pending = download_instance.download()
    assert pending == ["OfflineTile"]
    assert downloaded == []

def test_download_already_downloaded(monkeypatch, download_instance):
    """
    Simula que el producto ya fue descargado (archivo existente) y por ello se agrega a descargados.
    """
    df = pd.DataFrame([{"Id": "1", "Name": "AlreadyTile", "Online": True}])
    monkeypatch.setattr(download_instance, "search", lambda: df)
    monkeypatch.setattr(download_instance, "get_keycloak_token", lambda: "dummy_token")
    
    original_exists = os.path.exists
    monkeypatch.setattr(os.path, "exists", lambda path: True if "AlreadyTile" in path else original_exists(path))
    
    downloaded, pending = download_instance.download()
    assert "AlreadyTile" in downloaded
    assert pending == []

