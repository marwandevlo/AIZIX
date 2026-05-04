const ROWS = [
  { pair: "BTC3L/USDT", side: "Long", size: "4,200", entry: "18.02", pnl: "+$412.30" },
  { pair: "ETH3L/USDT", side: "Long", size: "2,850", entry: "62.40", pnl: "+$198.12" },
  { pair: "SOL3S/USDT", side: "Short", size: "1,100", entry: "142.20", pnl: "+$76.45" },
  { pair: "DOGE5L/USDT", side: "Long", size: "9,500", entry: "0.184", pnl: "+$54.08" },
] as const;

export function AuroraPositions() {
  return (
    <section
      aria-label="Open positions"
      className="overflow-hidden rounded-2xl border border-white/10 bg-slate-950/55 shadow-2xl backdrop-blur-2xl"
    >
      <div className="border-b border-white/10 px-6 py-4">
        <h2 className="text-lg font-bold tracking-tight text-white">Open Positions</h2>
        <p className="mt-1 text-xs text-slate-500">Live sleeve exposure · Simulated book</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[32rem] text-left text-sm">
          <thead>
            <tr className="border-b border-white/10 text-aizix-micro font-bold uppercase tracking-widest text-slate-500">
              <th className="px-6 py-3">Pair</th>
              <th className="px-4 py-3">Side</th>
              <th className="px-4 py-3">Size</th>
              <th className="px-4 py-3">Entry</th>
              <th className="px-6 py-3 text-right">PnL</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {ROWS.map((r) => (
              <tr
                key={r.pair}
                className="font-mono text-slate-200 transition-colors hover:bg-white/5"
              >
                <td className="px-6 py-3.5 font-semibold text-cyan-100">{r.pair}</td>
                <td className="px-4 py-3.5">
                  <span
                    className={`rounded-md px-2 py-0.5 text-xs font-bold ${
                      r.side === "Long"
                        ? "border border-emerald-500/35 bg-emerald-500/15 text-emerald-300"
                        : "border border-rose-500/35 bg-rose-500/15 text-rose-300"
                    }`}
                  >
                    {r.side}
                  </span>
                </td>
                <td className="px-4 py-3.5">{r.size}</td>
                <td className="px-4 py-3.5 text-slate-400">{r.entry}</td>
                <td className="px-6 py-3.5 text-right font-semibold text-emerald-400">
                  {r.pnl}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
