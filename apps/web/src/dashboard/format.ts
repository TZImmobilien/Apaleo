const de = "de-DE";

export const formatCurrency = (value: number | null | undefined, currency = "EUR"): string =>
  value === null || value === undefined
    ? "–"
    : new Intl.NumberFormat(de, { style: "currency", currency, maximumFractionDigits: 0 }).format(value);

export const formatCurrencyPrecise = (value: number | null | undefined, currency = "EUR"): string =>
  value === null || value === undefined
    ? "–"
    : new Intl.NumberFormat(de, { style: "currency", currency, maximumFractionDigits: 2 }).format(value);

export const formatNumber = (value: number | null | undefined, digits = 0): string =>
  value === null || value === undefined
    ? "–"
    : new Intl.NumberFormat(de, { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(value);

export const formatPercent = (value: number | null | undefined, digits = 1): string =>
  value === null || value === undefined ? "–" : `${formatNumber(value, digits)} %`;

export const formatDelta = (value: number | null | undefined): string =>
  value === null || value === undefined ? "–" : `${value > 0 ? "+" : ""}${formatNumber(value, 1)} %`;

export const formatNights = (value: number | null | undefined): string =>
  value === null || value === undefined ? "–" : `${formatNumber(value, 1)} Nächte`;

const monthName = new Intl.DateTimeFormat(de, { month: "short" });
const monthNameFull = new Intl.DateTimeFormat(de, { month: "long", year: "numeric" });

/** "2026-11" -> "Nov 26" */
export const monthLabel = (key: string): string => {
  const [year, month] = key.split("-").map(Number);
  return `${monthName.format(new Date(Date.UTC(year, month - 1, 1)))} ${String(year).slice(2)}`;
};

/** "2026-11" -> "November 2026" */
export const monthLabelLong = (key: string): string => {
  const [year, month] = key.split("-").map(Number);
  return monthNameFull.format(new Date(Date.UTC(year, month - 1, 1)));
};

export const shortLabel = (purpose: string | null): string => purpose ?? "Ohne Angabe";
