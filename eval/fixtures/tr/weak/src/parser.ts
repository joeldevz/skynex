export function parse(input: string): Record<string, string> {
  const result: Record<string, string> = {};
  input.split('&').forEach(p => { const [k, v] = p.split('='); if (k) result[k] = v ?? ''; });
  return result;
}
