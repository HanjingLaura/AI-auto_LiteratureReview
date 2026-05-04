export function trimTrailingFragment(text: string): string {
  if (!text) return text;
  const trimmed = text.trim();
  if (!trimmed) return trimmed;
  const lastChar = trimmed[trimmed.length - 1];
  if (/[。.!?！？]$/.test(lastChar)) return trimmed;
  const lastStop = Math.max(
    trimmed.lastIndexOf("。"),
    trimmed.lastIndexOf("."),
    trimmed.lastIndexOf("!"),
    trimmed.lastIndexOf("?"),
    trimmed.lastIndexOf("！"),
    trimmed.lastIndexOf("？")
  );
  if (lastStop > 0) return trimmed.slice(0, lastStop + 1);
  return trimmed;
}

export function downloadText(filename: string, content: string, type = "text/plain"): void {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
