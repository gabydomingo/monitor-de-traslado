import pandas as pd

from monitor.informes import leer_listado


def bloque(fecha, titulo, archivo, copete=""):
    return f"""
  <div class="row">
    <div class="col-lg-9"><div>{fecha}</div>
      <div class="mb-3"><span class="font-bold">{titulo}</span></div>
      <div><span class="copete">{copete}</span></div>
    </div>
    <div class="col-lg-3">
      <a class="btn" href="/uploads/informesdeprensa/{archivo}">pdf</a>
    </div>
  </div>"""


HTML = (
    '<div id="resultadosbusqueda">'
    + bloque("17/11/2026", "SIPM", "ipm_11_26ABC123.pdf", "El IPIM subio 1,6%")
    + bloque("25/11/2026", "Supermercados", "super_11_26X.pdf")
    + bloque("15/02/2018", "SIPM, base 1993 = 100", "ipm_02_18.pdf")
    + bloque("13/11/2026", "IPC", "ipc_11_26F00.pdf")
    + "</div>"
)


def test_lee_solo_mayorista_e_ipc_desde_la_base_nueva():
    df = leer_listado(HTML)
    # supermercados no va, y el mayorista de feb-2018 es de la base 1993
    assert df["archivo"].tolist() == ["ipc_11_26F00.pdf", "ipm_11_26ABC123.pdf"]
    ipm = df[df["tipo"] == "ipm"].iloc[0]
    assert ipm["publicado"] == pd.Timestamp("2026-11-17")
    assert "1,6%" in ipm["resumen"]
    assert ipm["url"] == "/uploads/informesdeprensa/ipm_11_26ABC123.pdf"
