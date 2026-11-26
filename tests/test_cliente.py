import pytest
import requests

from monitor.cliente import ClienteIndec, ErrorApi

from fakes import Respuesta, SesionFalsa, fila_ipc


def cliente(sesion, **kw):
    esperas = []
    c = ClienteIndec("https://api.test/v1", "tok", session=sesion, dormir=esperas.append, **kw)
    return c, esperas


def test_manda_el_token():
    sesion = SesionFalsa([fila_ipc()])
    cliente(sesion)
    assert sesion.headers["Authorization"] == "Bearer tok"


def test_pagina_hasta_la_ultima_pagina():
    filas = [fila_ipc(periodo=202610, valor=i) for i in range(2500)]
    sesion = SesionFalsa(filas)
    c, _ = cliente(sesion)
    bajadas = c.bajar("ipc_nacional", {}, ["codigo", "periodo"])
    assert len(bajadas) == 2500
    offsets = [ll["params"]["offset"] for ll in sesion.llamadas]
    assert offsets == [0, 1000, 2000]
    # el orden tiene que ir en todas las paginas
    assert all(ll["params"]["order"] == "codigo,periodo" for ll in sesion.llamadas)


def test_pagina_exacta_hace_una_llamada_mas():
    sesion = SesionFalsa([fila_ipc() for _ in range(1000)])
    c, _ = cliente(sesion)
    assert len(c.bajar("x", {}, ["periodo"])) == 1000
    assert len(sesion.llamadas) == 2


def test_reintenta_con_429_y_respeta_retry_after():
    sesion = SesionFalsa(
        [fila_ipc()],
        programadas=[Respuesta(status=429, headers={"Retry-After": "7"})],
    )
    c, esperas = cliente(sesion)
    assert len(c.bajar("x", {}, ["periodo"])) == 1
    assert esperas == [7.0]


def test_espera_progresiva_sin_retry_after():
    sesion = SesionFalsa([fila_ipc()], programadas=[Respuesta(status=503)] * 2)
    c, esperas = cliente(sesion)
    c.bajar("x", {}, ["periodo"])
    assert esperas == [5.0, 10.0]


def test_se_rinde_despues_de_los_reintentos():
    sesion = SesionFalsa(programadas=[Respuesta(status=429)] * 10)
    c, esperas = cliente(sesion, reintentos=2)
    with pytest.raises(ErrorApi):
        c.bajar("x", {}, ["periodo"])
    assert len(esperas) == 2


def test_reintenta_si_se_corta_la_conexion():
    class SesionQueSeCorta(SesionFalsa):
        cortes = 1

        def get(self, *a, **kw):
            if self.cortes:
                self.cortes -= 1
                raise requests.ConnectionError("se corto")
            return super().get(*a, **kw)

    c, esperas = cliente(SesionQueSeCorta([fila_ipc()]))
    assert len(c.bajar("x", {}, ["periodo"])) == 1
    assert len(esperas) == 1


def test_401_no_se_reintenta():
    sesion = SesionFalsa(programadas=[Respuesta(status=401)])
    c, esperas = cliente(sesion)
    with pytest.raises(ErrorApi, match="token"):
        c.bajar("x", {}, ["periodo"])
    assert esperas == []


def test_contar_lee_content_range():
    sesion = SesionFalsa([fila_ipc() for _ in range(42)])
    c, _ = cliente(sesion)
    assert c.contar("x") == 42


def test_contar_falla_si_no_hay_content_range():
    sesion = SesionFalsa(programadas=[Respuesta([{}])])
    c, _ = cliente(sesion)
    with pytest.raises(ErrorApi, match="Content-Range"):
        c.contar("x")


def test_ultimo_periodo():
    sesion = SesionFalsa([fila_ipc(periodo=p) for p in (202608, 202610, 202609)])
    c, _ = cliente(sesion)
    assert c.ultimo_periodo("x") == 202610


def test_corta_si_la_api_ignora_el_offset():
    class SesionQueRepite(SesionFalsa):
        def get(self, url, params=None, headers=None, timeout=None):
            self.llamadas.append({"params": params})
            return Respuesta([fila_ipc()] * 1000)  # siempre la misma pagina

    sesion = SesionQueRepite()
    c, _ = cliente(sesion)
    with pytest.raises(ErrorApi, match="paginas"):
        c.bajar("x", {}, ["periodo"], esperadas=2500)
    assert len(sesion.llamadas) == 4  # 2500 // 1000 + 2


def test_espera_tiene_techo():
    sesion = SesionFalsa(
        [fila_ipc()], programadas=[Respuesta(status=429, headers={"Retry-After": "3600"})]
    )
    c, esperas = cliente(sesion)
    c.bajar("x", {}, ["periodo"])
    assert esperas == [120]
