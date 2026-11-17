import { env } from "../env";

import type { Bootstrap, DashboardData } from "./types";

const baseUrl = env.VITE_API_URL.replace(/\/+$/u, "");

class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${baseUrl}/api${path}`, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    const detail = await response.json().catch(() => undefined);
    const message =
      detail && typeof detail === "object" && "detail" in detail && typeof detail.detail === "string"
        ? detail.detail
        : `HTTP ${response.status}`;
    throw new ApiError(message, response.status);
  }
  return (await response.json()) as T;
}

export const fetchBootstrap = () => getJson<Bootstrap>("/dashboard/bootstrap");

export const fetchDashboard = (property: string, pastMonths: number, futureMonths: number) =>
  getJson<DashboardData>(
    `/dashboard?property=${encodeURIComponent(property)}&past_months=${pastMonths}&future_months=${futureMonths}`,
  );
