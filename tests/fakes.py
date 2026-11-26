"""Api del indec de mentira para los tests."""


class Respuesta:
    def __init__(self, datos=None, status=200, headers=None):
        self._datos = datos if datos is not None else []
        self.status_code = status
        self.headers = headers or {}
        self.text = str(datos)

    def json(self):
        return self._datos


class SesionFalsa:
    """Hace de requests.Session."""

    def __init__(self, filas=None, programadas=None):
        self.filas = filas or []
        self.programadas = list(programadas or [])  # se devuelven primero, en orden
        self.headers = {}
        self.llamadas = []

    def get(self, url, params=None, headers=None, timeout=None):
        params = params or {}
        self.llamadas.append({"url": url, "params": params, "headers": headers})
        if self.programadas:
            return self.programadas.pop(0)

        filas = self.filas
        filtro = params.get("periodo", "")
        if filtro.startswith("gte."):
            desde = int(filtro[4:])
            filas = [f for f in filas if int(f["periodo"]) >= desde]
        if (headers or {}).get("Prefer") == "count=exact":
            return Respuesta(filas[:1], headers={"Content-Range": f"0-0/{len(filas)}"})
        if params.get("select") == "periodo":
            return Respuesta([{"periodo": max(int(f["periodo"]) for f in filas)}])
        offset, limite = params.get("offset", 0), params.get("limit", 1000)
        return Respuesta(filas[offset : offset + limite])


def fila_ipc(codigo="01", region="GBA", periodo=202610, valor=100.0, tipo="Indice"):
    return {
        "clasificador": "COICOP Argentina 2019",
        "nivel": "Divisi\u00f3n",  # la api lo manda con tilde
        "codigo": codigo,
        "descripcion": f"rubro {codigo}",
        "periodo": periodo,
        "anio": periodo // 100,
        "mes": periodo % 100,
        "indicador": "IPC base Dic16=100",
        "tipo_de_indicador": tipo,
        "tipo_de_indicador_descripcion": "x",
        "region": region,
        "unidad_de_medida": "Unidad",
        "valor": valor,
        "valor_null": None,
        "observaciones": None,
    }
