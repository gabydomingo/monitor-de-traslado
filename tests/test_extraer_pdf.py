import re

import pytest

from monitor.extraer_pdf import NUM, filas_con_numeros, leer_ipc, leer_mayorista, numero

RAYA = "\u2013"


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("1,6 -0,1 ///", [1.6, -0.1, None]),
        ("- - -", [0.0, 0.0, 0.0]),  # mayorista: guion comun solo es cero
        # ipc 2017: dos rayas largas es cero y "raya 1,2" es negativo (verificado contra la api)
        (f"{RAYA} 1,2 {RAYA} 0,3 {RAYA} {RAYA} {RAYA} 0,2", [-1.2, -0.3, 0.0, -0.2]),
        (f"0,7 {RAYA} {RAYA} 0,6", [0.7, 0.0, 0.6]),
    ],
)
def test_numeros_con_las_convenciones_del_indec(texto, esperado):
    assert [numero(x) for x in re.findall(NUM, texto)] == esperado


def test_nombre_partido_en_dos_renglones():
    lineas = [
        "Vivienda, agua, electricidad, gas y otros",
        "2,0 2,7 1,6 2,8 1,6 -0,4 1,5",
        "combustibles",
        "Salud 4,8 5,3 4,3 3,9 4,8 4,9 4,2",
    ]
    filas = filas_con_numeros(lineas, 7)
    assert filas[0][0] == "Vivienda, agua, electricidad, gas y otros combustibles"
    assert filas[1][0] == "Salud"


PAGINA_MAYORISTA = """Cuadro 2. Sistema de indices de precios mayoristas. Variacion porcentual
respecto al mes anterior. Octubre de 2026*
Nivel general y divisiones IPIM IPIB IPP
%
Nivel general 1,6 1,5 1,5
Tabaco - - -
Productos importados 0,9 0,9 ///
Fuente: INDEC"""


def test_mayorista():
    filas = leer_mayorista(iter(["indice", PAGINA_MAYORISTA]), "ipm_11_26.pdf")
    assert {f["periodo"] for f in filas} == {202610}
    tabaco = [f for f in filas if f["nombre"] == "tabaco"]
    assert [f["valor"] for f in tabaco] == [0.0, 0.0, 0.0]
    assert filas[-1]["indicador"] == "IPP" and filas[-1]["valor"] is None


PAGINA_IPC = """Indice de precios al consumidor
Diciembre de 2018
Cuadro 1. Indice de precios al consumidor.
Region geografica del pais
Nivel general y divisiones Nacional
GBA Pampeana Noreste Noroeste Cuyo Patagonia
Porcentaje
Nivel general 2,6 2,5 2,7 2,6 2,6 2,8 2,7
Recreacion y cultura (1) 2,6 2,6 2,5 2,7 2,4 2,8 2,5
Nivel general 47,6 47,4 47,8 46,9 47,5 48,1 47,2
Recreacion y cultura (1) 43,4 43,0 44,1 42,0 43,9 44,0 43,1
Fuente: INDEC"""


def test_ipc_corta_en_la_tabla_anual_de_diciembre():
    filas = leer_ipc(iter([PAGINA_IPC]), "ipc_01_19.pdf")
    assert len(filas) == 2 * 7  # nivel general y recreacion, sin la tabla del anio
    assert {f["periodo"] for f in filas} == {201812}
    assert {f["nombre"] for f in filas} == {"nivel general", "recreacion y cultura"}
    nacional = [f["valor"] for f in filas if f["region"] == "Nacional"]
    assert nacional == [2.6, 2.6]
