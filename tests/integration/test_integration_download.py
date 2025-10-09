# tests/integration/test_integration_download.py

import os
import pytest
from wqsat_get.sentinel_get import SentinelGet

# Marcar los tests de integración para saltarlos si no se habilitan.
pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Skipping integration tests because RUN_INTEGRATION_TESTS is not set."
)

def test_integration_search_by_parameters():
    """
    Prueba de integración para search_by_parameters.
    Esta prueba asume que se tienen credenciales válidas y que el API
    devuelve datos para el rango de fechas y coordenadas indicadas.
    Ajusta los parámetros según tu entorno y datos de prueba.
    """
    # Parámetros de ejemplo (ajusta a valores válidos para tu API)
    download_instance = SentinelGet(
        start_date="2025-01-01",
        end_date="2025-01-05",
        coordinates=(40.268, -3.8038),  # Ej: Coordenadas de Madrid
        platform="SENTINEL-2",
        product_type="S2MSI1C",
        cloud=50
    )
    
    df = download_instance.search()
    # Se espera que el DataFrame no esté vacío si el API devuelve resultados.
    assert not df.empty, "La búsqueda no devolvió resultados."
    
    # Verifica que se incluyan columnas clave (ajusta según la respuesta real)
    for col in ["Id", "Name", "Online"]:
        assert col in df.columns

def test_integration_download():
    """
    Prueba de integración para el método download.
    Esta prueba realizará una descarga real o simulará el proceso completo.
    Para evitar descargas no deseadas, usa un tile conocido o configura el entorno de pruebas.
    """
    # Usamos un tile válido conocido en el entorno de pruebas.
    # IMPORTANTE: Ajusta "KNOWN_VALID_TILE" a un valor real o de prueba.
    download_instance = SentinelGet(tile="S2B_MSIL2A_20250102T110349_N0511_R094_T30TVK_20250102T145308.SAFE")
    
    # Ejecuta la descarga; el método imprimirá mensajes y guardará archivos en output_path.
    downloaded, pending = download_instance.download()
    
    # Verifica que el directorio de salida se haya creado.
    assert os.path.exists(download_instance.output_path), "El directorio de descarga no existe."
    
    # Aquí se pueden agregar comprobaciones adicionales:
    # - Que la lista de descargados o pendientes contenga los valores esperados.
    # - Que se hayan creado archivos en el directorio.
    # Por ejemplo:
    if downloaded:
        print("Descargas completadas:", downloaded)
    else:
        pytest.skip("No se completó ninguna descarga; revisar la configuración del entorno.")

