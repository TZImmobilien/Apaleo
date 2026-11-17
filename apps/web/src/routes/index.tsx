import { queryOptions, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { fetchBootstrap, fetchDashboard } from "../dashboard/api";
import {
  BreakdownTable,
  FutureChart,
  OccupancyChart,
  PurposeDonut,
  RevenueTimelineChart,
  TimelineTable,
} from "../dashboard/charts";
import { ErrorPanel, KpiCard, Section, Spinner, currentMonthCards } from "../dashboard/components";
import { formatCurrency, formatNumber, formatPercent, monthLabelLong } from "../dashboard/format";
import type { Bootstrap, DashboardData } from "../dashboard/types";

const PAST_MONTHS = 12;
const FUTURE_MONTHS = 9;

const bootstrapQuery = queryOptions({
  queryKey: ["apaleo", "bootstrap"],
  queryFn: fetchBootstrap,
  staleTime: 10 * 60 * 1000,
});

const dashboardQuery = (property: string) =>
  queryOptions({
    queryKey: ["apaleo", "dashboard", property],
    queryFn: () => fetchDashboard(property, PAST_MONTHS, FUTURE_MONTHS),
    staleTime: 5 * 60 * 1000,
  });

function PropertySelector({
  bootstrap,
  value,
  onChange,
}: {
  bootstrap: Bootstrap;
  value: string;
  onChange: (next: string) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="text-slate-500">Property</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:border-amber-500 focus:outline-none"
      >
        <option value="all">Alle Properties</option>
        {bootstrap.properties.map((property) => (
          <option key={property.id} value={property.id}>
            {property.name ?? property.id}
            {property.city ? ` · ${property.city}` : ""}
          </option>
        ))}
      </select>
    </label>
  );
}

function Dashboard({ bootstrap, data }: { bootstrap: Bootstrap; data: DashboardData }) {
  const { currency } = data;
  const current = data.current_month;
  const futureMonths = data.timeline.filter((entry) => entry.is_future);

  return (
    <main className="mx-auto flex max-w-7xl flex-col gap-6 p-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500">
            {bootstrap.account.name}
            {bootstrap.account.type ? ` · ${bootstrap.account.type}` : ""}
          </p>
          <h1 className="text-2xl font-semibold text-slate-900">Umsatzdashboard</h1>
          <p className="text-sm text-slate-500">
            Stand {new Date(data.today).toLocaleDateString("de-DE", { day: "2-digit", month: "long", year: "numeric" })}{" "}
            · Währung {currency}
          </p>
        </div>
      </header>

      <Section
        title={`Aktueller Monat · ${monthLabelLong(current.month)}`}
        subtitle="Monat bis heute (MTD); Werte laufender Tage können sich noch ändern"
      >
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {currentMonthCards(current, currency).map((card) => (
            <KpiCard key={card.label} {...card} />
          ))}
        </div>
        <div className="mt-5 grid gap-6 lg:grid-cols-2">
          <div>
            <h3 className="mb-2 text-sm font-medium text-slate-700">Erlöskonten (MTD)</h3>
            <BreakdownTable rows={data.revenue_breakdown} currency={currency} />
          </div>
          <div>
            <h3 className="mb-2 text-sm font-medium text-slate-700">Anreisen nach Reisegrund</h3>
            {data.travel_purpose.length > 0 ? (
              <PurposeDonut purposes={data.travel_purpose} />
            ) : (
              <p className="text-sm text-slate-500">Für „Alle Properties" steht diese Aufteilung nicht zur Verfügung.</p>
            )}
          </div>
        </div>
      </Section>

      <Section
        title="Historie & Ausblick"
        subtitle="12 Monate zurück, laufender Monat, 9 Monate on the books (OTB)"
      >
        <RevenueTimelineChart timeline={data.timeline} currency={currency} />
        <div className="mt-6">
          <OccupancyChart timeline={data.timeline} />
        </div>
        <div className="mt-6">
          <TimelineTable timeline={data.timeline} currency={currency} />
        </div>
      </Section>

      <Section title="Zukunft · On the books" subtitle="Bereits gebuchte Umsätze und Auslastung der kommenden Monate">
        {futureMonths.length > 0 ? (
          <>
            <FutureChart timeline={data.timeline} currency={currency} />
            <div className="mt-4">
              <TimelineTable timeline={futureMonths} currency={currency} />
            </div>
          </>
        ) : (
          <p className="text-sm text-slate-500">Keine Zukunftsmonate im Zeitraum.</p>
        )}
      </Section>

      <Section title={`Jahresübersicht ${data.year_overview.year}`} subtitle="Ist (Jahr bis heute) plus on-the-books-Prognose">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <KpiCard label="Umsatz YTD" value={formatCurrency(data.year_overview.ytd_revenue_gross, currency)} accent="amber" />
          <KpiCard label="Umsatz OTB" value={formatCurrency(data.year_overview.otb_revenue_gross, currency)} accent="sky" />
          <KpiCard
            label="Jahresprognose"
            value={formatCurrency(data.year_overview.forecast_revenue_gross, currency)}
            hint="YTD + OTB"
          />
          <KpiCard label="ADR YTD" value={formatCurrency(data.year_overview.ytd_adr, currency)} />
          <KpiCard label="RevPAR YTD" value={formatCurrency(data.year_overview.ytd_revpar, currency)} />
          <KpiCard label="Auslastung YTD" value={formatPercent(data.year_overview.ytd_occupancy)} />
          <KpiCard label="Ø Aufenthalt YTD" value={data.year_overview.ytd_los == null ? "–" : `${formatNumber(data.year_overview.ytd_los, 1)} Nächte`} />
          <KpiCard label="Room Nights YTD" value={formatNumber(data.year_overview.ytd_room_nights)} />
          <KpiCard label="Anreisen YTD" value={formatNumber(data.year_overview.ytd_arrivals)} />
          <KpiCard label="Stornierungen YTD" value={formatNumber(data.year_overview.ytd_cancellations)} />
        </div>
        <div className="mt-5">
          <TimelineTable timeline={data.year_overview.months} currency={currency} />
        </div>
      </Section>
    </main>
  );
}

function DashboardScreen() {
  const [property, setProperty] = useState("all");
  const queryClient = useQueryClient();

  const bootstrap = useQuery(bootstrapQuery);
  const dashboard = useQuery(dashboardQuery(property));

  if (bootstrap.isPending || dashboard.isPending) {
    return <Spinner label="Apaleo-Daten werden geladen … (erste Abfrage kann bis zu einer Minute dauern)" />;
  }
  if (bootstrap.isError) {
    return <ErrorPanel message={String(bootstrap.error)} />;
  }
  if (dashboard.isError) {
    return <ErrorPanel message={String(dashboard.error)} />;
  }
  if (!bootstrap.data || !dashboard.data) {
    return <Spinner label="Keine Daten" />;
  }

  return (
    <main className="min-h-full bg-slate-100">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-6 pt-6">
        <PropertySelector bootstrap={bootstrap.data} value={property} onChange={setProperty} />
        <button
          type="button"
          onClick={() => queryClient.invalidateQueries({ queryKey: ["apaleo", "dashboard", property] })}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm shadow-sm hover:bg-slate-50"
        >
          Aktualisieren
        </button>
      </div>
      <Dashboard bootstrap={bootstrap.data} data={dashboard.data} />
    </main>
  );
}

export const Route = createFileRoute("/")({
  component: DashboardScreen,
});
