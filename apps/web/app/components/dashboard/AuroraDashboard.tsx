"use client";

import { useState } from "react";
import type { DashboardBotStatus } from "./types";
import { AuroraSidebar } from "./AuroraSidebar";
import { AuroraTopHeader } from "./AuroraTopHeader";
import { AuroraMetrics } from "./AuroraMetrics";
import { AuroraChart } from "./AuroraChart";
import { AuroraBotCenter } from "./AuroraBotCenter";
import { AuroraCompounding } from "./AuroraCompounding";
import { AuroraAIAnalysis } from "./AuroraAIAnalysis";
import { AuroraWhale } from "./AuroraWhale";
import { AuroraPositions } from "./AuroraPositions";
import { AuroraSignalCards } from "./AuroraSignalCards";
import { AuroraFeatures } from "./AuroraFeatures";

export function AuroraDashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [botStatus, setBotStatus] = useState<DashboardBotStatus>("ACTIVE");
  const [risk, setRisk] = useState(72);

  return (
    <div className="min-h-screen bg-aizix-bg text-slate-100">
      <div className="pointer-events-none fixed inset-0 bg-aizix-radial-violet" />
      <div className="pointer-events-none fixed inset-0 bg-aizix-radial-cyan" />
      <div className="pointer-events-none fixed inset-0 bg-aurora-floor" />

      <div className="relative flex min-h-screen">
        <AuroraSidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <div className="flex min-w-0 flex-1 flex-col">
          <AuroraTopHeader
            onMenu={() => setSidebarOpen(true)}
            balance="12,540.25 USDT"
          />

          <div className="flex-1 space-y-8 overflow-y-auto px-4 py-6 sm:px-6 lg:space-y-10 lg:px-10 lg:py-8">
            <AuroraMetrics />

            <div className="grid gap-8 xl:grid-cols-12 xl:gap-10">
              <div className="flex min-w-0 flex-col gap-8 xl:col-span-8">
                <AuroraChart />
                <div className="grid gap-8 lg:grid-cols-2">
                  <AuroraBotCenter
                    status={botStatus}
                    onStatusChange={setBotStatus}
                    risk={risk}
                    onRiskChange={setRisk}
                  />
                  <AuroraCompounding />
                </div>
                <AuroraAIAnalysis />
                <AuroraWhale />
                <AuroraPositions />
              </div>

              <div className="flex min-w-0 flex-col gap-8 xl:col-span-4 xl:sticky xl:top-18 xl:self-start">
                <AuroraSignalCards />
              </div>
            </div>

            <AuroraFeatures />
          </div>
        </div>
      </div>
    </div>
  );
}
