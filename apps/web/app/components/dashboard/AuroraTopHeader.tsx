"use client";

type Props = {
  onMenu: () => void;
  balance: string;
};

export function AuroraTopHeader({ onMenu, balance }: Props) {
  return (
    <header className="sticky top-0 z-20 border-b border-violet-500/20 bg-slate-950/55 shadow-aurora-header backdrop-blur-2xl">
      <div className="flex flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <button
            type="button"
            onClick={onMenu}
            className="shrink-0 rounded-xl border border-white/10 bg-white/5 p-2.5 text-slate-300 hover:border-cyan-500/30 hover:bg-white/10 lg:hidden"
            aria-label="Open navigation"
          >
            <span className="flex size-5 flex-col justify-center gap-1">
              <span className="h-0.5 rounded-full bg-current" />
              <span className="h-0.5 rounded-full bg-current" />
              <span className="h-0.5 rounded-full bg-current" />
            </span>
          </button>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2 sm:gap-3">
              <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/35 bg-emerald-500/10 px-3 py-1 text-xs font-bold uppercase tracking-wide text-emerald-300 shadow-aizix-status-emerald">
                <span className="relative flex size-2">
                  <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                  <span className="relative size-2 rounded-full bg-emerald-400 shadow-aizix-dot-emerald" />
                </span>
                Bot Status: ACTIVE
              </span>
              <span className="hidden text-slate-500 sm:inline">·</span>
              <p className="truncate text-sm text-cyan-200/90 sm:max-w-md">
                AI is analyzing the market 24/7
              </p>
            </div>
          </div>
        </div>

        <div className="flex w-full flex-wrap items-center justify-end gap-3 sm:w-auto">
          <div className="rounded-2xl border border-white/10 bg-slate-900/60 px-4 py-2.5 text-right shadow-aurora-inset-top">
            <p className="text-aizix-micro font-bold uppercase tracking-widest text-slate-500">
              Main account
            </p>
            <p className="font-mono text-lg font-semibold tracking-tight text-white sm:text-xl">
              {balance}
            </p>
          </div>
          <button
            type="button"
            className="rounded-xl border border-cyan-400/40 bg-linear-to-r from-violet-600 to-cyan-500 px-5 py-2.5 text-sm font-bold uppercase tracking-wide text-white shadow-aizix-cta transition-all hover:shadow-aurora-cta-hover"
          >
            Deposit
          </button>
        </div>
      </div>
    </header>
  );
}
