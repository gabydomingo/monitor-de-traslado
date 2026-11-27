# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Next.js (App Router) exportado como sitio estatico (`output: 'export'`), Tailwind CSS, Observable Plot para los graficos y d3-geo para el mapa en SVG. Deploy en Vercel. Sin servidor ni base de datos: los datos llegan como JSON livianos que genera el pipeline de Python (`monitor.web`) despues de cada actualizacion mensual.

## Users

Publico general curioso de Argentina que quiere entender como pega la inflacion en su region y en lo que compra: lee desde el celular, sin formacion en estadistica. Un reclutador o alguien de datos tambien tiene que poder entenderlo y encontrar el detalle tecnico si lo busca, pero no es el lector principal.

## Product Purpose

Mostrar cuanto y en cuanto tiempo una suba de precios mayoristas (SIPM) llega a la gondola (IPC), por rubro y por region, que se espera para el mes que viene y cuanto confiar en los datos del INDEC. Exito: que alguien sin formacion tecnica entienda en un par de minutos que esta pasando en su region y que tan seguro es el pronostico.

## Positioning

Cruza el mayorista con el IPC rubro por rubro y region por region, algo que el INDEC no publica asi. Pronostica con bandas de incertidumbre calibradas y muestra cuanto le erro antes. Guarda las versiones de los datos y reconstruye nueve anios de informes para comprobar que el INDEC no corrige sus variaciones mensuales.

## Operating Context

Se actualiza solo: la ingesta diaria baja INDEC y BCRA; cuando sale el mayorista del mes, el pipeline corre los modelos y regenera los JSON; Vercel publica. Repositorio publico en GitHub (gabydomingo/monitor-de-traslado) con notebooks que documentan cada analisis.

## Capabilities and Constraints

- Regiones del IPC: GBA, Pampeana, Noreste, Noroeste, Cuyo y Patagonia. El INDEC no publica por provincia: el mapa pinta las provincias por region y separa el conurbano (GBA) del resto de Buenos Aires (Pampeana).
- 19 rubros con correspondencia mayorista-gondola. Energia es tarifa regulada: aparece como contraste y lo dice siempre que aparece.
- El pronostico es de un mes, con bandas del 80% y del 90%. Puede errar, sobre todo con devaluaciones y en verduras; hay que decirlo.
- El traslado tiene intervalos: 57 de 132 estimaciones no son significativas y no se pueden mostrar como si lo fueran.
- Todo en espaniol rioplatense. Textos en lenguaje llano; la jerga (cuantiles, conformal, HC3) queda en Metodologia.
- Geometrias: IGN (SIG 250, via CONAE), convertidas a GeoJSON por github.com/mgaitan/departamentos_argentina.

## Brand Commitments

- Nombre publico: Efecto Gondola. Repositorio: Monitor de Traslado.
- Firma discreta al pie: "Un proyecto de Gabriel Domingo", con links a LinkedIn y GitHub.
- Tono sobrio y riguroso, de periodismo de datos. Nada de lenguaje de venta.

## Evidence on Hand

- Datos reales: IPC desde 2016 y mayorista desde 2015 (API del INDEC), dolar y REM (API del BCRA), 223 informes de prensa del INDEC.
- Resultados en `data/resultados/` y notebooks `01_eda` a `04_revisiones`.
- No hay testimonios, usuarios ni prensa: no inventarlos.

## Product Principles

- La incertidumbre siempre a la vista: ningun pronostico ni traslado sin su rango.
- Decir lo que el modelo no sabe y cuando fallo.
- Llano primero, tecnico a un clic.
- Cada numero con su fuente y su fecha.

## Accessibility & Inclusion

WCAG AA en contraste de textos. Colores distinguibles con daltonismo. Mapa usable con teclado y con un selector de region como alternativa. Todo funciona en celular.
