import Chart from "chart.js/auto";
import { Bar, Doughnut, Line } from "react-chartjs-2";

import { formatCurrency, formatNumber, formatPercent, monthLabel } from "./format";
import type { MonthEntry, RevenueRow, TravelPurpose } from "./types";

const PAST_BAR = "rgb(51 65 85)";
const CURRENT_BAR = "rgb(217 119 6)";
const FUTURE_BAR = "rgb(125 211 252)";
const ADR_LINE = "rgb(234 88 12)";
const OCC_LINE = "rgb(22 163 74)";
const REVPAR_LINE = "rgb(37 99 235)";

const baseOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: "bottom" as const } },
};

const barColor = (entry: MonthEntry) =>
  entry.is_future ? FUTURE_BAR : entry.is_current ? CURRENT_BAR : PAST_BAR;

export const RevenueTimelineChart = ({ timeline, currency }: { timeline: MonthEntry[]; currency: string }) => (
  <div className="h-72">
    <Bar
      options={{
        ...baseOptions,
        scales: {
          revenue: { type: "linear" as const, position: "left" as const, ticks: { callback: (v) => formatCurrency(Number(v), currency) } },
          rate: { type: "linear" as const, position: "right" as const, grid: { drawOnChartArea: false } },
        },
      }}
      data={{
        labels: timeline.map((entry) => monthLabel(entry.month)),
        datasets: [
          {
            label: "Umsatz (brutto)",
            data: timeline.map((entry) => entry.revenue_gross),
            backgroundColor: timeline.map(barColor),
            yAxisID: "revenue",
          },
          {
            type: "line" as const,
            label: "ADR",
            data: timeline.map((entry) => entry.adr_gross),
            borderColor: ADR_LINE,
            backgroundColor: ADR_LINE,
            yAxisID: "rate",
            tension: 0.3,
          },
          {
            type: "line" as const,
            label: "RevPAR",
            data: timeline.map((entry) => entry.revpar),
            borderColor: REVPAR_LINE,
            backgroundColor: REVPAR_LINE,
            yAxisID: "rate",
            tension: 0.3,
          },
        ],
      }}
    />
  </div>
);

export const OccupancyChart = ({ timeline }: { timeline: MonthEntry[] }) => (
  <div className="h-64">
    <Bar
      options={{
        ...baseOptions,
        scales: {
          occupancy: { type: "linear" as const, position: "left" as const, suggestedMax: 100, ticks: { callback: (v) => `${v} %` } },
          revpar: { type: "linear" as const, position: "right" as const, grid: { drawOnChartArea: false } },
        },
      }}
      data={{
        labels: timeline.map((entry) => monthLabel(entry.month)),
        datasets: [
          {
            type: "line" as const,
            label: "Auslastung",
            data: timeline.map((entry) => entry.occupancy),
            borderColor: OCC_LINE,
            backgroundColor: OCC_LINE,
            yAxisID: "occupancy",
            tension: 0.3,
          },
          {
            label: "RevPAR",
            data: timeline.map((entry) => entry.revpar),
            backgroundColor: timeline.map((entry) => `${barColor(entry)}99`),
            yAxisID: "revpar",
          },
        ],
      }}
    />
  </div>
);

export const FutureChart = ({ timeline, currency }: { timeline: MonthEntry[]; currency: string }) => {
  const future = timeline.filter((entry) => entry.is_future);
  return (
    <div className="h-64">
      <Bar
        options={{
          ...baseOptions,
          scales: {
            revenue: { type: "linear" as const, position: "left" as const, ticks: { callback: (v) => formatCurrency(Number(v), currency) } },
            occupancy: { type: "linear" as const, position: "right" as const, suggestedMax: 100, grid: { drawOnChartArea: false }, ticks: { callback: (v) => `${v} %` } },
          },
        }}
        data={{
          labels: future.map((entry) => monthLabel(entry.month)),
          datasets: [
            {
              label: "Umsatz on the books",
              data: future.map((entry) => entry.revenue_gross),
              backgroundColor: FUTURE_BAR,
              yAxisID: "revenue",
            },
            {
              type: "line" as const,
              label: "Auslastung on the books",
              data: future.map((entry) => entry.occupancy),
              borderColor: OCC_LINE,
              backgroundColor: OCC_LINE,
              yAxisID: "occupancy",
              tension: 0.3,
            },
          ],
        }}
      />
    </div>
  );
};

