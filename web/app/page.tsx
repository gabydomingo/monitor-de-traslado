import { cargar } from "@/lib/datos";
import { armarMapa } from "@/lib/mapa";
import { Monitor } from "@/componentes/Monitor";
import { Cabecera, ComoSeActualiza, ElIndecNoCorrige, Metodologia, Pie } from "@/componentes/Secciones";

// todo se arma en el build. lo interactivo (region, rubro, graficos) corre en el navegador
export default function Pagina() {
  const { resumen, series, backtest } = cargar();
  const mapa = armarMapa();
  return (
    <>
      <Cabecera resumen={resumen} />
      <main>
        <Monitor resumen={resumen} series={series} backtest={backtest} mapa={mapa} />
        <ComoSeActualiza resumen={resumen} />
        <ElIndecNoCorrige resumen={resumen} />
        <Metodologia resumen={resumen} />
      </main>
      <Pie resumen={resumen} />
    </>
  );
}
