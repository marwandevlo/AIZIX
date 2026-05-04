export const getApiBaseUrl = (): string =>
  (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export type BotStatus = "ACTIVE" | "PAUSED" | "STOPPED";

export type Balances = {
  trading_balance: number;
  safety_balance: number;
  total: number;
};

export type BotStatusPayload = {
  status: BotStatus;
  compounding_enabled: boolean;
  balances: Balances;
  win_rate_pct: number;
  daily_pnl_usd: number;
};

export type WhaleActivity = {
  net_flow_usd: number;
  large_wallet_moves: number;
  narrative: string;
};

export type SignalPayload = {
  action: "BUY" | "SELL" | "HOLD";
  symbol: string;
  etf_symbol: string;
  confidence_pct: number;
  market_mood: string;
  reason: string;
  risk_status: string;
  etf_bias: string;
  whale_activity: WhaleActivity;
  prices: Record<string, number>;
  latency_ms: number;
  market?: Record<string, unknown> | null;
};

export type SignalsPayload = {
  latest: SignalPayload;
  history: SignalPayload[];
};

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export async function fetchBotStatus(): Promise<BotStatusPayload> {
  const res = await fetch(`${getApiBaseUrl()}/bot/status`, {
    cache: "no-store",
  });
  return parseJson<BotStatusPayload>(res);
}

export async function fetchSignals(): Promise<SignalsPayload> {
  const res = await fetch(`${getApiBaseUrl()}/signals`, {
    cache: "no-store",
  });
  return parseJson<SignalsPayload>(res);
}

export type BotActionResponse = {
  ok: boolean;
  status: BotStatus;
  message: string;
};

export async function postBotStart(): Promise<BotActionResponse> {
  const res = await fetch(`${getApiBaseUrl()}/bot/start`, { method: "POST" });
  return parseJson<BotActionResponse>(res);
}

export async function postBotPause(): Promise<BotActionResponse> {
  const res = await fetch(`${getApiBaseUrl()}/bot/pause`, { method: "POST" });
  return parseJson<BotActionResponse>(res);
}

export async function postBotStop(): Promise<BotActionResponse> {
  const res = await fetch(`${getApiBaseUrl()}/bot/stop`, { method: "POST" });
  return parseJson<BotActionResponse>(res);
}

export async function postCompounding(
  enabled: boolean,
): Promise<BotStatusPayload> {
  const res = await fetch(`${getApiBaseUrl()}/bot/compounding`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  return parseJson<BotStatusPayload>(res);
}

export function formatUsd(n: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: n >= 100 ? 0 : 2,
  }).format(n);
}
