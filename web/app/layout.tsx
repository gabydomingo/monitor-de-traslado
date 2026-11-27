import type { Metadata, Viewport } from "next";
import "@fontsource/public-sans/latin-400.css";
import "@fontsource/public-sans/latin-600.css";
import "@fontsource/public-sans/latin-700.css";
import "@fontsource-variable/source-serif-4/opsz.css";
import "./globals.css";

// vercel pasa el dominio de produccion en el build; las vistas previas de links lo necesitan
const sitio = process.env.VERCEL_PROJECT_PRODUCTION_URL
  ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
  : "http://localhost:3000";

const descripcion =
  "Cuanto de lo que sube en el mayorista llega a la gondola, region por region, con un pronostico del mes que viene y cuanto le erra. Datos del INDEC y del BCRA, actualizados solos.";

export const metadata: Metadata = {
  metadataBase: new URL(sitio),
  title: "Efecto Gondola",
  description: descripcion,
  openGraph: {
    title: "Efecto Gondola",
    description: descripcion,
    type: "website",
    locale: "es_AR",
  },
  twitter: { card: "summary_large_image" },
};

export const viewport: Viewport = { themeColor: "#FAF9F6" };

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es-AR">
      <body className="bg-papel text-tinta antialiased">{children}</body>
    </html>
  );
}
