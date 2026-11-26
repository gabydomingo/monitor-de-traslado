"""Cliente para la API del INDEC."""

import contextlib
import logging
import time
from collections.abc import Callable

import requests

log = logging.getLogger(__name__)

REINTENTABLES = {429, 500, 502, 503, 504}
ESPERA_MAXIMA_SEG = 120
MAX_PAGINAS = 2000


class ErrorApi(RuntimeError):
    pass


class ClienteIndec:
    def __init__(
        self,
        base_url: str,
        token: str,
        limite_filas: int = 1000,
        timeout_seg: int = 60,
        reintentos: int = 3,
        session: requests.Session | None = None,
        dormir: Callable[[float], None] = time.sleep,
    ):
        self.base_url = base_url.rstrip("/")
        self.limite = limite_filas
        self.timeout = timeout_seg
        self.reintentos = reintentos
        self.session = session or requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.dormir = dormir  # en los tests lo piso para no esperar

    def _espera(self, intento: int, respuesta=None) -> float:
        # 5, 10, 20... salvo que la api mande Retry-After
        espera = 5.0 * 2**intento
        if respuesta is not None:
            with contextlib.suppress(ValueError):
                espera = float(respuesta.headers.get("Retry-After", ""))
        return min(espera, ESPERA_MAXIMA_SEG)

    def _get(self, endpoint: str, params: dict, headers: dict | None = None):
        url = f"{self.base_url}/{endpoint}"
        for intento in range(self.reintentos + 1):
            ultimo = intento == self.reintentos
            try:
                r = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout) as e:
                if ultimo:
                    raise ErrorApi(f"{endpoint}: sin respuesta despues de reintentar") from e
                espera = self._espera(intento)
                log.warning("%s: %s, reintento en %.0fs", endpoint, type(e).__name__, espera)
                self.dormir(espera)
                continue

            if r.status_code in REINTENTABLES and not ultimo:
                espera = self._espera(intento, r)
                log.warning("%s: status %s, reintento en %.0fs", endpoint, r.status_code, espera)
                self.dormir(espera)
                continue
            if r.status_code == 401:
                raise ErrorApi("401: el token es invalido o vencio")
            if r.status_code >= 400:
                raise ErrorApi(f"{endpoint}: status {r.status_code}: {r.text[:200]}")
            return r
        raise ErrorApi(f"{endpoint}: se agotaron los reintentos")

    def contar(self, endpoint: str, filtros: dict | None = None) -> int:
        r = self._get(endpoint, {**(filtros or {}), "limit": 1}, {"Prefer": "count=exact"})
        rango = r.headers.get("Content-Range", "")  # viene como 0-0/235683
        try:
            return int(rango.rsplit("/", 1)[1])
        except (IndexError, ValueError) as e:
            raise ErrorApi(f"{endpoint}: Content-Range inesperado {rango!r}") from e

    def ultimo_periodo(self, endpoint: str) -> int:
        params = {"select": "periodo", "order": "periodo.desc", "limit": 1}
        filas = self._get(endpoint, params).json()
        if not filas:
            raise ErrorApi(f"{endpoint}: no devolvio ninguna fila")
        return int(filas[0]["periodo"])

    def bajar(
        self, endpoint: str, filtros: dict, orden: list[str], esperadas: int | None = None
    ) -> list[dict]:
        # sin orden fijo la api puede repetir o saltear filas entre paginas.
        # el tope de paginas es por si algun dia ignora el offset y devuelve siempre lo mismo
        max_paginas = MAX_PAGINAS if esperadas is None else esperadas // self.limite + 2
        base = {**filtros, "order": ",".join(orden)}
        filas: list[dict] = []
        offset = 0
        for _ in range(max_paginas):
            pagina = self._get(endpoint, {**base, "limit": self.limite, "offset": offset}).json()
            filas.extend(pagina)
            if len(pagina) < self.limite:
                break
            offset += self.limite
        else:
            raise ErrorApi(f"{endpoint}: se pasaron las {max_paginas} paginas esperadas, corto")
        log.info("%s: %d filas en %d paginas", endpoint, len(filas), offset // self.limite + 1)
        return filas
