export function PageIntro({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-4 rounded-xl border border-noc-border/80 bg-noc-panel/60 px-4 py-3">
      <h2 className="text-lg font-semibold text-white">{title}</h2>
      <p className="mt-1 text-sm leading-relaxed text-noc-muted">{description}</p>
    </div>
  );
}
