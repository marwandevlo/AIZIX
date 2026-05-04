"use client";

import type { ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";
import type { BotStatusPayload, SignalsPayload } from "@/lib/aizix-api";
import { fetchBotStatus, fetchSignals } from "@/lib/aizix-api";
import { SignalFeed } from "./SignalFeed";
import { BotControlPanel } from "./BotControlPanel";
import { LiveMetricsCards } from "./LiveMetricsCards";

function jitter(min: number, max: number) {
  return min + Math.floor(Math.random() * (max - min + 1));
}

type Props = {
  children?: ReactNode;
};

export function DashboardLive({ children }: Props) {
  const [status, setStatus] = useState<BotStatusPayload | null>(null);
  const [signals, setSignals] = useState<SignalsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pulse, setPulse] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const [s, sig] = await Promise.all([fetchBotStatus(), fetchSignals()]);
      setStatus(s);
      setSignals(sig);
      setPulse(true);
      setTimeout(() => setPulse(false), 380);
    } catch (e) {
      setError(e instanceof Error ? e.message : "API unreachable");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    let t: ReturnType<typeof setTimeout>;

    const loop = async () => {
      if (cancelled) return;
      await refresh();
      t = setTimeout(loop, jitter(5_000, 8_500));
    };
    void loop();
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [refresh]);

  return (
    <div className="flex flex-col gap-8 lg:gap-10">
      <LiveMetricsCards status={status} signals={signals} error={error} />

      <div className="aizix-signals-grid">
        <div className="flex min-w-0 flex-col gap-6">
          {children}
          <BotControlPanel
            status={status?.status ?? "STOPPED"}
            compoundingEnabled={status?.compounding_enabled ?? true}
            balances={status?.balances ?? null}
            onRemoteChange={refresh}
          />
        </div>
        <div className="min-w-0">
          <SignalFeed signals={signals} pulse={pulse} error={error} />
        </div>
      </div>
    </div>
  );
}
