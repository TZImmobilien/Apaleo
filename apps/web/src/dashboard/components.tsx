import { formatCurrency, formatDelta, formatNights, formatNumber, formatPercent } from "./format";

interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
  delta?: number | null;
  accent?: "default" | "amber" | "sky";
}

const accentClass = {
  default: "text-slate-900",
  amber: "text-amber-700",
  sky: "text-sky-700",
} as const;

export const KpiCard = ({ label, value, hint, delta, accent = "default" }: KpiCardProps) => (
  <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
    <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">{label}</p>
    <p className={`mt-1 text-2xl font-semibold tabular-nums ${accentClass[accent]}`}>{value}</p>
    <p className="mt-1 flex min-h-4 items-center gap-2 text-xs text-slate-500">
      {delta !== undefined && delta !== null && (
        <span className={delta >= 0 ? "font-medium text-emerald-700" : "font-medium text-rose-700"}>
          {formatDelta(delta)} vs. Vormonat
        </span>
      )}
      {hint && <span>{hint}</span>}
    </p>
  </div>
);

export const Section = ({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) => (
  <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
    <div className="mb-4">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
    </div>
    {children}
  </section>
);

export const Spinner = ({ label }: { label: string }) => (
  <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3 text-slate-500">
    <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
    <p className="text-sm">{label}</p>
  </div>
);

export const ErrorPanel = ({ message }: { message: string }) => (
  <div className="mx-auto my-10 max-w-xl rounded-lg border border-rose-200 bg-rose-50 p-5 text-sm text-rose-800">
    <p className="font-semibold">Daten konnten nicht geladen werden</p>
    <p className="mt-1">{message}</p>
  </div>
);

export const currentMonthCards = (
  entry: MonthEntry,
  currency: string,
): { label: string; value: string; hint?: string; accent?: "default" | "amber" | "sky" }[] => [
  { label: "Umsatz (brutto)", value: formatCurrency(entry.revenue_gross, currency), accent: "amber" },
  {
    label: "Übernachtungsumsatz",
    value: formatCurrency(entry.accommodation_revenue_gross, currency),
    hint: `Übrige Erlöse ${formatCurrency(entry.other_revenue_gross + entry.fnb_revenue_gross, currency)}`,
  },
  { label: "ADR", value: formatCurrency(entry.adr_gross, currency), hint: "Ø Tagesrate" },
  { label: "RevPAR", value: formatCurrency(entry.revpar, currency) },
  { label: "Auslastung", value: formatPercent(entry.occupancy) },
  { label: "Room Nights", value: formatNumber(entry.room_nights) },
  { label: "Anreisen", value: formatNumber(entry.arrivals), hint: `${formatNumber(entry.departures)} Abreisen` },
  { label: "Ø Aufenthaltsdauer", value: formatNights(entry.los) },
  {
    label: "Stornierungen",
    value: formatNumber(entry.cancellations),
    hint: `${formatNumber(entry.no_shows)} No-Shows`,
  },
];
