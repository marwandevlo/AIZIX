"use client";

import type { ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";
import type { BotStatusPayload, SignalsPayload } from "@/lib/aizix-api";
import { fetchBotStatus, fetchSignals, postBotStart } from "@/lib/aizix-api";
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
  const [ctaBusy, setCtaBusy] = useState(false);

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

  const mood = signals?.latest.market_mood ?? "—";

  async function onHeroStart() {
    setCtaBusy(true);
    try {
      await postBotStart();
      await refresh();
    } catch {
      /* surfaced via next refresh error state */
      await refresh();
    } finally {
      setCtaBusy(false);
    }
  }

  return (
    <>
      <LiveMetricsCards status={status} mood={mood} error={error} />
      <SignalFeed signals={signals} pulse={pulse} error={error} />
      {children}
      <BotControlPanel
        status={status?.status ?? "STOPPED"}
        compoundingEnabled={status?.compounding_enabled ?? true}
        balances={status?.balances ?? null}
        onRemoteChange={refresh}
      />
      <div className="flex justify-center pb-8 sm:justify-start">
        <button
          type="button"
          disabled={ctaBusy}
          onClick={() => void onHeroStart()}
          className="group relative w-full overflow-hidden rounded-2xl border border-cyan-400/30 bg-linear-to-r from-violet-600 via-blue-600 to-cyan-500 px-10 py-5 text-lg font-semibold tracking-wide text-white shadow-aizix-cta transition-all duration-300 hover:shadow-aizix-cta-hover disabled:opacity-60 sm:w-auto sm:min-w-70"
        >
          <span className="absolute inset-0 bg-linear-to-r from-white/0 via-white/10 to-white/0 opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
          <span className="relative">{ctaBusy ? "Arming…" : "Start Trading"}</span>
        </button>
      </div>
    </>
  );
}
