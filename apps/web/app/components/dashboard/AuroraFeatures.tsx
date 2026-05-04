const FEATURES = [
  "AI Powered",
  "24/7 Monitoring",
  "Risk Protection",
  "Lightning Fast",
  "Secure & Private",
  "Multi-Exchange",
] as const;

export function AuroraFeatures() {
  return (
    <section
      aria-label="Platform features"
      className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6"
    >
      {FEATURES.map((f) => (
        <div
          key={f}
          className="rounded-2xl border border-white/10 bg-slate-950/40 px-3 py-4 text-center shadow-aurora-inset-top backdrop-blur-xl transition-transform hover:-translate-y-0.5 hover:border-cyan-500/25 hover:shadow-aurora-feature-hover"
        >
          <p className="text-xs font-bold uppercase tracking-wide text-slate-200 sm:text-sm">
            {f}
          </p>
        </div>
      ))}
    </section>
  );
}
