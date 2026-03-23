export function abbreviateCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

export function formatTick(value: number): string {
  return abbreviateCount(value);
}

export function rollingAverage(data: { value: number }[], window: number): { value: number }[] {
  return data.map((_, i, arr) => {
    const start = Math.max(0, i - window + 1);
    const slice = arr.slice(start, i + 1);
    const avg = slice.reduce((sum, d) => sum + d.value, 0) / slice.length;
    return { value: Math.round(avg * 100) / 100 };
  });
}
