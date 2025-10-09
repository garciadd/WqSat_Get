# tests/integration/test_integration_get_keycloak.py

import os
import pytest
from wqsat_get.sentinel_get import SentinelGet

# Este marker hace que se salte el test si la variable de entorno RUN_INTEGRATION_TESTS no está definida.
pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Skipping integration tests because RUN_INTEGRATION_TESTS is not set."
)

def test_integration_credentials():
    """
    Test de integración para get_keycloak.
    
    Este test crea una instancia de Download y realiza una llamada real al endpoint de Keycloak.
    Se asume que en el entorno de integración se tienen credenciales válidas configuradas.
    """
    # Se pueden pasar parámetros mínimos, ya que get_keycloak solo usa las credenciales cargadas.
    download_instance = SentinelGet(tile="dummy_tile")
    
    # Realiza la solicitud real para obtener el token.
    token = download_instance.get_keycloak()
    
    # Verifica que se haya obtenido un token no vacío.
    assert isinstance(token, str) and len(token) > 0, "El token de Keycloak es vacío o inválido."

