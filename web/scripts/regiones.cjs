// provincia del IGN -> region del IPC. GBA es la ciudad mas los 24 partidos del conurbano
const PROVINCIA = {
  'CIUDAD AUTONOMA DE BUENOS AIRES': 'GBA', 'BUENOS AIRES': 'Pampeana', 'CORDOBA': 'Pampeana',
  'ENTRE RIOS': 'Pampeana', 'LA PAMPA': 'Pampeana', 'SANTA FE': 'Pampeana',
  'CHACO': 'Noreste', 'CORRIENTES': 'Noreste', 'FORMOSA': 'Noreste', 'MISIONES': 'Noreste',
  'CATAMARCA': 'Noroeste', 'JUJUY': 'Noroeste', 'LA RIOJA': 'Noroeste', 'SALTA': 'Noroeste',
  'SANTIAGO DEL ESTERO': 'Noroeste', 'TUCUMAN': 'Noroeste',
  'MENDOZA': 'Cuyo', 'SAN JUAN': 'Cuyo', 'SAN LUIS': 'Cuyo',
  'CHUBUT': 'Patagonia', 'NEUQUEN': 'Patagonia', 'RIO NEGRO': 'Patagonia',
  'SANTA CRUZ': 'Patagonia', 'TIERRA DEL FUEGO': 'Patagonia',
}
const CONURBANO = new Set([
  'ALMIRANTE BROWN', 'AVELLANEDA', 'BERAZATEGUI', 'ESTEBAN ECHEVERRIA', 'EZEIZA',
  'FLORENCIO VARELA', 'GENERAL SAN MARTIN', 'HURLINGHAM', 'ITUZAINGO', 'JOSE C PAZ',
  'LA MATANZA', 'LANUS', 'LOMAS DE ZAMORA', 'MALVINAS ARGENTINAS', 'MERLO', 'MORENO',
  'MORON', 'QUILMES', 'SAN FERNANDO', 'SAN ISIDRO', 'SAN MIGUEL', 'TIGRE',
  'TRES DE FEBRERO', 'VICENTE LOPEZ',
])
module.exports = { PROVINCIA, CONURBANO }
