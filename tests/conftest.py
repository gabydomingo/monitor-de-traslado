import pandas as pd
import pytest

from fakes import fila_ipc


@pytest.fixture
def conf_ipc():
    from monitor.config import cargar_config

    return cargar_config()["datasets"]["ipc"]


@pytest.fixture
def filas_ipc():
    # 12 rubros x 7 regiones x 4 meses = 336 filas
    regiones = ["Nacional", "GBA", "Pampeana", "Noreste", "Noroeste", "Cuyo", "Patagonia"]
    return [
        fila_ipc(f"{c:02d}", r, p, 100.0 + c)
        for p in (202607, 202608, 202609, 202610)
        for r in regiones
        for c in range(1, 13)
    ]


@pytest.fixture
def df_ipc(filas_ipc):
    return pd.DataFrame(filas_ipc)
