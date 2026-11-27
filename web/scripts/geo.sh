#!/usr/bin/env bash
# arma lib/argentina.topo.json: las seis regiones del ipc, los limites de provincia y un
# recuadro del gba por partido. fuente: IGN (SIG 250, via CONAE), en geojson por mgaitan.
# solo hace falta correrlo si cambia la fuente o la simplificacion: el resultado se sube
set -euo pipefail
cd "$(dirname "$0")"
COMMIT=a3b3e106ac0b16ac9531c24539e6dc662ba8add1
FUENTE=fuente/departamentos-argentina.json
TMP=$(mktemp -d)
mkdir -p fuente
if [ ! -f "$FUENTE" ]; then
  curl -sSfL -o "$FUENTE" \
    "https://raw.githubusercontent.com/mgaitan/departamentos_argentina/$COMMIT/departamentos-argentina.json"
fi
MS="npx --no-install mapshaper"

# en la fuente los nombres de dos departamentos de tierra del fuego estan cruzados: el que dice
# "islas malvinas" es el sector antartico y el que dice "islas del atlantico sur" trae las
# malvinas y las georgias. me quedo con las malvinas; lo demas no entra en la escala del mapa
$MS -i "$FUENTE" \
  -require ./regiones.cjs \
  -filter "departamento !== 'ISLAS MALVINAS'" \
  -explode \
  -filter "departamento !== 'ISLAS DEL ATLANTICO SUR' || (this.bounds[0] > -62 && this.bounds[2] < -57)" \
  -each "if (departamento === 'ISLAS DEL ATLANTICO SUR') departamento = 'ISLAS MALVINAS'" \
  -dissolve id copy-fields=provincia,departamento \
  -each "region = CONURBANO.has(departamento) && provincia === 'BUENOS AIRES' ? 'GBA' : PROVINCIA[provincia]" \
  -clean \
  -o "$TMP/base.json"

# pais entero, bien simplificado
$MS -i "$TMP/base.json" -simplify weighted 1.2% keep-shapes -clean \
  -dissolve region -rename-layers regiones -o "$TMP/regiones.json"
$MS -i "$TMP/base.json" -simplify weighted 1.2% keep-shapes \
  -dissolve provincia -innerlines -rename-layers provincias -o "$TMP/provincias.json"

# recuadro del gba: ciudad y partidos de alrededor, con mas detalle
$MS -i "$TMP/base.json" -clip bbox=-59.05,-35.0,-58.0,-34.28 \
  -simplify weighted 18% keep-shapes -clean -filter-fields region,departamento \
  -o "$TMP/partidos.json"
$MS -i "$TMP/partidos.json" -dissolve region -rename-layers gba_regiones -o "$TMP/gba_regiones.json"
$MS -i "$TMP/partidos.json" -innerlines -rename-layers gba_limites -o "$TMP/gba_limites.json"

$MS -i "$TMP/regiones.json" "$TMP/provincias.json" "$TMP/gba_regiones.json" "$TMP/gba_limites.json" \
  combine-files -o format=topojson quantization=1e5 ../lib/argentina.topo.json force
rm -rf "$TMP"
