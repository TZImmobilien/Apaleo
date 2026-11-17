export interface PropertyInfo {
  id: string;
  name: string | null;
  city: string | null;
  currency: string | null;
}

export interface Bootstrap {
  account: { name: string | null; code: string | null; type: string | null };
  today: string;
  properties: PropertyInfo[];
}

export interface MonthEntry {
  month: string;
  is_future: boolean;
  is_current: boolean;
  days_in_month: number;
  revenue_gross: number;
  revenue_net: number;
  accommodation_revenue_gross: number;
  fnb_revenue_gross: number;
  other_revenue_gross: number;
  adr_gross: number | null;
  adr_net: number | null;
  revpar: number | null;
  occupancy: number | null;
  room_nights: number;
  available_room_nights: number;
  arrivals: number;
  departures: number;
  cancellations: number;
  no_shows: number;
  currency: string | null;
  los: number | null;
  delta_revenue?: number | null;
  delta_adr?: number | null;
  delta_revpar?: number | null;
  delta_occupancy?: number | null;
}

export interface RevenueRow {
  account: string | null;
  number: string | null;
  net: number;
  gross: number;
  level: number;
}

export interface TravelPurpose {
  purpose: string | null;
  count: number | null;
  percent: number | null;
}

export interface YearOverview {
  year: number;
  ytd_revenue_gross: number;
  ytd_room_nights: number;
  ytd_arrivals: number;
  ytd_cancellations: number;
  ytd_revpar: number | null;
  ytd_adr: number | null;
  ytd_occupancy: number | null;
  ytd_los: number | null;
  otb_revenue_gross: number;
  otb_room_nights: number;
  otb_occupancy: number | null;
  otb_adr: number | null;
  forecast_revenue_gross: number;
  months: MonthEntry[];
}

export interface DashboardData {
  today: string;
  currency: string;
  selected_property: string;
  current_month: MonthEntry;
  previous_month: MonthEntry | null;
  timeline: MonthEntry[];
  revenue_breakdown: RevenueRow[];
  travel_purpose: TravelPurpose[];
  year_overview: YearOverview;
}
