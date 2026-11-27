import "server-only";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { geoConicConformal, geoMercator, geoPath, type GeoPermissibleObjects } from "d3-geo";
import { feature, mesh } from "topojson-client";
import type { Topology, GeometryCollection } from "topojson-specification";
import type { FeatureCollection, Feature, Geometry } from "geojson";
import type { RegionId } from "./colores";
import { ALTO, RECUADRO, type Mapa, type Trazo } from "./medidas";

export type { Mapa, Trazo };

// el mapa se dibuja en el build: al navegador llegan solo los trazos, sin d3 ni topojson


type Props = { region: RegionId };

export function armarMapa(): Mapa {
  const topo = JSON.parse(
    readFileSync(join(process.cwd(), "lib", "argentina.topo.json"), "utf8"),
  ) as Topology;
  const capa = (n: string) => topo.objects[n] as GeometryCollection<Props>;
  const regiones = feature(topo, capa("regiones")) as FeatureCollection<Geometry, Props>;
  const gba = feature(topo, capa("gba_regiones")) as FeatureCollection<Geometry, Props>;

  // conica conforme centrada en el pais, como los mapas del ign
  const proy = geoConicConformal()
    .parallels([-28, -48])
    .rotate([64, 0])
    .fitExtent(
      [
        [8, 8],
        [330, ALTO - 8],
      ],
      regiones,
    );
  const camino = geoPath(proy).digits(1);

  const zoom = geoMercator().fitExtent(
    [
      [RECUADRO.x + 1, RECUADRO.y + 1],
      [RECUADRO.x + RECUADRO.ancho - 1, RECUADRO.y + RECUADRO.alto - 1],
    ],
    { type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [caja()] } },
  );
  const caminoZoom = geoPath(zoom).digits(1);

  const soloGba = gba.features.find((f) => f.properties.region === "GBA") as Feature<Geometry, Props>;
  const [[x0, y0], [x1, y1]] = camino.bounds(soloGba);

  const trazo = (f: Feature<Geometry, Props>, c: typeof camino): Trazo => {
    const [x, y] = c.centroid(f as GeoPermissibleObjects);
    return { region: f.properties.region, d: c(f) ?? "", etiqueta: [r(x), r(y)] };
  };

  return {
    regiones: regiones.features.map((f) => trazo(f, camino)),
    provincias: camino(mesh(topo, capa("provincias"))) ?? "",
    recuadro: {
      regiones: gba.features.map((f) => trazo(f, caminoZoom)),
      limites: caminoZoom(mesh(topo, capa("gba_limites"))) ?? "",
    },
    marca: { x: r(x0 - 2), y: r(y0 - 2), ancho: r(x1 - x0 + 4), alto: r(y1 - y0 + 4) },
  };
}

// la misma caja con la que se recorto el gba en scripts/geo.sh
function caja(): [number, number][] {
  const [o, s, e, n] = [-59.05, -35.0, -58.0, -34.28];
  return [
    [o, s],
    [o, n],
    [e, n],
    [e, s],
    [o, s],
  ];
}

function r(v: number) {
  return Math.round(v * 10) / 10;
}
