import { readFileSync } from "node:fs";
import { join } from "node:path";
import { ImageResponse } from "next/og";
import { cargar } from "@/lib/datos";
import { armarMapa } from "@/lib/mapa";
import { ANCHO, ALTO, RECUADRO } from "@/lib/medidas";
import { COLOR_REGION } from "@/lib/colores";
import { NG } from "@/lib/consultas";
import { nombreMes, pct } from "@/lib/formato";

// la imagen que aparece al compartir el link. se arma en cada build, asi que trae el ultimo dato
export const dynamic = "force-static";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt =
  "Efecto Gondola: mapa de las regiones del IPC con la inflacion y el pronostico";

const fuente = (paquete: string, archivo: string) =>
  readFileSync(
    join(
      process.cwd(),
      "node_modules",
      "@fontsource",
      paquete,
      "files",
      archivo,
    ),
  );

export default function Imagen() {
  const { resumen } = cargar();
  const mapa = armarMapa();
  const { meta } = resumen;
  const ultimo = resumen.ultimoDato.find(
    (d) => d.region === "GBA" && d.rubro === NG,
  )!;
  const pron = resumen.pronosticos.find(
    (d) => d.region === "GBA" && d.rubro === NG,
  )!;
  const alto = 590;
  const ancho = Math.round((alto * ANCHO) / ALTO);

  return new ImageResponse(
    <div
      style={{
        display: "flex",
        width: "100%",
        height: "100%",
        background: "#FAF9F6",
        color: "#1A1A1A",
        padding: "48px 40px 40px 64px",
        fontFamily: "Public Sans",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          flexGrow: 1,
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div
            style={{
              fontFamily: "Source Serif",
              fontSize: 92,
              fontWeight: 700,
              letterSpacing: -2,
              lineHeight: 1,
            }}
          >
            Efecto Gondola
          </div>
          <div
            style={{
              fontSize: 30,
              color: "#595752",
              marginTop: 20,
              maxWidth: 600,
              lineHeight: 1.3,
            }}
          >
            Cuanto de lo que sube en el mayorista llega al precio que pagas,
            region por region.
          </div>
        </div>
        <div
          style={{
            display: "flex",
            borderTop: "2px solid #1A1A1A",
            paddingTop: 22,
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", width: 300 }}>
            <div
              style={{ fontSize: 22, color: "#595752" }}
            >{`Inflacion de ${nombreMes(meta.ultimoMes)}, GBA`}</div>
            <div
              style={{
                fontFamily: "Source Serif",
                fontSize: 64,
                fontWeight: 600,
              }}
            >
              {pct(ultimo.valor)}
            </div>
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              borderLeft: "1px solid #DFDDD5",
              paddingLeft: 28,
            }}
          >
            <div
              style={{ fontSize: 22, color: "#595752" }}
            >{`Pronostico para ${nombreMes(meta.mesPronosticado)}`}</div>
            <div
              style={{
                fontFamily: "Source Serif",
                fontSize: 64,
                fontWeight: 600,
              }}
            >
              {pct(pron.valor)}
            </div>
            <div style={{ fontSize: 20, color: "#595752" }}>
              {`8 de cada 10 veces: ${pct(pron.banda80[0])} a ${pct(pron.banda80[1])}`}
            </div>
          </div>
        </div>
      </div>
      <div style={{ display: "flex", position: "relative", marginTop: -20 }}>
        <svg width={ancho} height={alto} viewBox={`0 0 ${ANCHO} ${ALTO}`}>
          {mapa.regiones.map((t) => (
            <path key={t.region} d={t.d} fill={COLOR_REGION[t.region]} />
          ))}
          <path
            d={mapa.provincias}
            fill="none"
            stroke="#FAF9F6"
            strokeWidth={0.8}
          />
          <rect
            x={RECUADRO.x}
            y={RECUADRO.y}
            width={RECUADRO.ancho}
            height={RECUADRO.alto}
            fill="#FAF9F6"
            stroke="#1A1A1A"
            strokeWidth={1.2}
          />
          {mapa.recuadro.regiones.map((t) => (
            <path key={t.region} d={t.d} fill={COLOR_REGION[t.region]} />
          ))}
          <path
            d={mapa.recuadro.limites}
            fill="none"
            stroke="#FAF9F6"
            strokeWidth={0.6}
          />
          <line
            x1={mapa.marca.x + mapa.marca.ancho}
            y1={mapa.marca.y + mapa.marca.alto / 2}
            x2={RECUADRO.x}
            y2={RECUADRO.y + RECUADRO.alto / 2}
            stroke="#1A1A1A"
            strokeWidth={1}
          />
        </svg>
        {/* satori no dibuja texto dentro de un svg: la etiqueta va encima, en la misma escala */}
        <div
          style={{
            position: "absolute",
            left: Math.round((RECUADRO.x * alto) / ALTO),
            top: Math.round((RECUADRO.y * alto) / ALTO) - 30,
            fontSize: 22,
            fontWeight: 600,
            fontFamily: "Source Serif",
          }}
        >
          GBA
        </div>
      </div>
    </div>,
    {
      ...size,
      fonts: [
        {
          name: "Public Sans",
          data: fuente("public-sans", "public-sans-latin-400-normal.woff"),
          weight: 400,
        },
        {
          name: "Source Serif",
          data: fuente(
            "source-serif-4",
            "source-serif-4-latin-600-normal.woff",
          ),
          weight: 600,
        },
        {
          name: "Source Serif",
          data: fuente(
            "source-serif-4",
            "source-serif-4-latin-700-normal.woff",
          ),
          weight: 700,
        },
      ],
    },
  );
}
