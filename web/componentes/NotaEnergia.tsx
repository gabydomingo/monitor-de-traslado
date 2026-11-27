// va en cada grafico, tabla o selector donde aparece energia
export function NotaEnergia({ className = "" }: { className?: string }) {
  return (
    <p className={`mt-2 flex flex-wrap items-center gap-2 text-[0.8125rem] text-tinta-2 ${className}`}>
      <span className="inline-flex items-center gap-1.5 rounded-sm border border-filete px-1.5 py-0.5 text-xs">
        <svg aria-hidden viewBox="0 0 16 4" className="w-4">
          <line x1="0" y1="2" x2="16" y2="2" stroke="#6B7280" strokeWidth="2" strokeDasharray="4 3" />
        </svg>
        Tarifa regulada — referencia de contraste
      </span>
      <span>Electricidad y gas del hogar tienen tarifas reguladas: lo que suben no es traslado de mercado.</span>
    </p>
  );
}
