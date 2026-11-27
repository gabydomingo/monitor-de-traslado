---
version: 1
slug: "web-app-page-tsx"
primary_target: "web/app/page.tsx"
related_targets: []
---

# Monitor (pagina unica)

Modo: Read, con un panel de Operate (mapa y selectores). Lector: publico general curioso, desde el celular. Tarea: entender en dos minutos como viene la inflacion en su region, que se espera para el mes que viene y cuanto confiar en eso. Prueba: datos reales del INDEC y del BCRA, el registro de pronosticos y el backtest. Restricciones: energia siempre marcada como contraste; ningun numero sin su rango; lo no significativo en gris.

## Direction contract

THESIS: Una pagina de periodismo de datos que se lee como una nota y se usa como un instrumento: el mapa de las seis regiones gobierna todo lo demas. Rechaza el tablero de tarjetas con KPIs y el hero centrado.

OWN-WORLD: Papel #FAF9F6 y #F2F0E9, tinta #1A1A1A y #595752, filetes de 1px #DFDDD5, sin sombras ni redondeos mayores a 2px. Okabe-Ito solo para regiones; ambar y celeste solo como relleno. El pronostico va en tinta: linea punteada y abanico gris, nunca en el azul de GBA. Source Serif 4 para titulos y cifras grandes, Public Sans para interfaz y tablas, cifras tabulares en todo.

STORY: El lector ve la inflacion de su region y el pronostico con su rango, toca otra region en el mapa o el selector y todo cambia junto; despues baja a un rubro, ve cuanto del mayorista llega y en cuantos meses, y termina sabiendo cuanto le erro el modelo y que el INDEC no corrige.

FIRST VIEWPORT: Arriba una linea de cabecera con el nombre y la fecha del dato. Debajo la franja de cuatro celdas divididas por filetes: ultimo dato, pronostico con banda, proximo dato del INDEC, selector de region. Debajo, a dos columnas, el mapa a la izquierda con el recuadro del GBA y el panel de la region a la derecha. En celular, franja en dos por dos y el mapa arriba del panel.

FORM: seed: none (pinned) - "Editorial Suizo (Swiss Data Journalism)", "Tokens de Diseno y Tipografia", "Paleta Accesible" del brief del usuario.

Interaccion firma: elegir una region en el mapa, el recuadro o el selector actualiza franja, panel y graficos en el mismo instante; transiciones secas de 150ms.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
