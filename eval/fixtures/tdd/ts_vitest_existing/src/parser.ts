export function parse(input: string): Record<string, string> {
  const result: Record<string, string> = {};
  if (!input) return result;
  const pairs = input.split('&');
  for (const pair of pairs) {
    const [key, value] = pair.split('=');
    if (key) result[key] = value ?? '';
  }
  return result;
}
