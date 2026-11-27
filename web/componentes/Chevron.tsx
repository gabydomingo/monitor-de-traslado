// la flecha de los select, dibujada: la del navegador cambia segun el sistema
export function Chevron({ className = "" }: { className?: string }) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 12 8"
      className={`pointer-events-none absolute top-1/2 right-1 w-3 -translate-y-1/2 ${className}`}
    >
      <path d="M1 1.5 6 6.5 11 1.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}