const DONUT_COLORS = ["rgb(51 65 85)", "rgb(217 119 6)", "rgb(22 163 74)", "rgb(37 99 235)", "rgb(190 24 93)"];

export const PurposeDonut = ({ purposes }: { purposes: TravelPurpose[] }) => (
  <div className="mx-auto h-56 max-w-sm">
    <Doughnut
      options={{ ...baseOptions, plugins: { ...baseOptions.plugins, tooltip: { enabled: true } } }}
      data={{
        labels: purposes.map((entry) => entry.purpose ?? "Ohne Angabe"),
        datasets: [
          {
            data: purposes.map((entry) => entry.count ?? 0),
            backgroundColor: purposes.map((_, index) => DONUT_COLORS[index % DONUT_COLORS.length]),
          },
        ],
      }}
    />
  </div>
);

export const BreakdownTable = ({ rows, currency }: { rows: RevenueRow[]; currency: string }) => (
  <table className="w-full text-sm">
    <thead>
      <tr className="border-b text-left text-slate-500">
        <th className="py-2 font-medium">Erlöskonto</th>
        <th className="py-2 text-right font-medium">Netto</th>
        <th className="py-2 text-right font-medium">Brutto</th>
      </tr>
    </thead>
    <tbody>
      {rows.map((row) => (
        <tr key={`${row.level}-${row.number}`} className={row.level === 0 ? "border-b font-medium" : "text-slate-600"}>
          <td className="py-1.5 pl-0" style={{ paddingLeft: row.level === 0 ? 0 : "1.25rem" }}>
            {row.account}
          </td>
          <td className="py-1.5 text-right tabular-nums">{formatCurrencyPrecise(row.net, currency)}</td>
          <td className="py-1.5 text-right tabular-nums">{formatCurrencyPrecise(row.gross, currency)}</td>
        </tr>
      ))}
    </tbody>
  </table>
);

export const TimelineTable = ({ timeline, currency }: { timeline: MonthEntry[]; currency: string }) => (
  <div className="overflow-x-auto">
    <table className="w-full min-w-max text-sm">
      <thead>
        <tr className="border-b text-right text-slate-500">
          <th className="py-2 pr-4 text-left font-medium">Monat</th>
          <th className="py-2 px-3 font-medium">Umsatz</th>
          <th className="py-2 px-3 font-medium">Δ Umsatz</th>
          <th className="py-2 px-3 font-medium">ADR</th>
          <th className="py-2 px-3 font-medium">RevPAR</th>
          <th className="py-2 px-3 font-medium">Auslastung</th>
          <th className="py-2 px-3 font-medium">Room Nights</th>
          <th className="py-2 px-3 font-medium">Anreisen</th>
          <th className="py-2 px-3 font-medium">Ø Aufenthalt</th>
          <th className="py-2 px-3 font-medium">Stornos</th>
        </tr>
      </thead>
      <tbody>
        {timeline.map((entry) => (
          <tr
            key={entry.month}
            className={`border-b tabular-nums ${entry.is_current ? "bg-amber-50 font-medium" : ""} ${entry.is_future ? "text-sky-700" : ""}`}
          >
            <td className="py-1.5 pr-4 text-left">
              {monthLabel(entry.month)}
              {entry.is_future ? " (OTB)" : ""}
            </td>
            <td className="py-1.5 px-3 text-right">{formatCurrency(entry.revenue_gross, currency)}</td>
            <td className="py-1.5 px-3 text-right">{entry.delta_revenue == null ? "–" : formatNumber(entry.delta_revenue, 1)}</td>
            <td className="py-1.5 px-3 text-right">{formatCurrencyPrecise(entry.adr_gross, currency)}</td>
            <td className="py-1.5 px-3 text-right">{formatCurrencyPrecise(entry.revpar, currency)}</td>
            <td className="py-1.5 px-3 text-right">{formatPercent(entry.occupancy)}</td>
            <td className="py-1.5 px-3 text-right">{formatNumber(entry.room_nights)}</td>
            <td className="py-1.5 px-3 text-right">{formatNumber(entry.arrivals)}</td>
            <td className="py-1.5 px-3 text-right">{entry.los == null ? "–" : formatNumber(entry.los, 1)}</td>
            <td className="py-1.5 px-3 text-right">{formatNumber(entry.cancellations)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
